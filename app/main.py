"""
Adds the /query endpoint and serves the chat UI.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.database import get_db
from app.retriever import retrieve_relevant_chunks, format_context_for_prompt
from app.claude_client import ask_claude_with_history

app = FastAPI(
    title="SafetyIQ API",
    description="AI-powered workplace safety knowledge assistant",
    version="0.2.0"
)

# CORS — allows mobile app to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # We'll lock this down later once we have our app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the chat UI from the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Request / Response models ──────────────────────────────────────────────

class Message(BaseModel):
    """A single message in the conversation history."""
    role: str    # "user" or "assistant"
    content: str


class QueryRequest(BaseModel):
    """
    The request body for the /query endpoint.

    question: The user's current question
    history:  Optional list of previous messages for multi-turn conversation
    """
    question: str
    history: list[Message] = []


class SourceChunk(BaseModel):
    """A source chunk returned alongside the answer."""
    document_title: str
    page_number: int
    similarity: float
    content: str


class QueryResponse(BaseModel):
    """
    The response from the /query endpoint.

    answer:  Claude's answer with citations
    sources: The chunks that were retrieved and used as context
    """
    answer: str
    sources: list[SourceChunk]


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
def serve_chat_ui():
    """Serves the chat UI at the root URL."""
    return FileResponse("static/index.html")


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check — returns document and chunk counts."""
    chunk_count = db.execute(text("SELECT COUNT(*) FROM chunks")).scalar()
    doc_count = db.execute(text("SELECT COUNT(*) FROM documents")).scalar()
    return {
        "status": "ok",
        "documents_in_db": doc_count,
        "chunks_in_db": chunk_count
    }


@app.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """Lists all ingested documents."""
    results = db.execute(
        text("SELECT id, filename, title, created_at FROM documents ORDER BY created_at DESC")
    ).fetchall()
    return {
        "documents": [
            {"id": r[0], "filename": r[1], "title": r[2], "ingested_at": str(r[3])}
            for r in results
        ]
    }


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    The main endpoint — takes a safety question and returns an AI answer with citations.

    Flow:
    1. Retrieve the most relevant chunks from the database
    2. Format them as context for Claude
    3. Send question + context to Claude
    4. Return the answer + the source chunks
    """

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Step 1: Retrieve relevant chunks via vector similarity search
    chunks = retrieve_relevant_chunks(
        question=request.question,
        db=db,
        top_k=8
    )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No relevant documents found. Try ingesting more PDFs first."
        )

    # Step 2: Format chunks into a context string for the prompt
    context = format_context_for_prompt(chunks)

    # Step 3: Convert history to the format Claude expects
    history = [{"role": m.role, "content": m.content} for m in request.history]

    # Step 4: Ask Claude
    answer = ask_claude_with_history(
        question=request.question,
        context=context,
        history=history
    )

    # Step 5: Return answer + source chunks
    return QueryResponse(
        answer=answer,
        sources=[
            SourceChunk(
                document_title=c["document_title"],
                page_number=c["page_number"],
                similarity=c["similarity"],
                content=c["content"]
            )
            for c in chunks
        ]
    )
