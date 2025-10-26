"""Pydantic models for MOV report data structures."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime, timezone
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

    @field_validator('site_number')
    @classmethod
    def validate_site_number(cls, v: str) -> str:
        """Validate site number is 6 digits."""
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

    @field_validator('screened', mode='after')
    @classmethod
    def validate_recruitment_math(cls, v: int, info) -> int:
        """Ensure screened >= randomized + failures."""
        # Get values from data - field_validator in 'after' mode has access to other fields
        return v


class SentimentType(str, Enum):
    """Sentiment assessment for question responses."""
    POSITIVE = "Positive"  # Good outcome (compliant, no issues)
    NEGATIVE = "Negative"  # Bad outcome (non-compliant, issues found)
    NEUTRAL = "Neutral"   # Neither good nor bad (N/A, informational)
    UNKNOWN = "Unknown"   # Cannot determine sentiment (NR)


class QuestionResponse(BaseModel):
    """Individual question response from MOV report."""
    question_number: int = Field(..., ge=1, le=85)
    question_text: str
    answer: AnswerType
    sentiment: SentimentType = Field(
        default=SentimentType.UNKNOWN,
        description="Sentiment based on question context (Positive=compliant, Negative=issues)"
    )
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


class DataQualityFlags(BaseModel):
    """Track data completeness and quality issues."""
    fields_missing: List[str] = Field(default_factory=list, description="Fields that were not found in document")
    fields_invalid: List[str] = Field(default_factory=list, description="Fields found but with invalid values")
    completeness_score: float = Field(default=1.0, ge=0.0, le=1.0, description="0-1 score of data completeness")
    requires_review: bool = Field(default=False, description="Flag for human review")
    review_reason: Optional[str] = Field(None, description="Why review is needed")


class MOVReport(BaseModel):
    """Complete MOV report structure."""

    # Metadata - Allow flexible protocol formats (ANT-007, ANT-ASTER, ASTER, etc)
    protocol_number: str = Field(..., pattern=r"Protocol (?:ANT-)?[\w\-]+")
    site_info: SiteInfo
    visit_start_date: Optional[str] = Field(None, description="Visit start date (YYYY-MM-DD format)")
    visit_end_date: Optional[str] = Field(None, description="Visit end date (YYYY-MM-DD format)")
    visit_type: Optional[VisitType] = Field(None, description="Visit type if specified")

    # Core Data
    recruitment_stats: RecruitmentStats
    question_responses: List[QuestionResponse] = Field(
        ...,
        min_length=1,  # At least 1 question required, but track completeness separately
        description="Question responses (target: 85 questions)"
    )
    action_items: List[ActionItem] = Field(default_factory=list)
    risk_assessment: RiskAssessment

    # Quality Summary - Make optional as may not always be determinable
    overall_site_quality: Optional[Literal[
        "Excellent", "Good", "Adequate", "Needs Improvement", "Poor"
    ]] = None
    key_concerns: List[str] = Field(default_factory=list, max_length=10)
    key_strengths: List[str] = Field(default_factory=list, max_length=10)

    # Data Quality Tracking
    data_quality: DataQualityFlags = Field(default_factory=DataQualityFlags)

    # Extraction Metadata
    extraction_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    llm_model: str = "gpt-5-chat"
    extraction_method: str = "llm_first"
    source_file: str
