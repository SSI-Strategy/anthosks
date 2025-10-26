# Implementation Plan: MOV Report Extraction System
## Local Development with Azure OpenAI Integration

**Project:** AnthosKS - Automated MOV Report Extraction
**Date:** 2025-10-23
**Approach:** LLM-First extraction using Azure OpenAI (gpt-5-chat)
**Scope:** Local development with cloud-deployment-ready architecture

---

## Executive Summary

Build a local Python application that extracts structured data from 41-page MOV (Monitoring Oversight Visit) clinical trial reports using Azure OpenAI's `gpt-5-chat-deployment`. The system will use Azure CLI delegated credentials for authentication (no API keys), maintain a clean separation of concerns, and be architected for future cloud deployment while remaining fully functional locally.

---

## Architecture Principles

### 1. **Cloud-Native Design, Local Execution**
- Use Azure SDK patterns that work identically locally and in cloud
- Leverage `DefaultAzureCredential` for seamless authentication
- Store configuration in environment variables (`.env` file locally, App Settings in cloud)
- Design for horizontal scaling (stateless processing)

### 2. **Dependency on Shared Resources ONLY**
- **Azure OpenAI:** `oai-shared-se-01-p` in `rg-shared_resources-se-01-p`
  - Deployment: `gpt-5-chat-deployment`
  - Model: `gpt-5-chat` (version 2025-08-07)
- **No other Azure resources** during local development
- Local alternatives for storage/database (SQLite, local files)

### 3. **Authentication Strategy**
- Primary: Azure CLI delegated credentials (`DefaultAzureCredential`)
- Fallback: API key from environment variable (for contingency)
- No hardcoded secrets

### 4. **Deployment-Friendly Architecture**
```
┌─────────────────────────────────────────────────┐
│  LOCAL DEVELOPMENT                              │
├─────────────────────────────────────────────────┤
│  • Azure CLI credentials (az login)             │
│  • Local file storage (data/input, data/output) │
│  • SQLite database (data/reports.db)            │
│  • Streamlit UI (localhost:8501)                │
└─────────────────────────────────────────────────┘
              ↓
         (Future: Same Codebase)
              ↓
┌─────────────────────────────────────────────────┐
│  CLOUD DEPLOYMENT                               │
├─────────────────────────────────────────────────┤
│  • Managed Identity / Service Principal         │
│  • Azure Blob Storage                           │
│  • Azure SQL / Cosmos DB                        │
│  • Azure App Service / Container Apps           │
└─────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation Setup (Week 1)

### 1.1 Project Structure
```
AnthosKS/
├── .env                          # Local environment config (git-ignored)
├── .env.example                  # Template for required variables
├── .gitignore                    # Exclude secrets, data, venv
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Modern Python project config (optional)
├── README.md                     # Project documentation
├── PLAN.md                       # This file
├── LLM_FIRST_APPROACH.md        # Strategy document (existing)
│
├── data/                         # Local data storage (git-ignored)
│   ├── input/                   # Upload MOV PDFs here
│   ├── output/                  # Extracted JSON + Excel outputs
│   ├── reports.db               # SQLite database
│   └── cache/                   # Optional: cache LLM responses
│
├── references/                   # Reference materials (existing)
│   ├── suggestions.md
│   ├── Anthos_MOV Rpt _Palomares_772412_20250528.pdf
│   └── ...
│
├── src/                          # Application source code
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   ├── models.py                # Pydantic data models
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py       # PDF text extraction
│   │   ├── llm_extractor.py    # Azure OpenAI integration
│   │   └── validator.py        # Business rule validation
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py             # Storage interface (ABC)
│   │   ├── local_storage.py    # Local file system
│   │   └── azure_storage.py    # Azure Blob (for future)
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py             # Database interface (ABC)
│   │   ├── sqlite_db.py        # SQLite implementation
│   │   └── azure_sql_db.py     # Azure SQL (for future)
│   └── ui/
│       ├── __init__.py
│       └── streamlit_app.py    # Review interface
│
├── scripts/                      # Utility scripts
│   ├── setup_local_env.sh       # Initialize local environment
│   ├── test_azure_connection.py # Verify Azure OpenAI access
│   └── process_single_report.py # CLI tool for testing
│
└── tests/                        # Unit and integration tests
    ├── __init__.py
    ├── test_extraction.py
    ├── test_models.py
    └── fixtures/
        └── sample_report.pdf
```

### 1.2 Environment Setup

**Tasks:**
1. Create Python virtual environment (3.10+)
2. Install dependencies:
   ```bash
   pip install azure-identity azure-ai-openai pdfplumber python-docx \
               pydantic pandas openpyxl python-dotenv streamlit sqlalchemy
   ```
3. Verify Azure CLI login:
   ```bash
   az login
   az account show
   az cognitiveservices account show \
     --name oai-shared-se-01-p \
     --resource-group rg-shared_resources-se-01-p
   ```
4. Create `.env` file from template:
   ```bash
   # Azure OpenAI Configuration
   AZURE_OPENAI_ENDPOINT=https://swedencentral.api.cognitive.microsoft.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-5-chat-deployment
   AZURE_OPENAI_API_VERSION=2024-08-01-preview

   # Local Storage
   INPUT_PATH=./data/input
   OUTPUT_PATH=./data/output
   DATABASE_PATH=./data/reports.db

   # Application Settings
   LOG_LEVEL=INFO
   ENABLE_CACHE=true
   ```

### 1.3 Azure OpenAI Authentication Test

**Create:** `scripts/test_azure_connection.py`

```python
#!/usr/bin/env python3
"""Test Azure OpenAI connection using DefaultAzureCredential."""

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.ai.openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test Azure OpenAI authentication and basic call."""

    print("🔐 Testing Azure OpenAI Connection...")
    print("-" * 50)

    # Try Azure CLI credential first (local dev)
    try:
        credential = AzureCliCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        print("✅ Azure CLI authentication successful")
        print(f"   Token expires: {token.expires_on}")
    except Exception as e:
        print(f"❌ Azure CLI auth failed: {e}")
        print("   Run: az login")
        return False

    # Initialize OpenAI client
    try:
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_ad_token_provider=lambda: credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            ).token
        )
        print("✅ Azure OpenAI client initialized")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False

    # Test simple completion
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Connection test successful' in JSON format."}
            ],
            max_tokens=50,
            temperature=0
        )
        result = response.choices[0].message.content
        print("✅ Test completion successful")
        print(f"   Response: {result}")
        print(f"   Tokens used: {response.usage.total_tokens}")
        return True
    except Exception as e:
        print(f"❌ Completion failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
```

**Acceptance Criteria:**
- Script runs successfully with `az login` credentials
- Returns valid response from gpt-5-chat
- No API key required

---

## Phase 2: Core Data Models (Week 1-2)

### 2.1 Pydantic Models

**Create:** `src/models.py`

Define all data structures based on MOV report structure:

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class AnswerType(str, Enum):
    """Allowed answer values for MOV questions."""
    YES = "Yes"
    NO = "No"
    NA = "N/A"
    NR = "NR"  # Not Reported

class VisitType(str, Enum):
    """Types of monitoring visits."""
    SIV_MOV = "SIV MOV"
    IMV_MOV = "IMV MOV"
    COV_MOV = "COV MOV"

class SiteInfo(BaseModel):
    """Site identification and contact information."""
    site_number: str = Field(..., description="6-digit site number")
    country: str
    institution: str
    pi_first_name: str
    pi_last_name: str
    city: Optional[str] = None
    anthos_staff: str = Field(..., description="Clinical Oversight Manager")
    cra_name: Optional[str] = Field(None, description="Clinical Research Associate")

    @validator('site_number')
    def validate_site_number(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('Site number must be 6 digits')
        return v

class RecruitmentStats(BaseModel):
    """Patient recruitment and enrollment statistics."""
    screened: int = Field(..., ge=0)
    screen_failures: int = Field(..., ge=0)
    randomized_enrolled: int = Field(..., ge=0)
    early_discontinued: int = Field(..., ge=0)
    completed_treatment: int = Field(..., ge=0)
    completed_study: int = Field(..., ge=0)

    @validator('screened')
    def validate_recruitment_math(cls, v, values):
        """Ensure screened >= randomized + failures."""
        if 'randomized_enrolled' in values and 'screen_failures' in values:
            total = values['randomized_enrolled'] + values['screen_failures']
            if v < total:
                raise ValueError(
                    f'Screened ({v}) must be >= randomized ({values["randomized_enrolled"]}) '
                    f'+ failures ({values["screen_failures"]})'
                )
        return v

class QuestionResponse(BaseModel):
    """Individual question response from MOV report."""
    question_number: int = Field(..., ge=1, le=85)
    question_text: str
    answer: AnswerType
    narrative_summary: Optional[str] = Field(
        None,
        max_length=500,
        description="2-3 sentence summary of narrative response"
    )
    key_finding: Optional[str] = Field(
        None,
        max_length=200,
        description="One-liner if critical finding"
    )
    evidence: Optional[str] = Field(
        None,
        max_length=400,
        description="Short text excerpt for QC verification"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

class ActionItem(BaseModel):
    """Action item from MOV report."""
    item_number: int = Field(..., ge=1)
    description: str
    action_to_be_taken: str
    responsible: str
    due_date: str  # Keep as string, parse separately
    status: Optional[str] = None

class RiskAssessment(BaseModel):
    """Risk assessment findings."""
    site_level_risks_identified: bool
    cra_level_risks_identified: bool
    impact_country_level: bool
    impact_study_level: bool
    narrative: str

class MOVReport(BaseModel):
    """Complete MOV report structure."""

    # Metadata
    protocol_number: str = Field(..., pattern=r"Protocol ANT-\d+")
    site_info: SiteInfo
    visit_start_date: str  # Format: YYYY-MM-DD
    visit_end_date: str
    visit_type: VisitType

    # Core Data
    recruitment_stats: RecruitmentStats
    question_responses: List[QuestionResponse] = Field(
        ...,
        min_items=70,  # Expect at least 70 of 85 questions
        description="Question responses (target: 76+ questions)"
    )
    action_items: List[ActionItem] = Field(default_factory=list)
    risk_assessment: RiskAssessment

    # Quality Summary
    overall_site_quality: Literal[
        "Excellent", "Good", "Adequate", "Needs Improvement", "Poor"
    ]
    key_concerns: List[str] = Field(default_factory=list, max_items=5)
    key_strengths: List[str] = Field(default_factory=list, max_items=5)

    # Extraction Metadata
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    llm_model: str = "gpt-5-chat"
    extraction_method: str = "llm_first"
    source_file: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

**Tasks:**
1. Implement all Pydantic models
2. Add comprehensive validation rules
3. Create JSON schema export utility
4. Write unit tests for model validation

---

## Phase 3: PDF Text Extraction (Week 2)

### 3.1 PDF Parser Implementation

**Create:** `src/extraction/pdf_parser.py`

```python
"""PDF text extraction with layout preservation."""

import pdfplumber
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class PDFParser:
    """Extract text from MOV PDF reports with layout preservation."""

    def __init__(self, preserve_layout: bool = True):
        self.preserve_layout = preserve_layout

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract all text from PDF with page markers.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Full text with page separators
        """
        logger.info(f"Extracting text from: {pdf_path}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_text = []

                for i, page in enumerate(pdf.pages, 1):
                    # Extract with layout preservation
                    text = page.extract_text(layout=self.preserve_layout)

                    if text:
                        pages_text.append(f"--- PAGE {i} ---\n{text}\n")
                    else:
                        logger.warning(f"No text extracted from page {i}")

                full_text = "\n".join(pages_text)

                logger.info(
                    f"Extracted {len(pages_text)} pages, "
                    f"{len(full_text)} characters"
                )

                return full_text

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise

    def extract_metadata(self, pdf_path: Path) -> Dict:
        """Extract PDF metadata."""
        with pdfplumber.open(pdf_path) as pdf:
            return {
                "page_count": len(pdf.pages),
                "metadata": pdf.metadata,
                "file_size_mb": pdf_path.stat().st_size / (1024 * 1024)
            }
```

**Tasks:**
1. Implement PDF text extraction with layout preservation
2. Handle edge cases (scanned PDFs, malformed files)
3. Add metadata extraction
4. Test with sample MOV reports from `references/`

---

## Phase 4: Azure OpenAI Integration (Week 2-3)

### 4.1 LLM Extractor Implementation

**Create:** `src/extraction/llm_extractor.py`

```python
"""Azure OpenAI integration for MOV report extraction."""

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.ai.openai import AzureOpenAI
from typing import Optional
import json
import logging
from pathlib import Path

from ..models import MOVReport
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
        max_tokens: int = 8000
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
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}  # Force JSON output
            )

            # Parse and validate response
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)

            # Add metadata
            result_json["source_file"] = source_file

            # Validate with Pydantic
            report = MOVReport(**result_json)

            logger.info(
                f"Extraction successful: {len(report.question_responses)} questions, "
                f"{len(report.action_items)} action items, "
                f"Tokens: {response.usage.total_tokens}"
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
2. For Yes/No questions, look for checkbox symbols (☒ vs ☐)
3. For missing data, use null rather than guessing
4. For dates, extract in YYYY-MM-DD format
5. For narrative summaries, condense to 2-3 sentences maximum
6. Return ONLY valid JSON matching the schema
7. Do NOT invent or hallucinate data - if you cannot find information, set it to null or "NR"

**ANSWER VALUES:**
- Use "Yes", "No", "N/A", or "NR" (Not Reported) for questions
- Be consistent with capitalization
"""

    def _build_extraction_prompt(self, pdf_text: str) -> str:
        """Build extraction prompt with schema."""
        schema = MOVReport.schema_json(indent=2)

        return f"""Extract structured data from this MOV report.

**REPORT TEXT:**
{pdf_text}

**OUTPUT SCHEMA:**
{schema}

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
   - Extract all questions (target: 76+)
   - For each: question number, text, answer (Yes/No/N/A/NR)
   - Summarize narrative in 2-3 sentences if present
   - Flag critical findings

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

Return structured JSON ONLY. No additional text."""

```

**Tasks:**
1. Implement LLM extractor with Azure AD authentication
2. Create robust error handling and retry logic
3. Add token counting and cost estimation
4. Test with sample reports

---

## Phase 5: Configuration Management (Week 2)

### 5.1 Configuration Module

**Create:** `src/config.py`

```python
"""Application configuration management."""

from pydantic import BaseSettings, Field, validator
from pathlib import Path
from typing import Optional
import os

class Config(BaseSettings):
    """Application configuration from environment variables."""

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = Field(
        ...,
        description="Azure OpenAI endpoint URL"
    )
    AZURE_OPENAI_DEPLOYMENT: str = Field(
        default="gpt-5-chat-deployment",
        description="Deployment name"
    )
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-08-01-preview",
        description="API version"
    )

    # Local Storage
    INPUT_PATH: Path = Field(default="./data/input")
    OUTPUT_PATH: Path = Field(default="./data/output")
    DATABASE_PATH: Path = Field(default="./data/reports.db")
    CACHE_PATH: Optional[Path] = Field(default="./data/cache")

    # Application Settings
    LOG_LEVEL: str = Field(default="INFO")
    ENABLE_CACHE: bool = Field(default=True)
    MAX_RETRIES: int = Field(default=3)
    TIMEOUT_SECONDS: int = Field(default=120)

    # Extraction Parameters
    LLM_TEMPERATURE: float = Field(default=0.0, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int = Field(default=8000)
    CONFIDENCE_THRESHOLD: float = Field(default=0.7, ge=0.0, le=1.0)

    @validator('INPUT_PATH', 'OUTPUT_PATH', 'DATABASE_PATH', 'CACHE_PATH')
    def ensure_path_exists(cls, v):
        """Create directories if they don't exist."""
        if v:
            Path(v).mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Global config instance
config = Config()
```

**Tasks:**
1. Implement configuration with Pydantic Settings
2. Create `.env.example` template
3. Add validation for required settings
4. Document all configuration options

---

## Phase 6: Storage Abstraction (Week 3)

### 6.1 Storage Interface

**Create:** `src/storage/base.py`

```python
"""Abstract storage interface for deployment flexibility."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List

class StorageProvider(ABC):
    """Abstract storage provider interface."""

    @abstractmethod
    def upload_file(self, local_path: Path, remote_path: str) -> str:
        """Upload file and return remote URL/path."""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path) -> Path:
        """Download file to local path."""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """List files with optional prefix filter."""
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Delete file."""
        pass

    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists."""
        pass
```

**Create:** `src/storage/local_storage.py`

```python
"""Local file system storage implementation."""

from pathlib import Path
from typing import List
import shutil
import logging

from .base import StorageProvider

logger = logging.getLogger(__name__)

class LocalStorage(StorageProvider):
    """Local file system storage."""

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_file(self, local_path: Path, remote_path: str) -> str:
        """Copy file to storage location."""
        dest = self.base_path / remote_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, dest)
        logger.info(f"Uploaded: {local_path} -> {dest}")
        return str(dest)

    def download_file(self, remote_path: str, local_path: Path) -> Path:
        """Copy file from storage."""
        source = self.base_path / remote_path
        shutil.copy2(source, local_path)
        logger.info(f"Downloaded: {source} -> {local_path}")
        return local_path

    def list_files(self, prefix: str = "") -> List[str]:
        """List files matching prefix."""
        pattern = f"{prefix}*" if prefix else "*"
        files = list(self.base_path.glob(pattern))
        return [str(f.relative_to(self.base_path)) for f in files if f.is_file()]

    def delete_file(self, remote_path: str) -> bool:
        """Delete file."""
        file_path = self.base_path / remote_path
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted: {file_path}")
            return True
        return False

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists."""
        return (self.base_path / remote_path).exists()
```

**Create:** `src/storage/azure_storage.py` (stub for future)

```python
"""Azure Blob Storage implementation (for future cloud deployment)."""

from .base import StorageProvider
from pathlib import Path
from typing import List

class AzureBlobStorage(StorageProvider):
    """Azure Blob Storage provider - to be implemented for cloud deployment."""

    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name
        # TODO: Initialize Azure Blob client
        raise NotImplementedError("Azure Blob Storage not yet implemented")

    def upload_file(self, local_path: Path, remote_path: str) -> str:
        raise NotImplementedError()

    def download_file(self, remote_path: str, local_path: Path) -> Path:
        raise NotImplementedError()

    def list_files(self, prefix: str = "") -> List[str]:
        raise NotImplementedError()

    def delete_file(self, remote_path: str) -> bool:
        raise NotImplementedError()

    def file_exists(self, remote_path: str) -> bool:
        raise NotImplementedError()
```

---

## Phase 7: Database Abstraction (Week 3)

### 7.1 Database Interface

**Create:** `src/database/base.py`

```python
"""Abstract database interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..models import MOVReport

class DatabaseProvider(ABC):
    """Abstract database provider."""

    @abstractmethod
    def save_report(self, report: MOVReport) -> str:
        """Save report and return ID."""
        pass

    @abstractmethod
    def get_report(self, report_id: str) -> Optional[MOVReport]:
        """Retrieve report by ID."""
        pass

    @abstractmethod
    def list_reports(
        self,
        limit: int = 100,
        offset: int = 0,
        filter_dict: Optional[dict] = None
    ) -> List[MOVReport]:
        """List reports with pagination and filters."""
        pass

    @abstractmethod
    def delete_report(self, report_id: str) -> bool:
        """Delete report."""
        pass

    @abstractmethod
    def search_reports(self, query: str) -> List[MOVReport]:
        """Full-text search."""
        pass
```

**Create:** `src/database/sqlite_db.py`

```python
"""SQLite database implementation for local development."""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

from .base import DatabaseProvider
from ..models import MOVReport

Base = declarative_base()

class ReportRecord(Base):
    """SQLAlchemy model for MOV reports."""
    __tablename__ = "mov_reports"

    id = Column(String, primary_key=True)
    protocol_number = Column(String, index=True)
    site_number = Column(String, index=True)
    visit_date = Column(DateTime, index=True)
    visit_type = Column(String)
    overall_quality = Column(String)
    extraction_timestamp = Column(DateTime)
    json_data = Column(Text)  # Full report as JSON
    source_file = Column(String)

class SQLiteDatabase(DatabaseProvider):
    """SQLite database implementation."""

    def __init__(self, db_path: Path):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_report(self, report: MOVReport) -> str:
        """Save report to SQLite."""
        session = self.Session()
        try:
            report_id = f"{report.site_info.site_number}_{report.visit_start_date}"

            record = ReportRecord(
                id=report_id,
                protocol_number=report.protocol_number,
                site_number=report.site_info.site_number,
                visit_date=datetime.fromisoformat(report.visit_start_date),
                visit_type=report.visit_type,
                overall_quality=report.overall_site_quality,
                extraction_timestamp=report.extraction_timestamp,
                json_data=report.json(),
                source_file=report.source_file
            )

            session.merge(record)  # Insert or update
            session.commit()
            return report_id
        finally:
            session.close()

    def get_report(self, report_id: str) -> Optional[MOVReport]:
        """Retrieve report by ID."""
        session = self.Session()
        try:
            record = session.query(ReportRecord).filter_by(id=report_id).first()
            if record:
                return MOVReport.parse_raw(record.json_data)
            return None
        finally:
            session.close()

    def list_reports(
        self,
        limit: int = 100,
        offset: int = 0,
        filter_dict: Optional[dict] = None
    ) -> List[MOVReport]:
        """List reports with pagination."""
        session = self.Session()
        try:
            query = session.query(ReportRecord)

            if filter_dict:
                if 'protocol_number' in filter_dict:
                    query = query.filter_by(protocol_number=filter_dict['protocol_number'])
                if 'site_number' in filter_dict:
                    query = query.filter_by(site_number=filter_dict['site_number'])

            records = query.order_by(ReportRecord.extraction_timestamp.desc()) \
                           .limit(limit).offset(offset).all()

            return [MOVReport.parse_raw(r.json_data) for r in records]
        finally:
            session.close()

    def delete_report(self, report_id: str) -> bool:
        """Delete report."""
        session = self.Session()
        try:
            record = session.query(ReportRecord).filter_by(id=report_id).first()
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def search_reports(self, query: str) -> List[MOVReport]:
        """Basic text search (can be enhanced)."""
        session = self.Session()
        try:
            records = session.query(ReportRecord) \
                             .filter(ReportRecord.json_data.like(f"%{query}%")) \
                             .all()
            return [MOVReport.parse_raw(r.json_data) for r in records]
        finally:
            session.close()
```

---

## Phase 8: CLI & Orchestration (Week 4)

### 8.1 Main Processing Script

**Create:** `scripts/process_single_report.py`

```python
#!/usr/bin/env python3
"""CLI tool for processing single MOV report."""

import sys
from pathlib import Path
import logging
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.extraction.pdf_parser import PDFParser
from src.extraction.llm_extractor import LLMExtractor
from src.extraction.validator import ReportValidator
from src.storage.local_storage import LocalStorage
from src.database.sqlite_db import SQLiteDatabase

logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_report(pdf_path: Path) -> dict:
    """
    Process single MOV report end-to-end.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Processing result summary
    """
    logger.info(f"Processing: {pdf_path}")
    start_time = datetime.now()

    try:
        # 1. Extract PDF text
        parser = PDFParser()
        pdf_text = parser.extract_text(pdf_path)
        logger.info(f"Extracted {len(pdf_text)} characters")

        # 2. LLM extraction
        extractor = LLMExtractor()
        report = extractor.extract_report(pdf_text, pdf_path.name)
        logger.info(f"Extracted {len(report.question_responses)} questions")

        # 3. Validation
        validator = ReportValidator()
        validation_result = validator.validate(report)
        logger.info(f"Validation: {validation_result['data_quality']}")

        # 4. Save to database
        db = SQLiteDatabase(config.DATABASE_PATH)
        report_id = db.save_report(report)
        logger.info(f"Saved to database: {report_id}")

        # 5. Save JSON output
        storage = LocalStorage(config.OUTPUT_PATH)
        output_file = f"{pdf_path.stem}_extracted.json"
        output_path = config.OUTPUT_PATH / output_file
        output_path.write_text(report.json(indent=2))
        logger.info(f"Saved JSON: {output_path}")

        # 6. Generate Excel (optional - implement later)
        # excel_exporter = ExcelExporter()
        # excel_exporter.export(report, config.OUTPUT_PATH / f"{pdf_path.stem}.xlsx")

        duration = (datetime.now() - start_time).total_seconds()

        return {
            "status": "success",
            "report_id": report_id,
            "questions_extracted": len(report.question_responses),
            "action_items": len(report.action_items),
            "validation": validation_result,
            "duration_seconds": duration,
            "output_file": str(output_path)
        }

    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python process_single_report.py <pdf_file>")
        print("Example: python process_single_report.py data/input/report.pdf")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    if not pdf_path.suffix.lower() == '.pdf':
        print(f"Error: Not a PDF file: {pdf_path}")
        sys.exit(1)

    print("=" * 60)
    print("MOV Report Extraction")
    print("=" * 60)
    print(f"Input: {pdf_path}")
    print(f"Model: {config.AZURE_OPENAI_DEPLOYMENT}")
    print("-" * 60)

    result = process_report(pdf_path)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(json.dumps(result, indent=2))

    sys.exit(0 if result['status'] == 'success' else 1)

if __name__ == "__main__":
    main()
```

---

## Phase 9: Streamlit UI (Week 4-5)

### 9.1 Review Interface

**Create:** `src/ui/streamlit_app.py`

```python
"""Streamlit UI for MOV report review and approval."""

import streamlit as st
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import config
from src.database.sqlite_db import SQLiteDatabase
from src.extraction.pdf_parser import PDFParser
from src.extraction.llm_extractor import LLMExtractor

st.set_page_config(
    page_title="MOV Report Extraction",
    page_icon="📋",
    layout="wide"
)

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = SQLiteDatabase(config.DATABASE_PATH)

def main():
    """Main Streamlit app."""
    st.title("📋 MOV Report Extraction & Review")

    tabs = st.tabs(["Upload", "Review", "Reports", "Analytics"])

    with tabs[0]:
        upload_tab()

    with tabs[1]:
        review_tab()

    with tabs[2]:
        reports_tab()

    with tabs[3]:
        analytics_tab()

def upload_tab():
    """Upload and process new report."""
    st.header("Upload MOV Report")

    uploaded_file = st.file_uploader(
        "Choose PDF file",
        type=['pdf'],
        help="Upload a 41-page MOV report PDF"
    )

    if uploaded_file:
        st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

        if st.button("🚀 Extract Data", type="primary"):
            with st.spinner("Extracting data from PDF..."):
                # Save uploaded file
                temp_path = Path(config.INPUT_PATH) / uploaded_file.name
                temp_path.write_bytes(uploaded_file.read())

                # Process
                try:
                    # Extract text
                    parser = PDFParser()
                    pdf_text = parser.extract_text(temp_path)

                    # LLM extraction
                    extractor = LLMExtractor()
                    report = extractor.extract_report(pdf_text, uploaded_file.name)

                    # Save
                    report_id = st.session_state.db.save_report(report)

                    st.success(f"✅ Extraction complete! Report ID: {report_id}")
                    st.json({
                        "questions": len(report.question_responses),
                        "action_items": len(report.action_items),
                        "quality": report.overall_site_quality
                    })

                except Exception as e:
                    st.error(f"❌ Extraction failed: {e}")

def review_tab():
    """Review extracted reports."""
    st.header("Review Extracted Data")

    # Get recent reports
    reports = st.session_state.db.list_reports(limit=10)

    if not reports:
        st.info("No reports to review. Upload a report in the Upload tab.")
        return

    # Select report
    report_options = {
        f"{r.site_info.site_number} - {r.visit_start_date}": r
        for r in reports
    }

    selected = st.selectbox("Select report", list(report_options.keys()))
    report = report_options[selected]

    # Display report details
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Site Information")
        st.write(f"**Site:** {report.site_info.site_number} - {report.site_info.institution}")
        st.write(f"**Country:** {report.site_info.country}")
        st.write(f"**PI:** Dr. {report.site_info.pi_first_name} {report.site_info.pi_last_name}")
        st.write(f"**Visit:** {report.visit_type} ({report.visit_start_date} to {report.visit_end_date})")

        st.subheader("Recruitment Statistics")
        st.json(report.recruitment_stats.dict())

        st.subheader(f"Questions ({len(report.question_responses)})")
        for q in report.question_responses[:10]:  # Show first 10
            with st.expander(f"Q{q.question_number}: {q.question_text[:60]}..."):
                st.write(f"**Answer:** {q.answer}")
                if q.narrative_summary:
                    st.write(f"**Summary:** {q.narrative_summary}")

    with col2:
        st.subheader("Quality Assessment")
        st.metric("Overall Quality", report.overall_site_quality)

        if report.key_concerns:
            st.warning("**Concerns:**")
            for concern in report.key_concerns:
                st.write(f"- {concern}")

        if report.key_strengths:
            st.success("**Strengths:**")
            for strength in report.key_strengths:
                st.write(f"- {strength}")

def reports_tab():
    """List all reports."""
    st.header("All Reports")

    reports = st.session_state.db.list_reports(limit=100)

    if reports:
        # Create summary table
        data = []
        for r in reports:
            data.append({
                "Site": r.site_info.site_number,
                "Country": r.site_info.country,
                "Visit Date": r.visit_start_date,
                "Type": r.visit_type,
                "Quality": r.overall_site_quality,
                "Questions": len(r.question_responses)
            })

        st.dataframe(data, use_container_width=True)
    else:
        st.info("No reports found.")

def analytics_tab():
    """Analytics dashboard (placeholder)."""
    st.header("Analytics")
    st.info("📊 Analytics dashboard coming soon!")

    # TODO: Implement analytics
    # - Questions by answer distribution
    # - Quality trends
    # - Action item categories
    # - Risk patterns

if __name__ == "__main__":
    main()
```

**Run with:**
```bash
streamlit run src/ui/streamlit_app.py
```

---

## Phase 10: Testing & Validation (Week 5)

### 10.1 Test Suite

**Create:** `tests/test_extraction.py`

```python
"""Tests for extraction pipeline."""

import pytest
from pathlib import Path
from src.extraction.pdf_parser import PDFParser
from src.extraction.llm_extractor import LLMExtractor
from src.models import MOVReport

def test_pdf_extraction():
    """Test PDF text extraction."""
    parser = PDFParser()
    sample_pdf = Path("references/Anthos_MOV Rpt _Palomares_772412_20250528.pdf")

    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    text = parser.extract_text(sample_pdf)

    assert len(text) > 10000  # Should have substantial text
    assert "Protocol ANT-007" in text
    assert "772412" in text

def test_llm_extraction_structure():
    """Test that LLM returns valid structure."""
    # This requires Azure credentials
    # Mark as integration test
    pytest.skip("Integration test - requires Azure credentials")

def test_model_validation():
    """Test Pydantic model validation."""
    # Test with invalid data
    with pytest.raises(ValueError):
        MOVReport(
            protocol_number="INVALID",
            site_info={"site_number": "12345"},  # Should be 6 digits
            # ... missing required fields
        )

# More tests...
```

**Tasks:**
1. Write unit tests for all modules
2. Create integration tests for LLM extraction
3. Add validation tests
4. Test error handling

---

## Deliverables

### Week 1-2
- [ ] Project structure created
- [ ] Azure OpenAI connection working (CLI auth)
- [ ] Pydantic models implemented
- [ ] PDF extraction working
- [ ] Configuration system in place

### Week 3-4
- [ ] LLM extraction functional
- [ ] Storage abstraction implemented
- [ ] Database abstraction implemented
- [ ] CLI tool working end-to-end

### Week 4-5
- [ ] Streamlit UI functional
- [ ] Test suite with >80% coverage
- [ ] Documentation complete
- [ ] Tested on 20+ real reports

---

## Success Criteria

1. **Authentication:** Azure CLI credentials work without API keys
2. **Extraction:** ≥85% accuracy on sample reports
3. **Cost:** ≤$0.30 per report
4. **Performance:** <2 minutes per report
5. **Deployment Ready:** Clear separation of local vs. cloud components
6. **Documentation:** Complete setup and usage guides

---

## Future Cloud Deployment (Out of Scope)

When ready to deploy to Azure:

1. **Create new resource group:** `rg-anthosks-se-01-p`
2. **Add resources:**
   - Azure App Service or Container Apps (UI + API)
   - Azure Blob Storage (PDF storage)
   - Azure SQL Database (replace SQLite)
   - Managed Identity (replace Azure CLI auth)
3. **Keep using:** Shared OpenAI resource (`oai-shared-se-01-p`)
4. **Code changes:** Minimal - swap storage/db providers via config

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Azure CLI auth fails | Add API key fallback |
| GPT-5 costs exceed budget | Monitor token usage, set alerts |
| LLM hallucinations | Use temperature=0, validation layer, evidence spans |
| PDF format variations | Test with diverse samples, refine prompt |
| Large PDFs timeout | Implement chunking strategy |

---

## Cost Estimation

**Development (Local):**
- Developer time: 4-5 weeks
- Azure OpenAI usage: ~$20-50 (testing 50-100 reports)
- **Total:** Minimal cloud costs

**Per Report Processing:**
- Input tokens: ~42,000 × GPT-5 pricing
- Output tokens: ~6,000 × GPT-5 pricing
- **Estimated:** $0.20-0.30 per report (adjust based on actual GPT-5 pricing)

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Verify Azure OpenAI access** with CLI credentials
3. **Obtain sample MOV reports** (5-10 for testing)
4. **Begin Week 1 tasks** - setup and foundation
5. **Weekly check-ins** to review progress

---

**Questions?**
- Contact: johan.stromquist@ssistrategy.com
- Azure Subscription: SSI Strategy Innovation
- Shared Resource Group: `rg-shared_resources-se-01-p`
