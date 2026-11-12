function resolveApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const paramBase = new URLSearchParams(window.location.search).get('apiBase');
    if (paramBase && /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(paramBase)) {
      return paramBase.replace(/\/+$/, '');
    }
  }
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
}

export const API_BASE_URL = resolveApiBaseUrl();

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
}

function buildUrl(path: string, params?: RequestOptions['params']): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${API_BASE_URL}${normalized}`);
  if (params) {
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined) {
        url.searchParams.set(key, String(val));
      }
    });
  }
  return url.toString();
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, params, headers, ...rest } = options;
  const url = buildUrl(path, params);

  const response = await fetch(url, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(headers ?? {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text().catch(() => null);
    }
    throw new ApiError(
      response.status,
      `API request failed (${response.status}): ${response.statusText}`,
      detail
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'offline';
  version: string;
  uptime_seconds: number;
  database: string;
  ai_providers: Record<string, boolean>;
  cpu_percent: number;
  memory_percent: number;
}

export interface AgentDto {
  id: string;
  number: number;
  name: string;
  role: string;
  category: string;
  enabled: boolean;
  status: 'active' | 'idle' | 'running' | 'error' | 'disabled';
  tasks_completed: number;
  success_rate: number;
  last_run?: string;
}

export interface GoalDto {
  id: string;
  title: string;
  description: string;
  progress: number;
  target_value: number;
  current_value: number;
  unit: string;
  status: 'on_track' | 'at_risk' | 'completed' | 'paused';
  deadline: string;
}

export interface ContentAssetDto {
  id: string;
  title: string;
  type: 'video' | 'image' | 'carousel' | 'post' | 'audio';
  status: 'draft' | 'ready' | 'scheduled' | 'published';
  platform: string;
  scheduled_at?: string;
  created_at: string;
}

export interface WorkflowDto {
  id: string;
  name: string;
  description: string;
  active: boolean;
  nodes: unknown[];
  edges: unknown[];
  last_run?: string;
}

export const apiClient = {
  health: {
    check: () => apiRequest<HealthResponse>('/api/health'),
    diagnostics: () => apiRequest<Record<string, unknown>>('/api/health/diagnostics'),
  },
  agents: {
    list: () => apiRequest<AgentDto[]>('/api/agents'),
    toggle: (id: string, enabled: boolean) =>
      apiRequest<AgentDto>(`/api/agents/${id}`, {
        method: 'PATCH',
        body: { enabled },
      }),
    run: (id: string, payload?: Record<string, unknown>) =>
      apiRequest<Record<string, unknown>>(`/api/agents/${id}/run`, {
        method: 'POST',
        body: payload ?? {},
      }),
  },
  goals: {
    list: () => apiRequest<GoalDto[]>('/api/goals'),
    create: (payload: Partial<GoalDto>) =>
      apiRequest<GoalDto>('/api/goals', { method: 'POST', body: payload }),
    update: (id: string, payload: Partial<GoalDto>) =>
      apiRequest<GoalDto>(`/api/goals/${id}`, { method: 'PATCH', body: payload }),
  },
  content: {
    list: () => apiRequest<ContentAssetDto[]>('/api/content'),
    scanFolder: (path: string) =>
      apiRequest<{ scanned: number }>('/api/content/scan', {
        method: 'POST',
        body: { path },
      }),
  },
  workflows: {
    list: () => apiRequest<WorkflowDto[]>('/api/workflows'),
    save: (workflow: Partial<WorkflowDto>) =>
      apiRequest<WorkflowDto>('/api/workflows', {
        method: 'POST',
        body: workflow,
      }),
    execute: (id: string) =>
      apiRequest<{ execution_id: string }>(`/api/workflows/${id}/execute`, {
        method: 'POST',
      }),
  },
  analytics: {
    summary: (range = '7d') =>
      apiRequest<Record<string, unknown>>('/api/analytics/summary', {
        params: { range },
      }),
  },
  security: {
    status: () => apiRequest<Record<string, unknown>>('/api/security/status'),
    emergencyStop: () =>
      apiRequest<{ stopped: boolean }>('/api/security/emergency-stop', {
        method: 'POST',
      }),
  },
  settings: {
    get: () => apiRequest<Record<string, unknown>>('/api/settings'),
    update: (payload: Record<string, unknown>) =>
      apiRequest<Record<string, unknown>>('/api/settings', {
        method: 'PUT',
        body: payload,
      }),
  },
};
