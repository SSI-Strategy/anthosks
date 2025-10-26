"""Tests for Pydantic models."""

import pytest
from datetime import datetime
from src.models import (
    SiteInfo, RecruitmentStats, QuestionResponse,
    ActionItem, RiskAssessment, MOVReport,
    AnswerType, VisitType
)


def test_site_info_validation():
    """Test site info validation."""
    # Valid site number
    site = SiteInfo(
        site_number="123456",
        country="USA",
        institution="Test Hospital",
        pi_first_name="John",
        pi_last_name="Doe",
        anthos_staff="Jane Smith"
    )
    assert site.site_number == "123456"

    # Invalid site number (not 6 digits)
    with pytest.raises(ValueError):
        SiteInfo(
            site_number="12345",  # Only 5 digits
            country="USA",
            institution="Test Hospital",
            pi_first_name="John",
            pi_last_name="Doe",
            anthos_staff="Jane Smith"
        )


def test_recruitment_stats_validation():
    """Test recruitment statistics validation."""
    # Valid stats
    stats = RecruitmentStats(
        screened=100,
        screen_failures=20,
        randomized_enrolled=80,
        early_discontinued=5,
        completed_treatment=70,
        completed_study=65
    )
    assert stats.screened == 100

    # Test negative values should fail
    with pytest.raises(ValueError):
        RecruitmentStats(
            screened=-10,  # Negative not allowed
            screen_failures=20,
            randomized_enrolled=80,
            early_discontinued=5,
            completed_treatment=70,
            completed_study=65
        )


def test_question_response():
    """Test question response model."""
    q = QuestionResponse(
        question_number=1,
        question_text="Is the site properly equipped?",
        answer=AnswerType.YES,
        confidence=0.95
    )
    assert q.question_number == 1
    assert q.answer == AnswerType.YES


def test_action_item():
    """Test action item model."""
    item = ActionItem(
        item_number=1,
        description="Update training logs",
        action_to_be_taken="Complete training documentation",
        responsible="Site Coordinator",
        due_date="2025-11-30"
    )
    assert item.item_number == 1


def test_mov_report_structure():
    """Test complete MOV report structure."""
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
            ) for i in range(1, 76)  # 75 questions
        ],
        action_items=[],
        risk_assessment=RiskAssessment(
            site_level_risks_identified=False,
            cra_level_risks_identified=False,
            impact_country_level=False,
            impact_study_level=False,
            narrative="No significant risks identified"
        ),
        overall_site_quality="Good",
        source_file="test_report.pdf"
    )

    assert report.protocol_number == "Protocol ANT-007"
    assert len(report.question_responses) == 75
    assert report.overall_site_quality == "Good"
