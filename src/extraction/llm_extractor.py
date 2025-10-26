"""Azure OpenAI integration for MOV report extraction."""

from azure.identity import DefaultAzureCredential, AzureCliCredential
from openai import AzureOpenAI
from typing import Optional, List, Dict, Any
import json
import logging
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

from ..models import MOVReport, QuestionResponse, SiteInfo, RecruitmentStats, ActionItem, RiskAssessment, VisitType
from ..config import config

logger = logging.getLogger(__name__)


class LLMExtractor:
    """Extract structured MOV data using Azure OpenAI."""

    def __init__(self):
        """Initialize with Azure credentials."""
        self.credential = self._get_credential()
        self.client = self._initialize_client()
        self.deployment = config.AZURE_OPENAI_DEPLOYMENT

    def _get_credential(self):
        """Get Azure credential (CLI for local, Managed Identity for cloud)."""
        # Check if API key is available
        if config.AZURE_OPENAI_API_KEY:
            logger.info("Using API key authentication")
            return None  # Will use API key directly

        try:
            # Try Azure CLI first (local development)
            credential = AzureCliCredential()
            # Test credential
            credential.get_token("https://cognitiveservices.azure.com/.default")
            logger.info("Using Azure CLI credentials")
            return credential
        except Exception as e:
            logger.warning(f"Azure CLI auth failed: {e}")
            # Fallback to DefaultAzureCredential (works in cloud)
            logger.info("Falling back to DefaultAzureCredential")
            return DefaultAzureCredential()

    def _initialize_client(self) -> AzureOpenAI:
        """Initialize Azure OpenAI client."""
        if config.AZURE_OPENAI_API_KEY:
            # Use API key authentication
            return AzureOpenAI(
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
                api_key=config.AZURE_OPENAI_API_KEY,
                api_version=config.AZURE_OPENAI_API_VERSION
            )
        else:
            # Use Azure AD token authentication
            return AzureOpenAI(
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
                api_version=config.AZURE_OPENAI_API_VERSION,
                azure_ad_token_provider=lambda: self.credential.get_token(
                    "https://cognitiveservices.azure.com/.default"
                ).token
            )

    def extract_report(
        self,
        pdf_text: str,
        source_file: str,
        temperature: float = 0.0,
        max_tokens: int = None
    ) -> MOVReport:
        """
        Extract MOV report data using LLM.

        Args:
            pdf_text: Extracted PDF text
            source_file: Source PDF filename
            temperature: LLM temperature (0 = deterministic)
            max_tokens: Maximum response tokens

        Returns:
            Validated MOVReport object
        """
        logger.info(f"Extracting data from {source_file}")

        # Generate extraction prompt
        prompt = self._build_extraction_prompt(pdf_text)

        # Call Azure OpenAI
        try:
            # Build completion parameters
            completion_params = {
                "model": self.deployment,
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "response_format": {"type": "json_object"}  # Force JSON output
            }

            # Only add max_tokens if specified
            if max_tokens is not None:
                completion_params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**completion_params)

            # Parse and validate response
            result_text = response.choices[0].message.content

            # Log token usage and response stats
            finish_reason = response.choices[0].finish_reason
            logger.info(
                f"LLM Response: {response.usage.total_tokens} tokens "
                f"(prompt: {response.usage.prompt_tokens}, "
                f"completion: {response.usage.completion_tokens})"
            )
            logger.info(f"Response length: {len(result_text)} characters")
            logger.info(f"Finish reason: {finish_reason}")

            if finish_reason == "length":
                logger.warning("Response was truncated due to length limit!")
            elif finish_reason != "stop":
                logger.warning(f"Unexpected finish reason: {finish_reason}")

            result_json = json.loads(result_text)

            # Log what we got before validation
            questions_count = len(result_json.get("question_responses", []))
            logger.info(f"Parsed JSON: {questions_count} questions found in response")

            # Save response for debugging
            debug_file = Path(config.OUTPUT_PATH) / f"debug_llm_response_{source_file}.json"
            debug_file.write_text(json.dumps(result_json, indent=2))
            logger.info(f"Saved LLM response to {debug_file} for debugging")

            # Add metadata
            result_json["source_file"] = source_file

            # Validate with Pydantic
            report = MOVReport(**result_json)

            logger.info(
                f"Extraction successful: {len(report.question_responses)} questions, "
                f"{len(report.action_items)} action items"
            )

            return report

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

    def _get_system_prompt(self) -> str:
        """Get system prompt for extraction."""
        return """You are extracting structured data from a Monitoring Oversight Visit (MOV) report for a clinical trial.

**CRITICAL INSTRUCTIONS:**
1. Extract ALL data exactly as it appears in the report
2. EXTRACT ALL 85 QUESTIONS - The report contains questions numbered 1-85. You MUST extract EVERY SINGLE ONE.
3. For Yes/No questions, look for checkbox symbols (☒ vs ☐)
4. If a question exists but is marked N/A, extract it with answer "N/A" - DO NOT SKIP IT
5. If you genuinely cannot find a specific question in the text, set answer to "NR" (Not Reported) - but still include it
6. For dates, extract in YYYY-MM-DD format
7. For narrative summaries, condense to 2-3 sentences maximum
8. Return ONLY valid JSON matching the schema
9. Do NOT invent or hallucinate data - if you cannot find information, set it to null or "NR"

**ANSWER VALUES:**
- "Yes" - Question answered affirmatively with checkbox ☒ or explicit "Yes"
- "No" - Question answered negatively with checkbox ☐ or explicit "No"
- "N/A" - Question is marked as Not Applicable (still extract it!)
- "NR" - Question not found in the document (Not Reported)

**SENTIMENT ASSESSMENT:**
For each question, determine the sentiment based on the QUESTION CONTEXT, not just the answer:
- "Positive" - Good outcome (e.g., "Were all procedures followed?" → Yes = Positive, No = Negative)
- "Negative" - Bad outcome (e.g., "Were any protocol deviations found?" → Yes = Negative, No = Positive)
- "Neutral" - Neither good nor bad (informational questions, or N/A answers)
- "Unknown" - Cannot determine sentiment (NR answers or unclear context)

**EXAMPLES:**
- Q: "Were all ICFs signed and dated?" Answer: "Yes" → Sentiment: "Positive" (compliance good)
- Q: "Were any SAEs not reported within 24h?" Answer: "Yes" → Sentiment: "Negative" (compliance issue)
- Q: "Were any SAEs not reported within 24h?" Answer: "No" → Sentiment: "Positive" (no issues)
- Q: "How many subjects were screened?" Answer: "15" → Sentiment: "Neutral" (informational)

**CRITICAL:** You MUST extract ALL 85 questions (numbered 1-85). If you see a question marked N/A, include it. Do not stop at 10, 20, or 74. Extract ALL 85.
"""

    def _build_extraction_prompt(self, pdf_text: str) -> str:
        """Build extraction prompt with simplified schema."""
        # Don't send the full JSON schema - it's too large and confuses the model
        # Instead, give a clear example structure

        example_structure = {
            "protocol_number": "Protocol ANT-XXX",
            "site_info": {"site_number": "123456", "country": "...", "institution": "...", "pi_first_name": "...", "pi_last_name": "...", "anthos_staff": "...", "cra_name": "..."},
            "visit_start_date": "YYYY-MM-DD",
            "visit_end_date": "YYYY-MM-DD",
            "visit_type": "IMV MOV or SIV MOV or COV MOV",
            "recruitment_stats": {"screened": 0, "screen_failures": 0, "randomized_enrolled": 0, "early_discontinued": 0, "completed_treatment": 0, "completed_study": 0},
            "question_responses": [
                {"question_number": 1, "question_text": "...", "answer": "Yes/No/N/A/NR", "sentiment": "Positive/Negative/Neutral/Unknown", "narrative_summary": "...", "key_finding": "...", "evidence": "...", "confidence": 1.0},
                {"question_number": 2, "question_text": "...", "answer": "Yes/No/N/A/NR", "sentiment": "Positive/Negative/Neutral/Unknown", "narrative_summary": "...", "key_finding": "...", "evidence": "...", "confidence": 1.0},
                "... continue for ALL 85 questions (3, 4, 5, ... 84, 85). YOU MUST INCLUDE ALL 85 QUESTIONS IN THE ARRAY!"
            ],
            "action_items": [{"item_number": 1, "description": "...", "action_to_be_taken": "...", "responsible": "...", "due_date": "..."}],
            "risk_assessment": {"site_level_risks_identified": False, "cra_level_risks_identified": False, "impact_country_level": False, "impact_study_level": False, "narrative": "..."},
            "overall_site_quality": "Excellent/Good/Adequate/Needs Improvement/Poor",
            "key_concerns": ["...", "..."],
            "key_strengths": ["...", "..."]
        }

        return f"""Extract ALL structured data from this MOV report.

**REPORT TEXT:**
{pdf_text}

**OUTPUT FORMAT (JSON):**
{json.dumps(example_structure, indent=2)}

**IMPORTANT SECTIONS TO EXTRACT:**

1. **HEADER (Page 1):**
   - Protocol Number (format: "Protocol ANT-XXX")
   - Site Number (6-digit)
   - Country
   - Principal Investigator name
   - Visit dates (convert to YYYY-MM-DD)
   - ANTHOS Staff (Clinical Oversight Manager)
   - CRA name
   - Visit Type (SIV MOV, IMV MOV, or COV MOV)

2. **RECRUITMENT STATISTICS (Pages 1-2):**
   - # screened
   - # screen failures
   - # randomized enrolled
   - # early discontinued
   - # completed treatment
   - # completed study

3. **QUESTIONS (Pages 2-34):**
   - **CRITICAL:** Extract ALL 85 questions numbered 1-85 from the report
   - Go through the entire report page by page to find every question
   - For each question: question number, text, answer (Yes/No/N/A/NR)
   - If a question is marked N/A, extract it with answer "N/A" - don't skip it
   - If you can't find a question, include it anyway with answer "NR" and note you couldn't find it
   - Summarize narrative in 2-3 sentences if present
   - Flag critical findings
   - **YOUR GOAL: Extract all 85 questions. Count them as you go: 1, 2, 3... up to 85**

4. **ACTION ITEMS TABLE (Pages 35-39):**
   - Item number
   - Description
   - Action to be taken
   - Responsible party
   - Due date

5. **RISK ASSESSMENT (Page 34):**
   - Site-level risks (boolean)
   - CRA-level risks (boolean)
   - Impact levels (boolean)
   - Narrative summary

6. **OVERALL ASSESSMENT:**
   - Site quality rating (Excellent/Good/Adequate/Needs Improvement/Poor)
   - Top 3-5 key concerns
   - Top 3-5 key strengths

**CRITICAL REMINDER BEFORE YOU START:**
The question_responses array MUST contain 70-85 question objects. If you return fewer than 70 questions, the system will reject your response.
Take your time and extract EVERY SINGLE QUESTION from 1 to 85. This is the most important part of the extraction.

Return structured JSON ONLY. No additional text."""
