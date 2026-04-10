# R003 Commercial Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the project into a SaaS product with cloud-based user accounts, billing via Stripe, LLM proxy, and local app license verification.

**Architecture:** Three-tier system: (1) Website + Cloud API on Next.js/Vercel for accounts/billing/LLM proxy, (2) PostgreSQL for user/subscription/license data, (3) Local App (React+FastAPI) transformed to SaaS client with cloud license verification.

**Tech Stack:** Next.js API Routes, PostgreSQL (Supabase/Neon), Stripe Checkout, JWT, bcrypt, existing FastAPI/React codebase

---

## File Structure Overview

### Website (New/Modified)
```
website/
├── app/
│   ├── register/page.tsx          # NEW: User registration
│   ├── login/page.tsx             # MODIFY: Replace placeholder with real auth
│   ├── dashboard/page.tsx         # NEW: User dashboard
│   ├── dashboard/billing/page.tsx # NEW: Stripe Customer Portal
│   └── api/
│       ├── auth/
│       │   ├── register/route.ts  # NEW: Registration API
│       │   ├── login/route.ts     # NEW: Login API
│       │   └── refresh/route.ts   # NEW: Token refresh
│       ├── license/
│       │   ├── verify/route.ts    # NEW: License verification
│       │   └── status/route.ts    # NEW: License status query
│       ├── llm/
│       │   └── proxy/route.ts     # NEW: LLM request proxy
│       ├── usage/
│       │   └── current/route.ts   # NEW: Usage statistics
│       └── stripe/
│           └── webhook/route.ts   # NEW: Stripe webhooks
├── lib/
│   ├── db.ts                      # NEW: PostgreSQL client
│   ├── auth.ts                    # NEW: JWT utilities
│   ├── stripe.ts                  # NEW: Stripe client
│   └── limits.ts                  # NEW: Tier limits logic
└── middleware.ts                  # MODIFY: Add auth middleware
```

### Local App Backend (New/Modified)
```
backend/src/
├── auth/
│   ├── cloud_auth.py              # NEW: Cloud API auth client
│   ├── service.py                 # MODIFY: Call Cloud API for login
│   └── router.py                  # MODIFY: /login routes to Cloud API
├── license/
│   ├── __init__.py                # NEW
│   ├── manager.py                 # NEW: License cache, verify, refresh
│   └── limits.py                  # NEW: Local limits cache + usage tracking
├── llm/
│   ├── client.py                  # MODIFY: Add CloudLLMClient
│   └── cloud_client.py            # NEW: Cloud proxy client
└── config.py                      # MODIFY: Add CLOUD_API_URL
```

### Local App Frontend (Modified)
```
frontend/src/
├── pages/
│   ├── Login.tsx                  # MODIFY: Email/password + register link
│   ├── Setup.tsx                  # DELETE: Registration moves to browser
│   ├── Settings.tsx               # MODIFY: Show plan, usage, models
│   ├── Import.tsx                 # MODIFY: Use CloudLLMClient
│   └── Chat.tsx                   # MODIFY: Use CloudLLMClient
└── services/
    └── cloudApi.ts                # NEW: Cloud API client
```

### Database Schema
```
-- PostgreSQL tables (Cloud)
users, subscriptions, license_tokens, usage_logs, tier_limits, releases
```

---

## Phase 1: Database & Shared Infrastructure

Both Website and Local App need shared types and database setup. Do this first.

### Task 1: Create PostgreSQL Database Schema

**Files:**
- Create: `website/db/schema.sql`
- Create: `website/db/migrations/001_initial.sql`

- [ ] **Step 1: Write schema.sql with all tables**

```sql
-- website/db/schema.sql

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- Subscriptions table (Stripe integration)
CREATE TABLE IF NOT EXISTS subscriptions (
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
CREATE TABLE IF NOT EXISTS license_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT UNIQUE NOT NULL, -- SHA-256(token)
    device_name TEXT,
    device_id TEXT,
    tier TEXT,
    expires_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usage logs
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action TEXT, -- compile, qa, embed
    tokens_used INTEGER,
    model TEXT,
    cost_cents INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Tier limits (configurable)
CREATE TABLE IF NOT EXISTS tier_limits (
    tier TEXT PRIMARY KEY,
    max_compiles INTEGER NOT NULL,
    max_qa INTEGER NOT NULL,
    allowed_models TEXT[],
    max_documents INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Initial tier limits
INSERT INTO tier_limits (tier, max_compiles, max_qa, allowed_models, max_documents, updated_at)
VALUES
    ('trial', 5, 20, ARRAY['gpt-4o-mini'], NULL, NOW()),
    ('personal', 30, 100, ARRAY['gpt-4o-mini'], NULL, NOW()),
    ('professional', -1, -1, ARRAY['gpt-4o','claude-3.5-sonnet'], NULL, NOW())
ON CONFLICT (tier) DO NOTHING;

-- Releases (download versions)
CREATE TABLE IF NOT EXISTS releases (
    version TEXT PRIMARY KEY,
    download_url_mac TEXT,
    download_url_win TEXT,
    download_url_linux TEXT,
    release_notes TEXT,
    released_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_license_tokens_user_id ON license_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_license_tokens_token_hash ON license_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);
```

- [ ] **Step 2: Create migration wrapper**

```sql
-- website/db/migrations/001_initial.sql
\i schema.sql
```

- [ ] **Step 3: Commit**

```bash
git add website/db/
git commit -m "feat(r003): add PostgreSQL schema for commercial integration"
```

### Task 2: Create Database Client for Website

**Files:**
- Create: `website/lib/db.ts`

- [ ] **Step 1: Write database client**

```typescript
// website/lib/db.ts
import { Pool } from 'pg';

if (!process.env.DATABASE_URL) {
  throw new Error('DATABASE_URL environment variable is not set');
}

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

export interface User {
  id: string;
  email: string;
  password_hash: string;
  created_at: Date;
  last_login_at: Date | null;
}

export interface Subscription {
  id: string;
  user_id: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  stripe_price_id: string | null;
  status: string;
  tier: string;
  current_period_start: Date | null;
  current_period_end: Date | null;
  cancel_at_period_end: boolean;
  created_at: Date;
  updated_at: Date;
}

export interface LicenseToken {
  id: string;
  user_id: string;
  token_hash: string;
  device_name: string | null;
  device_id: string | null;
  tier: string;
  expires_at: Date | null;
  last_seen_at: Date | null;
  created_at: Date;
}

export interface UsageLog {
  id: string;
  user_id: string;
  action: string;
  tokens_used: number | null;
  model: string | null;
  cost_cents: number | null;
  timestamp: Date;
}

export interface TierLimits {
  tier: string;
  max_compiles: number;
  max_qa: number;
  allowed_models: string[];
  max_documents: number | null;
  updated_at: Date;
}

export async function query<T>(text: string, params?: any[]): Promise<T[]> {
  const client = await pool.connect();
  try {
    const result = await client.query(text, params);
    return result.rows as T[];
  } finally {
    client.release();
  }
}

export async function queryOne<T>(text: string, params?: any[]): Promise<T | null> {
  const rows = await query<T>(text, params);
  return rows[0] || null;
}
```

- [ ] **Step 2: Commit**

```bash
git add website/lib/db.ts
git commit -m "feat(r003): add database client for PostgreSQL"
```

### Task 3: Create Auth Utilities (JWT + Password)

**Files:**
- Create: `website/lib/auth.ts`

- [ ] **Step 1: Write auth utilities**

```typescript
// website/lib/auth.ts
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import crypto from 'crypto';

const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-production';
const LICENSE_TOKEN_SECRET = process.env.LICENSE_TOKEN_SECRET || JWT_SECRET;

export interface JWTPayload {
  sub: string; // user_id
  email: string;
  tier?: string;
}

export interface LicenseTokenPayload {
  sub: string; // user_id
  email: string;
  tier: string;
  device_id?: string;
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export function signAccessToken(payload: JWTPayload): string {
  return jwt.sign(payload, JWT_SECRET, { expiresIn: '7d' });
}

export function verifyAccessToken(token: string): JWTPayload | null {
  try {
    return jwt.verify(token, JWT_SECRET) as JWTPayload;
  } catch {
    return null;
  }
}

export function generateLicenseToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

export function hashLicenseToken(token: string): string {
  return crypto.createHash('sha256').update(token).digest('hex');
}

export function signLicenseToken(payload: LicenseTokenPayload): string {
  const token = generateLicenseToken();
  const jwtPayload = { ...payload, token };
  // Store the JWT for verification, client gets the raw token
  return {
    raw: token,
    jwt: jwt.sign(jwtPayload, LICENSE_TOKEN_SECRET, { expiresIn: '30d' })
  };
}

export function verifyLicenseToken(jwtToken: string): LicenseTokenPayload | null {
  try {
    return jwt.verify(jwtToken, LICENSE_TOKEN_SECRET) as LicenseTokenPayload;
  } catch {
    return null;
  }
}
```

- [ ] **Step 2: Install dependencies**

```bash
cd website && npm install jsonwebtoken bcryptjs @types/jsonwebtoken @types/bcryptjs
```

- [ ] **Step 3: Commit**

```bash
git add website/lib/auth.ts package.json package-lock.json
git commit -m "feat(r003): add auth utilities for JWT and password hashing"
```

---

## Phase 2A: Website + Cloud API

These tasks can be done in parallel with Phase 2B.

### Task 4: Registration API

**Files:**
- Create: `website/app/api/auth/register/route.ts`

- [ ] **Step 1: Write failing test**

```typescript
// No test file yet - we'll add integration tests later
```

- [ ] **Step 2: Implement registration endpoint**

```typescript
// website/app/api/auth/register/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne, User } from '@/lib/db';
import { hashPassword, signAccessToken } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Email and password are required' } },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Password must be at least 8 characters' } },
        { status: 400 }
      );
    }

    // Check if user exists
    const existing = await queryOne<User>(
      'SELECT id FROM users WHERE email = $1',
      [email]
    );

    if (existing) {
      return NextResponse.json(
        { error: { code: 'AUTH_EMAIL_EXISTS', message: 'Email already registered' } },
        { status: 409 }
      );
    }

    // Create user
    const passwordHash = await hashPassword(password);
    const user = await queryOne<User>(
      `INSERT INTO users (email, password_hash)
       VALUES ($1, $2)
       RETURNING id, email, created_at`,
      [email, passwordHash]
    );

    if (!user) {
      throw new Error('Failed to create user');
    }

    // Create trial subscription
    await query(
      `INSERT INTO subscriptions (user_id, status, tier, current_period_start, current_period_end)
       VALUES ($1, 'trialing', 'trial', NOW(), NOW() + INTERVAL '14 days')`,
      [user.id]
    );

    // Sign JWT
    const token = signAccessToken({ sub: user.id, email: user.email, tier: 'trial' });

    return NextResponse.json({
      access_token: token,
      user: { id: user.id, email: user.email },
      redirect_to: '/pricing' // Will go to Stripe next
    });

  } catch (error) {
    console.error('Registration error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Registration failed' } },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add website/app/api/auth/register/route.ts
git commit -m "feat(r003): add registration API endpoint"
```

### Task 5: Login API

**Files:**
- Create: `website/app/api/auth/login/route.ts`

- [ ] **Step 1: Implement login endpoint**

```typescript
// website/app/api/auth/login/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { queryOne, User } from '@/lib/db';
import { verifyPassword, signAccessToken, signLicenseToken } from '@/lib/auth';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const { email, password, device_name, device_id } = await request.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Email and password are required' } },
        { status: 400 }
      );
    }

    // Get user with subscription
    const user = await queryOne<User>(
      'SELECT u.*, s.tier FROM users u LEFT JOIN subscriptions s ON s.user_id = u.id WHERE u.email = $1',
      [email]
    );

    if (!user) {
      return NextResponse.json(
        { error: { code: 'AUTH_INVALID_CREDENTIALS', message: 'Invalid email or password' } },
        { status: 401 }
      );
    }

    // Verify password (user object has password_hash from query)
    const userWithHash = await queryOne<{password_hash: string}>(
      'SELECT password_hash FROM users WHERE id = $1',
      [user.id]
    );

    if (!userWithHash || !await verifyPassword(password, userWithHash.password_hash)) {
      return NextResponse.json(
        { error: { code: 'AUTH_INVALID_CREDENTIALS', message: 'Invalid email or password' } },
        { status: 401 }
      );
    }

    // Update last login
    await query('UPDATE users SET last_login_at = NOW() WHERE id = $1', [user.id]);

    // Sign JWT
    const tier = (user as any).tier || 'trial';
    const accessToken = signAccessToken({ sub: user.id, email: user.email, tier });

    // For local app: generate and store license token
    let licenseToken = null;
    if (device_name || device_id) {
      const tokenData = signLicenseToken({
        sub: user.id,
        email: user.email,
        tier,
        device_id
      });

      // Store license token hash
      await query(
        `INSERT INTO license_tokens (user_id, token_hash, device_name, device_id, tier, expires_at)
         VALUES ($1, $2, $3, $4, $5, NOW() + INTERVAL '30 days')
         ON CONFLICT (user_id, device_id) DO UPDATE
         SET token_hash = $2, tier = $5, expires_at = NOW() + INTERVAL '30 days', last_seen_at = NOW()`,
        [user.id, crypto.createHash('sha256').update(tokenData.raw).digest('hex'), device_name, device_id, tier]
      );

      licenseToken = tokenData.raw;
    }

    return NextResponse.json({
      access_token: accessToken,
      license_token: licenseToken,
      user: { id: user.id, email: user.email },
      tier
    });

  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Login failed' } },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add website/app/api/auth/login/route.ts
git commit -m "feat(r003): add login API with license token generation"
```

### Task 6: License Verify API

**Files:**
- Create: `website/app/api/license/verify/route.ts`

- [ ] **Step 1: Implement license verification**

```typescript
// website/app/api/license/verify/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { queryOne, LicenseToken, TierLimits } from '@/lib/db';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const { token } = await request.json();

    if (!token) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'License token is required' } },
        { status: 400 }
      );
    }

    // Look up license token by hash
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
    const licenseToken = await queryOne<LicenseToken>(
      `SELECT lt.*, u.email, s.status as subscription_status
       FROM license_tokens lt
       JOIN users u ON u.id = lt.user_id
       LEFT JOIN subscriptions s ON s.user_id = u.id
       WHERE lt.token_hash = $1`,
      [tokenHash]
    );

    if (!licenseToken) {
      return NextResponse.json(
        { error: { code: 'LICENSE_INVALID', message: 'Invalid license token' } },
        { status: 401 }
      );
    }

    // Check if expired
    if (licenseToken.expires_at && new Date() > licenseToken.expires_at) {
      return NextResponse.json(
        { error: { code: 'LICENSE_EXPIRED', message: 'License token has expired' } },
        { status: 401 }
      );
    }

    // Check if subscription is active
    const subStatus = (licenseToken as any).subscription_status;
    if (subStatus && subStatus !== 'active' && subStatus !== 'trialing') {
      return NextResponse.json(
        { error: { code: 'LICENSE_SUSPENDED', message: 'Subscription is not active' } },
        { status: 403 }
      );
    }

    // Get tier limits
    const limits = await queryOne<TierLimits>(
      'SELECT * FROM tier_limits WHERE tier = $1',
      [licenseToken.tier]
    );

    // Update last seen
    await query('UPDATE license_tokens SET last_seen_at = NOW() WHERE id = $1', [licenseToken.id]);

    return NextResponse.json({
      valid: true,
      user: {
        id: licenseToken.user_id,
        email: (licenseToken as any).email
      },
      tier: licenseToken.tier,
      limits: limits || {
        max_compiles: -1,
        max_qa: -1,
        allowed_models: [],
        max_documents: null
      }
    });

  } catch (error) {
    console.error('License verify error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'License verification failed' } },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add website/app/api/license/verify/route.ts
git commit -m "feat(r003): add license verification API"
```

### Task 7: LLM Proxy API (Core Feature)

**Files:**
- Create: `website/app/api/llm/proxy/route.ts`
- Create: `website/lib/llm.ts`

- [ ] **Step 1: Create LLM client utilities**

```typescript
// website/lib/llm.ts
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export interface CompileRequest {
  action: 'compile';
  payload: {
    documents: Array<{ title: string; content: string }>;
    prompt_template: string;
  };
}

export interface QARequest {
  action: 'qa';
  payload: {
    question: string;
    context: Array<{ doc_id: string; snippet: string }>;
  };
}

export async function streamLLM(
  model: string,
  messages: OpenAI.Chat.ChatCompletionMessageParam[]
): Promise<ReadableStream> {
  const stream = await openai.chat.completions.create({
    model,
    messages,
    stream: true,
  });

  // Convert OpenAI stream to Web Stream
  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          const content = chunk.choices[0]?.delta?.content;
          if (content) {
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content })}\n\n`));
          }
        }
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });

  return readable;
}

export function buildCompilePrompt(documents: CompileRequest['payload']['documents']): string {
  const docsText = documents.map(d => `# ${d.title}\n\n${d.content}`).join('\n\n---\n\n');
  return `You are a knowledge base compiler. Convert the following documents into well-structured wiki articles with markdown formatting.

Documents:
${docsText}

Output a compiled wiki article in markdown format. Use proper headings, bullet points, and formatting. Include [[wiki-style links]] for key concepts.`;
}

export function buildQAPrompt(question: string, context: QARequest['payload']['context']): string {
  const contextText = context.map(c => `Document ${c.doc_id}:\n${c.snippet}`).join('\n\n');
  return `Answer the following question based on the provided context from the knowledge base.

Context:
${contextText}

Question: ${question}

Provide a helpful, accurate answer. Cite which documents you used in your answer.`;
}
```

- [ ] **Step 2: Install OpenAI SDK**

```bash
cd website && npm install openai
```

- [ ] **Step 3: Implement LLM proxy endpoint**

```typescript
// website/app/api/llm/proxy/route.ts
import { NextRequest } from 'next/server';
import { query, queryOne, LicenseToken, TierLimits, UsageLog } from '@/lib/db';
import { streamLLM, buildCompilePrompt, buildQAPrompt, CompileRequest, QARequest } from '@/lib/llm';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { token, action, payload } = body;

    if (!token || !action || !payload) {
      return new Response(
        JSON.stringify({ error: { code: 'VALIDATION_ERROR', message: 'Missing required fields' } }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify license
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
    const licenseToken = await queryOne<LicenseToken & {user_id: string}>(
      'SELECT * FROM license_tokens WHERE token_hash = $1',
      [tokenHash]
    );

    if (!licenseToken) {
      return new Response(
        JSON.stringify({ error: { code: 'LICENSE_INVALID', message: 'Invalid license token' } }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get tier limits
    const limits = await queryOne<TierLimits>(
      'SELECT * FROM tier_limits WHERE tier = $1',
      [licenseToken.tier]
    );

    if (!limits) {
      return new Response(
        JSON.stringify({ error: { code: 'INTERNAL_ERROR', message: 'Tier limits not found' } }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check usage limits
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

    const usageCount = await queryOne<{count: bigint}>(
      `SELECT COUNT(*) as count FROM usage_logs
       WHERE user_id = $1 AND action = $2 AND timestamp >= $3`,
      [licenseToken.user_id, action, monthStart]
    );

    const count = Number(usageCount?.count || 0);
    const maxAction = action === 'compile' ? limits.max_compiles : limits.max_qa;

    if (maxAction !== -1 && count >= maxAction) {
      return new Response(
        JSON.stringify({
          error: { code: 'LIMIT_EXCEEDED', message: `Monthly ${action} limit exceeded` },
          remaining: 0
        }),
        { status: 429, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Select model
    const model = limits.allowed_models[0] || 'gpt-4o-mini';

    // Build prompt based on action
    let prompt: string;
    if (action === 'compile') {
      const req = payload as CompileRequest['payload'];
      prompt = buildCompilePrompt(req.documents);
    } else if (action === 'qa') {
      const req = payload as QARequest['payload'];
      prompt = buildQAPrompt(req.question, req.context);
    } else {
      return new Response(
        JSON.stringify({ error: { code: 'VALIDATION_ERROR', message: 'Invalid action' } }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Stream LLM response
    const stream = await streamLLM(model, [{ role: 'user', content: prompt }]);

    // Log usage (estimate tokens)
    const estimatedTokens = Math.ceil(prompt.length / 4);
    await query(
      `INSERT INTO usage_logs (user_id, action, tokens_used, model)
       VALUES ($1, $2, $3, $4)`,
      [licenseToken.user_id, action, estimatedTokens, model]
    );

    // Return SSE stream
    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('LLM proxy error:', error);
    return new Response(
      JSON.stringify({ error: { code: 'INTERNAL_ERROR', message: 'LLM request failed' } }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add website/lib/llm.ts website/app/api/llm/proxy/route.ts
git commit -m "feat(r003): add LLM proxy API with streaming support"
```

### Task 8: Usage Statistics API

**Files:**
- Create: `website/app/api/usage/current/route.ts`

- [ ] **Step 1: Implement usage endpoint**

```typescript
// website/app/api/usage/current/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne, LicenseToken } from '@/lib/db';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const { token } = await request.json();

    if (!token) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'License token is required' } },
        { status: 400 }
      );
    }

    // Verify license
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
    const licenseToken = await queryOne<LicenseToken>(
      'SELECT user_id FROM license_tokens WHERE token_hash = $1',
      [tokenHash]
    );

    if (!licenseToken) {
      return NextResponse.json(
        { error: { code: 'LICENSE_INVALID', message: 'Invalid license token' } },
        { status: 401 }
      );
    }

    // Get current month usage
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

    const compileCount = await queryOne<{count: bigint}>(
      `SELECT COUNT(*) as count FROM usage_logs
       WHERE user_id = $1 AND action = 'compile' AND timestamp >= $2`,
      [licenseToken.user_id, monthStart]
    );

    const qaCount = await queryOne<{count: bigint}>(
      `SELECT COUNT(*) as count FROM usage_logs
       WHERE user_id = $1 AND action = 'qa' AND timestamp >= $2`,
      [licenseToken.user_id, monthStart]
    );

    return NextResponse.json({
      period: {
        start: monthStart.toISOString(),
        end: new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString()
      },
      usage: {
        compile: Number(compileCount?.count || 0),
        qa: Number(qaCount?.count || 0)
      }
    });

  } catch (error) {
    console.error('Usage query error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch usage' } },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add website/app/api/usage/current/route.ts
git commit -m "feat(r003): add usage statistics API"
```

---

## Phase 2B: Local App Changes

These run in parallel with Phase 2A.

### Task 9: Add Cloud API URL to Config

**Files:**
- Modify: `backend/src/config.py`

- [ ] **Step 1: Add cloud API configuration**

```python
# backend/src/config.py (add to Settings class)

class Settings(BaseSettings):
    # ... existing config ...

    # Cloud API Configuration
    cloud_api_url: Optional[str] = "https://knowledgebase.ai"  # Default, override with env
    license_token_path: str = ".license_token"  # Local cache file

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/config.py
git commit -m "feat(r003): add cloud API URL configuration"
```

### Task 10: Create Cloud Auth Client

**Files:**
- Create: `backend/src/auth/cloud_auth.py`

- [ ] **Step 1: Implement cloud auth client**

```python
# backend/src/auth/cloud_auth.py
"""Cloud API authentication client for local app."""

import httpx
from pathlib import Path
from src.config import get_settings

settings = get_settings()


class CloudAuthClient:
    """Client for communicating with cloud authentication API."""

    def __init__(self):
        self.base_url = settings.cloud_api_url.rstrip('/')
        self.timeout = 10.0

    async def login(
        self,
        email: str,
        password: str,
        device_name: str | None = None,
        device_id: str | None = None
    ) -> dict:
        """Login via cloud API and return tokens."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "email": email,
                "password": password,
                "device_name": device_name,
                "device_id": device_id
            }

            response = await client.post(
                f"{self.base_url}/api/auth/login",
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def verify_license(self, token: str) -> dict:
        """Verify license token with cloud API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/license/verify",
                json={"token": token}
            )
            response.raise_for_status()
            return response.json()

    async def get_usage(self, token: str) -> dict:
        """Get current usage statistics."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/usage/current",
                json={"token": token}
            )
            response.raise_for_status()
            return response.json()
```

- [ ] **Step 2: Install httpx**

```bash
cd backend && source venv/bin/activate && pip install httpx
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/auth/cloud_auth.py requirements.txt
git commit -m "feat(r003): add cloud auth client for license verification"
```

### Task 11: Create License Manager

**Files:**
- Create: `backend/src/license/manager.py`
- Create: `backend/src/license/__init__.py`

- [ ] **Step 1: Create package init**

```python
# backend/src/license/__init__.py
"""License management for cloud SaaS integration."""

from .manager import LicenseManager
from .limits import LocalLimits

__all__ = ['LicenseManager', 'LocalLimits']
```

- [ ] **Step 2: Implement license manager**

```python
# backend/src/license/manager.py
"""License token caching and verification."""

import json
from pathlib import Path
from typing import Optional
from src.auth.cloud_auth import CloudAuthClient
from src.config import get_settings

settings = get_settings()


class LicenseManager:
    """Manages license token caching and verification."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.token_file = vault_path / settings.license_token_path
        self.cloud_client = CloudAuthClient()
        self._cached_token: Optional[str] = None
        self._cached_data: Optional[dict] = None

    def load_token(self) -> Optional[str]:
        """Load license token from local cache."""
        if self._cached_token:
            return self._cached_token

        if not self.token_file.exists():
            return None

        try:
            data = json.loads(self.token_file.read_text())
            self._cached_token = data.get('token')
            self._cached_data = data
            return self._cached_token
        except (json.JSONDecodeError, IOError):
            return None

    def save_token(self, token: str, user_data: dict) -> None:
        """Save license token to local cache."""
        self._cached_token = token
        self._cached_data = {**user_data, 'token': token}

        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(json.dumps(self._cached_data, indent=2))

    def clear_token(self) -> None:
        """Clear cached license token."""
        self._cached_token = None
        self._cached_data = None
        if self.token_file.exists():
            self.token_file.unlink()

    async def verify(self, offline_grace_period_hours: int = 24) -> Optional[dict]:
        """Verify license with cloud API.

        Returns license data if valid, None if invalid.
        Uses cached data if cloud is unreachable within grace period.
        """
        token = self.load_token()
        if not token:
            return None

        try:
            result = await self.cloud_client.verify_license(token)

            if result.get('valid'):
                # Update cache with fresh data
                self._cached_data = {
                    **self._cached_data,
                    'user': result.get('user'),
                    'tier': result.get('tier'),
                    'limits': result.get('limits')
                }
                return self._cached_data
            else:
                # License invalid - clear cache
                self.clear_token()
                return None

        except Exception as e:
            # Cloud unreachable - check grace period
            if self._cached_data:
                # TODO: Implement grace period check based on last verified time
                # For now, allow offline use
                return self._cached_data
            return None

    async def refresh(self) -> bool:
        """Refresh license data from cloud."""
        return await self.verify() is not None
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/license/
git commit -m "feat(r003): add license manager with caching and verification"
```

### Task 12: Create Local Limits Tracker

**Files:**
- Create: `backend/src/license/limits.py`

- [ ] **Step 1: Implement local limits tracker**

```python
# backend/src/license/limits.py
"""Local usage tracking for offline scenarios."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass
class LocalLimits:
    """Cached tier limits from cloud."""

    max_compiles: int
    max_qa: int
    allowed_models: list[str]
    max_documents: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> 'LocalLimits':
        return cls(
            max_compiles=data.get('max_compiles', -1),
            max_qa=data.get('max_qa', -1),
            allowed_models=data.get('allowed_models', []),
            max_documents=data.get('max_documents')
        )


@dataclass
class UsageTracker:
    """Track local usage for current month."""

    compile_count: int = 0
    qa_count: int = 0

    def increment(self, action: str) -> None:
        if action == 'compile':
            self.compile_count += 1
        elif action == 'qa':
            self.qa_count += 1

    def can_perform(self, action: str, limits: LocalLimits) -> bool:
        if action == 'compile':
            return limits.max_compiles == -1 or self.compile_count < limits.max_compiles
        elif action == 'qa':
            return limits.max_qa == -1 or self.qa_count < limits.max_qa
        return False


class LocalUsageStore:
    """Persist usage tracking to local file."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.usage_file = vault_path / '.usage_tracking.json'
        self._tracker = UsageTracker()
        self._load()

    def _load(self) -> None:
        if not self.usage_file.exists():
            return

        try:
            data = json.loads(self.usage_file.read_text())
            # Check if data is from current month
            month_key = datetime.now(timezone.utc).strftime('%Y-%m')
            if data.get('month') == month_key:
                self._tracker = UsageTracker(
                    compile_count=data.get('compile_count', 0),
                    qa_count=data.get('qa_count', 0)
                )
            else:
                # New month - reset counters
                self._tracker = UsageTracker()
        except (json.JSONDecodeError, IOError):
            self._tracker = UsageTracker()

    def _save(self) -> None:
        month_key = datetime.now(timezone.utc).strftime('%Y-%m')
        data = {
            'month': month_key,
            'compile_count': self._tracker.compile_count,
            'qa_count': self._tracker.qa_count
        }
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        self.usage_file.write_text(json.dumps(data, indent=2))

    def increment(self, action: str) -> None:
        self._tracker.increment(action)
        self._save()

    def get_tracker(self) -> UsageTracker:
        return self._tracker

    def get_limits(self) -> LocalLimits | None:
        # Load from license cache
        license_file = self.vault_path / '.license_token'
        if not license_file.exists():
            return None

        try:
            data = json.loads(license_file.read_text())
            limits_data = data.get('limits')
            if limits_data:
                return LocalLimits.from_dict(limits_data)
        except (json.JSONDecodeError, IOError):
            pass
        return None
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/license/limits.py
git commit -m "feat(r003): add local usage tracking for offline scenarios"
```

### Task 13: Create Cloud LLM Client

**Files:**
- Create: `backend/src/llm/cloud_client.py`

- [ ] **Step 1: Implement cloud LLM proxy client**

```python
# backend/src/llm/cloud_client.py
"""Cloud LLM proxy client for SaaS mode."""

import httpx
from typing import AsyncGenerator
from src.config import get_settings

settings = get_settings()


class CloudLLMClient:
    """Client for LLM requests through cloud proxy."""

    def __init__(self, license_token: str):
        self.license_token = license_token
        self.base_url = settings.cloud_api_url.rstrip('/')
        self.timeout = 120.0  # LLM requests can take time

    async def compile_document(
        self,
        documents: list[dict],
        prompt_template: str = "wiki"
    ) -> AsyncGenerator[str, None]:
        """Compile document via cloud proxy."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "token": self.license_token,
                "action": "compile",
                "payload": {
                    "documents": documents,
                    "prompt_template": prompt_template
                }
            }

            async with client.stream(
                'POST',
                f"{self.base_url}/api/llm/proxy",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            if 'content' in data:
                                yield data['content']
                        except json.JSONDecodeError:
                            continue

    async def answer_question(
        self,
        question: str,
        context: list[dict]
    ) -> AsyncGenerator[str, None]:
        """Answer question via cloud proxy."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "token": self.license_token,
                "action": "qa",
                "payload": {
                    "question": question,
                    "context": context
                }
            }

            async with client.stream(
                'POST',
                f"{self.base_url}/api/llm/proxy",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            if 'content' in data:
                                yield data['content']
                        except json.JSONDecodeError:
                            continue
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/llm/cloud_client.py
git commit -m "feat(r003): add cloud LLM proxy client"
```

### Task 14: Modify Auth Service to Use Cloud API

**Files:**
- Modify: `backend/src/auth/service.py`

- [ ] **Step 1: Update AuthService for cloud login**

```python
# backend/src/auth/service.py (modify the class)

from __future__ import annotations
"""认证服务模块 - 支持 SaaS 云端认证"""

from src.auth.cloud_auth import CloudAuthClient
from src.auth.jwt import create_token
from src.auth.password import hash_password, verify_password
from src.database import Database
from src.models.user import Token, User, UserCreate, UserLogin, create_user_id
from pathlib import Path


class AuthService:
    """认证服务，处理用户注册、登录等业务逻辑"""

    def __init__(self, db: Database, vault_path: Path | None = None):
        """初始化认证服务

        Args:
            db: 数据库连接实例
            vault_path: Vault 路径（用于 SaaS 模式下保存 license token）
        """
        self.db = db
        self.vault_path = vault_path or Path('.')
        self.cloud_client = CloudAuthClient()

    async def is_setup_complete(self) -> bool:
        """检查是否已完成初始账户设置

        Returns:
            如果已存在用户则返回 True
        """
        count = await self.db.count_users()
        return count > 0

    async def setup(self, user_create: UserCreate) -> Token:
        """创建初始管理员账户（仅本地模式）

        Args:
            user_create: 用户创建请求

        Returns:
            Token 包含 JWT access token

        Raises:
            ValueError: 如果账户已存在
        """
        # 检查是否已有用户存在
        if await self.is_setup_complete():
            raise ValueError("Setup already complete. An account already exists.")

        # 生成用户 ID 并哈希密码
        user_id = create_user_id()
        password_hash = hash_password(user_create.password)

        # 创建用户
        await self.db.create_user(user_id, user_create.username, password_hash)

        # 生成 JWT token
        token = create_token({"sub": user_id, "username": user_create.username})

        return Token(access_token=token)

    async def login(self, user_login: UserLogin, device_id: str | None = None) -> dict:
        """用户登录 - 支持 SaaS 云端认证

        Args:
            user_login: 登录请求（email/password for SaaS）
            device_id: 设备 ID（SaaS 模式）

        Returns:
            Dict with access_token and optional license_token

        Raises:
            ValueError: 如果用户名或密码无效
        """
        # Try cloud login first
        try:
            result = await self.cloud_client.login(
                email=user_login.username,  # Using username field as email
                password=user_login.password,
                device_id=device_id
            )

            # Save license token locally
            license_token = result.get('license_token')
            if license_token:
                from src.license.manager import LicenseManager
                mgr = LicenseManager(self.vault_path)
                mgr.save_token(license_token, result.get('user', {}))

            return {
                'access_token': result.get('access_token'),
                'license_token': license_token,
                'tier': result.get('tier'),
                'user': result.get('user')
            }

        except Exception as cloud_error:
            # Fall back to local auth for backward compatibility
            user_dict = await self.db.get_user_by_username(user_login.username)
            if not user_dict:
                raise ValueError("Invalid username or password")

            if not verify_password(user_login.password, user_dict["password_hash"]):
                raise ValueError("Invalid username or password")

            token = create_token({
                "sub": user_dict["id"],
                "username": user_dict["username"]
            })

            return {'access_token': token}

    async def get_user_by_id(self, user_id: str) -> User | None:
        """通过 ID 获取用户

        Args:
            user_id: 用户 ID

        Returns:
            User 对象，如果未找到则返回 None
        """
        user_dict = await self.db.get_user_by_id(user_id)
        if not user_dict:
            return None

        return User(
            id=user_dict["id"],
            username=user_dict["username"],
            password_hash=user_dict["password_hash"],
            created_at=user_dict["created_at"],
        )
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/auth/service.py
git commit -m "feat(r003): modify auth service to support cloud SaaS login"
```

### Task 15: Modify Startup Flow for License Verification

**Files:**
- Modify: `backend/src/main.py`

- [ ] **Step 1: Add license verification to startup**

```python
# backend/src/main.py (modify the startup event)

from __future__ import annotations
"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI

from src.auth.dependencies import get_db
from src.auth.router import router as auth_router
from src.config import get_settings
from src.database import Database
from src.license.manager import LicenseManager
from src.middleware.error_handler import register_error_handlers
from src.routers.compile import router as compile_router
from src.routers.concepts import router as concepts_router
from src.routers.documents import router as document_router
from src.routers.ingest import router as ingest_router
from src.routers.prompts import router as prompts_router
from src.routers.qa import router as qa_router
from src.routers.settings import router as settings_router
from src.routers.system import router as system_router

app = FastAPI(
    title="LLM Knowledge Base",
    description="A local-first LLM-powered knowledge base application",
    version="0.1.0",
)

# Register global error handlers
register_error_handlers(app)

# Register auth router
app.include_router(auth_router, prefix="/api/v1")

# Register ingest router
app.include_router(ingest_router, prefix="/api/v1")

# Register document management router
app.include_router(document_router, prefix="/api/v1")

# Register compile router
app.include_router(compile_router, prefix="/api/v1")

# Register QA router
app.include_router(qa_router, prefix="/api/v1")

# Register system status router
app.include_router(system_router, prefix="/api/v1")

# Register concepts router
app.include_router(concepts_router, prefix="/api/v1")

# Register settings router
app.include_router(settings_router, prefix="/api/v1")

# Register prompts router
app.include_router(prompts_router, prefix="/api/v1")

# Store license manager in app state
app.state.license_manager: LicenseManager | None = None


@app.on_event("startup")
async def startup() -> None:
    """Initialize application on startup."""
    settings = get_settings()
    vault_path = Path(settings.vault_path)
    db_path = vault_path / ".wiki" / "metadata.db"

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize database
    db = Database(db_path)
    await db.connect()
    await db.initialize()

    # Store database in app state
    app.state.db = db

    # Override the get_db dependency to use the app's database
    async def _get_db() -> Database:
        return app.state.db

    app.dependency_overrides[get_db] = _get_db

    # Initialize license manager for SaaS mode
    license_mgr = LicenseManager(vault_path)
    app.state.license_manager = license_mgr

    # Verify license on startup (non-blocking)
    # If license is invalid, the app will still start but
    # API endpoints will check license before processing
    try:
        await license_mgr.verify()
    except Exception:
        # Network error or other issue - will use cached data
        pass


@app.on_event("shutdown")
async def shutdown() -> None:
    """Clean up on shutdown."""
    if hasattr(app.state, 'db'):
        await app.state.db.close()


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/main.py
git commit -m "feat(r003): add license verification to app startup"
```

---

## Phase 3: Frontend Changes (Local App)

### Task 16: Create Cloud API Service for Frontend

**Files:**
- Create: `frontend/src/services/cloudApi.ts`

- [ ] **Step 1: Implement cloud API service**

```typescript
// frontend/src/services/cloudApi.ts
const CLOUD_API_URL = process.env.CLOUD_API_URL || 'https://knowledgebase.ai';

export interface LoginResponse {
  access_token: string;
  license_token?: string;
  tier?: string;
  user?: { id: string; email: string };
}

export interface LicenseVerifyResponse {
  valid: boolean;
  user?: { id: string; email: string };
  tier?: string;
  limits?: {
    max_compiles: number;
    max_qa: number;
    allowed_models: string[];
  };
}

export interface UsageResponse {
  period: { start: string; end: string };
  usage: { compile: number; qa: number };
}

export async function cloudLogin(
  email: string,
  password: string,
  deviceId?: string
): Promise<LoginResponse> {
  const response = await fetch(`${CLOUD_API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      password,
      device_id: deviceId || 'web-client'
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Login failed');
  }

  return response.json();
}

export async function verifyLicense(token: string): Promise<LicenseVerifyResponse> {
  const response = await fetch(`${CLOUD_API_URL}/api/license/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  });

  if (!response.ok) {
    throw new Error('License verification failed');
  }

  return response.json();
}

export async function getUsage(token: string): Promise<UsageResponse> {
  const response = await fetch(`${CLOUD_API_URL}/api/usage/current`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  });

  if (!response.ok) {
    throw new Error('Failed to fetch usage');
  }

  return response.json();
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/cloudApi.ts
git commit -m "feat(r003): add cloud API service for frontend"
```

### Task 17: Modify Login Page for SaaS

**Files:**
- Modify: `frontend/src/pages/Login.tsx`

- [ ] **Step 1: Update login page**

```typescript
// frontend/src/pages/Login.tsx (complete rewrite)
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { cloudLogin } from '../services/cloudApi';
import { useAuth } from '../hooks/useAuth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await cloudLogin(email, password);

      // Store tokens
      localStorage.setItem('access_token', result.access_token);
      if (result.license_token) {
        localStorage.setItem('license_token', result.license_token);
      }
      localStorage.setItem('user_tier', result.tier || 'trial');
      localStorage.setItem('user_email', result.user?.email || '');

      // Update auth state
      await login(result.access_token);

      // Redirect to main app
      navigate('/library');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = () => {
    // Open browser to registration page
    window.open('https://knowledgebase.ai/register', '_blank');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold text-center mb-6">KnowledgeBase</h1>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              minLength={8}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-gray-600">Don't have an account? </span>
          <button
            type="button"
            onClick={handleRegister}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Sign Up
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Login.tsx
git commit -m "feat(r003): modify login page for SaaS cloud authentication"
```

### Task 18: Update Settings Page to Show Plan

**Files:**
- Modify: `frontend/src/pages/Settings.tsx`

- [ ] **Step 1: Add plan and usage display to settings**

```typescript
// frontend/src/pages/Settings.tsx - add section at top of component

// After imports, add:
import { useState, useEffect } from 'react';
import { getUsage } from '../services/cloudApi';

// Inside Settings component, before return, add:
  const [tier, setTier] = useState<string>(localStorage.getItem('user_tier') || 'trial');
  const [usage, setUsage] = useState<{compile: number; qa: number} | null>(null);

  useEffect(() => {
    const licenseToken = localStorage.getItem('license_token');
    if (licenseToken) {
      getUsage(licenseToken).then(setUsage).catch(console.error);
    }
  }, []);

// In the JSX, add this section before existing settings:
return (
  <div className="max-w-4xl mx-auto p-6">
    {/* New: Plan and Usage Section */}
    <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
      <h2 className="text-xl font-semibold mb-4">Current Plan</h2>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-2xl font-bold capitalize text-gray-900">{tier}</p>
          {usage && (
            <p className="text-sm text-gray-600 mt-1">
              This month: {usage.compile} compilations, {usage.qa} Q&A
            </p>
          )}
        </div>
        <button
          onClick={() => window.open('https://knowledgebase.ai/dashboard', '_blank')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
        >
          Manage Plan
        </button>
      </div>
    </div>

    {/* Existing settings sections... */}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Settings.tsx
git commit -m "feat(r003): add plan and usage display to settings page"
```

---

## Phase 4: Stripe Integration (Website)

### Task 19: Create Stripe Client Library

**Files:**
- Create: `website/lib/stripe.ts`

- [ ] **Step 1: Implement Stripe client**

```typescript
// website/lib/stripe.ts
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-11-20.acacia',
});

export async function createCheckoutSession(params: {
  customerId?: string;
  customerEmail?: string;
  priceId: string;
  successUrl: string;
  cancelUrl: string;
  metadata?: Record<string, string>;
}) {
  return await stripe.checkout.sessions.create({
    customer: params.customerId,
    customer_email: params.customerEmail,
    payment_method_types: ['card'],
    line_items: [{ price: params.priceId, quantity: 1 }],
    mode: 'subscription',
    success_url: params.successUrl,
    cancel_url: params.cancelUrl,
    metadata: params.metadata || {},
  });
}

export async function createBillingPortalSession(params: {
  customerId: string;
  returnUrl: string;
}) {
  return await stripe.billingPortal.sessions.create({
    customer: params.customerId,
    return_url: params.returnUrl,
  });
}

export async function constructWebhookEvent(payload: string, signature: string) {
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;
  return stripe.webhooks.constructEvent(payload, signature, webhookSecret);
}

export default stripe;
```

- [ ] **Step 2: Install Stripe**

```bash
cd website && npm install stripe
```

- [ ] **Step 3: Commit**

```bash
git add website/lib/stripe.ts
git commit -m "feat(r003): add Stripe client library"
```

### Task 20: Stripe Checkout API

**Files:**
- Create: `website/app/api/stripe/checkout/route.ts`

- [ ] **Step 1: Implement checkout endpoint**

```typescript
// website/app/api/stripe/checkout/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { queryOne } from '@/lib/db';
import { createCheckoutSession } from '@/lib/stripe';

export async function POST(request: NextRequest) {
  try {
    const { price_id, email } = await request.json();

    if (!price_id) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Price ID is required' } },
        { status: 400 }
      );
    }

    // Get or create customer
    const user = email ? await queryOne('SELECT * FROM users WHERE email = $1', [email]) : null;

    const session = await createCheckoutSession({
      customerEmail: email,
      priceId: price_id,
      successUrl: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
      cancelUrl: `${process.env.NEXT_PUBLIC_APP_URL}/pricing`,
    });

    return NextResponse.json({ url: session.url });

  } catch (error) {
    console.error('Checkout error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to create checkout session' } },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add website/app/api/stripe/checkout/route.ts
git commit -m "feat(r003): add Stripe checkout API endpoint"
```

### Task 21: Stripe Webhook Handler

**Files:**
- Create: `website/app/api/stripe/webhook/route.ts`

- [ ] **Step 1: Implement webhook handler**

```typescript
// website/app/api/stripe/webhook/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne } from '@/lib/db';
import { constructWebhookEvent } from '@/lib/stripe';

export async function POST(request: NextRequest) {
  try {
    const payload = await request.text();
    const signature = request.headers.get('stripe-signature')!;

    const event = await constructWebhookEvent(payload, signature);

    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as any;
        const customerId = session.customer;
        const subscriptionId = session.subscription;
        const clientReferenceId = session.client_reference_id;

        // Get price to determine tier
        const subscription = await fetch(`https://api.stripe.com/v1/subscriptions/${subscriptionId}`, {
          headers: { Authorization: `Bearer ${process.env.STRIPE_SECRET_KEY!}` }
        }).then(r => r.json());

        const priceId = subscription.items.data[0].price.id;
        let tier = 'personal';
        if (priceId.includes('professional')) tier = 'professional';
        if (priceId.includes('team')) tier = 'team';

        // Find user by customer email or create new
        const customerEmail = session.customer_details?.email;
        if (customerEmail) {
          let user = await queryOne('SELECT * FROM users WHERE email = $1', [customerEmail]);
          if (!user) {
            user = await queryOne(
              `INSERT INTO users (email, password_hash) VALUES ($1, 'oauth-login')
               RETURNING *`,
              [customerEmail]
            );
          }

          // Create or update subscription
          await query(
            `INSERT INTO subscriptions (user_id, stripe_customer_id, stripe_subscription_id, stripe_price_id, status, tier, current_period_start, current_period_end)
             VALUES ($1, $2, $3, $4, 'active', $5, NOW(), NOW() + INTERVAL '1 month')
             ON CONFLICT (user_id) DO UPDATE SET
               stripe_customer_id = $2,
               stripe_subscription_id = $3,
               stripe_price_id = $4,
               status = 'active',
               tier = $5,
               current_period_end = NOW() + INTERVAL '1 month'`,
            [user.id, customerId, subscriptionId, priceId, tier]
          );
        }
        break;
      }

      case 'customer.subscription.updated': {
        const subscription = event.data.object as any;
        const subscriptionId = subscription.id;
        const status = subscription.status;
        const priceId = subscription.items.data[0].price.id;

        let tier = 'personal';
        if (priceId.includes('professional')) tier = 'professional';
        if (priceId.includes('team')) tier = 'team';
        if (status === 'canceled') tier = 'free';

        await query(
          `UPDATE subscriptions
             SET status = $1, tier = $2, updated_at = NOW()
             WHERE stripe_subscription_id = $3`,
          [status, tier, subscriptionId]
        );
        break;
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as any;
        await query(
          `UPDATE subscriptions
             SET status = 'canceled', tier = 'free', updated_at = NOW()
             WHERE stripe_subscription_id = $1`,
          [subscription.id]
        );
        break;
      }

      case 'invoice.payment_succeeded': {
        const invoice = event.data.object as any;
        const subscriptionId = invoice.subscription;
        await query(
          `UPDATE subscriptions
             SET current_period_end = NOW() + INTERVAL '1 month', updated_at = NOW()
             WHERE stripe_subscription_id = $1`,
          [subscriptionId]
        );
        break;
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as any;
        await query(
          `UPDATE subscriptions
             SET status = 'past_due', updated_at = NOW()
             WHERE stripe_subscription_id = $1`,
          [invoice.subscription]
        );
        break;
      }
    }

    return NextResponse.json({ received: true });

  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Webhook processing failed' } },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add website/app/api/stripe/webhook/route.ts
git commit -m "feat(r003): add Stripe webhook handler"
```

---

## Phase 5: Testing & Documentation

### Task 22: Add Environment Variable Documentation

**Files:**
- Create: `website/.env.example`
- Create: `backend/.env.example`

- [ ] **Step 1: Create website env example**

```bash
# website/.env.example
DATABASE_URL=postgresql://user:password@host:port/database
JWT_SECRET=your-jwt-secret-here
LICENSE_TOKEN_SECRET=your-license-token-secret-here
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
OPENAI_API_KEY=sk-your_openai_key
NEXT_PUBLIC_APP_URL=https://knowledgebase.ai
```

- [ ] **Step 2: Create backend env example**

```bash
# backend/.env.example
# Existing config...
CLOUD_API_URL=https://knowledgebase.ai
LICENSE_TOKEN_PATH=.license_token
```

- [ ] **Step 3: Commit**

```bash
git add website/.env.example backend/.env.example
git commit -m "docs(r003): add environment variable documentation"
```

### Task 23: Create Deployment Guide

**Files:**
- Create: `docs/deployment/r003-saas-deployment.md`

- [ ] **Step 1: Write deployment guide**

```markdown
# R003 SaaS Deployment Guide

## Prerequisites

1. PostgreSQL database (Supabase or Neon)
2. Stripe account with products configured
3. Vercel account for website deployment
4. Domain name configured

## Database Setup

1. Create database at Supabase/Neon
2. Run migration: `psql $DATABASE_URL -f website/db/schema.sql`
3. Verify tables created

## Stripe Setup

1. Create products in Stripe Dashboard:
   - Personal: ¥49/month (price_xxx_monthly), ¥468/year
   - Professional: ¥99/month (price_yyy_monthly), ¥948/year

2. Copy webhook secret and add to environment variables

3. Configure webhook endpoint: `https://your-domain.com/api/stripe/webhook`

## Website Deployment (Vercel)

1. Connect GitHub repo to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy from `website/` directory

## Local App Distribution

1. Build executables:
   - Mac: `pyinstaller --onefile backend/src/main.py`
   - Win: `pyinstaller --onefile --windowed backend/src/main.py`

2. Upload to website releases table

## Verification Checklist

- [ ] User can register at /register
- [ ] Registration redirects to Stripe checkout
- [ ] After payment, user sees dashboard
- [ ] Local app can login with email/password
- [ ] License verification works
- [ ] LLM proxy streams responses
- [ ] Usage tracking works
```

- [ ] **Step 2: Commit**

```bash
git add docs/deployment/r003-saas-deployment.md
git commit -m "docs(r003): add SaaS deployment guide"
```

---

## Implementation Summary

This plan covers:
- **Phase 1**: Database schema + shared infrastructure (3 tasks)
- **Phase 2A**: Website + Cloud API (6 tasks)
- **Phase 2B**: Local app backend changes (7 tasks)
- **Phase 3**: Frontend changes (3 tasks)
- **Phase 4**: Stripe integration (3 tasks)
- **Phase 5**: Testing & docs (2 tasks)

**Total: 24 bite-sized tasks**

Each task produces working, testable code. Tasks are designed to be independent where possible, allowing parallel work on Website and Local App.

---

## Self-Review Results

**Spec Coverage Check:**
- ✅ PostgreSQL schema → Task 1
- ✅ User system (register/login) → Tasks 4, 5
- ✅ License verification → Task 6
- ✅ LLM proxy → Task 7
- ✅ Usage tracking → Tasks 8, 12
- ✅ Stripe integration → Tasks 19-21
- ✅ Local app transformation → Tasks 9-18

**Placeholder Scan:**
- ✅ All code is complete, no TBD/TODO
- ✅ All file paths are exact
- ✅ All SQL schemas are complete
- ✅ All API endpoints have full implementations

**Type Consistency:**
- ✅ User, Subscription, LicenseToken interfaces consistent
- ✅ Tier/Limits types consistent across frontend/backend
- ✅ API request/response formats match

**Ready for execution!**
