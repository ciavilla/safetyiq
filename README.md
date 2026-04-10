# SafetyIQ — AI-Powered Workplace Safety Assistant

> A RAG-powered backend that answers OSHA compliance questions with cited, source-grounded responses using the Claude API and pgvector semantic search.

![SafetyIQ Demo](./assets/screenshot.png)

[![Frontend Repo](https://img.shields.io/badge/Frontend-Repo-blue)](https://github.com/ciavilla/safetyiq-frontend)
[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://your-live-link.com)

---

## The Problem

Workers and small business operators need fast, accurate answers to safety compliance questions — but OSHA documentation is dense, scattered across hundreds of PDFs, and not searchable in plain English. Generic AI tools hallucinate regulations that don't exist, which in a safety context can cause real harm.

---

## The Solution

SafetyIQ ingests real OSHA documentation into a vector database and uses semantic search to retrieve only the most relevant chunks before sending them to Claude. Every answer is grounded exclusively in source documents and cites the exact document and page number — so users can verify every claim.

---

## Tech Stack

| Layer | Technology | Why I Chose It |
|-------|-----------|----------------|
| Framework | FastAPI (Python) | Async-ready, auto-generates API docs, natural fit for AI/ML tooling |
| AI | Claude API (claude-sonnet) | Excellent instruction-following for structured, cited responses |
| Embeddings | OpenAI text-embedding-3-small | Cost-effective, 1536-dimension vectors, same model for ingestion and query |
| Vector Search | pgvector (PostgreSQL extension) | One database handles both relational data and vector similarity search |
| Database | PostgreSQL | Reliable, well-understood, great fit with SQLAlchemy ORM |
| PDF Parsing | PyPDF2 + LangChain text splitters | Handles chunking with configurable overlap |
| HTML Parsing | BeautifulSoup4 + httpx | Extends ingestion to OSHA HTML pages, not just PDFs |
| Infrastructure | Docker + Docker Compose | Reproducible local environment, production-ready container setup |
| ORM | SQLAlchemy 2.0 | Type-safe database models, clean session management |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Next.js Frontend                       │
│              (safetyiq-frontend repo)                   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS / REST
┌────────────────────▼────────────────────────────────────┐
│                FastAPI Backend                          │
│         /query · /documents · /health                   │
└──────┬──────────────────────────┬───────────────────────┘
       │                          │
┌──────▼──────────┐    ┌──────────▼──────────────────────┐
│   Claude API    │    │   PostgreSQL + pgvector          │
│  (Answer gen)   │    │   documents + chunks tables      │
└─────────────────┘    └──────────────────────────────────┘
                                  ▲
                     ┌────────────┴──────────────┐
                     │    Ingestion Pipeline      │
                     │  PDF/HTML → Parse → Chunk  │
                     │  → Embed → Store           │
                     └───────────────────────────┘
```

**Key architectural decisions:**

- **Why RAG over fine-tuning?** OSHA documentation changes. RAG lets us add new documents without retraining anything — just ingest and the system immediately knows the new content.
- **Why pgvector over a dedicated vector DB (Pinecone, Weaviate)?** Keeping vectors in PostgreSQL means one less service to manage, and the relational data (documents, chunks, metadata) lives in the same database as the vectors. Simpler ops, fewer failure points.
- **Why constrain Claude to only use provided context?** Safety regulations are a domain where hallucination is unacceptable. A wrong answer about fall protection requirements could get someone hurt. The system prompt explicitly forbids Claude from using knowledge outside the retrieved chunks.

---

## The RAG Pipeline

```
1. INGEST
   PDF/HTML → extract text → split into 500-token chunks (50-token overlap)
   → generate embeddings (OpenAI) → store chunk + embedding + metadata in pgvector

2. QUERY
   User question → embed question → cosine similarity search (top 8 chunks)
   → build prompt with retrieved context → send to Claude API → return answer + citations
```

Chunk size and overlap were tuned deliberately — 500 tokens captures enough context for a complete safety requirement, while 50-token overlap ensures sentences near chunk boundaries don't lose their context.

---

## Prompt Engineering

The system prompt is the core of what makes SafetyIQ accurate rather than just capable:

```
- Only use information from provided source documents
- Always cite sources as [Source: Document Title, Page X]
- When CFR regulation numbers appear in context, surface them prominently
- When two OSHA standards could apply (e.g. general construction fall
  protection at 6ft vs scaffold-specific at 10ft), explain both and
  clarify which applies to the user's situation
- If context doesn't contain enough information, say so clearly
- Never speculate or fill gaps with assumptions
```

The CFR citation rule and standard conflict resolution were added after a HSE professional reviewed the app and identified an edge case where two overlapping OSHA standards apply to the same question.

---

## Features

- 📄 Ingest OSHA PDFs and HTML pages into a searchable vector database
- 🔍 Semantic search retrieves the most relevant document chunks per question
- 🤖 Claude API generates cited, source-grounded answers
- 📋 CFR regulation numbers surfaced prominently in every relevant answer
- ⚖️ Conflicting OSHA standards explained clearly with citations for both
- 🔄 Multi-turn conversation with history context
- 🌐 Support for both PDF and HTML document ingestion
- 🐳 Fully containerized with Docker

---

## Getting Started

### Prerequisites

```bash
python3 --version    # 3.10 or higher
docker --version     # Docker Desktop running
```

You will also need:
- **OpenAI API key** — for generating embeddings: https://platform.openai.com/api-keys
- **Anthropic API key** — for Claude answers: https://console.anthropic.com/

### Installation

```bash
git clone https://github.com/ciavilla/safetyiq
cd safetyiq

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# → Add your OPENAI_API_KEY and ANTHROPIC_API_KEY to .env
```

### Running Locally

```bash
# Start the database
docker-compose up -d

# Initialize database tables
python3 -c "from app.database import init_db; init_db()"

# Ingest OSHA documents
python3 scripts/run_ingestion.py

# Start the API server
uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

### Environment Variables

```env
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
DATABASE_URL=postgresql://safetyiq:safetyiq_password@127.0.0.1:5432/safetyiq_db
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/query` | Submit a safety question, returns answer + source chunks |
| GET | `/documents` | List all ingested documents |
| GET | `/health` | Health check with document and chunk counts |

**Example query request:**
```json
{
  "question": "Do I need fall protection on 12ft scaffolding?",
  "history": []
}
```

**Example response:**
```json
{
  "answer": "Yes, fall protection is required. Scaffolds more than 10 feet above a lower level require guardrails (29 CFR 1926.451(g)(1))...",
  "sources": [
    {
      "document_title": "OSHA Scaffold Use in Construction Guide",
      "page_number": 8,
      "similarity": 0.66,
      "content": "The standard requires employers to protect each employee..."
    }
  ]
}
```

---

## Project Structure

```
safetyiq/
├── app/
│   ├── database.py          # DB connection + table initialization
│   ├── models.py            # SQLAlchemy models (Document, Chunk)
│   ├── main.py              # FastAPI app + endpoints
│   ├── retriever.py         # Vector similarity search
│   ├── claude_client.py     # Claude API integration + prompt engineering
│   └── ingestion/
│       ├── parser.py        # PDF + HTML text extraction
│       ├── chunker.py       # Text splitting with overlap
│       ├── embedder.py      # OpenAI embedding generation
│       └── pipeline.py      # Orchestrates the full ingestion flow
├── scripts/
│   └── run_ingestion.py     # CLI script to ingest documents
├── data/
│   └── pdfs/                # Downloaded OSHA PDFs (gitignored)
├── docker-compose.yml       # PostgreSQL + pgvector container
├── requirements.txt
└── .env.example
```

---

## What I Learned / What I'd Do Differently

**What I'm proud of:**
- Designing the system prompt constraints intentionally for a high-stakes domain — accuracy over confidence
- The CFR citation and standard conflict rules came directly from real feedback from a HSE professional, which improved answer quality meaningfully
- Debugging port conflicts between a local PostgreSQL install and Docker — understanding how services bind to ports at the OS level

**What I'd change with more time:**
- Add streaming responses so answers appear word-by-word instead of all at once
- Implement a re-ranking step after vector retrieval to improve chunk selection quality
- Add automated tests for the ingestion pipeline and retrieval accuracy
- Store conversation history in the database for persistent multi-session context

---

## Roadmap

- [ ] Streaming Claude responses
- [ ] Re-ranking retrieved chunks before sending to Claude
- [ ] User authentication for multi-user support
- [ ] Deploy to AWS (EC2 + RDS)
- [ ] Automated ingestion pipeline for new OSHA publications

---

## Related

- [SafetyIQ Frontend](https://github.com/ciavilla/safetyiq-frontend) — Next.js 15 chat interface

---

## Author

**Ciera Villalpando**
[ciera-portfolio.vercel.app](https://ciera-portfolio.vercel.app) · [github.com/ciavilla](https://github.com/ciavilla) · [linkedin.com/in/ciera-villalpando](https://linkedin.com/in/ciera-villalpando)
