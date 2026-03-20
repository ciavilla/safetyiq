"""
ingestion/pipeline.py
Orchestrates the full ingestion pipeline for one PDF file.

The pipeline order is:
  PDF file → parse (extract text) → chunk (split text) → embed (generate vectors) → store (save to DB)
"""

from pathlib import Path
from sqlalchemy.orm import Session

from app.models import Document, Chunk
from app.ingestion.parser import parse_pdf
from app.ingestion.chunker import chunk_pages
from app.ingestion.embedder import generate_embeddings_batch


def ingest_pdf(pdf_path: str, db: Session, title: str = None, source_url: str = None) -> Document:
    """
    Runs the full ingestion pipeline for a single PDF.

    Args:
        pdf_path:   Path to the PDF file on disk
        db:         Database session
        title:      Optional human-readable title for the document
        source_url: Optional URL where the PDF was downloaded from

    Returns:
        The Document object that was created in the database
    """
    filename = Path(pdf_path).name

    # --- Check if already ingested ---
    existing = db.query(Document).filter(Document.filename == filename).first()
    if existing:
        print(f"   ⚠️  Already ingested: {filename} — skipping")
        return existing

    print(f"\n📄 Processing: {filename}")

    # --- Step 1: Parse PDF → extract text by page ---
    pages = parse_pdf(pdf_path)

    if not pages:
        print(f"   ❌ No text extracted from {filename}. Is it a scanned image PDF?")
        return None

    # --- Step 2: Chunk → split pages into overlapping text chunks ---
    chunks = chunk_pages(pages)
    print(f"   ✂️  Split into {len(chunks)} chunks")

    # --- Step 3: Embed → generate a vector for each chunk ---
    chunks_with_embeddings = generate_embeddings_batch(chunks)

    # --- Step 4: Store → save document and all chunks to database ---
    document = Document(
        filename=filename,
        title=title or filename.replace(".pdf", "").replace("_", " ").title(),
        source_url=source_url
    )
    db.add(document)
    db.flush()  # Flush so document.id is assigned before we use it below

    for chunk_data in chunks_with_embeddings:
        chunk = Chunk(
            document_id=document.id,
            content=chunk_data["content"],
            chunk_index=chunk_data["chunk_index"],
            page_number=chunk_data["page_number"],
            embedding=chunk_data["embedding"]
        )
        db.add(chunk)

    db.commit()

    print(f"   💾 Stored {len(chunks_with_embeddings)} chunks in database")
    return document
