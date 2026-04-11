# Frontend-Backend API Integration Spec

> Date: 2026-04-11
> Status: Draft
> Scope: R004 - Full frontend-backend API integration

## Goal

Connect all 7 frontend pages to their corresponding backend FastAPI endpoints, completing the end-to-end user journey: Login → Import → Compile → Chat.

## Current State

- **7 pages built**: Login, Setup, Import, Library, Chat, Settings, Concepts
- **API client exists**: `api.ts` wraps most endpoints but some pages use stubs
- **Cloud API exists**: `cloudApi.ts` for SaaS auth/license/usage
- **Key gaps**: Settings saves are simulated, Chat has no streaming, auth has two disjoint paths, compile has no frontend trigger

## Architecture Decisions

- **Auth**: Dual-mode (local username/password + cloud SaaS email/password), user selects at login
- **Streaming**: fetch + ReadableStream for SSE (not EventSource)
- **Compile trigger**: Embedded in Library page document cards
- **Approach**: Incremental — each step independently testable

---

## 1. Auth Unification (Dual-Mode)

### 1.1 Login Page Changes

Add a mode toggle at the top of the login form:

- **Local mode**: username + password fields → calls `api.login(username, password)` → stores JWT in localStorage under `llm_kb_token`
- **Cloud mode**: email + password fields → calls `cloudLogin(email, password)` → stores cloud access_token + license_token, then calls `api.setToken(access_token)` so subsequent API calls are authorized

Mode selection persisted in `localStorage('auth_mode')` — `'local' | 'cloud'`. On next visit, auto-select last used mode.

### 1.2 useAuth Hook Extension

```typescript
interface UseAuthReturn {
  user: UserInfo | null;
  loading: boolean;
  authMode: 'local' | 'cloud';
  login: (credentials: { username: string; password: string } | { email: string; password: string }) => Promise<void>;
  logout: () => void;
  setup: (username: string, password: string) => Promise<void>;
}
```

The `login()` method dispatches based on `authMode`:
- `'local'` → `api.login(username, password)`
- `'cloud'` → `cloudLogin(email, password)` then `api.setToken(access_token)`

### 1.3 ProtectedRoute Adjustment

- In local mode: check `/api/v1/status` for `setup_required`, redirect to `/setup` if true
- In cloud mode: skip setup check, only verify token exists

### 1.4 New API Methods

None — uses existing `api.login()`, `api.setup()`, and `cloudLogin()`.

---

## 2. Settings Real API

### 2.1 Current Mismatch

Frontend sends: `{ provider, model, api_key }`
Backend expects: `{ llm_default_model, openai_api_key, anthropic_api_key, gemini_api_key, ollama_base_url }`

### 2.2 Mapping

| Frontend Field | Backend Field |
|---|---|
| provider + model | `llm_default_model` in "provider/model" format (e.g., "openai/gpt-4o", "anthropic/claude-sonnet-4-20250514") |
| provider=openai, api_key | `openai_api_key` |
| provider=anthropic, api_key | `anthropic_api_key` |
| provider=google, api_key | `gemini_api_key` |
| provider=local | `ollama_base_url` (user enters URL instead of key) |

### 2.3 New API Methods in api.ts

```typescript
async getSettings(): Promise<SettingsResponse>    // GET /settings
async saveSettings(config: UpdateSettingsRequest): Promise<SettingsResponse>  // PUT /settings
async verifyLLM(request: VerifyLLMRequest): Promise<VerifyLLMResult>  // POST /settings/verify-llm
```

### 2.4 Settings Page Changes

- On mount: call `api.getSettings()`, populate form fields from response
  - Parse `llm_default_model` to extract provider and model
  - Show masked keys from `llm_providers` dict
- Save: build `UpdateSettingsRequest` from form, call `api.saveSettings()`
- Test Connection: call `api.verifyLLM({ model, api_key })` — display `success`, `message`, `latency_ms`
- SaaS plan/usage section: keep as-is (already uses `cloudApi.getUsage()`)

### 2.5 Backend Response Shapes

```typescript
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

interface VerifyLLMResult {
  success: boolean;
  message: string;
  latency_ms?: number;
}
```

---

## 3. Chat SSE Streaming

### 3.1 Backend SSE Format

The backend sends SSE events with `data: {"chunk": "token text"}\n\n` format. On error: `data: {"error": {"code": "...", "message": "..."}}`.

### 3.2 New API Method in api.ts

```typescript
async askQuestionStream(question: string, topK?: number): Promise<ReadableStreamDefaultReader<Uint8Array>>
```

Implementation:
- `fetch('/api/v1/qa/ask', { method: 'POST', body: { question, stream: true, top_k: topK ?? 5 }, headers: { Authorization: 'Bearer ...', 'Content-Type': 'application/json' } })`
- Return `response.body.getReader()`

### 3.3 Chat Page Changes

Replace `useMutation` with manual stream handling:

```
1. User submits question → add user message to state
2. Add empty assistant message to state
3. Call api.askQuestionStream(question)
4. Read chunks via reader loop:
   - Decode Uint8Array via TextDecoder
   - Parse SSE lines (split on \n\n, extract data: prefix)
   - JSON.parse each data payload
   - If { chunk }: append to assistant message content
   - If { error }: show error, stop reading
5. On reader done: finalize message, extract sources if present in final event
```

Keep `askQuestion()` (non-streaming) for potential future use (export, history replay).

### 3.4 Sources Handling

The backend `QAResponse` includes `sources: [{ id, title, relevance }]` and `related_concepts: [str]`. For streaming mode, sources are sent as a final SSE event:
- `data: {"sources": [...], "related_concepts": [...]}\n\n`

Parse this final event and attach to the assistant message.

---

## 4. Library Compile Button

### 4.1 New API Methods in api.ts

```typescript
async compileDocuments(docIds: string[], outputLanguage?: string): Promise<CompileResponse>
async getCompileTaskStatus(taskId: string): Promise<TaskStatusResponse>
async listCompileTasks(): Promise<TaskListResponse>
```

### 4.2 Backend Response Shapes

```typescript
interface CompileResponse {
  task_id?: string;
  total: number;
  completed: number;
  failed: number;
  results?: CompileSingleResult[];
  status: string;  // 'pending' | 'completed'
}

interface CompileSingleResult {
  success: boolean;
  doc_id: string;
  wiki_path?: string;
  title?: string;
  error?: string;
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

### 4.3 Library Page Changes

- Each document card gets a compile action button:
  - Visible when `status === 'pending'` or `status === 'failed'`
  - Hidden when `status === 'processed'` (show checkmark instead)
  - New status `compiling` shown with spinner during active compilation
- Click handler:
  1. Update local doc status to `compiling`
  2. Call `api.compileDocuments([docId])`
  3. For sync results (<=5 docs): update status immediately from `results[0].success`
  4. For async (task_id returned): poll `api.getCompileTaskStatus(taskId)` every 2s until `status === 'completed'`
- Batch compile: Add a "Compile All Pending" button in the page header that compiles all docs with `status === 'pending'`

### 4.4 Document Status Refresh

After compile completes, invalidate the documents query cache via React Query's `queryClient.invalidateQueries({ queryKey: ['documents'] })` to refresh the library list.

---

## 5. End-to-End Flow Polish

### 5.1 Import → Library Navigation

After successful import, show a "View in Library" link/button that navigates to `/library`.

### 5.2 QA History in Chat

Add a collapsible sidebar panel to the Chat page:
- Loads `api.getQAHistory(page, limit)` on mount
- Shows list of past Q&A pairs (truncated question + timestamp)
- Clicking a history item populates the input but doesn't resend
- Separate from the main message stream

### 5.3 Vite Dev Proxy

Ensure `frontend/vite.config.ts` has a proxy to the backend:
```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

---

## 6. Implementation Order

1. **Vite proxy config** — enables all subsequent API calls
2. **Auth unification** — unblocks all authenticated endpoints
3. **Settings real API** — LLM configuration needed for compile + chat
4. **Library compile button** — completes the import → compile flow
5. **Chat SSE streaming** — completes the compile → chat flow
6. **QA history + Import navigation** — polish items

## Files Modified

| File | Changes |
|---|---|
| `frontend/vite.config.ts` | Add API proxy |
| `frontend/src/services/api.ts` | Add getSettings, saveSettings, verifyLLM, askQuestionStream, compileDocuments, getCompileTaskStatus, listCompileTasks |
| `frontend/src/hooks/useAuth.ts` | Add authMode, dual login dispatch |
| `frontend/src/pages/Login.tsx` | Mode toggle, conditional fields |
| `frontend/src/pages/Settings.tsx` | Real API calls, form mapping |
| `frontend/src/pages/Library.tsx` | Compile buttons, status polling |
| `frontend/src/pages/Chat.tsx` | SSE streaming, history panel |
| `frontend/src/pages/Import.tsx` | "View in Library" link |

## Out of Scope

- New page creation (e.g., standalone Compile page)
- E2E test framework setup (separate spec)
- Docker/deployment configuration (separate spec)
- Website ↔ app integration (separate spec)
- Error handling redesign (use existing ErrorAlert component)
