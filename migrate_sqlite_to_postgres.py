#!/usr/bin/env python3
"""Migrate data from SQLite to PostgreSQL."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.database.sqlite_db import SQLiteDatabase
from src.database.postgres_db import PostgreSQLDatabase
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate():
    """Migrate all reports from SQLite to PostgreSQL."""

    # Check if DATABASE_URL is configured
    if not config.DATABASE_URL:
        logger.error("DATABASE_URL not configured in .env file!")
        sys.exit(1)

    logger.info(f"Migrating from SQLite: {config.DATABASE_PATH}")
    logger.info(f"Migrating to PostgreSQL: {config.DATABASE_URL}")

    # Initialize databases
    sqlite_db = SQLiteDatabase(config.DATABASE_PATH)
    postgres_db = PostgreSQLDatabase(config.DATABASE_URL)

    # Get all reports from SQLite
    logger.info("Reading reports from SQLite...")
    reports = sqlite_db.list_reports(limit=1000)  # Adjust limit if needed

    if not reports:
        logger.warning("No reports found in SQLite database!")
        return

    logger.info(f"Found {len(reports)} reports to migrate")

    # Migrate each report
    migrated = 0
    failed = 0

    for i, report in enumerate(reports, 1):
        try:
            report_id = postgres_db.save_report(report)
            logger.info(f"[{i}/{len(reports)}] Migrated: {report.source_file} (ID: {report_id})")
            migrated += 1
        except Exception as e:
            logger.error(f"[{i}/{len(reports)}] Failed to migrate {report.source_file}: {e}")
            failed += 1

    # Summary
    logger.info("=" * 60)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total reports: {len(reports)}")
    logger.info(f"Successfully migrated: {migrated}")
    logger.info(f"Failed: {failed}")
    logger.info("=" * 60)


if __name__ == "__main__":
    migrate()
