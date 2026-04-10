[中文](README.zh.md) | **English**

# 🧠 zero-to-ai-fullstack

> A Java backend engineer's journey into AI full-stack development.
> Building a RAG-powered knowledge base from scratch — one week at a time.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14+-black?logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Week_2_In_Progress-blue)

---

## 👋 Who this is for

If you are:

- A **backend developer** (Java / Go / Node) curious about AI full-stack
- Wondering how RAG, vector databases, and LLM APIs fit together in a real project
- Looking for a **realistic learning path** rather than another polished tutorial

…then follow along. This repo documents not just the code, but the *why* behind every technical decision — written from the perspective of someone who thinks in Java and is learning to think in Python + AI.

---

## 🗺️ What I'm building

A self-hostable, RAG-powered knowledge base:

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

**Tech stack:** Python · FastAPI · LangChain · PostgreSQL · pgvector · Next.js · Docker

---

## 📅 8-Week Roadmap

| Week | Focus | Status |
|------|-------|--------|
| 1 | Python speed run + Claude API + Prompt Engineering | ✅ Done |
| 2 | LangChain + document processing pipeline | 🔄 In progress |
| 3 | PostgreSQL + pgvector + vector search | ⬜ |
| 4 | Full RAG pipeline + FastAPI backend | ⬜ |
| 5 | RAG optimization + evaluation | ⬜ |
| 6 | AI feature integration into production SaaS | ⬜ |
| 7 | Docker deployment + CI/CD | ⬜ |
| 8 | Interview prep + start applying | ⬜ |

---

## 📓 Learning Log

Weekly notes on what I learned, what surprised me, and how things map to my Java background.

→ [Read the full Learning Log](LEARNING_LOG.en.md)

**Recent entries:**

- **Week 1** — Python feels familiar once you stop fighting the lack of braces. Claude API multi-turn dialogue clicked immediately — it's stateless, just like HTTP. [Read →](LEARNING_LOG.en.md#week-1)

---

## 📁 Project Structure

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

## 🚀 Quick Start (once complete)

```bash
git clone https://github.com/yanhua1010/zero-to-ai-fullstack.git
cd zero-to-ai-fullstack
cp .env.example .env   # add your API key
docker compose up -d
# open http://localhost:3000
```

*Full deployment guide coming in Week 7.*

---

## 💬 About me

8 years as a Java backend engineer. Built distributed systems, high-concurrency services, and data pipelines — all in Java/Spring. Now learning the AI full-stack: Python, FastAPI, RAG, pgvector, LangChain, Next.js.

Following along? Hit **Watch** to get notified of weekly updates, or open an issue if you have questions.

→ [GitHub: @yanhua1010](https://github.com/yanhua1010)

---

## 📄 License

MIT
