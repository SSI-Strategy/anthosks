#!/usr/bin/env python3
"""Process all MOV reports in the input folder."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from scripts.process_single_report import process_report

def main():
    """Process all PDFs in input folder."""
    input_path = Path(config.INPUT_PATH)
    pdf_files = list(input_path.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {input_path}")
        print("Copy your MOV reports to data/input/ and try again")
        return

    print(f"Found {len(pdf_files)} PDF files to process")
    print("=" * 60)

    results = []
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        print("-" * 60)

        result = process_report(pdf_file)
        results.append({
            "file": pdf_file.name,
            "status": result["status"],
            "questions": result.get("questions_extracted", 0) if result["status"] == "success" else 0
        })

        if result["status"] == "success":
            print(f"✅ Success: {result['questions_extracted']} questions extracted")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    successful = sum(1 for r in results if r["status"] == "success")
    print(f"Processed: {len(results)} files")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    if successful > 0:
        print(f"\nOutputs saved to: {config.OUTPUT_PATH}")
        print(f"Database: {config.DATABASE_PATH}")

if __name__ == "__main__":
    main()
