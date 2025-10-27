"""Analytics service for computing KPIs and aggregations."""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json

from ..models import MOVReport, AnswerType, SentimentType
from ..database.base import DatabaseProvider


class AnalyticsService:
    """Service for computing analytics and KPIs from MOV reports."""

    def __init__(self, db: DatabaseProvider):
        self.db = db

    def get_reports_in_range(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MOVReport]:
        """
        Get reports within a date range with optional filters.

        Args:
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            filters: Additional filters (protocol_number, site_number, country)

        Returns:
            List of MOVReport objects
        """
        all_reports_with_ids = self.db.list_reports(limit=10000)  # Get all reports (returns tuples of (id, report))

        filtered = []
        for report_id, report in all_reports_with_ids:
            # Date filtering
            if date_from or date_to:
                if not report.visit_start_date:
                    continue
                visit_date = datetime.fromisoformat(report.visit_start_date)
                if date_from and visit_date < date_from:
                    continue
                if date_to and visit_date > date_to:
                    continue

            # Additional filters
            if filters:
                if 'protocol_number' in filters and report.protocol_number != filters['protocol_number']:
                    continue
                if 'site_number' in filters and report.site_info.site_number != filters['site_number']:
                    continue
                if 'country' in filters and report.site_info.country != filters['country']:
                    continue
                if 'visit_type' in filters and report.visit_type and report.visit_type.value != filters['visit_type']:
                    continue

            filtered.append(report)

        return filtered

    def calculate_kpis(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate all KPIs for the given time period and filters.

        Returns:
            Dictionary with KPI metrics
        """
        reports = self.get_reports_in_range(date_from, date_to, filters)

        if not reports:
            return {
                "total_sites": 0,
                "total_reports": 0,
                "compliance_rate": 0.0,
                "non_compliance_rate": 0.0,
                "completeness_rate": 0.0,
                "avg_site_quality_score": 0.0,
                "high_risk_sites": 0,
                "avg_enrollment_rate": 0.0,
                "avg_completion_rate": 0.0,
                "total_action_items": 0,
                "overdue_action_items": 0
            }

        # Count unique sites
        unique_sites = set(r.site_info.site_number for r in reports)

        # Aggregate question responses
        total_yes = 0
        total_no = 0
        total_na = 0
        total_nr = 0
        total_questions = 0

        for report in reports:
            for q in report.question_responses:
                if q.answer == AnswerType.YES:
                    total_yes += 1
                elif q.answer == AnswerType.NO:
                    total_no += 1
                elif q.answer == AnswerType.NA:
                    total_na += 1
                elif q.answer == AnswerType.NR:
                    total_nr += 1
                total_questions += 1

        # Calculate compliance metrics
        total_non_nr = total_yes + total_no + total_na
        compliance_rate = (total_yes / total_non_nr * 100) if total_non_nr > 0 else 0.0
        non_compliance_rate = (total_no / total_non_nr * 100) if total_non_nr > 0 else 0.0
        completeness_rate = ((total_questions - total_nr) / total_questions * 100) if total_questions > 0 else 0.0

        # Calculate site quality score
        quality_scores = {
            "Excellent": 5,
            "Good": 4,
            "Adequate": 3,
            "Needs Improvement": 2,
            "Poor": 1
        }
        site_quality_sum = 0
        site_quality_count = 0
        for report in reports:
            if report.overall_site_quality:
                site_quality_sum += quality_scores.get(report.overall_site_quality, 0)
                site_quality_count += 1
        avg_site_quality = (site_quality_sum / site_quality_count) if site_quality_count > 0 else 0.0

        # Calculate recruitment metrics
        total_screened = sum(r.recruitment_stats.screened for r in reports)
        total_randomized = sum(r.recruitment_stats.randomized_enrolled for r in reports)
        total_completed = sum(r.recruitment_stats.completed_study for r in reports)

        avg_enrollment_rate = (total_randomized / total_screened * 100) if total_screened > 0 else 0.0
        avg_completion_rate = (total_completed / total_randomized * 100) if total_randomized > 0 else 0.0

        # Calculate risk metrics
        high_risk_sites = sum(1 for r in reports if self._calculate_risk_score(r) > 70)

        # Action items
        total_action_items = sum(len(r.action_items) for r in reports)
        overdue_action_items = 0  # TODO: Implement when action item status tracking is added

        return {
            "total_sites": len(unique_sites),
            "total_reports": len(reports),
            "compliance_rate": round(compliance_rate, 2),
            "non_compliance_rate": round(non_compliance_rate, 2),
            "completeness_rate": round(completeness_rate, 2),
            "avg_site_quality_score": round(avg_site_quality, 2),
            "high_risk_sites": high_risk_sites,
            "avg_enrollment_rate": round(avg_enrollment_rate, 2),
            "avg_completion_rate": round(avg_completion_rate, 2),
            "total_action_items": total_action_items,
            "overdue_action_items": overdue_action_items,
            "answer_distribution": {
                "yes": total_yes,
                "no": total_no,
                "na": total_na,
                "nr": total_nr
            }
        }

    def get_compliance_trends(
        self,
        date_from: datetime,
        date_to: datetime,
        granularity: str = "month",  # day, week, month, quarter
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get compliance rate trends over time.

        Returns:
            List of {period, compliance_rate, non_compliance_rate, report_count}
        """
        reports = self.get_reports_in_range(date_from, date_to, filters)

        # Group by time period
        period_data = defaultdict(lambda: {"yes": 0, "no": 0, "na": 0, "nr": 0, "count": 0})

        for report in reports:
            if not report.visit_start_date:
                continue

            visit_date = datetime.fromisoformat(report.visit_start_date)
            period_key = self._get_period_key(visit_date, granularity)

            for q in report.question_responses:
                if q.answer == AnswerType.YES:
                    period_data[period_key]["yes"] += 1
                elif q.answer == AnswerType.NO:
                    period_data[period_key]["no"] += 1
                elif q.answer == AnswerType.NA:
                    period_data[period_key]["na"] += 1
                elif q.answer == AnswerType.NR:
                    period_data[period_key]["nr"] += 1

            period_data[period_key]["count"] += 1

        # Calculate rates for each period
        trends = []
        for period, data in sorted(period_data.items()):
            total_non_nr = data["yes"] + data["no"] + data["na"]
            compliance_rate = (data["yes"] / total_non_nr * 100) if total_non_nr > 0 else 0.0
            non_compliance_rate = (data["no"] / total_non_nr * 100) if total_non_nr > 0 else 0.0

            trends.append({
                "period": period,
                "compliance_rate": round(compliance_rate, 2),
                "non_compliance_rate": round(non_compliance_rate, 2),
                "report_count": data["count"]
            })

        return trends

    def get_question_statistics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get compliance statistics for each question (1-85).

        Returns:
            List of {question_number, question_text, compliance_rate, yes_count, no_count, na_count, nr_count, total_responses}
        """
        reports = self.get_reports_in_range(date_from, date_to, filters)

        # Aggregate by question number
        question_data = defaultdict(lambda: {
            "question_text": "",
            "yes": 0,
            "no": 0,
            "na": 0,
            "nr": 0,
            "sentiment_positive": 0,
            "sentiment_negative": 0
        })

        for report in reports:
            for q in report.question_responses:
                qnum = q.question_number
                question_data[qnum]["question_text"] = q.question_text

                if q.answer == AnswerType.YES:
                    question_data[qnum]["yes"] += 1
                elif q.answer == AnswerType.NO:
                    question_data[qnum]["no"] += 1
                elif q.answer == AnswerType.NA:
                    question_data[qnum]["na"] += 1
                elif q.answer == AnswerType.NR:
                    question_data[qnum]["nr"] += 1

                if q.sentiment == SentimentType.POSITIVE:
                    question_data[qnum]["sentiment_positive"] += 1
                elif q.sentiment == SentimentType.NEGATIVE:
                    question_data[qnum]["sentiment_negative"] += 1

        # Calculate statistics
        stats = []
        for qnum in sorted(question_data.keys()):
            data = question_data[qnum]
            total_responses = data["yes"] + data["no"] + data["na"] + data["nr"]
            total_non_nr = data["yes"] + data["no"] + data["na"]
            compliance_rate = (data["yes"] / total_non_nr * 100) if total_non_nr > 0 else 0.0

            stats.append({
                "question_number": qnum,
                "question_text": data["question_text"],
                "compliance_rate": round(compliance_rate, 2),
                "yes_count": data["yes"],
                "no_count": data["no"],
                "na_count": data["na"],
                "nr_count": data["nr"],
                "total_responses": total_responses,
                "sentiment_positive": data["sentiment_positive"],
                "sentiment_negative": data["sentiment_negative"]
            })

        return stats

    def get_site_leaderboard(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "compliance_rate",  # compliance_rate, quality_score, enrollment_rate
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get site performance leaderboard.

        Returns:
            List of site performance metrics sorted by specified criteria
        """
        reports = self.get_reports_in_range(date_from, date_to, filters)

        # Group by site
        site_data = defaultdict(lambda: {
            "country": "",
            "institution": "",
            "pi_name": "",
            "reports": [],
            "yes": 0,
            "no": 0,
            "na": 0,
            "nr": 0,
            "quality_scores": [],
            "screened": 0,
            "randomized": 0,
            "completed": 0,
            "last_visit_date": None
        })

        for report in reports:
            site_num = report.site_info.site_number
            site_data[site_num]["country"] = report.site_info.country
            site_data[site_num]["institution"] = report.site_info.institution
            site_data[site_num]["pi_name"] = f"{report.site_info.pi_first_name} {report.site_info.pi_last_name}"
            site_data[site_num]["reports"].append(report)

            # Aggregate questions
            for q in report.question_responses:
                if q.answer == AnswerType.YES:
                    site_data[site_num]["yes"] += 1
                elif q.answer == AnswerType.NO:
                    site_data[site_num]["no"] += 1
                elif q.answer == AnswerType.NA:
                    site_data[site_num]["na"] += 1
                elif q.answer == AnswerType.NR:
                    site_data[site_num]["nr"] += 1

            # Quality scores
            if report.overall_site_quality:
                quality_map = {"Excellent": 5, "Good": 4, "Adequate": 3, "Needs Improvement": 2, "Poor": 1}
                site_data[site_num]["quality_scores"].append(quality_map.get(report.overall_site_quality, 0))

            # Recruitment
            site_data[site_num]["screened"] += report.recruitment_stats.screened
            site_data[site_num]["randomized"] += report.recruitment_stats.randomized_enrolled
            site_data[site_num]["completed"] += report.recruitment_stats.completed_study

            # Last visit
            if report.visit_start_date:
                visit_date = datetime.fromisoformat(report.visit_start_date)
                if not site_data[site_num]["last_visit_date"] or visit_date > site_data[site_num]["last_visit_date"]:
                    site_data[site_num]["last_visit_date"] = visit_date

        # Calculate metrics
        leaderboard = []
        for site_num, data in site_data.items():
            total_non_nr = data["yes"] + data["no"] + data["na"]
            compliance_rate = (data["yes"] / total_non_nr * 100) if total_non_nr > 0 else 0.0

            avg_quality = sum(data["quality_scores"]) / len(data["quality_scores"]) if data["quality_scores"] else 0.0

            enrollment_rate = (data["randomized"] / data["screened"] * 100) if data["screened"] > 0 else 0.0
            completion_rate = (data["completed"] / data["randomized"] * 100) if data["randomized"] > 0 else 0.0

            leaderboard.append({
                "site_number": site_num,
                "country": data["country"],
                "institution": data["institution"],
                "pi_name": data["pi_name"],
                "compliance_rate": round(compliance_rate, 2),
                "avg_quality_score": round(avg_quality, 2),
                "enrollment_rate": round(enrollment_rate, 2),
                "completion_rate": round(completion_rate, 2),
                "report_count": len(data["reports"]),
                "last_visit_date": data["last_visit_date"].isoformat() if data["last_visit_date"] else None
            })

        # Sort
        reverse = True
        leaderboard.sort(key=lambda x: x[sort_by], reverse=reverse)

        return leaderboard[:limit]

    def get_geographic_summary(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get compliance and performance metrics by country.

        Returns:
            List of country-level metrics
        """
        reports = self.get_reports_in_range(date_from, date_to, filters)

        # Group by country
        country_data = defaultdict(lambda: {
            "yes": 0,
            "no": 0,
            "na": 0,
            "nr": 0,
            "sites": set(),
            "reports": 0
        })

        for report in reports:
            country = report.site_info.country
            country_data[country]["sites"].add(report.site_info.site_number)
            country_data[country]["reports"] += 1

            for q in report.question_responses:
                if q.answer == AnswerType.YES:
                    country_data[country]["yes"] += 1
                elif q.answer == AnswerType.NO:
                    country_data[country]["no"] += 1
                elif q.answer == AnswerType.NA:
                    country_data[country]["na"] += 1
                elif q.answer == AnswerType.NR:
                    country_data[country]["nr"] += 1

        # Calculate metrics
        summary = []
        for country, data in country_data.items():
            total_non_nr = data["yes"] + data["no"] + data["na"]
            compliance_rate = (data["yes"] / total_non_nr * 100) if total_non_nr > 0 else 0.0

            summary.append({
                "country": country,
                "site_count": len(data["sites"]),
                "report_count": data["reports"],
                "compliance_rate": round(compliance_rate, 2),
                "yes_count": data["yes"],
                "no_count": data["no"],
                "na_count": data["na"],
                "nr_count": data["nr"]
            })

        summary.sort(key=lambda x: x["compliance_rate"], reverse=True)
        return summary

    def _calculate_risk_score(self, report: MOVReport) -> float:
        """
        Calculate composite risk score for a site (0-100, higher = more risk).

        Weights:
        - Non-compliance rate: 40%
        - Action items count: 20%
        - Risk assessment flags: 30%
        - Data quality concerns: 10%
        """
        # Non-compliance rate
        yes_count = sum(1 for q in report.question_responses if q.answer == AnswerType.YES)
        no_count = sum(1 for q in report.question_responses if q.answer == AnswerType.NO)
        na_count = sum(1 for q in report.question_responses if q.answer == AnswerType.NA)
        total_non_nr = yes_count + no_count + na_count
        non_compliance_rate = (no_count / total_non_nr * 100) if total_non_nr > 0 else 0.0

        # Action items (normalize to 0-100, assume 10+ items = max risk)
        action_item_score = min(len(report.action_items) / 10 * 100, 100)

        # Risk flags
        risk_score = 0
        if report.risk_assessment.site_level_risks_identified:
            risk_score += 25
        if report.risk_assessment.cra_level_risks_identified:
            risk_score += 25
        if report.risk_assessment.impact_country_level:
            risk_score += 25
        if report.risk_assessment.impact_study_level:
            risk_score += 25

        # Data quality (inverse: low quality = high risk)
        data_quality_risk = (1 - report.data_quality.completeness_score) * 100

        # Weighted composite
        composite = (
            non_compliance_rate * 0.4 +
            action_item_score * 0.2 +
            risk_score * 0.3 +
            data_quality_risk * 0.1
        )

        return round(composite, 2)

    def _get_period_key(self, date: datetime, granularity: str) -> str:
        """Get period key for grouping (e.g., '2025-Q1', '2025-03', '2025-W12')."""
        if granularity == "day":
            return date.strftime("%Y-%m-%d")
        elif granularity == "week":
            return date.strftime("%Y-W%U")
        elif granularity == "month":
            return date.strftime("%Y-%m")
        elif granularity == "quarter":
            quarter = (date.month - 1) // 3 + 1
            return f"{date.year}-Q{quarter}"
        else:
            return date.strftime("%Y-%m")
