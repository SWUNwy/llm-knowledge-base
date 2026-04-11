const API_BASE = '/api/v1';

// --- Error types ---

export class ApiError extends Error {
  code: string | null;
  status: number;

  constructor(message: string, code: string | null = null, status: number = 0) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

// --- Type definitions ---

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface UserInfo {
  id: string;
  username: string;
}

interface DocumentSummary {
  id: string;
  title: string;
  type: string;
  status: string;
  created_at: string;
  tags: string[];
}

interface DocumentListResponse {
  total: number;
  page: number;
  limit: number;
  items: DocumentSummary[];
}

interface IngestResponse {
  success: boolean;
  doc_id: string | null;
  title: string | null;
  path: string | null;
  error: string | null;
}

interface StatusResponse {
  status: string;
  setup_required?: boolean;
}

interface AskQuestionResponse {
  answer: string;
  sources?: Array<{ id: string; title: string; snippet: string }>;
}

interface QAHistoryResponse {
  total: number;
  page: number;
  limit: number;
  items: Array<{
    id: string;
    question: string;
    answer: string;
    sources: string[];
    created_at: string;
  }>;
}

interface ConceptSummary {
  id: string;
  name: string;
  mention_count: number;
  created_at: string;
}

interface ConceptListResponse {
  total: number;
  page: number;
  limit: number;
  items: ConceptSummary[];
}

interface ConceptDetail {
  id: string;
  name: string;
  wiki_path: string | null;
  mention_count: number;
  created_at: string;
  related_documents: Array<{ id: string; title: string }>;
}

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

class ApiService {
  private token: string | null = null;

  setToken(token: string | null): void {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...headers,
        ...(options?.headers as Record<string, string> | undefined),
      },
    });

    if (!response.ok) {
      let message = `Request failed with status ${response.status}`;
      let code: string | null = null;

      try {
        const body = await response.json();
        // New unified format: { error: { code, message } }
        if (body.error && typeof body.error === 'object') {
          code = body.error.code ?? null;
          message = body.error.message ?? message;
        } else if (body.detail) {
          // Legacy format fallback
          message = typeof body.detail === 'string'
            ? body.detail
            : JSON.stringify(body.detail);
        }
      } catch {
        // Response body is not JSON, use default message
      }

      throw new ApiError(message, code, response.status);
    }

    return response.json() as Promise<T>;
  }

  // --- Auth ---

  async setup(username: string, password: string): Promise<TokenResponse> {
    const result = await this.request<TokenResponse>('/auth/setup', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.token = result.access_token;
    return result;
  }

  async login(username: string, password: string): Promise<TokenResponse> {
    const result = await this.request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.token = result.access_token;
    return result;
  }

  // --- Documents ---

  async getDocuments(
    params?: { page?: number; limit?: number; search?: string },
  ): Promise<DocumentListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.search) searchParams.set('search', params.search);

    const query = searchParams.toString();
    const path = `/documents${query ? `?${query}` : ''}`;

    return this.request<DocumentListResponse>(path);
  }

  // --- Ingest ---

  async ingestUrl(url: string, tags?: string[]): Promise<IngestResponse> {
    return this.request<IngestResponse>('/ingest/url', {
      method: 'POST',
      body: JSON.stringify({ url, tags: tags ?? [] }),
    });
  }

  async ingestFile(path: string, tags?: string[]): Promise<IngestResponse> {
    return this.request<IngestResponse>('/ingest/file', {
      method: 'POST',
      body: JSON.stringify({ path, tags: tags ?? [] }),
    });
  }

  async ingestVideo(url: string, tags?: string[]): Promise<IngestResponse> {
    return this.request<IngestResponse>('/ingest/video', {
      method: 'POST',
      body: JSON.stringify({ url, tags: tags ?? [] }),
    });
  }

  async ingestGithub(repoUrl: string, tags?: string[]): Promise<IngestResponse> {
    return this.request<IngestResponse>('/ingest/github', {
      method: 'POST',
      body: JSON.stringify({ repo_url: repoUrl, tags: tags ?? [] }),
    });
  }

  // --- QA ---

  async askQuestion(
    question: string,
    stream?: boolean,
  ): Promise<AskQuestionResponse> {
    return this.request<AskQuestionResponse>('/qa/ask', {
      method: 'POST',
      body: JSON.stringify({ question, stream: stream ?? false }),
    });
  }

  async saveQA(question: string, answer: string, sources?: string[]): Promise<{ success: boolean; id: string }> {
    return this.request('/qa/save', {
      method: 'POST',
      body: JSON.stringify({ question, answer, sources: sources ?? [] }),
    });
  }

  async getQAHistory(page?: number, limit?: number): Promise<QAHistoryResponse> {
    const params = new URLSearchParams();
    if (page) params.set('page', String(page));
    if (limit) params.set('limit', String(limit));
    const query = params.toString();
    return this.request<QAHistoryResponse>(`/qa/history${query ? `?${query}` : ''}`);
  }

  // --- Concepts ---

  async getConcepts(page?: number, limit?: number): Promise<ConceptListResponse> {
    const params = new URLSearchParams();
    if (page) params.set('page', String(page));
    if (limit) params.set('limit', String(limit));
    const query = params.toString();
    return this.request<ConceptListResponse>(`/concepts${query ? `?${query}` : ''}`);
  }

  async getConcept(id: string): Promise<ConceptDetail> {
    return this.request<ConceptDetail>(`/concepts/${id}`);
  }

  // --- System ---

  async getStatus(): Promise<StatusResponse> {
    return this.request<StatusResponse>('/status');
  }

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
}

export const api = new ApiService();

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
