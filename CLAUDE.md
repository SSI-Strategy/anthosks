# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AnthosKS is a compliance document extraction and analytics system. The project extracts structured question-answer data from vendor audit/compliance documents (PDFs and DOCX files) and produces:
- A master Excel file with extracted Q&A data
- Analytics on completeness, distributions, and themes
- QC reports identifying data quality issues

## Architecture

### Two-Pass Extraction Strategy

1. **Deterministic Pass (regex/rule-based)**: Fast, cheap extraction for well-formatted documents
   - Handles 70-85% of cases with consistent formatting
   - Parses DOCX with python-docx, PDF with pdfplumber/pypdf
   - Anchors on question numbers (1-85) and fuzzy-matches canonical question list
   - Extracts: Question ID, Question text, Answer (Yes/No/N/A/NR), Comment

2. **LLM Backfill Pass**: Robust extraction for format chaos
   - For rows missing after deterministic pass (scanned PDFs, varied layouts)
   - Sends page/section chunks to LLM with strict JSON schema
   - Forces model to return null for unfound questions (no hallucination)
   - Requests evidence spans for QC

### Data Flow

```
input/ → Extraction (regex + LLM) → Validation → master.xlsx
                                              ↓
                                    Analytics (themes, trends)
                                              ↓
                                    qc_report.xlsx, themes.md, figures/
```

### Key Data Structures

**Canonical Questions** (canonical_questions.csv):
- QuestionID, CanonicalQuestionText

**Extraction Schema** (per file):
```json
{
  "file": "Vendor_Audit_01.pdf",
  "items": [{
    "question_id": 17,
    "question_text": "...",
    "answer": "Yes|No|N/A|NR",
    "comment": "string or null",
    "evidence": "short snippet for QC",
    "confidence": 0.0-1.0,
    "method": "regex|llm|ocr+llm"
  }]
}
```

**Master Excel Columns**: File, QuestionID, Question, Answer, Comment, Evidence, Confidence, ExtractionMethod

### Analytics Layer

1. **Data Quality**: Per-file coverage (% of 85 questions with non-NR answers)
2. **Descriptive Stats**: Question × Answer pivot counts and rates
3. **Theme Extraction**:
   - Clean comment text → embed/TF-IDF → cluster (HDBSCAN/k-means)
   - Auto-label clusters with top keywords + LLM summarizer
4. **Outlier Detection**: Flag questions with inconsistent answers across files

### Validation Rules

- **Locked Answer Set**: Only Yes/No/N/A/NR allowed
- **Evidence Snippets**: Keep short quote for auditor traceability
- **Confidence Threshold**: < 0.7 → human review queue
- **De-duplication**: Keep highest confidence per (File, QuestionID)

## Directory Structure

- `data/input/`: Place vendor audit documents (PDF, DOCX) here
- `data/output/`: Generated Excel files, reports, and figures
- `references/`: Reference materials and specifications
  - `suggestions.md`: Detailed extraction strategy and sample code
  - `Anthos_ABRS_Global Deployment Tracker_METRICS_20250826.xlsx`: Metrics reference
  - `Anthos_MOV Rpt Summary.docx`: Summary report reference

## Key Patterns

### Text Normalization
- Fix hyphen breaks: `-\n` → ``
- Join wrapped lines
- Normalize whitespace

### Question Block Detection
- Pattern: `Q(?:uestion)?\s*\d{1,3}[.)]?\s*[:\-]?\s*`
- Fuzzy match extracted text to canonical questions (threshold: 85% token_set_ratio)

### LLM Extraction Prompt Structure
**System**: "Extract 85 compliance questions. Allowed answers: Yes/No/N/A/NR. If question not found, set answer to NR. Return strict JSON only. Do not invent content."

**User**: Canonical question list (IDs + text) + text chunk + JSON schema + example + "Include 20-40 word evidence excerpt."

## Python Dependencies

Core stack (from suggestions.md):
```
pdfplumber
python-docx
rapidfuzz
pandas
openpyxl
pydantic
tiktoken
scikit-learn
```

## Analytics Deliverables

1. **master.xlsx**: All extracted Q&A data with metadata
2. **qc_report.xlsx**: Quality control metrics
3. **themes.md**: Clustered comment themes with prevalence rates
4. **Figures**: Heatmaps (Yes/No/N/A/NR by question), top questions by No/NR rate

## Development Notes

- All file paths should reference `data/input/` for source documents
- Maintain change log per run (files processed, timestamp, code version)
- Pin package versions in requirements.txt for reproducibility
- OCR with tesseract/Azure/AWS/GCP if PDFs are scanned images