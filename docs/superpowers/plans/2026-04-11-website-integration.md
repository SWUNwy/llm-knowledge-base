# Website Integration Implementation Plan (R005)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Complete the website user journey: registration → login → Stripe checkout → dashboard, with navbar auth state and pricing CTA integration.

**Architecture:** Next.js App Router pages calling existing API routes. Auth state managed via JWT in localStorage, checked client-side. No new API routes needed — all backend code exists.

**Tech Stack:** Next.js 16, TypeScript, TailwindCSS 3, existing UI components (Button, Logo, ScrollReveal)

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `website/app/register/page.tsx` | Create | Registration form (email + password) |
| `website/app/login/page.tsx` | Modify | Replace placeholder with real login form |
| `website/app/dashboard/page.tsx` | Create | Plan status, usage, download links |
| `website/components/navbar.tsx` | Modify | Show auth state (logged in/out) |
| `website/components/pricing.tsx` | Modify | CTA buttons → register or stripe checkout |
| `website/components/cta.tsx` | Modify | CTA → register or dashboard |
| `website/lib/auth-client.ts` | Create | Client-side auth utilities (token storage, decode, fetch user) |

---

### Task 1: Create Client-Side Auth Utilities

**Files:**
- Create: `website/lib/auth-client.ts`

- [ ] **Step 1: Write auth-client.ts**

```typescript
// website/lib/auth-client.ts
// Client-side auth utilities for JWT token management

const TOKEN_KEY = 'kb_access_token';
const USER_KEY = 'kb_user';

export interface AuthUser {
  id: string;
  email: string;
  tier?: string;
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getUser(): AuthUser | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setUser(user: AuthUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

// Decode JWT payload without library (client-side only)
export function decodeJWTPayload(token: string): Record<string, unknown> | null {
  try {
    const base64 = token.split('.')[1];
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeJWTPayload(token);
  if (!payload?.exp) return true;
  return (payload.exp as number) * 1000 < Date.now();
}

// Get valid token or null (checks expiry)
export function getValidToken(): string | null {
  const token = getToken();
  if (!token || isTokenExpired(token)) {
    clearAuth();
    return null;
  }
  return token;
}
```

- [ ] **Step 2: Commit**

```bash
git add website/lib/auth-client.ts
git commit -m "feat(website): add client-side auth utilities

JWT token storage, decode, expiry check, user management for
client-side auth state."
```

---

### Task 2: Create Registration Page

**Files:**
- Create: `website/app/register/page.tsx`

- [ ] **Step 1: Write register page**

```tsx
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { setToken, setUser } from "@/lib/auth-client";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error?.message || "Registration failed");
        return;
      }

      setToken(data.access_token);
      setUser({ id: data.user.id, email: data.user.email, tier: "trial" });
      router.push("/dashboard");
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-dark flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-brand-blue to-brand-purple mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white">Create Account</h1>
          <p className="text-sm text-text-on-dark-muted mt-1">
            Start your 14-day free trial
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4"
        >
          {error && (
            <div className="p-3 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-text-on-dark-muted mb-1"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-text-on-dark-muted mb-1"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue"
              placeholder="Min. 8 characters"
            />
          </div>

          <div>
            <label
              htmlFor="confirmPassword"
              className="block text-sm font-medium text-text-on-dark-muted mb-1"
            >
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue"
              placeholder="Repeat password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-gradient-to-r from-brand-blue to-brand-purple text-white text-sm font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-text-on-dark-muted">
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-brand-blue hover:text-brand-blue-light font-medium"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add website/app/register/page.tsx
git commit -m "feat(website): add registration page

Email + password registration form. On success, stores JWT and
redirects to /dashboard."
```

---

### Task 3: Replace Login Placeholder with Real Form

**Files:**
- Modify: `website/app/login/page.tsx`

- [ ] **Step 1: Replace login page**

```tsx
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { setToken, setUser } from "@/lib/auth-client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, device_id: "web" }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error?.message || "Login failed");
        return;
      }

      setToken(data.access_token);
      setUser({
        id: data.user?.id || "",
        email: data.user?.email || email,
        tier: data.tier || "trial",
      });
      router.push("/dashboard");
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-dark flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-brand-blue to-brand-purple mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white">Welcome back</h1>
          <p className="text-sm text-text-on-dark-muted mt-1">
            Sign in to your account
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4"
        >
          {error && (
            <div className="p-3 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-text-on-dark-muted mb-1"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-text-on-dark-muted mb-1"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue"
              placeholder="Enter password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-gradient-to-r from-brand-blue to-brand-purple text-white text-sm font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-text-on-dark-muted">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="text-brand-blue hover:text-brand-blue-light font-medium"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add website/app/login/page.tsx
git commit -m "feat(website): replace login placeholder with real form

Real email+password login calling /api/auth/login. Stores JWT
and redirects to /dashboard on success."
```

---

### Task 4: Create Dashboard Page

**Files:**
- Create: `website/app/dashboard/page.tsx`

- [ ] **Step 1: Write dashboard page**

```tsx
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getToken, getUser, clearAuth, type AuthUser } from "@/lib/auth-client";

interface UsageData {
  period: { start: string; end: string };
  usage: { compile: number; qa: number };
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    const userData = getUser();

    if (!token || !userData) {
      router.push("/login");
      return;
    }

    setUser(userData);

    // Fetch usage
    fetch("/api/usage/current", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.usage) setUsage(data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [router]);

  const handleLogout = () => {
    clearAuth();
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-dark flex items-center justify-center">
        <p className="text-text-on-dark-muted">Loading...</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-surface-dark">
      {/* Header */}
      <div className="border-b border-white/10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-blue to-brand-purple" />
            <span className="text-lg font-bold text-white">KnowledgeBase</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-text-on-dark-muted">{user.email}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-text-on-dark-muted hover:text-white transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold text-white mb-8">Dashboard</h1>

        {/* Plan card */}
        <div className="bg-gradient-to-r from-brand-blue/20 to-brand-purple/20 border border-white/10 rounded-2xl p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-on-dark-muted mb-1">Current Plan</p>
              <p className="text-3xl font-bold text-white capitalize">
                {user.tier || "trial"}
              </p>
              {usage && (
                <p className="text-sm text-text-on-dark-muted mt-2">
                  This period: {usage.usage.compile} compilations,{" "}
                  {usage.usage.qa} Q&A queries
                </p>
              )}
            </div>
            <Link
              href="#pricing"
              className="px-5 py-2 bg-white/10 text-white text-sm font-medium rounded-lg hover:bg-white/20 transition-colors"
            >
              Manage Plan
            </Link>
          </div>
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-2">
              Download App
            </h3>
            <p className="text-sm text-text-on-dark-muted mb-4">
              Get the desktop app for macOS, Windows, or Linux.
            </p>
            <div className="flex gap-2">
              <a
                href="#"
                className="px-4 py-2 bg-white/10 text-white text-xs font-medium rounded-lg hover:bg-white/20 transition-colors"
              >
                macOS
              </a>
              <a
                href="#"
                className="px-4 py-2 bg-white/10 text-white text-xs font-medium rounded-lg hover:bg-white/20 transition-colors"
              >
                Windows
              </a>
              <a
                href="#"
                className="px-4 py-2 bg-white/10 text-white text-xs font-medium rounded-lg hover:bg-white/20 transition-colors"
              >
                Linux
              </a>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-2">
              License Token
            </h3>
            <p className="text-sm text-text-on-dark-muted mb-4">
              Use this token to activate the desktop app.
            </p>
            <button
              onClick={() => {
                const token = getToken();
                if (token) {
                  navigator.clipboard.writeText(token);
                  alert("License token copied to clipboard!");
                }
              }}
              className="px-4 py-2 bg-white/10 text-white text-xs font-medium rounded-lg hover:bg-white/20 transition-colors"
            >
              Copy License Token
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add website/app/dashboard/page.tsx
git commit -m "feat(website): add dashboard page

Shows plan status, usage stats, download links, and license token.
Redirects to /login if not authenticated."
```

---

### Task 5: Update Navbar with Auth State

**Files:**
- Modify: `website/components/navbar.tsx`

- [ ] **Step 1: Update Navbar to show auth state**

The key changes:
- Import `getValidToken`, `getUser` from `@/lib/auth-client`
- On mount, check if user is logged in
- If logged in: show email + "Dashboard" link instead of "免费试用" button
- If not logged in: keep existing "免费试用" button linking to /login

Replace the desktop auth button section (line 42-44):

```tsx
          <div className="hidden md:block">
            {loggedIn ? (
              <div className="flex items-center gap-3">
                <a
                  href="/dashboard"
                  className="text-sm text-text-on-dark-muted hover:text-white transition-colors"
                >
                  Dashboard
                </a>
                <span className="text-sm text-text-on-dark-muted">
                  {user?.email}
                </span>
              </div>
            ) : (
              <Button variant="primary" href="/login" className="text-[13px] px-5 py-2">
                免费试用
              </Button>
            )}
          </div>
```

Add state and effect at the top of the component:

```tsx
  const [loggedIn, setLoggedIn] = useState(false);
  const [user, setUser] = useState<{ email: string } | null>(null);

  useEffect(() => {
    const token = getValidToken();
    const userData = getUser();
    setLoggedIn(!!token);
    setUser(userData ? { email: userData.email } : null);
  }, []);
```

Add imports:
```tsx
import { getValidToken, getUser } from "@/lib/auth-client";
```

Also update the mobile menu auth button similarly.

- [ ] **Step 2: Commit**

```bash
git add website/components/navbar.tsx
git commit -m "feat(website): navbar shows auth state

Logged-in users see email + Dashboard link. Logged-out users
see '免费试用' button."
```

---

### Task 6: Update Pricing CTA Buttons

**Files:**
- Modify: `website/components/pricing.tsx`

- [ ] **Step 1: Make pricing buttons interactive**

Add client auth check and Stripe checkout integration.

Key changes:
- Import `useState, useEffect` (already imported)
- Import `getValidToken` from `@/lib/auth-client`
- Add state for logged in status
- On CTA button click:
  - If logged in: call `/api/stripe/checkout` with price_id → redirect to Stripe
  - If not logged in: redirect to `/register`

Replace the button (lines 101-105):

```tsx
                  <button
                    onClick={() => handleCheckout(tier)}
                    disabled={checkoutLoading === tier.name}
                    className={`w-full py-3 rounded-button text-center font-semibold cursor-pointer disabled:opacity-50 ${style.cta}`}
                  >
                    {checkoutLoading === tier.name ? "Processing..." : "开始免费试用"}
                  </button>
```

Add state and handler inside the component:

```tsx
  const [loggedIn, setLoggedIn] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);

  useEffect(() => {
    setLoggedIn(!!getValidToken());
  }, []);

  const handleCheckout = async (tier: { name: string }) => {
    if (!loggedIn) {
      window.location.href = "/register";
      return;
    }

    // Map tier name to Stripe price_id (env vars)
    const priceMap: Record<string, string> = {
      "个人版": process.env.NEXT_PUBLIC_STRIPE_PERSONAL_PRICE || "",
      "专业版": process.env.NEXT_PUBLIC_STRIPE_PRO_PRICE || "",
      "团队版": process.env.NEXT_PUBLIC_STRIPE_TEAM_PRICE || "",
    };

    const priceId = priceMap[tier.name];
    if (!priceId) {
      window.location.href = "/dashboard";
      return;
    }

    setCheckoutLoading(tier.name);
    try {
      const res = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ price_id: priceId }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch {
      // Fallback to dashboard
      window.location.href = "/dashboard";
    }
  };
```

Add import:
```tsx
import { getValidToken } from "@/lib/auth-client";
```

- [ ] **Step 2: Commit**

```bash
git add website/components/pricing.tsx
git commit -m "feat(website): pricing buttons route to register or Stripe

Logged-in users go directly to Stripe checkout. Logged-out users
are redirected to registration."
```

---

### Task 7: Update CTA Section

**Files:**
- Modify: `website/components/cta.tsx`

- [ ] **Step 1: Make CTA button auth-aware**

Replace the Button href (line 22):

Change from `href="/login"` to use a click handler:

```tsx
          <Button
            variant="primary"
            onClick={handleCtaClick}
            className="mb-6"
          >
            免费试用 14 天
          </Button>
```

Add at the top of the component:

```tsx
  const handleCtaClick = () => {
    if (getValidToken()) {
      window.location.href = "/dashboard";
    } else {
      window.location.href = "/register";
    }
  };
```

Add import:
```tsx
import { getValidToken } from "@/lib/auth-client";
```

- [ ] **Step 2: Commit**

```bash
git add website/components/cta.tsx
git commit -m "feat(website): CTA button routes to register or dashboard

Logged-in users go to dashboard, others go to registration."
```

---

### Task 8: Verify Website Build

- [ ] **Step 1: Run TypeScript check**

Run: `cd website && npx tsc --noEmit 2>&1 | head -30`

- [ ] **Step 2: Run build**

Run: `cd website && npm run build 2>&1 | tail -20`

- [ ] **Step 3: Run lint**

Run: `cd website && npm run lint 2>&1`

- [ ] **Step 4: Fix any issues and commit**

```bash
git add -A
git commit -m "fix(website): resolve build/lint issues from integration"
```
