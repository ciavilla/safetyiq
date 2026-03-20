"""
main.py
The FastAPI application entry point.

Right now this just has a health check endpoint.
Week 2 will add the /query endpoint that connects to Claude.
"""

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

app = FastAPI(
    title="SafetyIQ API",
    description="AI-powered workplace safety knowledge assistant",
    version="0.1.0"
)


@app.get("/")
def root():
    """Simple root endpoint."""
    return {"message": "SafetyIQ API is running. Visit /docs for the full API."}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    Returns the number of chunks stored in the database.
    After running ingestion, this number should be > 0.
    """
    result = db.execute(text("SELECT COUNT(*) FROM chunks")).scalar()
    doc_count = db.execute(text("SELECT COUNT(*) FROM documents")).scalar()

    return {
        "status": "ok",
        "documents_in_db": doc_count,
        "chunks_in_db": result
    }


@app.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """
    Lists all ingested documents.
    Useful for verifying your ingestion pipeline worked.
    """
    result = db.execute(
        text("SELECT id, filename, title, created_at FROM documents ORDER BY created_at DESC")
    ).fetchall()

    return {
        "documents": [
            {
                "id": row[0],
                "filename": row[1],
                "title": row[2],
                "ingested_at": str(row[3])
            }
            for row in result
        ]
    }
