"""Detailed analysis of MOV report structure with text samples."""

import sys
from pathlib import Path
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from extraction.pdf_parser import PDFParser


def extract_page_content(text: str, page_num: int) -> str:
    """Extract content for a specific page."""
    pattern = f"--- PAGE {page_num} ---\n(.*?)(?=--- PAGE|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1) if match else ""


def analyze_document_detailed(pdf_path: Path):
    """Detailed analysis of a single MOV report."""
    print(f"\n{'='*80}")
    print(f"DETAILED ANALYSIS: {pdf_path.name}")
    print(f"{'='*80}")

    parser = PDFParser(preserve_layout=True)
    text = parser.extract_text(pdf_path)
    metadata = parser.extract_metadata(pdf_path)

    # Show first page (header)
    print("\n--- FIRST PAGE CONTENT (Header) ---")
    first_page = extract_page_content(text, 1)
    print(first_page[:1000] + "..." if len(first_page) > 1000 else first_page)

    # Show second page (where questions typically start)
    print("\n--- SECOND PAGE CONTENT (Question Start) ---")
    second_page = extract_page_content(text, 2)
    print(second_page[:1500] + "..." if len(second_page) > 1500 else second_page)

    # Find and show a mid-document page
    mid_page = metadata['page_count'] // 2
    print(f"\n--- MID-DOCUMENT PAGE {mid_page} ---")
    mid_content = extract_page_content(text, mid_page)
    print(mid_content[:1000] + "..." if len(mid_content) > 1000 else mid_content)

    # Show last page
    print(f"\n--- LAST PAGE {metadata['page_count']} ---")
    last_page = extract_page_content(text, metadata['page_count'])
    print(last_page[:1000] + "..." if len(last_page) > 1000 else last_page)

    # Search for section headers
    print("\n--- SECTION HEADERS FOUND ---")
    section_patterns = [
        r'(?:^|\n)([A-Z\s]{10,})\n',  # All caps headers
        r'(?:^|\n)((?:Question|Action|Risk|Recruitment|Site|Study)\s+[^\n]{5,50})\n',
        r'(?:^|\n)(\d+\.\s*[A-Z][^\n]{10,50})\n'  # Numbered sections
    ]

    for pattern in section_patterns:
        matches = re.finditer(pattern, text[:5000], re.MULTILINE)  # First 5000 chars
        for match in matches:
            header = match.group(1).strip()
            if len(header) > 10 and len(header) < 100:
                print(f"  - {header}")
            if len([m for m in re.finditer(pattern, text[:5000], re.MULTILINE)]) > 20:
                break  # Too many matches, probably not real headers


def main():
    """Analyze one document in detail."""
    base_path = Path(__file__).parent / "references"

    # Analyze just one document in detail
    pdf_path = base_path / "Anthos_MOV Rpt_Simioni_738010_20250409.pdf"

    if pdf_path.exists():
        analyze_document_detailed(pdf_path)
    else:
        print(f"File not found: {pdf_path}")


if __name__ == "__main__":
    main()
