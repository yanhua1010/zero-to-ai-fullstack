[中文](README.zh.md) | **English**

# zero-to-ai-fullstack

A Java backend engineer's attempt at AI full-stack. Building a RAG knowledge base from scratch, one week at a time.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14+-black?logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## What I'm building

A self-hostable RAG knowledge base: upload documents, ask questions, get answers with source citations.

```
┌─────────────────────────────────────────────┐
│              Next.js Frontend                │
│    Upload · Manage · Chat · View Sources     │
└──────────────────┬──────────────────────────┘
                   │ REST API / SSE
┌──────────────────┴──────────────────────────┐
│            Python Backend (FastAPI)          │
│   ETL Pipeline · RAG Engine · LLM Router    │
└────┬─────────────────┬───────────────────┬──┘
     │                 │                   │
┌────┴─────┐   ┌───────┴──────┐   ┌────────┴───┐
│PostgreSQL│   │   pgvector   │   │  LLM API   │
│ metadata │   │  embeddings  │   │ Claude/GPT │
└──────────┘   └──────────────┘   └────────────┘
```

Stack: Python · FastAPI · LangChain · PostgreSQL · pgvector · Next.js · Docker

---

## 8-Week Roadmap

| Week | Focus | Status |
|------|-------|--------|
| 1 | Python speed run + Claude API + Prompt Engineering | ✅ Done |
| 2 | LangChain + document processing pipeline | ✅ Done |
| 3 | PostgreSQL + pgvector + vector search | ⬜ |
| 4 | Full RAG pipeline + FastAPI backend | ⬜ |
| 5 | RAG optimization + evaluation | ⬜ |
| 6 | AI feature integration into production SaaS | ⬜ |
| 7 | Docker deployment + CI/CD | ⬜ |
| 8 | Interview prep + start applying | ⬜ |

---

## Learning Log

Weekly notes on what clicked, what didn't, and how it maps to my Java background.

→ [Read the full Learning Log](LEARNING_LOG.en.md)

**Recent entries:**

- **Week 1** — Python feels familiar once you stop fighting the lack of braces. Claude API multi-turn dialogue clicked immediately — it's stateless, just like HTTP. [Read →](LEARNING_LOG.en.md#week-1)

---

## Project Structure

```
zero-to-ai-fullstack/
├── backend/                  # Python FastAPI service
│   ├── etl/                  # ETL pipeline
│   │   ├── extractors/       # Document loaders (PDF, MD, TXT, HTML)
│   │   ├── transformers/     # Text cleaning & chunking
│   │   └── loaders/          # Database writers
│   ├── rag/                  # RAG pipeline
│   │   ├── embeddings/       # Embedding model wrappers
│   │   ├── retrieval/        # Vector + hybrid search
│   │   └── generation/       # LLM integration & prompts
│   ├── api/                  # FastAPI routes
│   ├── models/               # SQLAlchemy ORM models
│   └── prompts/              # Prompt templates (versioned)
├── frontend/                 # Next.js app
├── scripts/                  # Weekly learning exercises
│   ├── week1/                # Python basics + Claude API chatbot
│   └── week2/                # LangChain + document pipeline
├── sql/                      # Alembic migrations
├── docker-compose.yml
├── .env.example
└── LEARNING_LOG.md
```

---

## Quick Start

```bash
git clone https://github.com/yanhua1010/zero-to-ai-fullstack.git
cd zero-to-ai-fullstack
cp .env.example .env

# Install dependencies (requires uv)
uv sync

# Start backend
uv run uvicorn backend.main:app --reload

# Or with Docker (Week 7+)
docker compose up -d
```

Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## About

8 years as a Java backend engineer. Built distributed systems, high-concurrency services, data pipelines — all in Java/Spring. Now doing the AI full-stack thing.

Following along? Hit **Watch** for weekly updates, or open an issue if you have questions.

→ [GitHub: @yanhua1010](https://github.com/yanhua1010)

---

MIT License
