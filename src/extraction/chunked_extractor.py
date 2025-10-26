"""Chunked LLM extraction for better performance and accuracy."""

from typing import List, Dict, Any
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .llm_extractor import LLMExtractor
from ..models import MOVReport, QuestionResponse, SiteInfo, RecruitmentStats, ActionItem, RiskAssessment, VisitType, AnswerType, SentimentType, DataQualityFlags

logger = logging.getLogger(__name__)


class ChunkedExtractor(LLMExtractor):
    """Chunked extraction for parallel processing."""

    def extract_report_chunked(
        self,
        pdf_text: str,
        source_file: str,
        temperature: float = 0.0
    ) -> MOVReport:
        """
        Extract MOV report using chunked parallel extraction.

        Args:
            pdf_text: Full PDF text
            source_file: Source filename
            temperature: LLM temperature

        Returns:
            Complete MOVReport
        """
        logger.info(f"Starting chunked extraction for {source_file}")

        # Extract header/metadata sequentially (fast, small)
        logger.info("Extracting header and metadata...")
        header_data = self._extract_header(pdf_text, temperature)

        # Extract questions in parallel batches
        logger.info("Extracting questions in parallel batches...")
        questions = self._extract_questions_parallel(pdf_text, temperature)

        # Extract action items and assessment in parallel
        logger.info("Extracting action items and assessment...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            action_future = executor.submit(self._extract_action_items, pdf_text, temperature)
            assessment_future = executor.submit(self._extract_assessment, pdf_text, temperature)

            action_items = action_future.result()
            assessment_data = assessment_future.result()

        # Assemble final report
        logger.info(f"Assembling report: {len(questions)} questions, {len(action_items)} action items")

        # Track data quality
        fields_missing = []
        fields_invalid = []

        # Handle optional visit_type
        visit_type_value = None
        if header_data.get("visit_type"):
            try:
                visit_type_value = VisitType(header_data["visit_type"])
            except (ValueError, KeyError):
                fields_invalid.append("visit_type")
                logger.warning(f"Invalid visit_type: {header_data.get('visit_type')}")
        else:
            fields_missing.append("visit_type")

        # Handle optional visit dates
        if not header_data.get("visit_start_date"):
            fields_missing.append("visit_start_date")
            logger.warning("visit_start_date not extracted")

        if not header_data.get("visit_end_date"):
            fields_missing.append("visit_end_date")
            logger.warning("visit_end_date not extracted")

        # Calculate completeness score
        expected_fields = ["visit_type", "visit_start_date", "visit_end_date", "overall_site_quality"]
        total_fields = len(expected_fields) + 85  # 85 questions expected
        missing_count = len(fields_missing) + (85 - len(questions))
        completeness = max(0.0, 1.0 - (missing_count / total_fields))

        # Determine if review is needed
        requires_review = (
            len(questions) < 70 or  # Less than 70 questions
            visit_type_value is None or  # Missing visit type
            not header_data.get("visit_start_date") or  # Missing start date
            not header_data.get("visit_end_date") or  # Missing end date
            len(fields_invalid) > 0  # Invalid data found
        )

        review_reasons = []
        if len(questions) < 70:
            review_reasons.append(f"Only {len(questions)}/85 questions extracted")
        if visit_type_value is None:
            review_reasons.append("Visit type not specified")
        if not header_data.get("visit_start_date"):
            review_reasons.append("Visit start date missing")
        if not header_data.get("visit_end_date"):
            review_reasons.append("Visit end date missing")
        if fields_invalid:
            review_reasons.append(f"Invalid fields: {', '.join(fields_invalid)}")

        data_quality = DataQualityFlags(
            fields_missing=fields_missing,
            fields_invalid=fields_invalid,
            completeness_score=round(completeness, 3),
            requires_review=requires_review,
            review_reason="; ".join(review_reasons) if review_reasons else None
        )

        # Fallback: Extract site_number from filename if missing from document
        site_info_data = header_data["site_info"]
        if not site_info_data.get("site_number"):
            # Try to extract from filename (e.g., "Wang_812409_20250402.docx" -> "812409")
            import re
            filename_match = re.search(r'_(\d{6})_', source_file)
            if filename_match:
                site_info_data["site_number"] = filename_match.group(1)
                logger.warning(f"site_number extracted from filename: {site_info_data['site_number']}")
                fields_missing.append("site_number (extracted from filename)")
            else:
                logger.error(f"site_number not found in document or filename: {source_file}")
                # Set a placeholder to avoid validation error
                site_info_data["site_number"] = "000000"
                fields_missing.append("site_number")

        report = MOVReport(
            protocol_number=header_data["protocol_number"],
            site_info=SiteInfo(**site_info_data),
            visit_start_date=header_data["visit_start_date"],
            visit_end_date=header_data["visit_end_date"],
            visit_type=visit_type_value,
            recruitment_stats=RecruitmentStats(**header_data["recruitment_stats"]),
            question_responses=questions,
            action_items=action_items,
            risk_assessment=RiskAssessment(**assessment_data["risk_assessment"]),
            overall_site_quality=assessment_data.get("overall_site_quality"),
            key_concerns=assessment_data.get("key_concerns", []),
            key_strengths=assessment_data.get("key_strengths", []),
            data_quality=data_quality,
            source_file=source_file,
            extraction_timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            llm_model=self.deployment,
            extraction_method="chunked_parallel"
        )

        return report

    def _extract_header(self, pdf_text: str, temperature: float) -> Dict[str, Any]:
        """Extract header information (site info, dates, recruitment stats)."""
        # Take first ~20% of document to ensure we capture header and recruitment stats
        # Also take last ~5% for signature dates (some documents have visit dates at the end)
        header_text = pdf_text[:int(len(pdf_text) * 0.20)]
        footer_text = pdf_text[int(len(pdf_text) * 0.95):]
        combined_text = header_text + "\n\n--- END OF DOCUMENT SIGNATURE SECTION ---\n\n" + footer_text

        prompt = f"""Extract the header information from this MOV report.

**TEXT:**
{combined_text}

**EXTRACT:**
- Protocol number (format: "Protocol ANT-XXX" or "Protocol STUDY-NAME", if not found, use "Protocol UNKNOWN")
- Site number (6 digits, if available, otherwise null)
- Country
- Institution
- PI first and last name
- City (if available, otherwise null)
- ANTHOS Staff (Clinical Oversight Manager)
- CRA name (if available, otherwise null)
- Visit start and end dates (YYYY-MM-DD format, if available, otherwise null)
  Note: Some documents have the visit/report date at the end in a signature section. Check both header and signature section.
- Visit type (SIV MOV, IMV MOV, or COV MOV, if available, otherwise null)
- Recruitment statistics:
  - # screened
  - # screen failures
  - # randomized/enrolled
  - # early discontinued
  - # completed treatment
  - # completed study

Note: Some documents use "Protocol Short Title" instead of "Protocol number". Extract whatever is available.

Return ONLY valid JSON in this exact format (use null for missing optional fields):
{{
  "protocol_number": "Protocol ANT-XXX" or "Protocol MAGNOLIA" or "Protocol UNKNOWN",
  "site_info": {{
    "site_number": "123456" or null,
    "country": "...",
    "institution": "...",
    "pi_first_name": "...",
    "pi_last_name": "...",
    "city": "..." or null,
    "anthos_staff": "...",
    "cra_name": "..." or null
  }},
  "visit_start_date": "YYYY-MM-DD" or null,
  "visit_end_date": "YYYY-MM-DD" or null,
  "visit_type": "IMV MOV" or null,
  "recruitment_stats": {{
    "screened": 0,
    "screen_failures": 0,
    "randomized_enrolled": 0,
    "early_discontinued": 0,
    "completed_treatment": 0,
    "completed_study": 0
  }}
}}"""

        response = self._call_llm(prompt, temperature)
        return json.loads(response)

    def _extract_questions_parallel(self, pdf_text: str, temperature: float) -> List[QuestionResponse]:
        """Extract questions 1-85 in parallel batches."""
        # Split into batches of ~15 questions each (6 batches total)
        batches = [
            (1, 15),
            (16, 30),
            (31, 45),
            (46, 60),
            (61, 75),
            (76, 85)
        ]

        all_questions = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._extract_question_batch, pdf_text, start, end, temperature): (start, end)
                for start, end in batches
            }

            for future in as_completed(futures):
                start, end = futures[future]
                try:
                    questions = future.result()
                    logger.info(f"Extracted questions {start}-{end}: {len(questions)} questions")
                    all_questions.extend(questions)
                except Exception as e:
                    logger.error(f"Failed to extract questions {start}-{end}: {e}")

        # Sort by question number
        all_questions.sort(key=lambda q: q.question_number)
        return all_questions

    def _extract_question_batch(
        self,
        pdf_text: str,
        start_q: int,
        end_q: int,
        temperature: float
    ) -> List[QuestionResponse]:
        """Extract a batch of questions."""
        prompt = f"""Extract questions {start_q} through {end_q} from this MOV report.

**FULL REPORT TEXT:**
{pdf_text}

**INSTRUCTIONS:**
Extract ONLY questions numbered {start_q} to {end_q} (inclusive).
For each question, extract:
- question_number: The number ({start_q}-{end_q})
- question_text: Full question text
- answer: One of: "Yes", "No", "N/A", "NR"
- sentiment: Based on question context
  - "Positive" = good outcome (compliant, no issues)
  - "Negative" = bad outcome (non-compliant, issues found)
  - "Neutral" = neither good nor bad (N/A or informational)
  - "Unknown" = cannot determine (NR)
- narrative_summary: 2-3 sentence summary if narrative exists, otherwise null
- key_finding: One-liner if critical finding, otherwise null
- evidence: Short quote from text, otherwise null
- confidence: 0.0-1.0

**SENTIMENT EXAMPLES:**
- Q: "Were all ICFs signed?" Answer: "Yes" → Sentiment: "Positive"
- Q: "Were any protocol deviations found?" Answer: "Yes" → Sentiment: "Negative"
- Q: "Were any protocol deviations found?" Answer: "No" → Sentiment: "Positive"

If a question is not found in the text, still include it with answer "NR" and sentiment "Unknown".

Return ONLY valid JSON array:
[
  {{"question_number": {start_q}, "question_text": "...", "answer": "Yes", "sentiment": "Positive", "narrative_summary": null, "key_finding": null, "evidence": null, "confidence": 1.0}},
  ...
  {{"question_number": {end_q}, "question_text": "...", "answer": "No", "sentiment": "Negative", "narrative_summary": "...", "key_finding": "...", "evidence": "...", "confidence": 0.9}}
]

CRITICAL: You MUST return {end_q - start_q + 1} question objects in the array.

Wrap the array in a JSON object:
{{
  "questions": [...]
}}"""

        response = self._call_llm(prompt, temperature)
        result = json.loads(response)

        # Handle both formats
        questions_data = result if isinstance(result, list) else result.get("questions", [])

        return [
            QuestionResponse(
                question_number=q["question_number"],
                question_text=q["question_text"],
                answer=AnswerType(q["answer"]),
                sentiment=SentimentType(q["sentiment"]),
                narrative_summary=q.get("narrative_summary"),
                key_finding=q.get("key_finding"),
                evidence=q.get("evidence"),
                confidence=q.get("confidence", 1.0)
            )
            for q in questions_data
        ]

    def _extract_action_items(self, pdf_text: str, temperature: float) -> List[ActionItem]:
        """Extract action items table."""
        # Action items can appear anywhere - search full document
        # But limit to reasonable size to avoid token limits
        search_text = pdf_text if len(pdf_text) < 150000 else pdf_text[:150000]

        prompt = f"""Search this entire MOV report for the Action Items table. It may appear early (page 3) or late (page 25+) in the document.

Look for section headers like:
- "Action Items"
- "Issues identified/ Action items"
- A table with columns: Item #, Description, Action to be taken, Responsible, Due date

**FULL DOCUMENT TEXT:**
{search_text}

**EXTRACT:**
For each action item:
- item_number
- description
- action_to_be_taken
- responsible (person/role)
- due_date (as string)
- status (if available)

Return ONLY valid JSON with this structure:
{{
  "action_items": [
    {{"item_number": 1, "description": "...", "action_to_be_taken": "...", "responsible": "...", "due_date": "...", "status": "..."}}
  ]
}}

If no action items found, return: {{"action_items": []}}"""

        response = self._call_llm(prompt, temperature)
        result = json.loads(response)

        # Handle both formats: direct array or nested in "action_items"
        items_data = result if isinstance(result, list) else result.get("action_items", [])

        return [ActionItem(**item) for item in items_data]

    def _extract_assessment(self, pdf_text: str, temperature: float) -> Dict[str, Any]:
        """Extract risk assessment and overall quality."""
        # Risk assessment typically in last 30%, but search broader range to be safe
        assessment_text = pdf_text[int(len(pdf_text) * 0.60):]

        prompt = f"""Search for the Visit Summary and Risk Assessment section in this MOV report.

Look for section headers like:
- "VISIT SUMMARY WITH IMPACT/RISK LEVEL"
- "Visit Summary"
- Questions 84-85 (final summary questions)

**TEXT (Last 40% of document):**
{assessment_text}

**EXTRACT:**
- Risk assessment:
  - site_level_risks_identified (boolean)
  - cra_level_risks_identified (boolean)
  - impact_country_level (boolean)
  - impact_study_level (boolean)
  - narrative (text summary)
- overall_site_quality: One of: "Excellent", "Good", "Adequate", "Needs Improvement", "Poor"
- key_concerns: Array of 3-5 main concerns
- key_strengths: Array of 3-5 main strengths

Return ONLY valid JSON:
{{
  "risk_assessment": {{
    "site_level_risks_identified": false,
    "cra_level_risks_identified": false,
    "impact_country_level": false,
    "impact_study_level": false,
    "narrative": "..."
  }},
  "overall_site_quality": "Good",
  "key_concerns": ["...", "..."],
  "key_strengths": ["...", "..."]
}}"""

        response = self._call_llm(prompt, temperature)
        return json.loads(response)

    def _call_llm(self, prompt: str, temperature: float) -> str:
        """Make a single LLM call and return the text response."""
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise data extraction assistant. Extract ONLY the requested information and return valid JSON. Do not add explanatory text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )

        return response.choices[0].message.content
