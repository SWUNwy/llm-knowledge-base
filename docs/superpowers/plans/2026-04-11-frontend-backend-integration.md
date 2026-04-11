# Frontend-Backend API Integration (R004) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect all 7 frontend pages to their backend FastAPI endpoints, completing the end-to-end user journey.

**Architecture:** Incremental integration — add API methods to `api.ts` first, then update each page to use real calls instead of stubs. Auth supports dual-mode (local + cloud). Chat uses fetch+ReadableStream for SSE streaming. Compile is embedded in Library cards.

**Tech Stack:** React 19, TypeScript, TanStack React Query, Vite, TailwindCSS 4, FastAPI backend

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `frontend/src/services/api.ts` | Modify | Add Settings, Compile, SSE streaming API methods + types |
| `frontend/src/hooks/useAuth.ts` | Modify | Add authMode state, dual login dispatch |
| `frontend/src/pages/Login.tsx` | Modify | Mode toggle (local/cloud), conditional fields |
| `frontend/src/pages/Settings.tsx` | Modify | Real API calls replacing stubs, form↔backend mapping |
| `frontend/src/pages/Library.tsx` | Modify | Compile buttons per card, batch compile, status polling |
| `frontend/src/pages/Chat.tsx` | Modify | SSE streaming via fetch+ReadableStream, QA history sidebar |
| `frontend/src/pages/Import.tsx` | Modify | "View in Library" link after successful import |
| `frontend/src/components/ProtectedRoute.tsx` | Modify | Skip setup check in cloud mode |

No new files needed — all changes modify existing files.

---

### Task 1: Add API Types and Settings Methods to api.ts

**Files:**
- Modify: `frontend/src/services/api.ts` (full file)

This task adds all new types and API methods needed by subsequent tasks. The types mirror the backend Pydantic models exactly.

- [ ] **Step 1: Add new type definitions after the existing types (around line 98)**

Insert after `ConceptDetail` interface, before `class ApiService`:

```typescript
// --- Settings types ---

interface SettingsResponse {
  llm_default_model: string;
  auto_compile: boolean;
  compile_batch_size: number;
  max_concurrent_tasks: number;
  llm_providers: Record<string, { configured: boolean; key?: string; base_url?: string }>;
}

interface UpdateSettingsRequest {
  llm_default_model?: string;
  auto_compile?: boolean;
  compile_batch_size?: number;
  max_concurrent_tasks?: number;
  gemini_api_key?: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
  ollama_base_url?: string;
}

interface VerifyLLMRequest {
  model?: string;
  api_key?: string;
  base_url?: string;
}

interface VerifyLLMResult {
  success: boolean;
  message: string;
  latency_ms?: number;
}

// --- Compile types ---

interface CompileSingleResult {
  success: boolean;
  doc_id: string;
  wiki_path?: string;
  title?: string;
  error?: string;
}

interface CompileResponse {
  task_id?: string;
  total: number;
  completed: number;
  failed: number;
  results?: CompileSingleResult[];
  status: string;
}

interface TaskStatusResponse {
  id: string;
  status: string;
  total_docs: number;
  completed_docs: number;
  failed_docs: number;
  result?: string;
  created_at?: string;
  completed_at?: string;
}
```

- [ ] **Step 2: Add Settings API methods inside `class ApiService` after `getStatus()` method (around line 266)**

Insert before the closing `}` of the class:

```typescript
  // --- Settings ---

  async getSettings(): Promise<SettingsResponse> {
    return this.request<SettingsResponse>('/settings');
  }

  async saveSettings(config: UpdateSettingsRequest): Promise<SettingsResponse> {
    return this.request<SettingsResponse>('/settings', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async verifyLLM(request: VerifyLLMRequest): Promise<VerifyLLMResult> {
    return this.request<VerifyLLMResult>('/settings/verify-llm', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // --- Compile ---

  async compileDocuments(docIds: string[], outputLanguage?: string): Promise<CompileResponse> {
    return this.request<CompileResponse>('/compile', {
      method: 'POST',
      body: JSON.stringify({
        doc_ids: docIds,
        output_language: outputLanguage ?? '中文',
      }),
    });
  }

  async getCompileTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    return this.request<TaskStatusResponse>(`/compile/tasks/${taskId}`);
  }

  async listCompileTasks(): Promise<{ tasks: TaskStatusResponse[] }> {
    return this.request<{ tasks: TaskStatusResponse[] }>('/compile/tasks');
  }

  // --- QA Streaming ---

  async askQuestionStream(
    question: string,
    topK?: number,
  ): Promise<ReadableStreamDefaultReader<Uint8Array>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}/qa/ask`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        question,
        stream: true,
        top_k: topK ?? 5,
      }),
    });

    if (!response.ok) {
      let message = `Request failed with status ${response.status}`;
      try {
        const body = await response.json();
        if (body.error && typeof body.error === 'object') {
          message = body.error.message ?? message;
        } else if (body.detail) {
          message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
        }
      } catch { /* use default message */ }
      throw new ApiError(message, null, response.status);
    }

    if (!response.body) {
      throw new ApiError('Streaming not supported', null, 0);
    }

    return response.body.getReader();
  }
```

- [ ] **Step 3: Update the export block at the bottom of the file**

Replace the existing `export type` block with an expanded one that includes all new types:

```typescript
export type {
  TokenResponse,
  UserInfo,
  DocumentSummary,
  DocumentListResponse,
  IngestResponse,
  StatusResponse,
  AskQuestionResponse,
  QAHistoryResponse,
  ConceptSummary,
  ConceptListResponse,
  ConceptDetail,
  SettingsResponse,
  UpdateSettingsRequest,
  VerifyLLMRequest,
  VerifyLLMResult,
  CompileSingleResult,
  CompileResponse,
  TaskStatusResponse,
};
```

- [ ] **Step 4: Verify the file compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No errors (or only pre-existing errors unrelated to this file)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat(api): add Settings, Compile, and SSE streaming API methods

Adds types and methods for: getSettings, saveSettings, verifyLLM,
compileDocuments, getCompileTaskStatus, listCompileTasks, askQuestionStream."
```

---

### Task 2: Extend useAuth Hook for Dual-Mode Auth

**Files:**
- Modify: `frontend/src/hooks/useAuth.ts` (full file)

- [ ] **Step 1: Replace the entire file with the dual-mode version**

```typescript
import { useCallback, useEffect, useState } from 'react';

import { api } from '../services/api';
import { cloudLogin } from '../services/cloudApi';

import type { UserInfo } from '../services/api';

const TOKEN_KEY = 'llm_kb_token';
const USER_KEY = 'llm_kb_user';
const AUTH_MODE_KEY = 'auth_mode';

export type AuthMode = 'local' | 'cloud';

interface AuthState {
  user: UserInfo | null;
  loading: boolean;
  authMode: AuthMode;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    authMode: (localStorage.getItem(AUTH_MODE_KEY) as AuthMode) || 'local',
  });

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);

    if (storedToken && storedUser) {
      api.setToken(storedToken);

      try {
        const parsedUser: UserInfo = JSON.parse(storedUser);
        setState({ user: parsedUser, loading: false, authMode: state.authMode });
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        api.setToken(null);
        setState({ user: null, loading: false, authMode: state.authMode });
      }
    } else {
      setState((prev) => ({ ...prev, loading: false }));
    }
  }, []);

  const setAuthMode = useCallback((mode: AuthMode) => {
    localStorage.setItem(AUTH_MODE_KEY, mode);
    setState((prev) => ({ ...prev, authMode: mode }));
  }, []);

  const login = useCallback(
    async (credentials: { username: string; password: string } | { email: string; password: string }) => {
      if (state.authMode === 'cloud') {
        const { email, password } = credentials as { email: string; password: string };
        const result = await cloudLogin(email, password);

        localStorage.setItem('access_token', result.access_token);
        if (result.license_token) {
          localStorage.setItem('license_token', result.license_token);
        }
        localStorage.setItem('user_tier', result.tier || 'trial');
        localStorage.setItem('user_email', result.user?.email || '');

        api.setToken(result.access_token);

        const user: UserInfo = { id: result.user?.id || '', username: result.user?.email || email };
        localStorage.setItem(TOKEN_KEY, result.access_token);
        localStorage.setItem(USER_KEY, JSON.stringify(user));

        setState({ user, loading: false, authMode: 'cloud' });
      } else {
        const { username, password } = credentials as { username: string; password: string };
        const tokenResponse = await api.login(username, password);

        const user: UserInfo = { id: '', username };
        localStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
        localStorage.setItem(USER_KEY, JSON.stringify(user));

        setState({ user, loading: false, authMode: 'local' });
      }
    },
    [state.authMode],
  );

  const setup = useCallback(async (username: string, password: string) => {
    const tokenResponse = await api.setup(username, password);
    const user: UserInfo = { id: '', username };

    api.setToken(tokenResponse.access_token);
    localStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    setState({ user, loading: false, authMode: 'local' });
  }, []);

  const logout = useCallback(() => {
    api.setToken(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem('access_token');
    localStorage.removeItem('license_token');
    localStorage.removeItem('user_tier');
    localStorage.removeItem('user_email');

    setState({ user: null, loading: false, authMode: state.authMode });
  }, [state.authMode]);

  return {
    user: state.user,
    loading: state.loading,
    authMode: state.authMode,
    setAuthMode,
    login,
    logout,
    setup,
  };
}
```

- [ ] **Step 2: Verify the file compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useAuth.ts
git commit -m "feat(auth): add dual-mode auth (local + cloud) to useAuth hook

Login now dispatches to api.login() or cloudLogin() based on authMode.
Mode persisted in localStorage. Logout clears all tokens."
```

---

### Task 3: Update Login Page with Mode Toggle

**Files:**
- Modify: `frontend/src/pages/Login.tsx` (full file)

- [ ] **Step 1: Replace Login.tsx with dual-mode version**

```tsx
import { useState, type FormEvent } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth, type AuthMode } from '../hooks/useAuth';
import { Brain } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

export default function Login() {
  const { user, authMode, setAuthMode, login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) {
    return <Navigate to="/library" replace />;
  }

  const handleModeSwitch = (mode: AuthMode) => {
    setAuthMode(mode);
    setError('');
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (authMode === 'cloud') {
        await login({ email, password });
      } else {
        await login({ username, password });
      }
      navigate('/library');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = () => {
    window.open('https://knowledgebase.ai/register', '_blank');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Brain className="w-10 h-10 text-blue-600 mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-gray-900">KnowledgeBase</h1>
          <p className="text-gray-500 mt-1">Sign in to continue</p>
        </div>

        {/* Mode toggle */}
        <div className="flex mb-4 bg-gray-100 rounded-lg p-1">
          <button
            type="button"
            onClick={() => handleModeSwitch('local')}
            className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${
              authMode === 'local'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Local
          </button>
          <button
            type="button"
            onClick={() => handleModeSwitch('cloud')}
            className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${
              authMode === 'cloud'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Cloud
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4"
        >
          {error && <ErrorAlert error={new Error(error)} variant="inline" />}

          {authMode === 'cloud' ? (
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          ) : (
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          )}

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={authMode === 'cloud' ? 8 : 1}
              autoComplete="current-password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {authMode === 'cloud' && (
          <div className="mt-4 text-center text-sm">
            <span className="text-gray-600">Don't have an account? </span>
            <button
              type="button"
              onClick={handleRegister}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Sign Up
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Login.tsx
git commit -m "feat(login): add local/cloud mode toggle to login page

Users can switch between local auth (username) and cloud SaaS auth (email).
Mode is persisted and restored on next visit."
```

---

### Task 4: Update ProtectedRoute for Dual-Mode Auth

**Files:**
- Modify: `frontend/src/components/ProtectedRoute.tsx` (full file)

- [ ] **Step 1: Replace ProtectedRoute.tsx**

The current version only checks if user exists. We need to handle the setup check for local mode.

```tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
```

Note: The logic is the same as current — the setup redirect is handled by the Setup page itself (via checking `/api/v1/status`). The ProtectedRoute just needs to check authentication. No functional change needed here, but we keep it clean.

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ProtectedRoute.tsx
git commit -m "refactor(auth): clean up ProtectedRoute for dual-mode auth

No functional change — setup check remains handled by the status endpoint."
```

---

### Task 5: Update Settings Page with Real API Calls

**Files:**
- Modify: `frontend/src/pages/Settings.tsx` (full file)

This replaces the simulated save with real backend calls and maps between frontend form fields and backend API fields.

- [ ] **Step 1: Replace Settings.tsx with real API version**

```tsx
import { useState, useEffect, type FormEvent } from 'react';
import { api, type SettingsResponse } from '../services/api';
import { getUsage } from '../services/cloudApi';
import { Save, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

const PROVIDER_MODEL_MAP: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-sonnet-4-20250514', 'claude-haiku-4-20250414', 'claude-3-5-sonnet-20241022'],
  google: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
  local: ['llama3', 'mistral', 'codellama'],
};

function parseModelString(model: string): { provider: string; model: string } {
  const parts = model.split('/');
  if (parts.length >= 2) {
    const provider = parts[0];
    const modelName = parts.slice(1).join('/');
    if (provider in PROVIDER_MODEL_MAP) {
      return { provider, model: modelName };
    }
  }
  return { provider: 'openai', model };
}

export default function Settings() {
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-4o');
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [loadError, setLoadError] = useState<string | null>(null);

  const [tier, setTier] = useState<string>(localStorage.getItem('user_tier') || 'trial');
  const [usage, setUsage] = useState<{ compile: number; qa: number } | null>(null);

  // Load current settings from backend
  useEffect(() => {
    api.getSettings()
      .then((data: SettingsResponse) => {
        const parsed = parseModelString(data.llm_default_model);
        setProvider(parsed.provider);
        setModel(parsed.model);

        // Show masked key if provider is configured
        const providerConfig = data.llm_providers[parsed.provider === 'google' ? 'gemini' : parsed.provider];
        if (providerConfig?.key) {
          setApiKey(providerConfig.key);
        }
      })
      .catch((err) => {
        setLoadError(err instanceof Error ? err.message : 'Failed to load settings');
      });
  }, []);

  // Load cloud usage if applicable
  useEffect(() => {
    const licenseToken = localStorage.getItem('license_token');
    if (licenseToken) {
      getUsage(licenseToken).then(setUsage).catch(console.error);
    }
  }, []);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaveStatus('saving');

    try {
      await api.saveSettings({
        llm_default_model: `${provider}/${model}`,
        ...(provider === 'openai' && apiKey ? { openai_api_key: apiKey } : {}),
        ...(provider === 'anthropic' && apiKey ? { anthropic_api_key: apiKey } : {}),
        ...(provider === 'google' && apiKey ? { gemini_api_key: apiKey } : {}),
        ...(provider === 'local' && apiKey ? { ollama_base_url: apiKey } : {}),
      });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch {
      setSaveStatus('idle');
    }
  };

  const handleTestConnection = async () => {
    setTestStatus('testing');
    setTestMessage('');

    try {
      const result = await api.verifyLLM({
        model: `${provider}/${model}`,
        ...(provider !== 'local' && apiKey ? { api_key: apiKey } : {}),
        ...(provider === 'local' && apiKey ? { base_url: apiKey } : {}),
      });

      if (result.success) {
        setTestStatus('success');
        setTestMessage(`${result.message}${result.latency_ms ? ` (${result.latency_ms}ms)` : ''}`);
      } else {
        setTestStatus('error');
        setTestMessage(result.message);
      }
    } catch (err) {
      setTestStatus('error');
      setTestMessage(err instanceof Error ? err.message : 'Connection failed');
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      {/* Plan and Usage Section */}
      <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200">
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

      {loadError && <ErrorAlert error={new Error(loadError)} variant="inline" />}

      <form
        onSubmit={handleSave}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5"
      >
        {/* Provider */}
        <div>
          <label htmlFor="provider" className="block text-sm font-medium text-gray-700 mb-1">
            LLM Provider
          </label>
          <select
            id="provider"
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value);
              setModel(PROVIDER_MODEL_MAP[e.target.value]?.[0] ?? '');
              setApiKey('');
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
            <option value="local">Local (Ollama)</option>
          </select>
        </div>

        {/* Model */}
        <div>
          <label htmlFor="model" className="block text-sm font-medium text-gray-700 mb-1">
            Model
          </label>
          <select
            id="model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {PROVIDER_MODEL_MAP[provider]?.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        {/* API Key / Base URL */}
        <div>
          <label htmlFor="api-key" className="block text-sm font-medium text-gray-700 mb-1">
            {provider === 'local' ? 'Base URL' : 'API Key'}
          </label>
          <div className="relative">
            <input
              id="api-key"
              type={showApiKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={provider === 'local' ? 'http://localhost:11434' : 'sk-...'}
              className="w-full px-3 py-2 pr-16 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-700 px-2 py-1"
            >
              {showApiKey ? 'Hide' : 'Show'}
            </button>
          </div>
          {provider === 'local' && (
            <p className="text-xs text-gray-400 mt-1">
              No API key needed for local models
            </p>
          )}
        </div>

        {/* Test connection */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={testStatus === 'testing'}
            className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {testStatus === 'testing' && <Loader2 className="w-4 h-4 animate-spin" />}
            Test Connection
          </button>
          {testStatus === 'success' && (
            <span className="flex items-center gap-1 text-sm text-green-600">
              <CheckCircle className="w-4 h-4" />
              {testMessage}
            </span>
          )}
          {testStatus === 'error' && (
            <ErrorAlert error={new Error(testMessage)} variant="inline" />
          )}
        </div>

        <hr className="border-gray-200" />

        {/* Save */}
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saveStatus === 'saving'}
            className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {saveStatus === 'saving' ? 'Saving...' : 'Save Settings'}
          </button>
          {saveStatus === 'saved' && (
            <span className="flex items-center gap-1 text-sm text-green-600">
              <CheckCircle className="w-4 h-4" />
              Settings saved
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
```

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Settings.tsx
git commit -m "feat(settings): replace stub with real backend API calls

Settings now loads from GET /settings on mount, saves via PUT /settings,
and tests connection via POST /settings/verify-llm. Maps provider/model
form fields to backend's llm_default_model format."
```

---

### Task 6: Add Compile Buttons to Library Page

**Files:**
- Modify: `frontend/src/pages/Library.tsx` (full file)

Adds compile action buttons to each document card and a batch "Compile All Pending" button.

- [ ] **Step 1: Replace Library.tsx with compile-enabled version**

```tsx
import { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api, type DocumentSummary } from '../services/api';
import { Search, FileText, BookOpen, Video, Code, Filter, Play, CheckCircle, XCircle, Loader2, PlayCircle } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

const typeIcons: Record<string, typeof FileText> = {
  web: FileText,
  paper: BookOpen,
  video: Video,
  code: Code,
};

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  compiling: 'bg-blue-100 text-blue-800',
  processed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

export default function Library() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [compilingIds, setCompilingIds] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents', { search, page }],
    queryFn: () => api.getDocuments({ search: search || undefined, page, limit: 20 }),
  });

  const filteredItems = data?.items?.filter((doc: DocumentSummary) => {
    if (typeFilter && doc.type !== typeFilter) return false;
    if (statusFilter && doc.status !== statusFilter) return false;
    return true;
  });

  const pollCompileStatus = useCallback(
    async (taskId: string) => {
      const poll = async (): Promise<void> => {
        const status = await api.getCompileTaskStatus(taskId);
        if (status.status === 'completed' || status.status === 'failed') {
          queryClient.invalidateQueries({ queryKey: ['documents'] });
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 2000));
        return poll();
      };
      return poll();
    },
    [queryClient],
  );

  const handleCompile = useCallback(
    async (docId: string) => {
      setCompilingIds((prev) => new Set(prev).add(docId));
      try {
        const result = await api.compileDocuments([docId]);
        if (result.task_id) {
          await pollCompileStatus(result.task_id);
        } else {
          queryClient.invalidateQueries({ queryKey: ['documents'] });
        }
      } catch (err) {
        console.error('Compile failed:', err);
        queryClient.invalidateQueries({ queryKey: ['documents'] });
      } finally {
        setCompilingIds((prev) => {
          const next = new Set(prev);
          next.delete(docId);
          return next;
        });
      }
    },
    [pollCompileStatus, queryClient],
  );

  const handleCompileAll = useCallback(async () => {
    if (!filteredItems) return;
    const pendingDocs = filteredItems.filter(
      (doc: DocumentSummary) => doc.status === 'pending' || doc.status === 'failed',
    );
    if (pendingDocs.length === 0) return;

    const ids = pendingDocs.map((d: DocumentSummary) => d.id);
    setCompilingIds(new Set(ids));

    try {
      const result = await api.compileDocuments(ids);
      if (result.task_id) {
        await pollCompileStatus(result.task_id);
      } else {
        queryClient.invalidateQueries({ queryKey: ['documents'] });
      }
    } catch (err) {
      console.error('Batch compile failed:', err);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    } finally {
      setCompilingIds(new Set());
    }
  }, [filteredItems, pollCompileStatus, queryClient]);

  const pendingCount = filteredItems?.filter(
    (doc: DocumentSummary) => doc.status === 'pending' || doc.status === 'failed',
  ).length ?? 0;

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Library</h1>
        {pendingCount > 0 && (
          <button
            onClick={handleCompileAll}
            disabled={compilingIds.size > 0}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <PlayCircle className="w-4 h-4" />
            Compile All ({pendingCount})
          </button>
        )}
      </div>

      {/* Search and filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search documents..."
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="pl-9 pr-8 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none"
          >
            <option value="">All Types</option>
            <option value="web">Web</option>
            <option value="paper">Paper</option>
            <option value="video">Video</option>
            <option value="code">Code</option>
          </select>
        </div>

        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="pl-9 pr-8 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="compiling">Compiling</option>
            <option value="processed">Processed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {isLoading && (
        <div className="text-center py-12 text-gray-500">Loading documents...</div>
      )}

      {error && <ErrorAlert error={error} variant="card" onRetry={() => queryClient.invalidateQueries({ queryKey: ['documents'] })} />}

      {data && (
        <>
          <p className="text-sm text-gray-500 mb-3">
            {data.total} document{data.total !== 1 ? 's' : ''} total
          </p>

          {filteredItems && filteredItems.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No documents found</div>
          ) : (
            <div className="space-y-2">
              {filteredItems?.map((doc: DocumentSummary) => {
                const Icon = typeIcons[doc.type] ?? FileText;
                const isCompiling = compilingIds.has(doc.id);
                const canCompile = doc.status === 'pending' || doc.status === 'failed';
                const isProcessed = doc.status === 'processed';

                return (
                  <div
                    key={doc.id}
                    className="flex items-center gap-4 bg-white rounded-lg border border-gray-200 px-4 py-3 hover:border-gray-300 transition-colors"
                  >
                    <Icon className="w-5 h-5 text-gray-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{doc.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        {doc.tags.map((tag) => (
                          <span key={tag} className="inline-block text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Compile action */}
                    <div className="shrink-0">
                      {isCompiling ? (
                        <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                      ) : isProcessed ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : canCompile ? (
                        <button
                          onClick={() => handleCompile(doc.id)}
                          title="Compile document"
                          className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                        >
                          <Play className="w-5 h-5" />
                        </button>
                      ) : doc.status === 'failed' ? (
                        <XCircle className="w-5 h-5 text-red-500" />
                      ) : null}
                    </div>

                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[doc.status] ?? 'bg-gray-100 text-gray-600'}`}>
                      {doc.status}
                    </span>
                    <span className="text-xs text-gray-400 whitespace-nowrap">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {data.total > data.limit && (
            <div className="flex items-center justify-center gap-4 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500">Page {page}</span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * data.limit >= data.total}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Library.tsx
git commit -m "feat(library): add compile buttons and batch compile

Each document card shows compile action (pending/failed), checkmark
(processed), or spinner (compiling). 'Compile All Pending' button in
header. Polls async task status every 2s."
```

---

### Task 7: Add SSE Streaming to Chat Page

**Files:**
- Modify: `frontend/src/pages/Chat.tsx` (full file)

This replaces the `useMutation` approach with manual SSE stream handling via `fetch` + `ReadableStream`.

- [ ] **Step 1: Replace Chat.tsx with SSE streaming version**

```tsx
import { useState, useRef, useEffect, useCallback, type FormEvent } from 'react';
import { api, type AskQuestionResponse } from '../services/api';
import { Send, Bot, User, ExternalLink, Loader2 } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  sources?: AskQuestionResponse['sources'];
  error?: unknown;
}

export default function Chat() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const streamAnswer = useCallback(async (questionText: string, assistantId: string) => {
    setIsStreaming(true);
    const decoder = new TextDecoder();

    try {
      const reader = await api.askQuestionStream(questionText);
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          for (const line of part.split('\n')) {
            if (!line.startsWith('data: ')) continue;
            const jsonStr = line.slice(6);
            try {
              const data = JSON.parse(jsonStr);

              if (data.error) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, role: 'error', error: new Error(data.error.message || 'Stream error') }
                      : m,
                  ),
                );
                return;
              }

              if (data.chunk) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: m.content + data.chunk }
                      : m,
                  ),
                );
              }

              if (data.sources) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, sources: data.sources }
                      : m,
                  ),
                );
              }
            } catch {
              // Incomplete JSON, skip
            }
          }
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, role: 'error', error: err instanceof Error ? err : new Error('Stream failed') }
            : m,
        ),
      );
    } finally {
      setIsStreaming(false);
    }
  }, []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isStreaming) return;

    const userMsgId = crypto.randomUUID();
    const assistantMsgId = crypto.randomUUID();

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: trimmed },
      { id: assistantMsgId, role: 'assistant', content: '' },
    ]);
    setQuestion('');
    streamAnswer(trimmed, assistantMsgId);
  };

  const handleRetry = (msgId: string) => {
    const idx = messages.findIndex((m) => m.id === msgId);
    if (idx < 0) return;
    const lastUserMsg = [...messages.slice(0, idx)].reverse().find((m) => m.role === 'user');
    if (!lastUserMsg) return;

    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev.filter((m) => m.id !== msgId),
      { id: assistantId, role: 'assistant', content: '' },
    ]);
    streamAnswer(lastUserMsg.content, assistantId);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-8 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Ask questions about your knowledge base
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <Bot className="w-12 h-12 mx-auto mb-3" />
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm">Ask a question to get started</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'error' ? (
              <ErrorAlert
                error={msg.error instanceof Error ? msg.error : null}
                variant="card"
                onRetry={() => handleRetry(msg.id)}
              />
            ) : (
              <>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-blue-600" />
                  </div>
                )}
                <div
                  className={`max-w-[70%] rounded-xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">
                    {msg.content}
                    {msg.role === 'assistant' && isStreaming && msg.content === '' && (
                      <Loader2 className="w-4 h-4 inline-block animate-spin text-gray-400" />
                    )}
                    {msg.role === 'assistant' && isStreaming && msg.content !== '' && (
                      <span className="inline-block w-1.5 h-4 bg-gray-400 animate-pulse align-text-bottom" />
                    )}
                  </p>

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                      <p className="text-xs font-medium text-gray-500">Sources:</p>
                      {msg.sources.map((source) => (
                        <div key={source.id} className="text-xs text-gray-600">
                          <div className="flex items-center gap-1 font-medium">
                            <ExternalLink className="w-3 h-3" />
                            {source.title}
                          </div>
                          <p className="mt-0.5 line-clamp-2">{source.snippet}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                )}
              </>
            )}
          </div>
        ))}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="px-8 py-4 border-t border-gray-200 bg-white"
      >
        <div className="flex gap-3 max-w-3xl mx-auto">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question..."
            disabled={isStreaming}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isStreaming || !question.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
```

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Chat.tsx
git commit -m "feat(chat): add SSE streaming via fetch + ReadableStream

Replaces useMutation with manual stream handling. Shows typing
animation during streaming, cursor blink, and error recovery."
```

---

### Task 8: Add QA History Sidebar to Chat Page

**Files:**
- Modify: `frontend/src/pages/Chat.tsx` (add history sidebar)

This adds a collapsible history panel to the Chat page. It builds on the streaming version from Task 7.

- [ ] **Step 1: Update Chat.tsx to add history sidebar**

Add these imports at the top (merge with existing imports):

```typescript
import { useQuery } from '@tanstack/react-query';
import { History, ChevronLeft, ChevronRight } from 'lucide-react';
```

Add after the existing interfaces, before `export default function Chat()`:

```typescript
interface QAHistoryItem {
  id: string;
  question: string;
  answer: string;
  created_at: string;
}
```

Inside the component, add these state variables after `const abortRef = ...`:

```typescript
const [showHistory, setShowHistory] = useState(false);

const { data: historyData } = useQuery({
  queryKey: ['qa-history'],
  queryFn: () => api.getQAHistory(1, 50),
  enabled: showHistory,
});
```

Add this sidebar section right after the `<div className="flex flex-col h-full">` opening tag, before the Header div:

```tsx
        {/* History sidebar */}
        {showHistory && (
          <div className="w-72 border-r border-gray-200 bg-white overflow-y-auto shrink-0">
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-900">History</h2>
              <button
                onClick={() => setShowHistory(false)}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <div className="divide-y divide-gray-100">
              {historyData?.items.map((item: QAHistoryItem) => (
                <button
                  key={item.id}
                  onClick={() => setQuestion(item.question)}
                  className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors"
                >
                  <p className="text-sm text-gray-900 font-medium truncate">
                    {item.question}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </button>
              ))}
              {historyData?.items.length === 0 && (
                <p className="text-sm text-gray-400 px-4 py-6 text-center">
                  No history yet
                </p>
              )}
            </div>
          </div>
        )}
```

Add a history toggle button inside the Header div, after the `<p>` subtitle:

```tsx
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="text-gray-400 hover:text-gray-600 mt-1"
              title="Toggle history"
            >
              <History className="w-4 h-4" />
            </button>
```

Wrap the header text and history button in a flex row so they sit side by side:

The full header section should look like:

```tsx
      {/* Header */}
      <div className="px-8 py-4 border-b border-gray-200 bg-white flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Ask questions about your knowledge base
          </p>
        </div>
        <button
          onClick={() => setShowHistory(!showHistory)}
          className={`p-2 rounded-lg transition-colors ${showHistory ? 'bg-blue-50 text-blue-600' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'}`}
          title="Toggle history"
        >
          <History className="w-5 h-5" />
        </button>
      </div>
```

Also change the outer container from `flex flex-col h-full` to `flex h-full` to accommodate the sidebar + main content side by side, and wrap the header/messages/input in a `flex flex-col flex-1` div.

The full structure becomes:

```tsx
  return (
    <div className="flex h-full">
      {/* History sidebar */}
      {showHistory && (
        <div className="w-72 border-r border-gray-200 bg-white overflow-y-auto shrink-0">
          {/* ... sidebar content ... */}
        </div>
      )}

      {/* Main chat area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        {/* Messages */}
        {/* Input */}
      </div>
    </div>
  );
```

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Chat.tsx
git commit -m "feat(chat): add collapsible QA history sidebar

Shows past Q&A pairs loaded from /qa/history. Clicking a history
item populates the input field."
```

---

### Task 9: Add "View in Library" Link to Import Page

**Files:**
- Modify: `frontend/src/pages/Import.tsx`

- [ ] **Step 1: Add import to `Import.tsx`**

Add `Link` to the import from `react-router-dom`:

```typescript
import { Link } from 'react-router-dom';
```

- [ ] **Step 2: Add "View in Library" link after the Recent Imports header**

Find this section in Import.tsx (around line 193):

```tsx
      {recentImports.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Imports</h2>
```

Replace with:

```tsx
      {recentImports.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">Recent Imports</h2>
            <Link
              to="/library"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View in Library &rarr;
            </Link>
          </div>
```

- [ ] **Step 3: Verify compilation**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Import.tsx
git commit -m "feat(import): add 'View in Library' link after imports

Shows a link to the Library page in the recent imports section."
```

---

### Task 10: Final Verification and Build

**Files:**
- None (verification only)

- [ ] **Step 1: Run full TypeScript check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 2: Run production build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors

- [ ] **Step 3: Run lint check**

Run: `cd frontend && npm run lint`
Expected: No new lint errors (fix any that appear)

- [ ] **Step 4: Final commit with all changes if any lint fixes were needed**

```bash
git add -A
git commit -m "chore: fix lint issues from frontend-backend integration"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Section 1 (Auth Unification): Tasks 2, 3, 4
- [x] Section 2 (Settings Real API): Task 5
- [x] Section 3 (Chat SSE Streaming): Tasks 7, 8
- [x] Section 4 (Library Compile Button): Task 6
- [x] Section 5 (E2E Polish - Import navigation): Task 9
- [x] Section 5 (E2E Polish - QA History): Task 8
- [x] Section 5 (Vite proxy): Already configured, no task needed

**Placeholder scan:** No TBD, TODO, or placeholder steps found.

**Type consistency:** All types defined in Task 1 (`api.ts`) are used consistently across Tasks 5-8. `AuthMode` type exported from `useAuth.ts` in Task 2 is imported in Tasks 3 and 4. Method names (`compileDocuments`, `getCompileTaskStatus`, `getSettings`, `saveSettings`, `verifyLLM`, `askQuestionStream`, `getQAHistory`) are consistent between definition and usage.
