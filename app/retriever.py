"""
retriever.py
Searches the database for the most relevant chunks given a user question.

HOW VECTOR SEARCH WORKS:
1. We embed the user's question (turn it into 1536 numbers, same as we did for chunks)
2. We compare that question vector against every chunk vector in the database
3. Chunks with vectors "closest" to the question vector are most semantically relevant
4. We return the top k most relevant chunks as context for Claude

This is much better than keyword search because it understands meaning.
Example: "protective gear for electrical work" will match chunks about
"PPE requirements" even though the exact words are different.
"""

import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"


def embed_question(question: str) -> list[float]:
    """
    Turns the user's question into a vector embedding.
    Uses the exact same model we used during ingestion — this is important!
    If you embed chunks with model A but questions with model B,
    the similarity scores will be meaningless.
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=question
    )
    return response.data[0].embedding


def retrieve_relevant_chunks(question: str, db: Session, top_k: int = 4) -> list[dict]:
    """
    Finds the top_k most relevant chunks for a given question.

    Args:
        question: The user's question in plain English
        db:       Database session
        top_k:    How many chunks to return (4 is a good default —
                  enough context without overwhelming Claude's prompt)

    Returns:
        List of dicts, each containing:
        - content:       The text of the chunk
        - document_title: Which document it came from
        - page_number:   Which page
        - similarity:    How similar it was (0-1, higher = more relevant)
    """

    # Step 1: Embed the question
    question_embedding = embed_question(question)

    # Step 2: Convert to the format pgvector expects
    # pgvector uses the <=> operator for cosine distance (lower = more similar)
    embedding_str = "[" + ",".join(str(x) for x in question_embedding) + "]"

    # Step 3: Run the similarity search
    # We JOIN with documents so we can include the document title in results
    query = text("""
        SELECT
            c.content,
            c.page_number,
            c.chunk_index,
            d.title AS document_title,
            d.filename,
            1 - (c.embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.embedding IS NOT NULL
        ORDER BY c.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    results = db.execute(query, {
        "embedding": embedding_str,
        "top_k": top_k
    }).fetchall()

    # Step 4: Format results as a clean list of dicts
    chunks = []
    for row in results:
        chunks.append({
            "content": row.content,
            "page_number": row.page_number,
            "document_title": row.document_title,
            "filename": row.filename,
            "similarity": round(float(row.similarity), 3)
        })

    return chunks


def format_context_for_prompt(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a clean context block for the Claude prompt.

    Each chunk is labeled with its source so Claude can reference it in citations.

    Example output:
        [Source 1: OSHA Electrical Safety Quick Card, Page 1]
        Workers must use insulated tools when working near live electrical parts...

        [Source 2: OSHA Electrical Safety Quick Card, Page 2]
        Lock out/tag out procedures must be followed before...
    """
    context_parts = []

    for i, chunk in enumerate(chunks, start=1):
        source_label = f"[Source {i}: {chunk['document_title']}, Page {chunk['page_number']}]"
        context_parts.append(f"{source_label}\n{chunk['content']}")

    return "\n\n".join(context_parts)
