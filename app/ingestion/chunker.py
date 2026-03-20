"""
ingestion/chunker.py
Splits page text into smaller overlapping chunks.

WHY DO WE CHUNK?
A full PDF might be 50 pages. We can't send all 50 pages to Claude as context —
that would be too expensive and hit token limits. Instead, we split the document
into small chunks (~500 tokens each) and store them all. When a user asks a question,
we only retrieve the 3-5 most relevant chunks.

WHY OVERLAP?
We use a small overlap between chunks (50 tokens) so that sentences that fall
near a chunk boundary don't lose their context. Think of it like a sliding window.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Takes a list of pages and splits them into overlapping chunks.

    Args:
        pages: Output from parser.py — list of {page_number, text} dicts

    Returns:
        List of chunk dicts:
        [
            {
                "content": "chunk text here...",
                "chunk_index": 0,
                "page_number": 1
            },
            ...
        ]
    """

    # RecursiveCharacterTextSplitter tries to split on paragraphs first,
    # then sentences, then words — to keep chunks semantically meaningful
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       # Target ~500 tokens per chunk
        chunk_overlap=50,     # 50-token overlap between adjacent chunks
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = []
    chunk_index = 0

    for page in pages:
        # Split this page's text into chunks
        page_chunks = splitter.split_text(page["text"])

        for chunk_text in page_chunks:
            # Skip chunks that are just whitespace or very short
            if len(chunk_text.strip()) < 20:
                continue

            chunks.append({
                "content": chunk_text.strip(),
                "chunk_index": chunk_index,
                "page_number": page["page_number"]
            })
            chunk_index += 1

    return chunks
