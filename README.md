# LLM Knowledge Base

> Turn scattered materials into a connected knowledge base — automatically.

LLM Knowledge Base is a self-hosted web application that ingests documents (PDF, Office, web pages, videos, code, and more), converts them into clean Markdown via [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — the open-source engine that unifies 15+ file formats — and uses LLM to compile them into a structured Obsidian wiki with `[[bidirectional links]]`. Then ask questions against your knowledge base — and save answers back to grow it.

---

## The Knowledge Flywheel

```
Collect (Import) → Parse (MarkItDown) → Compile (LLM) → Wiki (Obsidian)
      ↑                                                        │
      └──────────── Ask & Save Back (Self-Reinforcing) ──────────┘
```

1. **Import anything** — Drop in PDFs, web URLs, videos, GitHub repos, Office documents
2. **Unified parsing** — Microsoft MarkItDown converts 15+ formats into clean Markdown
3. **Format-aware LLM compilation** — Different document types get specialized prompts (tables → data analysis, slides → narrative flow, papers → academic structure)
4. **Obsidian-native output** — `[[wiki-links]]`, frontmatter, organized under your vault
5. **Ask and grow** — Q&A against your wiki, with answers that can be saved back as new knowledge

---

## Key Highlights

### Unified Ingestion Pipeline

Instead of writing a separate parser for every format, the system integrates [**Microsoft MarkItDown**](https://github.com/microsoft/markitdown) — an open-source file-to-Markdown conversion engine — as a unified parser:

| Category | Formats |
|----------|---------|
| Documents | PDF, DOCX, PPTX, XLSX, XLS |
| Web | URL, HTML, HTM |
| E-Books | EPUB |
| Data | CSV |
| Images | JPG, JPEG, PNG (with optional LLM description) |
| Code | Jupyter Notebooks (ipynb), GitHub repos |
| Video | YouTube, Bilibili (subtitle extraction) |

Everything comes out as **clean Markdown** — the rest of the pipeline only speaks one format.

### Format-Aware Compilation

Not a single "dump text into LLM" prompt. The system routes each document type to a specialized compilation template:

- **PDF/Academic papers** → `COMPILE_PAPER` — preserves abstract/methodology/results structure
- **PPTX Presentations** → `COMPILE_PRESENTATION` — adds narrative transitions between slides
- **XLSX/CSV Tables** → `COMPILE_TABLE_DATA` — preserves numerical precision, highlights trends
- **General documents** → `COMPILE_DOCUMENT` — standard wiki structuring with `[[links]]`

### Smart Chunking

Documents are split by **heading hierarchy** (H1 → H2) before hitting the LLM, keeping context windows efficient. Presentations are split by slide boundary.

### Self-Reinforcing Knowledge Loop

```
Question → FTS5 Search → LLM Answer (with source citations)
                                     ↓
                          Save answer → Vault grows → Better answers next time
```

### Local-First, No Lock-In

- All data lives in your **Obsidian vault** — a folder of standard Markdown files
- `[[wiki-links]]` work natively in Obsidian's Graph View
- You own everything. No proprietary format, no cloud dependency for core features.

### Multi-LLM Support

Via LiteLLM — one interface for **Gemini, Claude, GPT, local models**, and 100+ LLM providers:

```env
LLM_PROVIDER=gemini    # or: openai, anthropic, ollama, ...
LLM_MODEL=gemini-2.0-flash
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + TailwindCSS |
| Backend | Python 3.11+ + FastAPI |
| Database | SQLite + FTS5 full-text search |
| File Parsing | Microsoft MarkItDown (open source) |
| LLM Gateway | LiteLLM (unified API for 100+ models) |
| E2E Testing | Playwright (25 tests across all user flows) |
| Deployment | Docker Compose (3 services with health checks) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An Obsidian vault (or any empty directory)

### Setup

```bash
# 1. Clone
git clone https://github.com/<your-org>/llm-knowledge-base
cd llm-knowledge-base

# 2. Run setup script
chmod +x scripts/*.sh
./scripts/setup.sh

# 3. Configure
cp .env.example .env
# Edit .env: set VAULT_PATH, APP_SECRET_KEY, and at least one LLM API key
```

### Development

**Terminal 1 — Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

### Production (Docker)

```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| Web App | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| OpenAPI Spec | `docs/api.yaml` |

---

## Project Structure

```
llm-knowledge-base/
├── backend/            # Python FastAPI backend
│   ├── src/            # Source code (9 routers, 4 parsers, 4 services)
│   │   ├── parsers/    # MarkItDown, Video, GitHub parsers
│   │   ├── services/   # Ingest, Compile, QA, DocumentProcessor
│   │   ├── llm/        # LLM client + prompt templates
│   │   ├── routers/    # API endpoints
│   │   └── ...
│   └── tests/          # Unit + integration tests
├── frontend/           # React SPA
│   ├── src/pages/      # Login, Import, Library, Chat, Settings, Concepts
│   └── e2e/            # Playwright E2E tests (25 tests)
├── website/            # SaaS marketing site (Next.js)
├── docs/               # Design docs, API spec, requirements
├── docker-compose.yml  # 3-service production deployment
└── .env.example        # Configuration template
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           Frontend (React + Vite)            │
│  Import │ Library │ Chat │ Settings          │
└──────────────────┬──────────────────────────┘
                   │ REST API / SSE
┌──────────────────▼──────────────────────────┐
│          Backend (Python FastAPI)             │
│                                              │
│  Ingestion Pipeline:                         │
│    MarkItDown → DocumentProcessor → Chunks   │
│                                              │
│  Compilation Pipeline:                       │
│    Chunks → Format-Specific Prompt → LLM     │
│           → Wiki Article with [[links]]      │
│                                              │
│  Q&A Pipeline:                               │
│    Question → FTS5 Search → Context Prompt   │
│           → LLM → Answer + Source Citations  │
└──────────────────┬──────────────────────────┘
                   │ File System I/O
┌──────────────────▼──────────────────────────┐
│        Obsidian Vault (Local Folder)          │
│  raw/ │ wiki/sources/ │ outputs/              │
│  All standard Markdown — use any editor       │
└─────────────────────────────────────────────┘
```

---

## Configuration

| Key | Description | Required |
|-----|-------------|----------|
| `APP_SECRET_KEY` | JWT signing secret | Yes |
| `VAULT_PATH` | Absolute path to your Obsidian vault | Yes |
| `LLM_PROVIDER` | `gemini` / `openai` / `anthropic` / `ollama` / etc. | Yes |
| `LLM_API_KEY` | API key for your LLM provider | Yes (one of) |
| `LLM_MODEL` | Model name (e.g., `gemini-2.0-flash`) | Optional |

---

## Running Tests

```bash
# Backend tests
cd backend && ./scripts/test.sh

# E2E tests
cd frontend && npx playwright test
```

---

## Documentation

- [Product Requirements](docs/requirements/active/R001-llm-knowledge-base/proposal.md)
- [System Design](docs/requirements/active/R001-llm-knowledge-base/design.md)
- [Project Overview (Chinese)](docs/project-overview.md)
- [API Specification](docs/api.yaml)

---

## Roadmap

- [x] Core pipeline: import → compile → Q&A
- [x] 15+ file formats via MarkItDown
- [x] Format-aware LLM prompts
- [x] Full Docker Compose deployment
- [x] 25 Playwright E2E tests
- [ ] Vector search (SQLite-vec) for semantic retrieval
- [ ] Knowledge graph visualization
- [ ] Multi-format output (slides, reports)
- [ ] CLI tooling

---

## License

MIT
