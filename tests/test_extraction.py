"""Tests for extraction pipeline."""

import pytest
from pathlib import Path
from src.extraction.pdf_parser import PDFParser
from src.extraction.validator import ReportValidator
from src.models import MOVReport, SiteInfo, RecruitmentStats, QuestionResponse, RiskAssessment, AnswerType, VisitType


def test_pdf_extraction():
    """Test PDF text extraction."""
    parser = PDFParser()
    sample_pdf = Path("references/Anthos_MOV Rpt _Palomares_772412_20250528.pdf")

    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    text = parser.extract_text(sample_pdf)

    assert len(text) > 10000  # Should have substantial text
    assert "Protocol ANT-007" in text or "ANT-007" in text
    assert "772412" in text


def test_pdf_metadata():
    """Test PDF metadata extraction."""
    parser = PDFParser()
    sample_pdf = Path("references/Anthos_MOV Rpt _Palomares_772412_20250528.pdf")

    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    metadata = parser.extract_metadata(sample_pdf)

    assert "page_count" in metadata
    assert metadata["page_count"] > 0
    assert "file_size_mb" in metadata


def test_validator_with_valid_report():
    """Test validator with valid report."""
    report = MOVReport(
        protocol_number="Protocol ANT-007",
        site_info=SiteInfo(
            site_number="772412",
            country="Spain",
            institution="Test Hospital",
            pi_first_name="Maria",
            pi_last_name="Garcia",
            anthos_staff="John Smith"
        ),
        visit_start_date="2025-05-28",
        visit_end_date="2025-05-28",
        visit_type=VisitType.IMV_MOV,
        recruitment_stats=RecruitmentStats(
            screened=10,
            screen_failures=2,
            randomized_enrolled=8,
            early_discontinued=0,
            completed_treatment=8,
            completed_study=8
        ),
        question_responses=[
            QuestionResponse(
                question_number=i,
                question_text=f"Question {i}",
                answer=AnswerType.YES,
                confidence=0.95
            ) for i in range(1, 77)  # 76 questions
        ],
        action_items=[],
        risk_assessment=RiskAssessment(
            site_level_risks_identified=False,
            cra_level_risks_identified=False,
            impact_country_level=False,
            impact_study_level=False,
            narrative="No significant risks"
        ),
        overall_site_quality="Good",
        source_file="test_report.pdf"
    )

    validator = ReportValidator()
    result = validator.validate(report)

    assert result["is_valid"] is True
    assert result["data_quality"] in ["Excellent", "Good"]
    assert result["total_questions"] == 76


def test_validator_with_insufficient_questions():
    """Test validator flags insufficient question coverage."""
    # Create report with exactly 70 questions (minimum) to avoid Pydantic validation error
    # The validator should still warn since target is 76
    report = MOVReport(
        protocol_number="Protocol ANT-007",
        site_info=SiteInfo(
            site_number="772412",
            country="Spain",
            institution="Test Hospital",
            pi_first_name="Maria",
            pi_last_name="Garcia",
            anthos_staff="John Smith"
        ),
        visit_start_date="2025-05-28",
        visit_end_date="2025-05-28",
        visit_type=VisitType.IMV_MOV,
        recruitment_stats=RecruitmentStats(
            screened=10,
            screen_failures=2,
            randomized_enrolled=8,
            early_discontinued=0,
            completed_treatment=8,
            completed_study=8
        ),
        question_responses=[
            QuestionResponse(
                question_number=i,
                question_text=f"Question {i}",
                answer=AnswerType.YES
            ) for i in range(1, 71)  # Exactly 70 questions (minimum allowed)
        ],
        action_items=[],
        risk_assessment=RiskAssessment(
            site_level_risks_identified=False,
            cra_level_risks_identified=False,
            impact_country_level=False,
            impact_study_level=False,
            narrative="No risks"
        ),
        overall_site_quality="Good",
        source_file="test_report.pdf"
    )

    validator = ReportValidator()
    result = validator.validate(report)

    # Should have warnings (not errors) since 70 < 76 (target)
    assert result["is_valid"] is True  # No critical issues, but has warnings
    assert len(result["warnings"]) > 0
    assert any("Below target" in warning for warning in result["warnings"])
