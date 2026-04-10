# Changelog

All notable changes to this project.

## [Unreleased]

### Added

### Changed

### Fixed

### Security

---

## [0.2.0] - 2026-04-10

### Added
- **R003 Commercial Integration**: Complete SaaS transformation
  - Website + Cloud API on Next.js
  - PostgreSQL database schema with 6 tables (users, subscriptions, license_tokens, usage_logs, tier_limits, releases)
  - JWT authentication with bcrypt password hashing
  - License verification and token management system
  - LLM proxy with SSE streaming and usage limits
  - Stripe integration (Checkout + Webhooks)
  - Local app transformation for SaaS mode (cloud auth, license manager, usage tracker)
  - Deployment documentation

**New Website Files** (25):
- `website/db/schema.sql`, `website/db/migrations/001_initial.sql`
- `website/lib/db.ts`, `website/lib/auth.ts`, `website/lib/stripe.ts`, `website/lib/llm.ts`
- API Routes: auth/register, auth/login, auth/refresh, license/verify, license/status
- API Routes: llm/proxy, usage/current, stripe/checkout, stripe/webhook
- `website/.env.example`, `docs/deployment/r003-saas-deployment.md`

**New Backend Files** (6):
- `backend/src/auth/cloud_auth.py`
- `backend/src/license/manager.py`, `backend/src/license/limits.py`, `backend/src/license/__init__.py`
- `backend/src/llm/cloud_client.py`
- `backend/.env.example`

**Modified Backend** (4):
- `config.py` - Added CLOUD_API_URL, LICENSE_TOKEN_PATH
- `auth/service.py` - Cloud SaaS login support
- `llm/client.py` - Fixed retry mechanism, added CloudLLMClient
- `main.py` - License verification on startup

**Modified Frontend** (3):
- `pages/Login.tsx` - SaaS cloud authentication
- `pages/Settings.tsx` - Plan and usage display
- `services/cloudApi.ts` - New cloud API client

**Infrastructure**:
- Implementation plan: `docs/superpowers/plans/2026-04-10-r003-commercial-integration.md`
- 27 commits implementing all 24 tasks + extras
- +2,329 lines, -1,388 lines across 49 files

### Changed
- Updated task lists (R001, R002-Website, R002-Error) to reflect actual progress
- Project overview updated with accurate statistics

### Fixed
- LLM Client retry mechanism - separated retry logic from error conversion

### Security
- License token verification on all protected endpoints
- Stripe webhook signature verification
- bcrypt password hashing
- JWT token expiration

---

## [0.1.0] - 2026-04-09

### Added
- Phase 1 MVP: Website with Hero, Features, Pricing, CTA, Footer sections
- Backend skeleton: FastAPI + SQLite, 9 routers, 4 parsers
- Frontend skeleton: React + Vite + TailwindCSS, 6 pages
- Testing: Pytest framework with 19 test files

### Changed
- Initial project structure

---

## Version Format
[MAJOR].[MINOR].[PATCH]
- MAJOR: Breaking changes
- MINOR: New features  
- PATCH: Bug fixes
