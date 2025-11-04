"""PostgreSQL database implementation for production."""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
from datetime import datetime

from .base import DatabaseProvider
from ..models import MOVReport
from ..config import config

Base = declarative_base()


class ReportRecord(Base):
    """SQLAlchemy model for MOV reports in PostgreSQL."""
    __tablename__ = "mov_reports"
    __table_args__ = {"schema": "anthosks"}

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


class PostgreSQLDatabase(DatabaseProvider):
    """PostgreSQL database implementation."""

    def __init__(self, connection_url: str):
        """
        Initialize PostgreSQL connection with connection pooling.

        Args:
            connection_url: PostgreSQL connection string
                Format: postgresql://user:password@host:port/database
                Example: postgresql://postgres:password@localhost:5432/sandbox_db
        """
        # Create engine with connection pooling
        # pool_pre_ping ensures connections are alive before using them
        # pool_size controls the number of persistent connections
        # max_overflow allows additional connections when needed
        # Settings are configurable via environment variables
        self.engine = create_engine(
            connection_url,
            pool_pre_ping=True,              # Verify connections before using
            pool_size=config.DB_POOL_SIZE,   # Configurable via DB_POOL_SIZE (default: 5)
            max_overflow=config.DB_MAX_OVERFLOW,  # Configurable via DB_MAX_OVERFLOW (default: 10)
            pool_recycle=config.DB_POOL_RECYCLE,  # Configurable via DB_POOL_RECYCLE (default: 3600s)
            echo=False                       # Set to True for SQL debugging
        )

        # Create schema if it doesn't exist
        with self.engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS anthosks"))
            conn.commit()

        # Create tables in anthosks schema
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_report(self, report: MOVReport) -> str:
        """Save report to PostgreSQL."""
        session = self.Session()
        try:
            # Handle None visit_start_date - use "UNKNOWN" in report_id
            visit_date_str = report.visit_start_date if report.visit_start_date else "UNKNOWN"
            report_id = f"{report.site_info.site_number}_{visit_date_str}"

            # Convert visit_start_date to datetime if available, otherwise None
            visit_date_obj = datetime.fromisoformat(report.visit_start_date) if report.visit_start_date else None

            record = ReportRecord(
                id=report_id,
                protocol_number=report.protocol_number,
                site_number=report.site_info.site_number,
                visit_date=visit_date_obj,
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
    ) -> List[tuple[str, MOVReport]]:
        """List reports with pagination. Returns list of (id, report) tuples."""
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

            return [(r.id, MOVReport.model_validate_json(r.json_data)) for r in records]
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
