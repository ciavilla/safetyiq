"""
ingestion/parser.py
Extracts raw text from PDF files.

Takes a PDF file path, returns a list of pages where each
page is a dict with the page number and its text content.
"""

import PyPDF2
from pathlib import Path


def parse_pdf(pdf_path: str) -> list[dict]:
    """
    Extracts text from a PDF file, page by page.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of dicts, one per page:
        [
            {"page_number": 1, "text": "page content here..."},
            {"page_number": 2, "text": "more content..."},
            ...
        ]
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = []

    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)

        print(f"   📖 Found {len(reader.pages)} pages")

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            # Skip pages with no extractable text (e.g. image-only pages)
            if text and text.strip():
                pages.append({
                    "page_number": page_num,
                    "text": text.strip()
                })

    print(f"   ✅ Extracted text from {len(pages)} pages")
    return pages
