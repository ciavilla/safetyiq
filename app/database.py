"""
database.py
Handles the database connection and table setup.
pgvector lets PostgreSQL store and search vector embeddings.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Pull the database URL from your .env file
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in your .env file")

# Create the SQLAlchemy engine (this is the connection to your database)
engine = create_engine(DATABASE_URL)

# SessionLocal is what you'll use to run database queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class that all database models inherit from."""
    pass


def init_db():
    """
    Creates the pgvector extension and all tables.
    Run this once when setting up the project.
    """
    with engine.connect() as conn:
        # Enable pgvector - this adds vector search capability to PostgreSQL
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Create all tables defined in models.py
    from app.models import Document, Chunk  # noqa: F401 - import needed to register models
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def get_db():
    """
    Dependency for FastAPI routes.
    Yields a database session and closes it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
