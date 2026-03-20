"""
scripts/run_ingestion.py
Run this script to ingest your OSHA PDF files into the database.

Usage:
    python3 scripts/run_ingestion.py

Make sure you have:
  1. Docker running with the database container up (docker-compose up -d)
  2. Your .env file configured
  3. PDF files downloaded to data/pdfs/

To download PDFs automatically, set DOWNLOAD_PDFS = True below.
"""

import sys
import os
import httpx
from pathlib import Path

# Add the project root to Python's path so we can import from app/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db

# ─────────────────────────────────────────────
# CONFIGURATION — edit these as needed
# ─────────────────────────────────────────────

# Set to True to automatically download PDFs from OSHA's website
DOWNLOAD_PDFS = True

# OSHA PDFs to ingest — add or remove as you like
# Format: (url, filename, human-readable title)
OSHA_PDFS = [
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3493QuickCardFallProtection.pdf",
        "osha_fall_protection_quick_card.pdf",
        "OSHA Fall Protection Quick Card"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/osha3545.pdf",
        "osha_electrical_safety_quick_card.pdf",
        "OSHA Electrical Safety Quick Card"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/osha3493.pdf",
        "osha_hazard_communication_quick_card.pdf",
        "OSHA Hazard Communication Quick Card"
    ),
]

PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"

# ─────────────────────────────────────────────


def download_pdfs():
    """Downloads OSHA PDFs from the web to data/pdfs/."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    for url, filename, title in OSHA_PDFS:
        dest = PDF_DIR / filename

        if dest.exists():
            print(f"   ✅ Already downloaded: {filename}")
            continue

        print(f"   ⬇️  Downloading: {filename}")
        try:
            response = httpx.get(url, follow_redirects=True, timeout=30)
            response.raise_for_status()
            dest.write_bytes(response.content)
            print(f"   ✅ Saved to {dest}")
        except Exception as e:
            print(f"   ❌ Failed to download {filename}: {e}")


def main():
    print("=" * 50)
    print("SafetyIQ — Ingestion Pipeline")
    print("=" * 50)

    # Step 1: Make sure DB tables exist
    print("\n🔧 Initializing database...")
    init_db()

    # Step 2: Download PDFs if configured
    if DOWNLOAD_PDFS:
        print("\n⬇️  Downloading OSHA PDFs...")
        download_pdfs()

    # Step 3: Find all PDFs in data/pdfs/
    pdf_files = list(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"\n❌ No PDF files found in {PDF_DIR}")
        print("   Either set DOWNLOAD_PDFS = True or manually add PDFs to data/pdfs/")
        return

    print(f"\n📂 Found {len(pdf_files)} PDF(s) to process")

    # Step 4: Ingest each PDF
    # Import here to avoid circular imports
    from app.ingestion.pipeline import ingest_pdf

    db = SessionLocal()
    total_chunks = 0

    try:
        for pdf_path in pdf_files:
            # Look up the title from our list (if it's one of our known PDFs)
            title = None
            source_url = None
            for url, filename, pdf_title in OSHA_PDFS:
                if pdf_path.name == filename:
                    title = pdf_title
                    source_url = url
                    break

            doc = ingest_pdf(
                pdf_path=str(pdf_path),
                db=db,
                title=title,
                source_url=source_url
            )

            if doc:
                chunk_count = db.query(__import__('app.models', fromlist=['Chunk']).Chunk).filter_by(document_id=doc.id).count()
                total_chunks += chunk_count

    finally:
        db.close()

    print("\n" + "=" * 50)
    print(f"✅ Ingestion complete!")
    print(f"   Documents processed: {len(pdf_files)}")
    print(f"   Total chunks stored: {total_chunks}")
    print("\nNext step: Start the API server with:")
    print("   uvicorn app.main:app --reload")
    print("Then visit http://localhost:8000/docs")
    print("=" * 50)


if __name__ == "__main__":
    main()
