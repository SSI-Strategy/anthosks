"""FastAPI backend for MOV report extraction system."""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import config
from src.database.sqlite_db import SQLiteDatabase
from src.database.postgres_db import PostgreSQLDatabase
from src.extraction.pdf_parser import PDFParser
from src.extraction.docx_parser import DOCXParser
from src.extraction.chunked_extractor import ChunkedExtractor
from src.models import MOVReport
from src.analytics.service import AnalyticsService
from src.auth import get_current_user, get_optional_user

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MOV Report Extraction API",
    description="API for extracting and managing MOV report data",
    version="1.0.0"
)

# Configure CORS
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database (use PostgreSQL if DATABASE_URL is set, otherwise SQLite)
if config.DATABASE_URL:
    logger.info(f"Using PostgreSQL database")
    db = PostgreSQLDatabase(config.DATABASE_URL)
else:
    logger.info(f"Using SQLite database at {config.DATABASE_PATH}")
    db = SQLiteDatabase(config.DATABASE_PATH)

# Initialize analytics service
analytics = AnalyticsService(db)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "MOV Report Extraction API"}


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "message": "Healthy"}


@app.post("/api/reports/upload")
async def upload_report(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload and process a PDF or DOCX report."""
    logger.info(f"Received file: {file.filename} from user: {user.get('email')}")

    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.pdf', '.docx']:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are accepted")

    try:
        # Save uploaded file
        temp_path = Path(config.INPUT_PATH) / file.filename
        content = await file.read()
        temp_path.write_bytes(content)
        logger.info(f"Saved file to: {temp_path}")

        # Extract text based on file type
        if file_ext == '.pdf':
            parser = PDFParser()
            document_text = parser.extract_text(temp_path)
            logger.info(f"Extracted {len(document_text)} characters from PDF")
        else:  # .docx
            parser = DOCXParser()
            document_text = parser.extract_text(temp_path)
            logger.info(f"Extracted {len(document_text)} characters from DOCX")

        # LLM extraction (chunked parallel approach)
        extractor = ChunkedExtractor()
        report = extractor.extract_report_chunked(document_text, file.filename)
        logger.info(f"Extracted report with {len(report.question_responses)} questions")

        # Save to database
        report_id = db.save_report(report)
        logger.info(f"Saved report with ID: {report_id}")

        return {
            "status": "success",
            "report_id": report_id,
            "questions": len(report.question_responses),
            "action_items": len(report.action_items),
            "quality": report.overall_site_quality
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports")
async def list_reports(limit: int = 100, offset: int = 0, user: dict = Depends(get_current_user)):
    """List all reports with pagination."""
    try:
        reports = db.list_reports(limit=limit, offset=offset)

        # Convert to dict format for JSON response
        reports_data = []
        for report in reports:
            reports_data.append({
                "id": f"{report.site_info.site_number}_{report.visit_start_date}",
                "site_number": report.site_info.site_number,
                "country": report.site_info.country,
                "institution": report.site_info.institution,
                "visit_start_date": report.visit_start_date,
                "visit_end_date": report.visit_end_date,
                "visit_type": report.visit_type.value if report.visit_type else None,
                "quality": report.overall_site_quality,
                "questions_count": len(report.question_responses),
                "action_items_count": len(report.action_items)
            })

        return {"reports": reports_data, "total": len(reports_data)}

    except Exception as e:
        logger.error(f"List reports failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str, user: dict = Depends(get_current_user)):
    """Get a specific report by ID."""
    try:
        report = db.get_report(report_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Convert to dict format
        return {
            "id": report_id,
            "protocol_number": report.protocol_number,
            "site_info": {
                "site_number": report.site_info.site_number,
                "country": report.site_info.country,
                "institution": report.site_info.institution,
                "pi_first_name": report.site_info.pi_first_name,
                "pi_last_name": report.site_info.pi_last_name,
                "city": report.site_info.city,
                "anthos_staff": report.site_info.anthos_staff,
                "cra_name": report.site_info.cra_name
            },
            "visit_start_date": report.visit_start_date,
            "visit_end_date": report.visit_end_date,
            "visit_type": report.visit_type.value if report.visit_type else None,
            "recruitment_stats": report.recruitment_stats.model_dump(),
            "question_responses": [
                {
                    "question_number": q.question_number,
                    "question_text": q.question_text,
                    "answer": q.answer.value,
                    "sentiment": q.sentiment.value,
                    "narrative_summary": q.narrative_summary,
                    "key_finding": q.key_finding,
                    "evidence": q.evidence,
                    "confidence": q.confidence
                }
                for q in report.question_responses
            ],
            "action_items": [
                {
                    "item_number": item.item_number,
                    "description": item.description,
                    "action_to_be_taken": item.action_to_be_taken,
                    "responsible": item.responsible,
                    "due_date": item.due_date,
                    "status": item.status
                }
                for item in report.action_items
            ],
            "risk_assessment": report.risk_assessment.model_dump(),
            "overall_site_quality": report.overall_site_quality,
            "key_concerns": report.key_concerns,
            "key_strengths": report.key_strengths,
            "extraction_timestamp": report.extraction_timestamp.isoformat(),
            "llm_model": report.llm_model,
            "source_file": report.source_file
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/reports/{report_id}")
async def delete_report(report_id: str, user: dict = Depends(get_current_user)):
    """Delete a report."""
    logger.info(f"User {user.get('email')} deleting report {report_id}")
    try:
        success = db.delete_report(report_id)

        if not success:
            raise HTTPException(status_code=404, detail="Report not found")

        return {"status": "success", "message": f"Report {report_id} deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete report failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== ANALYTICS ENDPOINTS =====

@app.get("/api/analytics/kpi")
async def get_kpis(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    country: Optional[str] = Query(None),
    protocol: Optional[str] = Query(None),
    site_number: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get KPI metrics for dashboard."""
    try:
        # Parse dates
        df = datetime.fromisoformat(date_from) if date_from else None
        dt = datetime.fromisoformat(date_to) if date_to else None

        # Build filters
        filters = {}
        if country:
            filters['country'] = country
        if protocol:
            filters['protocol_number'] = protocol
        if site_number:
            filters['site_number'] = site_number

        kpis = analytics.calculate_kpis(date_from=df, date_to=dt, filters=filters if filters else None)
        return kpis

    except Exception as e:
        logger.error(f"KPI calculation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/compliance/trends")
async def get_compliance_trends(
    date_from: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(..., description="End date (YYYY-MM-DD)"),
    granularity: str = Query("month", description="Time granularity: day, week, month, quarter"),
    country: Optional[str] = Query(None),
    protocol: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get compliance rate trends over time."""
    try:
        df = datetime.fromisoformat(date_from)
        dt = datetime.fromisoformat(date_to)

        filters = {}
        if country:
            filters['country'] = country
        if protocol:
            filters['protocol_number'] = protocol

        trends = analytics.get_compliance_trends(
            date_from=df,
            date_to=dt,
            granularity=granularity,
            filters=filters if filters else None
        )
        return {"trends": trends}

    except Exception as e:
        logger.error(f"Compliance trends failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/compliance/questions")
async def get_question_statistics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    protocol: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get compliance statistics for all 85 questions."""
    try:
        df = datetime.fromisoformat(date_from) if date_from else None
        dt = datetime.fromisoformat(date_to) if date_to else None

        filters = {}
        if country:
            filters['country'] = country
        if protocol:
            filters['protocol_number'] = protocol

        stats = analytics.get_question_statistics(
            date_from=df,
            date_to=dt,
            filters=filters if filters else None
        )
        return {"questions": stats}

    except Exception as e:
        logger.error(f"Question statistics failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/sites/leaderboard")
async def get_site_leaderboard(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort_by: str = Query("compliance_rate", description="Sort by: compliance_rate, quality_score, enrollment_rate"),
    limit: int = Query(100, ge=1, le=1000),
    country: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get site performance leaderboard."""
    try:
        df = datetime.fromisoformat(date_from) if date_from else None
        dt = datetime.fromisoformat(date_to) if date_to else None

        filters = {}
        if country:
            filters['country'] = country

        leaderboard = analytics.get_site_leaderboard(
            date_from=df,
            date_to=dt,
            filters=filters if filters else None,
            sort_by=sort_by,
            limit=limit
        )
        return {"sites": leaderboard}

    except Exception as e:
        logger.error(f"Site leaderboard failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/geographic")
async def get_geographic_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    protocol: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get compliance and performance metrics by country."""
    try:
        df = datetime.fromisoformat(date_from) if date_from else None
        dt = datetime.fromisoformat(date_to) if date_to else None

        filters = {}
        if protocol:
            filters['protocol_number'] = protocol

        summary = analytics.get_geographic_summary(
            date_from=df,
            date_to=dt,
            filters=filters if filters else None
        )
        return {"countries": summary}

    except Exception as e:
        logger.error(f"Geographic summary failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
