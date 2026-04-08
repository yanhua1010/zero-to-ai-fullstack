# 🧠 AI Knowledge Base

> A self-hostable RAG-powered knowledge base — upload documents, ask questions, get answers with source citations.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14+-black?logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-In_Development-orange)

## ✨ Features

- 📄 **Multi-format document ingestion** — PDF, Markdown, TXT, HTML
- 🔍 **Semantic search** — powered by pgvector and embedding models
- 💬 **Conversational Q&A** — multi-turn dialogue with source citations
- 🗂️ **Knowledge base management** — organize documents into separate knowledge bases
- ⚡ **Streaming responses** — real-time answer generation via SSE
- 🐳 **One-command deployment** — Docker Compose brings up the full stack

## 🏗️ Architecture

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

## 🛠️ Tech Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend  | Python 3.11, FastAPI, LangChain     |
| Database | PostgreSQL 16 + pgvector            |
| LLM      | Claude API (Anthropic) / OpenAI API  |
| ETL      | Pandas, custom pipeline             |
| Deploy   | Docker Compose, GitHub Actions      |

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- An API key from [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/)

### 1. Clone the repo

```bash
git clone https://github.com/yanhua1010/ai-knowledge-base.git
cd ai-knowledge-base
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API key
```

### 3. Start the full stack

```bash
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
ai-knowledge-base/
├── backend/                  # Python FastAPI service
│   ├── etl/                  # ETL pipeline (Extract → Transform → Load)
│   │   ├── extractors/       # Document loaders (PDF, MD, TXT, HTML)
│   │   ├── transformers/     # Text cleaning & chunking
│   │   └── loaders/          # Database writers
│   ├── rag/                  # RAG pipeline
│   │   ├── embeddings/       # Embedding model wrappers
│   │   ├── retrieval/        # Vector search & hybrid search
│   │   └── generation/       # LLM integration & prompt management
│   ├── api/                  # FastAPI routes
│   │   ├── documents.py
│   │   ├── knowledge_bases.py
│   │   └── chat.py
│   ├── models/               # SQLAlchemy ORM models
│   ├── prompts/              # Prompt templates (versioned)
│   └── main.py
├── frontend/                 # Next.js app
│   ├── app/
│   │   ├── knowledge-bases/  # KB management pages
│   │   └── chat/             # Chat interface pages
│   └── components/
├── sql/                      # Database migration scripts (Alembic)
├── scripts/                  # Dev utilities & data scripts
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🗺️ Roadmap

- [x] Week 1 — Python fundamentals & data processing basics
- [ ] Week 2-3 — ETL pipeline (document extraction & cleaning)
- [ ] Week 4-5 — PostgreSQL + pgvector setup & data modeling
- [ ] Week 6-7 — LLM integration & RAG pipeline
- [ ] Week 8-9 — FastAPI backend & streaming responses
- [ ] Week 10 — Next.js frontend
- [ ] Week 11 — Docker deployment & CI/CD
- [ ] Week 12 — Polish, docs & open beta

## 🤝 Contributing

This project is actively under development. Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built by [@yanhua1010](https://github.com/yanhua1010) — learning in public 🌱*
