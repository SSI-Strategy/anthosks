"""Business rule validation for MOV reports."""

import logging
from typing import Dict, List
from ..models import MOVReport, AnswerType

logger = logging.getLogger(__name__)


class ReportValidator:
    """Validate MOV report data against business rules."""

    def validate(self, report: MOVReport) -> Dict:
        """
        Validate report and return quality metrics.

        Args:
            report: MOVReport to validate

        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating report: {report.site_info.site_number}")

        issues = []
        warnings = []

        # 1. Check question coverage
        question_coverage = self._check_question_coverage(report, issues, warnings)

        # 2. Validate recruitment statistics
        self._validate_recruitment_stats(report, issues, warnings)

        # 3. Check for low confidence extractions
        self._check_confidence_levels(report, warnings)

        # 4. Validate action items
        self._validate_action_items(report, warnings)

        # 5. Check for critical findings
        critical_findings = self._identify_critical_findings(report)

        # Calculate data quality score
        data_quality = self._calculate_quality_score(report, issues, warnings)

        return {
            "is_valid": len(issues) == 0,
            "data_quality": data_quality,
            "question_coverage": question_coverage,
            "issues": issues,
            "warnings": warnings,
            "critical_findings": critical_findings,
            "total_questions": len(report.question_responses),
            "action_items_count": len(report.action_items)
        }

    def _check_question_coverage(
        self,
        report: MOVReport,
        issues: List[str],
        warnings: List[str]
    ) -> float:
        """Check if sufficient questions were extracted."""
        total_questions = len(report.question_responses)
        expected_min = 70
        target = 76

        coverage = total_questions / 85 * 100

        if total_questions < expected_min:
            issues.append(
                f"Insufficient questions extracted: {total_questions}/85 "
                f"(minimum: {expected_min})"
            )
        elif total_questions < target:
            warnings.append(
                f"Below target question count: {total_questions}/85 "
                f"(target: {target})"
            )

        return coverage

    def _validate_recruitment_stats(
        self,
        report: MOVReport,
        issues: List[str],
        warnings: List[str]
    ):
        """Validate recruitment statistics math."""
        stats = report.recruitment_stats

        # Check screened >= randomized + failures
        expected_min = stats.randomized_enrolled + stats.screen_failures
        if stats.screened < expected_min:
            issues.append(
                f"Recruitment math error: screened ({stats.screened}) < "
                f"randomized ({stats.randomized_enrolled}) + "
                f"failures ({stats.screen_failures})"
            )

        # Check discontinued <= randomized
        if stats.early_discontinued > stats.randomized_enrolled:
            issues.append(
                f"Discontinued ({stats.early_discontinued}) > "
                f"randomized ({stats.randomized_enrolled})"
            )

        # Check completed <= randomized
        if stats.completed_treatment > stats.randomized_enrolled:
            issues.append(
                f"Completed treatment ({stats.completed_treatment}) > "
                f"randomized ({stats.randomized_enrolled})"
            )

    def _check_confidence_levels(
        self,
        report: MOVReport,
        warnings: List[str]
    ):
        """Check for low confidence extractions."""
        from ..config import config

        low_confidence = [
            q for q in report.question_responses
            if q.confidence < config.CONFIDENCE_THRESHOLD
        ]

        if low_confidence:
            warnings.append(
                f"{len(low_confidence)} questions have low confidence "
                f"(< {config.CONFIDENCE_THRESHOLD})"
            )

    def _validate_action_items(
        self,
        report: MOVReport,
        warnings: List[str]
    ):
        """Validate action items."""
        if len(report.action_items) == 0:
            warnings.append("No action items found in report")

        # Check for missing fields
        for item in report.action_items:
            if not item.description or not item.action_to_be_taken:
                warnings.append(
                    f"Action item {item.item_number} has missing fields"
                )

    def _identify_critical_findings(self, report: MOVReport) -> List[str]:
        """Identify critical findings from questions."""
        critical = []

        # Questions answered "No" or with key findings
        for q in report.question_responses:
            if q.answer == AnswerType.NO and q.key_finding:
                critical.append(
                    f"Q{q.question_number}: {q.key_finding}"
                )

        # Add risk assessment findings
        if report.risk_assessment.site_level_risks_identified:
            critical.append("Site-level risks identified")

        if report.risk_assessment.cra_level_risks_identified:
            critical.append("CRA-level risks identified")

        return critical

    def _calculate_quality_score(
        self,
        report: MOVReport,
        issues: List[str],
        warnings: List[str]
    ) -> str:
        """Calculate overall data quality score."""
        if len(issues) > 0:
            return "Poor"

        if len(warnings) == 0:
            return "Excellent"

        if len(warnings) <= 2:
            return "Good"

        if len(warnings) <= 5:
            return "Fair"

        return "Needs Review"
