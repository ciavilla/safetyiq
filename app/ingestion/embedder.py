"""
ingestion/embedder.py
Generates vector embeddings for text chunks using OpenAI's API.

WHAT IS AN EMBEDDING?
An embedding is a list of 1536 numbers that represents the "meaning" of a piece of text.
Texts with similar meanings will have similar numbers (close vectors).

This is how we do semantic search: we embed the user's question,
then find the chunks whose embeddings are closest to the question's embedding.
That's much better than keyword search because it understands meaning, not just words.

COST NOTE:
text-embedding-3-small costs ~$0.00002 per 1000 tokens.
Embedding all your OSHA test PDFs will cost less than $0.01.
"""

import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI client using your API key from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# The embedding model we're using
# text-embedding-3-small is cost-effective and produces 1536-dimension vectors
EMBEDDING_MODEL = "text-embedding-3-small"


def generate_embedding(text: str) -> list[float]:
    """
    Generates a single embedding for one piece of text.

    Args:
        text: The text to embed

    Returns:
        A list of 1536 floats representing the text's meaning
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def generate_embeddings_batch(chunks: list[dict]) -> list[dict]:
    """
    Generates embeddings for a list of chunks.
    Adds the embedding to each chunk dict and returns the updated list.

    We process in batches of 100 and add a small delay between batches
    to avoid hitting OpenAI rate limits.

    Args:
        chunks: List of chunk dicts from chunker.py

    Returns:
        Same list but each chunk now has an "embedding" key
    """
    BATCH_SIZE = 100
    total = len(chunks)

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_texts = [chunk["content"] for chunk in batch]

        print(f"   🔢 Generating embeddings {i+1}-{min(i+BATCH_SIZE, total)} of {total}...")

        # Send the whole batch to OpenAI in one API call (much faster than one at a time)
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch_texts
        )

        # Attach each embedding back to its chunk
        for chunk, embedding_data in zip(batch, response.data):
            chunk["embedding"] = embedding_data.embedding

        # Small pause between batches to be polite to the API
        if i + BATCH_SIZE < total:
            time.sleep(0.5)

    return chunks
