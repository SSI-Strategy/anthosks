"""PDF text extraction with layout preservation."""

import pdfplumber
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class PDFParser:
    """Extract text from MOV PDF reports with layout preservation."""

    def __init__(self, preserve_layout: bool = True):
        self.preserve_layout = preserve_layout

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract all text from PDF with page markers.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Full text with page separators
        """
        logger.info(f"Extracting text from: {pdf_path}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_text = []

                for i, page in enumerate(pdf.pages, 1):
                    # Extract with layout preservation
                    text = page.extract_text(layout=self.preserve_layout)

                    if text:
                        pages_text.append(f"--- PAGE {i} ---\n{text}\n")
                    else:
                        logger.warning(f"No text extracted from page {i}")

                full_text = "\n".join(pages_text)

                logger.info(
                    f"Extracted {len(pages_text)} pages, "
                    f"{len(full_text)} characters"
                )

                return full_text

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise

    def extract_metadata(self, pdf_path: Path) -> Dict:
        """Extract PDF metadata."""
        with pdfplumber.open(pdf_path) as pdf:
            return {
                "page_count": len(pdf.pages),
                "metadata": pdf.metadata,
                "file_size_mb": pdf_path.stat().st_size / (1024 * 1024)
            }
