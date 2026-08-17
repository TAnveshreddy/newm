import { ChatResponse, ModelSummary, UserProfile } from '../models/types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * A function that returns a fresh backend access token. Supplied by the auth
 * layer so the API service never depends on MSAL directly. The frontend always
 * calls the backend — never Azure OpenAI or Power BI directly (NFR §3).
 */
export type TokenProvider = () => Promise<string>;

export class ApiClient {
  constructor(private readonly getToken: TokenProvider) {}

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const token = await this.getToken();
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...(init.headers ?? {}),
      },
    });

    if (!res.ok) {
      let message = `Request failed (${res.status})`;
      try {
        const body = await res.json();
        if (body?.message) message = body.message;
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(res.status, message);
    }
    return (await res.json()) as T;
  }

  getProfile(): Promise<UserProfile> {
    return this.request<UserProfile>('/me');
  }

  listModels(): Promise<{ models: ModelSummary[] }> {
    return this.request<{ models: ModelSummary[] }>('/models');
  }

  chat(modelId: string, prompt: string, conversationId?: string): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ modelId, prompt, conversationId }),
    });
  }
}
