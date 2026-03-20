"""
models.py
Defines the database tables using SQLAlchemy.

We have two tables:
- documents: one row per PDF file ingested
- chunks: one row per text chunk, with its vector embedding
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base


class Document(Base):
    """
    Represents one ingested PDF document.
    e.g. "OSHA Fall Protection Quick Card"
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)   # e.g. "osha_fall_protection.pdf"
    title = Column(String, nullable=True)                    # Human-readable title
    source_url = Column(String, nullable=True)               # Where it was downloaded from
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One document has many chunks
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document id={self.id} filename={self.filename}>"


class Chunk(Base):
    """
    Represents one text chunk from a document.
    Each chunk gets its own vector embedding for similarity search.

    Example: A 10-page PDF might produce 40 chunks.
    When a user asks a question, we find the most relevant chunks
    and send them to Claude as context.
    """
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)          # The actual text of this chunk
    chunk_index = Column(Integer, nullable=False)   # Position in the original document
    page_number = Column(Integer, nullable=True)    # Which page it came from

    # The vector embedding - 1536 dimensions is what OpenAI's text-embedding-3-small produces
    embedding = Column(Vector(1536), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to the parent document
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<Chunk id={self.id} doc_id={self.document_id} index={self.chunk_index}>"
