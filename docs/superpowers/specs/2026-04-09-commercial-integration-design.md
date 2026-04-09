# Commercial Integration Design - KnowledgeBase SaaS

> Date: 2026-04-09
> Status: Approved
> Scope: Website + Cloud API + Local App commercial integration

---

## 1. Overview

### 1.1 Business Model

SaaS cloud service with local storage + cloud LLM. User data stays in local Obsidian vault; cloud handles LLM computation, billing, and license management.

### 1.2 Core Architecture

Three systems, each with clear responsibilities:

| System | Responsibility | Tech | Deployment |
|--------|---------------|------|------------|
| Website + Cloud API | Display, accounts, billing, LLM proxy | Next.js API Routes + PostgreSQL | Vercel |
| Local App | Import, compile, QA, Vault management | React + FastAPI (existing codebase) | User local |
| Stripe | Payment, subscription management | Stripe Checkout + Webhook | Stripe hosted |

### 1.3 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Website (Next.js on Vercel)                 │
│                                                              │
│  Landing: Hero / Features / Pricing / Pain Points / CTA      │
│  Marketing SEO (SSG) + Structured data                       │
│                                                              │
│  User system:                                                │
│  ├── /register — Email + password signup                     │
│  ├── /login — Login                                         │
│  ├── /dashboard — Plan management / Usage / Download         │
│  ├── /dashboard/billing — Stripe Customer Portal             │
│  ├── /pricing — Stripe Checkout redirect                     │
│  └── /api/stripe/webhook — Payment callback                  │
│                                                              │
│  Cloud API:                                                  │
│  ├── /api/auth/* — JWT issue/verify                          │
│  ├── /api/license/* — License query/activate/renewal         │
│  ├── /api/llm/proxy — LLM request proxy (compile + QA)       │
│  └── /api/usage/* — Usage statistics                         │
│                                                              │
│  Database: PostgreSQL (Supabase/Neon)                        │
│  ├── users, subscriptions, usage_logs                        │
└──────────────────────────────────────────────────────────────┘
         │ HTTPS                    │ HTTPS
         ▼                         ▼
┌────────────────────┐   ┌─────────────────────────────┐
│  User browser       │   │  Local App (React + FastAPI)  │
│  Browse website     │   │                               │
│  Register/Login/Pay │   │  Startup: verify License      │
│  Download installer │   │  Import: local parsing        │
│                    │   │  Compile: → Cloud LLM Proxy    │
│                    │   │  QA: local FTS → Cloud LLM     │
│                    │   │  Library browse: local only     │
│                    │   └── Obsidian Vault (local files)  │
└────────────────────┘   └─────────────────────────────┘
```

---

## 2. Database Schema

### 2.1 PostgreSQL Tables

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- Subscriptions (Stripe integration)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT UNIQUE,
    stripe_price_id TEXT,
    status TEXT, -- active, canceled, past_due, trialing
    tier TEXT, -- trial, personal, professional, team
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- License Tokens (local app uses these)
CREATE TABLE license_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT UNIQUE NOT NULL, -- SHA-256(token)
    device_name TEXT,
    device_id TEXT, -- Device fingerprint from local app
    tier TEXT, -- Inherited from subscription.tier
    expires_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usage logs
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action TEXT, -- compile, qa, embed
    tokens_used INTEGER,
    model TEXT,
    cost_cents INTEGER, -- Cost in cents for analysis
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Tier limits (configurable by operator, no code changes needed)
CREATE TABLE tier_limits (
    tier TEXT PRIMARY KEY, -- trial, personal, professional
    max_compiles INTEGER NOT NULL, -- -1 = unlimited
    max_qa INTEGER NOT NULL, -- -1 = unlimited
    allowed_models TEXT[], -- Array of allowed model IDs
    max_documents INTEGER, -- NULL = unlimited
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Initial tier limits data
INSERT INTO tier_limits VALUES
    ('trial',        5,   20,  ARRAY['gpt-4o-mini'], NULL, NOW()),
    ('personal',     30,  100, ARRAY['gpt-4o-mini'], NULL, NOW()),
    ('professional', -1,  -1,   ARRAY['gpt-4o','claude-3.5-sonnet'], NULL, NOW());

-- Releases (download versions)
CREATE TABLE releases (
    version TEXT PRIMARY KEY, -- v1.0.0
    download_url_mac TEXT,
    download_url_win TEXT,
    download_url_linux TEXT,
    release_notes TEXT,
    released_at TIMESTAMP DEFAULT NOW()
);
```

### 2.2 Limits are Configurable

Tier limits live in `tier_limits` table. Adjusting limits is a single SQL UPDATE, no code deployment needed.

Runtime flow:
1. User requests compile/QA → Cloud API reads `tier_limits` for user's tier
2. Query `usage_logs` for current month's usage
3. Compare: used < limits → allow; else → 429 Too Many Requests

---

## 3. User Journey

### 3.1 Two Registration Paths

**Path 1: Website entry**
```
User visits landing page
  → Click "Start Free Trial"
  → /register (email + password)
  → Stripe Checkout (14-day free trial)
  → /dashboard (plan status, download link)
  → Download & install local app
  → Login with email/password
  → POST /api/auth/login → returns License Token
  → Enter main app (Import/Library/Chat/Settings)
```

**Path 2: App entry**
```
User downloads and opens local app
  → Not logged in → shows login/register screen
  → Register: opens browser to /register (same flow as Path 1)
  → Login: POST /api/auth/login directly from app
  → Returns License Token → enter main app
```

### 3.2 Website New Pages

| Route | Purpose | Notes |
|-------|---------|-------|
| `/register` | Registration | Email + password, then redirect to Stripe Checkout |
| `/login` | Login | Replace existing placeholder page |
| `/dashboard` | User dashboard | Plan status, usage charts, download link, upgrade |
| `/dashboard/billing` | Billing management | Stripe Customer Portal integration |
| `/api/auth/*` | Auth API | Register / login / refresh token |
| `/api/license/*` | License API | Verify / activate / status query |
| `/api/llm/proxy` | LLM proxy | Compile/QA request forwarding |
| `/api/usage/*` | Usage API | Current month usage stats |
| `/api/stripe/webhook` | Payment callback | Stripe event handling |

---

## 4. LLM Proxy

### 4.1 Compile Flow

```
Local App                         Cloud API (Next.js)                 LLM Provider
   │                                    │                                 │
   │ POST /api/llm/proxy                │                                 │
   │ { token, action: "compile",        │                                 │
   │   payload: {                       │                                 │
   │     documents: [{ title, content }],│                                 │
   │     prompt_template: "wiki"        │                                 │
   │   }}                               │                                 │
   │ ──────────────────────────────────►│                                 │
   │                                    │                                 │
   │                         1. Verify token                             │
   │                         2. Check tier_limits                       │
   │                         3. Check monthly usage                     │
   │                         4. Select prompt_template                  │
   │                         5. Assemble prompt                         │
   │                                    │                                 │
   │                                    │ POST /v1/chat/completions       │
   │                                    │ (with our API Key)              │
   │                                    │ ───────────────────────────────►│
   │                                    │                                 │
   │                         SSE stream ◀────────────────────────────── │
   │                                    │                                 │
   │              SSE stream (relay)    │                                 │
   │ ◀──────────────────────────────── │                                 │
   │                                    │                                 │
   │                                    │ 6. Log usage (tokens, model, cost)
   │                                    │                                 │
   │ Write to local wiki/*.md           │                                 │
   │ Update local SQLite index          │                                 │
```

### 4.2 QA Flow

```
Local App
   │ 1. User asks: "What is RAG?"
   │ 2. Local FTS5 retrieves relevant snippets → 3 document paragraphs
   │
   │ POST /api/llm/proxy
   │ { token, action: "qa",
   │   payload: { question: "...", context: [{ doc_id, snippet }] }}
   │
   │ 3. Cloud API forwards to LLM → streams answer back
   │ 4. Local app displays answer + source citations
   │ 5. User clicks "Save to knowledge base" → writes to outputs/answers/
```

### 4.3 Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Prompt templates stored where | Cloud API side | Optimize prompts anytime without user app updates |
| Document content uploaded? | Only retrieved snippets, not full text | Minimize data transfer, protect privacy |
| Billing granularity | Log tokens, limit by count | Tokens for cost analysis, count for user throttling |
| Streaming | Cloud API relays SSE | User experience identical to direct LLM connection |
| Model routing | Cloud API selects model by tier | Seamless for users, operator controls costs |

### 4.4 Proxy Pseudocode

```typescript
// Next.js API Route: /api/llm/proxy

export async function POST(request: Request) {
  // 1. Verify License
  const user = await verifyLicense(request.token);
  if (!user) return Response.json({ error: "unauthorized" }, { status: 401 });

  // 2. Check limits
  const limits = await getTierLimits(user.tier);
  const usage = await getMonthlyUsage(user.id);
  const action = request.action; // "compile" or "qa"

  if (limits[`max_${action}s`] !== -1 && usage[action] >= limits[`max_${action}s`]) {
    return Response.json({ error: "limit_exceeded", remaining: 0 }, { status: 429 });
  }

  // 3. Select model
  const model = selectModel(user.tier, action);

  // 4. Build prompt
  const prompt = buildPrompt(request.action, request.payload);

  // 5. Call LLM (streaming)
  const stream = await streamLLM(model, prompt);

  // 6. Log usage after completion
  stream.onComplete((tokens) => logUsage(user.id, action, tokens, model));

  return new Response(stream, { headers: { "Content-Type": "text/event-stream" } });
}
```

---

## 5. Stripe Integration

### 5.1 Checkout Flow

```
User clicks "Start Free Trial" or "Upgrade"
  → Website creates Stripe Checkout Session
  → Redirect to Stripe hosted payment page
  → User enters payment info
  → Stripe processes payment
  → Stripe sends webhook: checkout.session.completed
  → Website creates/updates subscription record
  → Redirect to /dashboard
```

### 5.2 Webhook Events

| Event | Handling |
|-------|----------|
| `checkout.session.completed` | First subscription → create subscription record, set tier + 14-day trial |
| `customer.subscription.updated` | Plan change → update tier, effective immediately |
| `customer.subscription.deleted` | Cancel/expired → tier becomes `free`, License token invalidated |
| `invoice.payment_succeeded` | Renewal success → extend period_end, reset monthly usage |
| `invoice.payment_failed` | Renewal failed → mark `past_due`, email user |

### 5.3 Stripe Products & Prices

```
KnowledgeBase Personal
  ├── Monthly price_xxx (¥49/month)
  └── Yearly price_yyy (¥468/year)

KnowledgeBase Professional
  ├── Monthly price_aaa (¥99/month)
  └── Yearly price_bbb (¥948/year)

KnowledgeBase Team
  ├── Monthly price_ccc (¥299/month)
  └── Yearly price_ddd (¥2868/year)
```

### 5.4 Dashboard Billing

| Feature | Implementation |
|---------|---------------|
| Upgrade | Redirect to Stripe Checkout with `upgrade=True` |
| Downgrade/Cancel | Redirect to Stripe Customer Portal (built-in) |
| Renewal | Stripe auto-handles, webhook notifies us |
| Billing history | Stripe Customer Portal built-in |
| Refunds | Manual via Stripe Dashboard |

### 5.5 Security

| Item | Measure |
|------|---------|
| Webhook verification | Validate Stripe Signature, prevent forgery |
| API Key security | Stripe Secret Key in environment variables only |
| Payment page security | Stripe Checkout hosted page, PCI compliance by Stripe |
| Fraud prevention | Stripe Radar built-in |

---

## 6. Local App Changes

### 6.1 Change Overview

| Component | Current | After |
|-----------|---------|-------|
| Login page | Local username/password | Email + password → Cloud API |
| Setup page | Local account setup | Removed; registration opens browser to /register |
| Settings page | Manual LLM API Key config | Show current plan + usage + available models |
| Compile flow | Direct LLM API call | Via Cloud /api/llm/proxy |
| QA flow | Direct LLM API call | Via Cloud /api/llm/proxy |

### 6.2 New Backend Modules

```
backend/src/
├── auth/
│   ├── service.py       # Modified: call Cloud API for login
│   ├── router.py        # Modified: /login → Cloud API
│   ├── jwt.py           # Kept: local token cache management
│   └── cloud_auth.py    # New: Cloud API auth client
├── llm/
│   ├── client.py        # Modified: add CloudLLMClient
│   └── prompts.py       # Kept: still need template names locally
├── license/
│   ├── __init__.py      # New
│   ├── manager.py       # New: License cache, verify, refresh
│   └── limits.py        # New: Local limits cache + usage tracking
└── config.py            # Modified: add CLOUD_API_URL
```

### 6.3 Startup Flow

```
App starts
  │
  ├─ Read cached license_token
  │   │
  │   ├─ Has token
  │   │   ├─ POST CLOUD_API_URL/api/license/verify
  │   │   │   ├─ Valid → load limits, enter main UI
  │   │   │   ├─ Expired → clear cache, show login
  │   │   │   └─ Network error → use cached limits, allow offline 24h
  │   │   │
  │   │   └─ Background: refresh token every 6h
  │   │
  │   └─ No token → show login page
```

### 6.4 Offline Grace Period

If cloud API is unreachable:
- Use last cached limits (allow 24h offline)
- LLM features disabled (cannot reach proxy)
- Local features work normally: browse library, full-text search, view documents

### 6.5 Compile Call Change

```python
# Before: direct LLM call
# response = await llm_client.generate(prompt, config)

# After: via Cloud proxy
response = await cloud_llm_client.proxy_compile(
    token=license_token,
    documents=[{"title": doc.title, "content": doc.content[:8000]}],
    prompt_template="wiki"
)
```

Offline fallback: if user configured their own LLM API Key, fall back to direct connection mode. Both modes coexist.

### 6.6 Settings Page

```
┌─ Settings ────────────────────────────┐
│                                        │
│  Current plan: Professional            │
│  Monthly usage:                        │
│    Compile: 23 / Unlimited             │
│    QA: 87 / Unlimited                  │
│                                        │
│  Available models: GPT-4o, Claude 3.5  │
│                                        │
│  [Logout]                              │
└────────────────────────────────────────┘
```

### 6.7 Change Effort Estimate

| Type | Files | Effort |
|------|-------|--------|
| New | `license/manager.py`, `license/limits.py`, `auth/cloud_auth.py` | Medium |
| Modified | `auth/service.py`, `auth/router.py`, `llm/client.py`, `config.py` | Medium |
| Modified | Frontend: `Login.tsx`, `Settings.tsx`, `Chat.tsx`, `Import.tsx` | Medium |
| Removed | Frontend: `Setup.tsx` (registration moves to browser) | Small |

---

## 7. Pricing Tiers

| Tier | Price | Compiles/month | QA/month | Models |
|------|-------|---------------|----------|--------|
| Trial (14 days) | Free | 5 | 20 | GPT-4o-mini |
| Personal | ¥49/month | 30 | 100 | GPT-4o-mini |
| Professional | ¥99/month | Unlimited | Unlimited | GPT-4o, Claude 3.5 |
| Team | ¥299/month | Unlimited | Unlimited | GPT-4o, Claude 3.5 + shared workspace |

All limits configurable via `tier_limits` table. No code changes needed to adjust.

---

## 8. Security Considerations

| Area | Measure |
|------|---------|
| User data | All documents stay local; only snippets sent to cloud for LLM processing |
| API Keys | LLM API keys stored only on server; users never see them |
| License tokens | Hashed in database; app stores raw token locally |
| Webhook | Stripe signature verification on every event |
| Passwords | bcrypt hash; never stored plaintext |
| Communication | All API calls over HTTPS |
| Rate limiting | Per-user rate limiting on Cloud API endpoints |

---

## 9. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Cloud database | PostgreSQL (Supabase or Neon) | Serverless, free tier, managed |
| Auth | Custom JWT + bcrypt | Simple for MVP; no third-party auth dependency |
| Payments | Stripe Checkout + Webhooks | Industry standard, PCI compliant, handles subscriptions |
| LLM proxy | Next.js API Routes | Same deployment as website, no extra service |
| Local app storage | SQLite + filesystem (unchanged) | Local-first architecture preserved |
| Hosting | Vercel | Free tier, global CDN, seamless Next.js deployment |
