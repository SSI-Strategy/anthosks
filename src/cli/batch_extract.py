#!/usr/bin/env python3
"""CLI tool for batch processing MOV reports (PDF and DOCX)."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import config
from src.database.sqlite_db import SQLiteDatabase
from src.database.postgres_db import PostgreSQLDatabase
from src.extraction.pdf_parser import PDFParser
from src.extraction.docx_parser import DOCXParser
from src.extraction.chunked_extractor import ChunkedExtractor
from src.models import MOVReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_supported_files(directory: Path) -> List[Path]:
    """Get all supported document files from directory."""
    supported_extensions = ['.pdf', '.docx']
    files = []

    for ext in supported_extensions:
        files.extend(directory.glob(f'*{ext}'))

    return sorted(files)


def extract_document(file_path: Path) -> Optional[MOVReport]:
    """Extract data from a single document (PDF or DOCX)."""
    logger.info(f"Processing: {file_path.name}")

    try:
        # Parse document based on extension
        file_ext = file_path.suffix.lower()

        if file_ext == '.pdf':
            parser = PDFParser()
            document_text = parser.extract_text(file_path)
            logger.info(f"Extracted {len(document_text)} characters from PDF")
        elif file_ext == '.docx':
            parser = DOCXParser()
            document_text = parser.extract_text(file_path)
            logger.info(f"Extracted {len(document_text)} characters from DOCX")
        else:
            logger.error(f"Unsupported file type: {file_ext}")
            return None

        # Extract structured data
        extractor = ChunkedExtractor()
        report = extractor.extract_report_chunked(document_text, file_path.name)

        logger.info(
            f"Extracted {len(report.question_responses)} questions, "
            f"{len(report.action_items)} action items"
        )

        return report

    except Exception as e:
        logger.error(f"Failed to process {file_path.name}: {e}", exc_info=True)
        return None


def export_to_excel(reports: List[MOVReport], output_path: Path):
    """Export reports to Excel file."""
    logger.info(f"Exporting {len(reports)} reports to Excel: {output_path}")

    # Prepare data for export
    rows = []

    for report in reports:
        for question in report.question_responses:
            rows.append({
                'File': report.source_file,
                'Site_Number': report.site_info.site_number,
                'Country': report.site_info.country,
                'Visit_Date': report.visit_start_date,
                'Visit_Type': report.visit_type.value if report.visit_type else None,
                'Question_Number': question.question_number,
                'Question_Text': question.question_text,
                'Answer': question.answer.value,
                'Sentiment': question.sentiment.value,
                'Narrative_Summary': question.narrative_summary,
                'Key_Finding': question.key_finding,
                'Evidence': question.evidence,
                'Confidence': question.confidence,
                'Overall_Quality': report.overall_site_quality
            })

    # Create DataFrame and export
    df = pd.DataFrame(rows)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Main data
        df.to_excel(writer, sheet_name='Extracted_Data', index=False)

        # Summary
        summary_data = []
        for report in reports:
            summary_data.append({
                'File': report.source_file,
                'Site_Number': report.site_info.site_number,
                'Country': report.site_info.country,
                'Visit_Start': report.visit_start_date,
                'Visit_End': report.visit_end_date,
                'Visit_Type': report.visit_type.value if report.visit_type else None,
                'Questions_Extracted': len(report.question_responses),
                'Action_Items': len(report.action_items),
                'Overall_Quality': report.overall_site_quality,
                'Extraction_Method': report.extraction_method,
                'LLM_Model': report.llm_model,
                'Extraction_Time': report.extraction_timestamp
            })

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

    logger.info(f"Exported {len(rows)} question responses to {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch extract MOV reports from PDF and DOCX files"
    )

    parser.add_argument(
        'input_dir',
        type=str,
        help='Directory containing PDF and DOCX files to process'
    )

    parser.add_argument(
        '--output-excel',
        type=str,
        help='Export results to Excel file (optional)'
    )

    parser.add_argument(
        '--save-to-db',
        action='store_true',
        help='Save results to database'
    )

    parser.add_argument(
        '--file-pattern',
        type=str,
        default='*',
        help='File pattern to match (e.g., "ANT-*")'
    )

    parser.add_argument(
        '--max-files',
        type=int,
        help='Maximum number of files to process (for testing)'
    )

    args = parser.parse_args()

    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)

    if not input_dir.is_dir():
        logger.error(f"Input path is not a directory: {input_dir}")
        sys.exit(1)

    # Get files to process
    all_files = get_supported_files(input_dir)

    # Filter by pattern if specified
    if args.file_pattern != '*':
        all_files = [f for f in all_files if f.match(args.file_pattern)]

    # Limit number of files if specified
    if args.max_files:
        all_files = all_files[:args.max_files]

    if not all_files:
        logger.error(f"No PDF or DOCX files found in {input_dir}")
        sys.exit(1)

    logger.info(f"Found {len(all_files)} files to process")

    # Process files
    reports = []
    failed_files = []

    for i, file_path in enumerate(all_files, 1):
        logger.info(f"\n[{i}/{len(all_files)}] Processing: {file_path.name}")

        report = extract_document(file_path)

        if report:
            reports.append(report)
            logger.info(f"✓ Successfully processed {file_path.name}")
        else:
            failed_files.append(file_path.name)
            logger.error(f"✗ Failed to process {file_path.name}")

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"BATCH PROCESSING SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total files: {len(all_files)}")
    logger.info(f"Successfully processed: {len(reports)}")
    logger.info(f"Failed: {len(failed_files)}")

    if failed_files:
        logger.info(f"\nFailed files:")
        for filename in failed_files:
            logger.info(f"  - {filename}")

    # Save to database if requested
    if args.save_to_db and reports:
        logger.info(f"\nSaving {len(reports)} reports to database...")

        # Use PostgreSQL if DATABASE_URL is set, otherwise SQLite
        if config.DATABASE_URL:
            logger.info(f"Using PostgreSQL database")
            db = PostgreSQLDatabase(config.DATABASE_URL)
        else:
            logger.info(f"Using SQLite database at {config.DATABASE_PATH}")
            db = SQLiteDatabase(config.DATABASE_PATH)

        for report in reports:
            try:
                report_id = db.save_report(report)
                logger.info(f"  Saved: {report.source_file} (ID: {report_id})")
            except Exception as e:
                logger.error(f"  Failed to save {report.source_file}: {e}")

    # Export to Excel if requested
    if args.output_excel and reports:
        output_path = Path(args.output_excel)
        export_to_excel(reports, output_path)

    logger.info(f"\n{'='*60}")
    logger.info("Batch processing complete!")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    main()
