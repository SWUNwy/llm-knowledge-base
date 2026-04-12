# Changelog

## 2026-04-12 — Frontend-Backend Integration + Website Auth + DevOps

### R004: Frontend-Backend API Integration
- **API client** (`frontend/src/services/api.ts`): Added Settings, Compile, SSE streaming, QA history methods
- **Dual-mode auth** (`frontend/src/hooks/useAuth.ts`): Local (username/password) and Cloud (email/password via cloudApi)
- **Login page** (`frontend/src/pages/Login.tsx`): Local/Cloud toggle UI
- **Settings page**: Real API calls to GET /settings, PUT /settings, POST /settings/verify-llm
- **Library page**: Per-document compile buttons + batch "Compile All Pending" with async polling
- **Chat page**: SSE streaming via fetch + ReadableStream, collapsible QA history sidebar
- **Import page**: "View in Library" link after successful imports
- **Cloud API** (`frontend/src/services/cloudApi.ts`): cloudLogin, verifyLicense, getUsage pointing to configurable CLOUD_API_URL

### R005: Website Auth + Stripe Integration
- **Register page** (`website/app/register/page.tsx`): Email/password registration with trial subscription
- **Login page** (`website/app/login/page.tsx`): Full login form replacing placeholder
- **Dashboard** (`website/app/dashboard/page.tsx`): Plan status, usage, "Launch App" link to frontend, license token
- **Navbar**: Shows auth state (Dashboard link + email for logged-in users)
- **Pricing/CTA**: Routes to /register (logged out) or Stripe checkout (logged in)
- **Stripe webhook**: Handles checkout, subscription update/delete, invoice events
- **Auth utilities** (`website/lib/auth-client.ts`): Client-side token/user management

### DevOps
- **Docker Compose**: 3-service setup (backend, frontend, website) with volume mounts for hot-reload
- **Dockerfiles**: One per service with proper build stages
- **E2E testing**: Playwright with Chromium, 3 smoke tests (login, setup, auth redirect)

### Bug Fixes
- useAuth: Refactored to lazy state initialization to fix react-hooks/set-state-in-effect lint error
- cloudApi: Changed process.env to import.meta.env for Vite compatibility
- Website build: Fixed bcrypt import (bcryptjs), Stripe API version, webhook null check

### Specs & Plans
- `docs/superpowers/specs/2026-04-11-frontend-backend-integration-design.md` — R004 spec
- `docs/superpowers/plans/2026-04-11-frontend-backend-integration.md` — R004 plan
- `docs/superpowers/plans/2026-04-11-website-integration.md` — R005 plan
- `docs/project-overview.md` — Updated to reflect all completed work
