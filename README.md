# Confluence Agentic RAG (Weaviate + UV)

[![CI (lint + test)](https://github.com/blitznihar/confluence-agentic-rag/actions/workflows/pylint.yml/badge.svg)](https://github.com/blitznihar/confluence-agentic-rag/actions/workflows/pylint.yml)
[![codecov](https://codecov.io/github/blitznihar/confluence-agentic-rag/graph/badge.svg?token=CxxB9Ew6Lx)](https://codecov.io/github/blitznihar/confluence-agentic-rag)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Last Commit](https://img.shields.io/github/last-commit/blitznihar/confluence-agentic-rag)
![License](https://img.shields.io/github/license/blitznihar/confluence-agentic-rag?cacheSeconds=0)
![License](https://img.shields.io/badge/license-MIT-green)



A production-style **Agentic RAG** starter project that ingests Confluence Cloud pages into a local **Weaviate vector database**, then answers questions using **semantic retrieval** + citations.

This project is designed for enterprise use cases like:

> "Find what we decided"  
> "Summarize architecture decisions"  
> "What is our RAG knowledge architecture?"  
> "What are our governance guardrails for agents?"

---

## Why this exists

In most enterprises, decisions and architecture knowledge live in documents (Confluence / SharePoint / PDFs), not databases.

Traditional DB query patterns fail because:

- decisions are written in **unstructured text**
- phrasing varies (e.g., "Accounting Center" vs "AC")
- people want answers **with citations**
- knowledge is distributed across many pages

**RAG is unavoidable** in these scenarios.

---

## Architecture Overview

### Components

- **Confluence Cloud** = source of truth for enterprise knowledge
- **Ingestion pipeline**
  - Search pages using CQL
  - Fetch page HTML
  - Convert to text + chunk
  - Generate embeddings (SentenceTransformers)
  - Store chunks in Weaviate
- **Weaviate** (local via Docker) = vector database
- **Agentic Query**
  - embed user question
  - retrieve top-k semantically similar chunks
  - generate grounded answer using retrieved excerpts + citations

---

## Project Structure

```
confluence-agentic-rag/
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── README.md
└── src/
├── confluence_agentic_rag/
│ ├── cli.py
│ ├── config.py
│ ├── tools/
│ │ └── confluence_client.py
│ ├── ingest/
│ │ └── ingest_confluence.py
│ ├── retrieval/
│ │ ├── chunking.py
│ ├── vectorstore/
│ │ ├── schema.py
│ │ └── weaviate_store.py
│ ├── agent/
│ │ ├── router.py
│ │ └── orchestrator.py
│ └── llm/
│ ├── base.py
│ └── stub.py
└── tests/
```

---

## Prerequisites

- Python **3.11+**
- Docker + Docker Compose
- Atlassian Confluence Cloud account (Free version works)

---

## Setup

### 1) Clone & install dependencies (UV)

```bash
uv sync
```

### 2) Start Weaviate (Local)

Weaviate runs locally using Docker Compose.

```bash
docker compose up -d
```

Verify:

```bash
curl http://localhost:6060/v1/meta
```

### 3) Configure environment variables

Copy .env.example → .env

```bash
cp .env.example .env
```

Example:

```env
CONFLUENCE_BASE_URL=https://<your-tenant>.atlassian.net
CONFLUENCE_EMAIL=<your-atlassian-email>
CONFLUENCE_API_TOKEN=<your-api-token>
CONFLUENCE_SPACE_KEY=AA

WEAVIATE_URL=http://localhost:6060
WEAVIATE_GRPC_PORT=6061
```

### How to get Confluence API Token

Confluence Admin UI does NOT show API tokens.

API Tokens are generated in Atlassian account settings:

- Go to Atlassian Account: Profile → Account Settings
- Security → API tokens
- Create token → Copy token

---

## Usage

### Ingest Confluence pages

This pulls relevant Confluence pages (ADRs, minutes, decision logs) and stores them into Weaviate.

```bash
uv run carag ingest --space AA --limit 200
```

Expected output:

```
Done. Pages=11 Chunks=15
```

### Ask questions (Agentic RAG)

```bash
uv run carag ask "What is our RAG + Knowledge Architecture?" --space AA --topk 10
```

Output includes:

- Answer
- Top sources + URLs
- similarity distances

---

## Example Questions (Best for Testing)

Use these questions to validate retrieval:

### Platform & Architecture

- "Summarize the Agentic AI Reference Architecture."
- "Explain our RAG + Knowledge Architecture and how Confluence is used."

### Governance

- "What guardrails, security, and privacy controls are required for agents?"
- "What is the ARB review process and required artifacts?"

### Delivery

- "What is our SDLC for agents and CI/CD + DevSecOps standards?"

### Operations

- "What monitoring and observability standards do we follow?"
- "What is our token budget/cost management approach?"

---

## Notes / Troubleshooting

### 1) 401 Unauthorized

This means:

- wrong email / token
- wrong Confluence base URL
- token not loaded from .env

Test auth:

```bash
curl -u "EMAIL:API_TOKEN" \
  "https://<tenant>.atlassian.net/wiki/rest/api/space?limit=1"
```

### 2) Duplicate URLs (double base URL issue)

If you previously ingested incorrect URLs, wipe the Weaviate data volume:

```bash
docker compose down
docker volume rm confluence-agentic-rag_weaviate_data
docker compose up -d
uv run carag ingest --space AA --limit 200
```

### 3) Vector store schema warning

If you see warnings like `vectorizer_config deprecated`, it's safe to ignore during dev. A future improvement is switching to vector_config.

---

## Roadmap / Enhancements

Planned improvements:

- Deduplicate chunks (deterministic chunk UUIDs)
- Incremental re-indexing by page version
- LLM integration (OpenAI/Azure/Local LM)
- Hybrid retrieval (Weaviate + live Confluence search fallback)
- Better chunking (by headings + bullet blocks)
- Decision Log structured extraction (DEC-ID, Date, Why, Options)

---

## License

MIT (or internal use)