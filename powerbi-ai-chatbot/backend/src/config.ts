/**
 * Centralized configuration. All values come from environment variables so
 * that secrets never live in source control (NFR §3, Phase 12).
 *
 * Non-secret values (tenant/client IDs, endpoints, URLs) are safe to set as
 * plain App Service application settings. Secret values (API keys, client
 * secrets) should be sourced from Key Vault references where possible.
 */

function env(name: string, fallback?: string): string {
  const value = process.env[name];
  if (value === undefined || value === '') {
    if (fallback !== undefined) return fallback;
    return '';
  }
  return value;
}

function boolEnv(name: string, fallback: boolean): boolean {
  const value = process.env[name];
  if (value === undefined || value === '') return fallback;
  return value.toLowerCase() === 'true' || value === '1';
}

function intEnv(name: string, fallback: number): number {
  const value = process.env[name];
  if (value === undefined || value === '') return fallback;
  const parsed = parseInt(value, 10);
  return Number.isNaN(parsed) ? fallback : parsed;
}

export interface AppConfig {
  env: string;
  port: number;
  /**
   * When true, external dependencies (Azure OpenAI, Power BI, Entra ID token
   * validation) run against in-process mock adapters so the full pipeline is
   * runnable locally without any secrets. Never enable in production.
   */
  mockMode: boolean;

  /** Comma-separated list of allowed frontend origins (CORS, Phase 11). */
  allowedOrigins: string[];

  entra: {
    tenantId: string;
    /** Audience the backend accepts (its own API app ID / client ID). */
    audience: string;
    issuer: string;
    jwksUri: string;
  };

  azureOpenAI: {
    endpoint: string;
    deployment: string;
    apiVersion: string;
    /** Only used when a key-based auth method is selected; prefer managed identity. */
    apiKey: string;
  };

  powerBI: {
    /** Default workspace used by the model registry when none is specified. */
    workspaceId: string;
    apiBaseUrl: string;
  };

  limits: {
    /** Max rows any single query may return. */
    maxRows: number;
    /** Query execution timeout in milliseconds. */
    queryTimeoutMs: number;
    /** Max chat requests per user per minute. */
    chatRateLimitPerMinute: number;
    /** Max request body size. */
    maxRequestBodyBytes: number;
  };
}

export function loadConfig(): AppConfig {
  const mockMode = boolEnv('MOCK_MODE', env('NODE_ENV', 'development') !== 'production');
  const tenantId = env('ENTRA_TENANT_ID');

  return {
    env: env('NODE_ENV', 'development'),
    port: intEnv('PORT', 8080),
    mockMode,
    allowedOrigins: env('ALLOWED_ORIGINS', 'http://localhost:5173')
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
    entra: {
      tenantId,
      audience: env('ENTRA_API_AUDIENCE'),
      issuer: env('ENTRA_ISSUER', tenantId ? `https://login.microsoftonline.com/${tenantId}/v2.0` : ''),
      jwksUri: env(
        'ENTRA_JWKS_URI',
        tenantId ? `https://login.microsoftonline.com/${tenantId}/discovery/v2.0/keys` : '',
      ),
    },
    azureOpenAI: {
      endpoint: env('AZURE_OPENAI_ENDPOINT'),
      deployment: env('AZURE_OPENAI_DEPLOYMENT_NAME'),
      apiVersion: env('AZURE_OPENAI_API_VERSION', '2024-06-01'),
      apiKey: env('AZURE_OPENAI_API_KEY'),
    },
    powerBI: {
      workspaceId: env('POWERBI_WORKSPACE_ID'),
      apiBaseUrl: env('POWERBI_API_BASE_URL', 'https://api.powerbi.com/v1.0/myorg'),
    },
    limits: {
      maxRows: intEnv('MAX_ROWS', 1000),
      queryTimeoutMs: intEnv('QUERY_TIMEOUT_MS', 30000),
      chatRateLimitPerMinute: intEnv('CHAT_RATE_LIMIT_PER_MINUTE', 30),
      maxRequestBodyBytes: intEnv('MAX_REQUEST_BODY_BYTES', 64 * 1024),
    },
  };
}

let cached: AppConfig | undefined;

export function getConfig(): AppConfig {
  if (!cached) cached = loadConfig();
  return cached;
}

/** For tests: reset the cached config so env changes take effect. */
export function resetConfigForTests(): void {
  cached = undefined;
}
