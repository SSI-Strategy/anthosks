"""Analyze MOV report structure to validate chunking strategy."""

import sys
from pathlib import Path
import re
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from extraction.pdf_parser import PDFParser


def find_question_locations(text: str) -> dict:
    """Find where questions 1-85 appear in the text."""
    # Look for question patterns like "Question 1:", "1.", "Q1:", etc.
    question_pattern = r'(?:Question\s*|Q\.?\s*)?(\d{1,2})(?:\.|:|\))\s+'

    locations = {}
    for match in re.finditer(question_pattern, text, re.IGNORECASE):
        q_num = int(match.group(1))
        if 1 <= q_num <= 85:
            # Find which page this is on
            text_before = text[:match.start()]
            page_markers = re.findall(r'--- PAGE (\d+) ---', text_before)
            if page_markers:
                page_num = int(page_markers[-1])
                if q_num not in locations:  # Keep first occurrence
                    locations[q_num] = {
                        'page': page_num,
                        'char_position': match.start(),
                        'context': text[match.start():match.start()+100]
                    }

    return locations


def find_sections(text: str) -> dict:
    """Find key sections in the document."""
    sections = {}

    # Look for header info patterns
    site_match = re.search(r'Site\s*(?:Name|ID)?[:\s]*([^\n]+)', text, re.IGNORECASE)
    if site_match:
        text_before = text[:site_match.start()]
        page_markers = re.findall(r'--- PAGE (\d+) ---', text_before)
        sections['site_info'] = int(page_markers[-1]) if page_markers else 1

    pi_match = re.search(r'(?:Principal\s*Investigator|PI)[:\s]*([^\n]+)', text, re.IGNORECASE)
    if pi_match:
        text_before = text[:pi_match.start()]
        page_markers = re.findall(r'--- PAGE (\d+) ---', text_before)
        sections['pi_info'] = int(page_markers[-1]) if page_markers else 1

    # Look for action items
    action_match = re.search(r'Action\s*Items?|Corrective\s*Actions?', text, re.IGNORECASE)
    if action_match:
        text_before = text[:action_match.start()]
        page_markers = re.findall(r'--- PAGE (\d+) ---', text_before)
        sections['action_items'] = int(page_markers[-1]) if page_markers else None

    # Look for risk assessment
    risk_match = re.search(r'Risk\s*Assessment|Overall\s*Risk', text, re.IGNORECASE)
    if risk_match:
        text_before = text[:risk_match.start()]
        page_markers = re.findall(r'--- PAGE (\d+) ---', text_before)
        sections['risk_assessment'] = int(page_markers[-1]) if page_markers else None

    return sections


def analyze_document(pdf_path: Path) -> dict:
    """Analyze a single MOV report."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path.name}")
    print(f"{'='*80}")

    parser = PDFParser(preserve_layout=True)

    # Extract metadata
    metadata = parser.extract_metadata(pdf_path)
    print(f"\nMetadata:")
    print(f"  Page count: {metadata['page_count']}")
    print(f"  File size: {metadata['file_size_mb']:.2f} MB")

    # Extract text
    text = parser.extract_text(pdf_path)
    char_count = len(text)
    print(f"  Total characters: {char_count:,}")

    # Find sections
    sections = find_sections(text)
    print(f"\nKey Sections:")
    for section_name, page_num in sections.items():
        print(f"  {section_name}: Page {page_num}")

    # Find questions
    question_locs = find_question_locations(text)
    print(f"\nQuestions Found: {len(question_locs)} out of 85")

    if question_locs:
        q_nums = sorted(question_locs.keys())
        first_q = q_nums[0]
        last_q = q_nums[-1]
        print(f"  First question: Q{first_q} on page {question_locs[first_q]['page']}")
        print(f"  Last question: Q{last_q} on page {question_locs[last_q]['page']}")

        # Analyze distribution across pages
        pages_with_questions = set(q['page'] for q in question_locs.values())
        print(f"  Questions span pages: {min(pages_with_questions)} - {max(pages_with_questions)}")

        # Check if questions are in order
        in_order = all(q_nums[i] < q_nums[i+1] for i in range(len(q_nums)-1))
        print(f"  Questions in sequential order: {in_order}")

        # Show question batches
        print(f"\n  Question Distribution by Proposed Batches:")
        batches = [
            (1, 15, "Batch 1"),
            (16, 30, "Batch 2"),
            (31, 45, "Batch 3"),
            (46, 60, "Batch 4"),
            (61, 75, "Batch 5"),
            (76, 85, "Batch 6")
        ]

        for start, end, batch_name in batches:
            batch_qs = [q for q in q_nums if start <= q <= end]
            if batch_qs:
                pages = sorted(set(question_locs[q]['page'] for q in batch_qs))
                print(f"    {batch_name} (Q{start}-{end}): {len(batch_qs)} questions on pages {pages[0]}-{pages[-1]}")

        # Show some missing questions
        missing = sorted(set(range(1, 86)) - set(q_nums))
        if missing:
            print(f"\n  Missing questions: {len(missing)}")
            if len(missing) <= 10:
                print(f"    {missing}")
            else:
                print(f"    First 10: {missing[:10]}")
                print(f"    Last 10: {missing[-10:]}")

    return {
        'file': pdf_path.name,
        'page_count': metadata['page_count'],
        'char_count': char_count,
        'sections': sections,
        'questions_found': len(question_locs),
        'question_locations': question_locs
    }


def main():
    """Analyze the three specified MOV reports."""
    base_path = Path(__file__).parent / "references"

    pdf_files = [
        "Anthos_MOV Rpt _Palomares_772412_20250528.pdf",
        "Anthos_MOV Rpt_Simioni_738010_20250409.pdf",
        "Anthos_MOV Rpt_Patel_784009_20250421.pdf"
    ]

    results = []
    for pdf_file in pdf_files:
        pdf_path = base_path / pdf_file
        if pdf_path.exists():
            result = analyze_document(pdf_path)
            results.append(result)
        else:
            print(f"WARNING: File not found: {pdf_path}")

    # Summary analysis
    print(f"\n{'='*80}")
    print("SUMMARY ANALYSIS")
    print(f"{'='*80}")

    if results:
        avg_pages = sum(r['page_count'] for r in results) / len(results)
        avg_chars = sum(r['char_count'] for r in results) / len(results)
        avg_questions = sum(r['questions_found'] for r in results) / len(results)

        print(f"\nAverage Statistics:")
        print(f"  Pages: {avg_pages:.1f}")
        print(f"  Characters: {avg_chars:,.0f}")
        print(f"  Questions found: {avg_questions:.1f} / 85")

        print(f"\nStructural Variations:")
        # Check if header sections are consistent
        header_pages = [r['sections'].get('site_info', 1) for r in results]
        print(f"  Site info appears on pages: {set(header_pages)}")

        # Check action items location
        action_pages = [r['sections'].get('action_items') for r in results if r['sections'].get('action_items')]
        if action_pages:
            print(f"  Action items appear on pages: {action_pages}")
            for r in results:
                if r['sections'].get('action_items'):
                    pct = (r['sections']['action_items'] / r['page_count']) * 100
                    print(f"    {r['file']}: Page {r['sections']['action_items']} ({pct:.0f}% through doc)")

        # Check risk assessment location
        risk_pages = [r['sections'].get('risk_assessment') for r in results if r['sections'].get('risk_assessment')]
        if risk_pages:
            print(f"  Risk assessment appears on pages: {risk_pages}")
            for r in results:
                if r['sections'].get('risk_assessment'):
                    pct = (r['sections']['risk_assessment'] / r['page_count']) * 100
                    print(f"    {r['file']}: Page {r['sections']['risk_assessment']} ({pct:.0f}% through doc)")

    print("\n")


if __name__ == "__main__":
    main()
