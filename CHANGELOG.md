# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- **R004 MarkItDown Integration**: Replace PDFParser and WebParser with unified MarkItDown engine
  - New file format support: DOCX, PPTX, XLSX, EPUB, CSV, images, Jupyter notebooks
  - Output preserves document structure as Markdown (headings, tables, lists)
  - DocumentProcessor: smart chunking by heading hierarchy with token estimation
  - Format-specific LLM compile prompts (tables, presentations, academic papers)
  - Removed PyMuPDF and readability-lxml dependencies
- **R001 Frontend-Backend Integration**
  - Settings page wired to backend save/verify-llm API
  - Configured providers display from backend settings response
- **R001 Deployment**
  - Multi-stage Dockerfile (Python backend + nginx frontend)
  - docker-compose.yml with volume persistence and health checks
  - Nginx config with API proxy and SPA routing
  - .env.example configuration template
- **R001 E2E Tests**
  - 25 Playwright E2E tests: login, import, library, chat, settings flows

### Changed
- R003: SaaS Commercial Integration
  - Updated backend config with markitdown_llm_image_description and chunk_token_limit fields
  - Added token refresh API endpoint (backend/src/routes/license.py)
  - Added license status query API endpoint
- Upgraded Python venv from 3.9 to 3.14 for markitdown compatibility

## [0.1.0] - 2026-04-10

### Added
- Initial project structure
  - Backend API with FastAPI
  - Frontend with React + Vite
  - SQLite database with aiosqlite
  - Multiple content parsers (PDF, Web, Video, GitHub)
  - LLM integration via LiteLLM
  - Knowledge base compilation and Q&A
