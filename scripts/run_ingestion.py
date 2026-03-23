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
        "https://www.osha.gov/sites/default/files/publications/OSHA3903.pdf",
        "osha_fall_protection_general_factsheet.pdf",
        "OSHA Fall Protection General Industry Factsheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/PPE-FACTSHEET.pdf",
        "osha_personal_protective_equipment_factsheet.pdf",
        "OSHA Personal Protective Equipment Factsheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3151.pdf",
        "osha_personal_protective_equipment.pdf",
        "OSHA Personal Protective Equipment"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHAFS3529.pdf",
        "osha_lockout_tagout_factsheet.pdf",
        "OSHA Lockout Tagout Factsheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/PORTABLE_LADDER_QC.pdf",
        "osha_portable_ladder_quickcard.pdf",
        "OSHA Portable Ladder Safety Quickcard"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3660.pdf",
        "osha_extension_ladder_factsheet.pdf",
        "OSHA Extension Ladder Safety FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3662.pdf",
        "osha_step_ladder_factsheet.pdf",
        "OSHA Step Ladder Safety FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3722.pdf",
        "osha_narrow_frame_scaffold_factsheet.pdf",
        "OSHA Narrow Frame Scaffold FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3857.pdf",
        "osha_ladder_jack_scaffold_factsheet.pdf",
        "OSHA Ladder Jack Scaffold FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA_FS-3759.pdf",
        "osha_tube_and_coupler_scaffold_factsheet.pdf",
        "OSHA Tube And Coupler Scaffold Erection and Use FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA_FS-3760.pdf",
        "osha_tube_and_coupler_scaffold_design_factsheet.pdf",
        "OSHA Tube And Coupler Scaffold Planning and Design FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3788.pdf",
        "osha_confined_space_pits_factsheet.pdf",
        "OSHA Confined Spaces in Construction Pits FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/ATMOSPHERIC_TEST_CONFINED.pdf",
        "osha_confined_space_atmospheric_testing_factsheet.pdf",
        "OSHA Confined Spaces Atmospheric Testing FactSheet"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/CONFINED_SPACE_PERMIT.pdf",
        "osha_confined_space_permit_required_quickcard.pdf",
        "OSHA Confined Spaces Permit Required QuickCard"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA4495.pdf",
        "osha_extension_cord_quickcard.pdf",
        "OSHA Extension Cord QuickCard"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3124.pdf",
        "osha_stairways_ladder_guide.pdf",
        "OSHA Stairways and Ladders Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3138.pdf",
        "osha_confined_space_guide.pdf",
        "OSHA Confined Spaces Permit-Required Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/CONSTRUCTION_PPE.pdf",
        "osha_ppe_quickcard.pdf",
        "OSHA Construction PPE Quickcard"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3146.pdf",
        "osha_fall_protection_guide.pdf",
        "OSHA Fall Protection in Construction Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3120.pdf",
        "osha_lockout_tagout_guide.pdf",
        "OSHA Lockout Tagout Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3150.pdf",
        "osha_scaffold_guide.pdf",
        "OSHA Scaffold Use in Construction Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3150.pdf",
        "osha_scaffold_guide.pdf",
        "OSHA Scaffold Use in Construction Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3666.pdf",
        "osha_fall_arrest_systems.pdf",
        "OSHA Fall Protection Personal Fall Arrest Systems"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/SAFETY_HELMET_SHIB.pdf",
        "osha_safety_helmets.pdf",
        "OSHA Safety Helmets Head Protection"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3074.pdf",
        "osha_hearing_conservation_guide.pdf",
        "OSHA Hearing Conservation Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/HEARING_PROTECTOR_FIT_TESTING_SHIB.pdf",
        "osha_hearing_protector_fit.pdf",
        "OSHA Hearing Protector Fit Testing Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3172.pdf",
        "osha_hazardous_chemicals.pdf",
        "OSHA Hazardous Chemicals Exposure"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/SHIB092203.pdf",
        "osha_Personal_Fall_Protection.pdf",
        "OSHA Personal Fall Protection System Components"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3825.pdf",
        "osha_confined_spaces.pdf",
        "OSHA Confined Spaces and Permit Spaces Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/OSHA3695.pdf",
        "osha_hazard_communication_Hazard_Chemicals.pdf",
        "OSHA Hazard Communication for Use of Hazardous Chemicals Guide"
    ),
    (
        "https://www.osha.gov/sites/default/files/publications/HYDROGEN_SULFIDE_FACT.pdf",
        "osha_hydrogen_sulfide_factsheet.pdf",
        "OSHA Hydrogen Sulfide H2S FactSheet"
    ),
]
OSHA_HTML_PAGES = [
    (
        "https://www.osha.gov/publications/hib19960514",
        "Chemical Exposure from Industrial Valve And Piping Systems"
    ),
    # add more as needed
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


def ingest_html_pages(db):
    """Fetches and ingests HTML pages into the database."""
    from app.ingestion.parser import parse_html_url
    from app.ingestion.chunker import chunk_pages
    from app.ingestion.embedder import generate_embeddings_batch
    from app.models import Document, Chunk

    if not OSHA_HTML_PAGES:
        return 0

    total = 0
    print(f"\n🌐 Processing {len(OSHA_HTML_PAGES)} HTML page(s)...")

    for url, title in OSHA_HTML_PAGES:
        print(f"\n🌐 Processing: {title}")

        # Skip if already ingested
        existing = db.query(Document).filter_by(title=title).first()
        if existing:
            print(f"   ⚠️  Already ingested — skipping")
            continue

        # Same pipeline as PDFs: parse → chunk → embed → store
        pages = parse_html_url(url)
        if not pages:
            continue

        chunks = chunk_pages(pages)
        print(f"   ✂️  Split into {len(chunks)} chunks")

        chunks_with_embeddings = generate_embeddings_batch(chunks)

        doc = Document(
            filename=title.lower().replace(" ", "_") + ".html",
            title=title,
            source_url=url
        )
        db.add(doc)
        db.flush()

        for chunk_data in chunks_with_embeddings:
            chunk = Chunk(
                document_id=doc.id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                page_number=chunk_data["page_number"],
                embedding=chunk_data["embedding"]
            )
            db.add(chunk)

        db.commit()
        print(f"   💾 Stored {len(chunks_with_embeddings)} chunks in database")
        total += len(chunks_with_embeddings)

    return total

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

        # ── Ingest HTML pages ────────────────────────────
        total_chunks += ingest_html_pages(db)

    finally:
        db.close()

    print("\n" + "=" * 50)
    print(f"✅ Ingestion complete!")
    print(f"   Documents processed: {len(pdf_files)}")
    print(f"   HTML pages processed: {len(OSHA_HTML_PAGES)}")
    print(f"   Total chunks stored: {total_chunks}")
    print("\nNext step: Start the API server with:")
    print("   uvicorn app.main:app --reload")
    print("Then visit http://localhost:8000/docs")
    print("=" * 50)


if __name__ == "__main__":
    main()
