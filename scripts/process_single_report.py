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
        logger.info("Step 1/5: Extracting PDF text...")
        parser = PDFParser()
        pdf_text = parser.extract_text(pdf_path)
        logger.info(f"Extracted {len(pdf_text)} characters")

        # 2. LLM extraction
        logger.info("Step 2/5: Extracting structured data with LLM...")
        extractor = LLMExtractor()
        report = extractor.extract_report(pdf_text, pdf_path.name)
        logger.info(f"Extracted {len(report.question_responses)} questions")

        # 3. Validation
        logger.info("Step 3/5: Validating extracted data...")
        validator = ReportValidator()
        validation_result = validator.validate(report)
        logger.info(f"Validation: {validation_result['data_quality']}")

        # 4. Save to database
        logger.info("Step 4/5: Saving to database...")
        db = SQLiteDatabase(config.DATABASE_PATH)
        report_id = db.save_report(report)
        logger.info(f"Saved to database: {report_id}")

        # 5. Save JSON output
        logger.info("Step 5/5: Saving JSON output...")
        storage = LocalStorage(config.OUTPUT_PATH)
        output_file = f"{pdf_path.stem}_extracted.json"
        output_path = config.OUTPUT_PATH / output_file
        output_path.write_text(report.model_dump_json(indent=2))
        logger.info(f"Saved JSON: {output_path}")

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
    print("MOV REPORT EXTRACTION")
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
