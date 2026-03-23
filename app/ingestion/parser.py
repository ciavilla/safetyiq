"""
ingestion/parser.py
Extracts raw text from PDF files.

Takes a PDF file path, returns a list of pages where each
page is a dict with the page number and its text content.
"""

import PyPDF2
from pathlib import Path
import httpx
from bs4 import BeautifulSoup


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

def parse_html_url(url: str) -> list[dict]:
    """
    Fetches an HTML page from a URL and extracts clean text.
    Returns the same format as parse_pdf() so the rest of
    the pipeline works identically.
    """
    print(f"   🌐 Fetching HTML page...")
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove nav, footer, scripts, styles — we only want content
    for tag in soup(["nav", "footer", "script", "style", "header"]):
        tag.decompose()

    # Try to find the main content area first
    main = soup.find("main") or soup.find("article") or soup.find("div", {"id": "main-content"}) or soup.body

    text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)

    # Clean up excessive blank lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)

    if not clean_text:
        print(f"   ❌ No text extracted from HTML")
        return []

    print(f"   ✅ Extracted text from HTML page")

    # Return as a single "page" so it fits the same format as PDF output
    return [{"page_number": 1, "text": clean_text}]
