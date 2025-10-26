"""SQLite database implementation for local development."""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from typing import List, Optional
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
    visit_type = Column(String, nullable=True)
    overall_quality = Column(String, nullable=True)
    extraction_timestamp = Column(DateTime)
    json_data = Column(Text)  # Full report as JSON
    source_file = Column(String)

    # Data quality metrics
    completeness_score = Column(Float, index=True)
    requires_review = Column(Boolean, index=True, default=False)
    review_reason = Column(Text, nullable=True)


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
                visit_type=report.visit_type.value if report.visit_type else None,
                overall_quality=report.overall_site_quality,
                extraction_timestamp=report.extraction_timestamp,
                json_data=report.model_dump_json(),
                source_file=report.source_file,
                completeness_score=report.data_quality.completeness_score,
                requires_review=report.data_quality.requires_review,
                review_reason=report.data_quality.review_reason
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
                return MOVReport.model_validate_json(record.json_data)
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

            return [MOVReport.model_validate_json(r.json_data) for r in records]
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
        """Basic text search."""
        session = self.Session()
        try:
            records = session.query(ReportRecord) \
                             .filter(ReportRecord.json_data.like(f"%{query}%")) \
                             .all()
            return [MOVReport.model_validate_json(r.json_data) for r in records]
        finally:
            session.close()
