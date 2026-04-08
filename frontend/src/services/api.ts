const API_BASE = '/api/v1';

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

      try {
        const body = await response.json();
        if (body.detail) {
          message = typeof body.detail === 'string'
            ? body.detail
            : JSON.stringify(body.detail);
        }
      } catch {
        // Response body is not JSON, use default message
      }

      throw new Error(message);
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

  // --- System ---

  async getStatus(): Promise<StatusResponse> {
    return this.request<StatusResponse>('/status');
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
};
