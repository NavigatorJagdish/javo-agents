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
let ownerToken = '';
export function setOwnerToken(token: string): void { ownerToken = token; }

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
      ...(ownerToken ? { Authorization: `Bearer ${ownerToken}` } : {}),
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
  agent_key: string;
  name: string;
  description: string | null;
  category: string | null;
  version: string;
  is_enabled: boolean;
  status: 'idle' | 'running' | 'paused' | 'error' | 'disabled';
  supported_actions: string[];
}

export interface AgentExecutionDto {
  id: string;
  agent_id: string;
  task_id: string | null;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout';
  inputs: Record<string, unknown> | null;
  outputs: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
}

export interface GoalObjective {
  metric: string;
  unit: string;
  baseline: number;
  baseline_source: string;
  target: number;
  constraints: string;
  stopping_conditions: string;
  uncertainty: string;
}

export interface GoalMeasurement {
  value: number;
  source: string;
  observed_at: string;
}

export interface MilestoneDto {
  id: string;
  goal_id: string;
  title: string;
  target_value: number;
  current_value: number;
  is_completed: boolean;
  due_date: string | null;
}

export interface GoalDto {
  goal_id: string;
  title: string;
  description: string | null;
  owner_id: string;
  target_metrics: Record<string, unknown> | null;
  objective: GoalObjective | null;
  measurement: GoalMeasurement | null;
  progress: number;
  progress_basis: 'measurement' | 'milestones' | 'legacy_manual' | 'unmeasured';
  total_milestones: number;
  completed_milestones: number;
  status: 'active' | 'paused' | 'completed' | 'cancelled';
  deadline: string | null;
  created_at: string;
  updated_at: string;
}

export interface GoalCreateDto {
  title: string;
  description?: string | null;
  objective?: GoalObjective;
  deadline?: string | null;
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
      apiRequest<AgentDto>(`/api/agents/${id}/${enabled ? "enable" : "disable"}`, {
        method: 'POST',
      }),
    run: (id: string, payload?: Record<string, unknown>) =>
      apiRequest<{ execution_id: string; agent_key: string; status: string }>(`/api/agents/${encodeURIComponent(id)}/run`, {
        method: 'POST',
        body: { task_data: payload ?? {} },
      }),
    executions: (key: string) => apiRequest<AgentExecutionDto[]>(`/api/agents/${encodeURIComponent(key)}/executions`),
    cancelExecution: (key: string, executionId: string) => apiRequest<void>(`/api/agents/${encodeURIComponent(key)}/executions/${encodeURIComponent(executionId)}/cancel`, { method: 'POST' }),
  },
  goals: {
    list: (offset = 0) => apiRequest<GoalDto[]>('/api/goals/', { params: { limit: 50, offset } }),
    create: (payload: GoalCreateDto) =>
      apiRequest<GoalDto>('/api/goals/', { method: 'POST', body: payload }),
    update: (id: string, payload: Partial<GoalCreateDto> & { status?: GoalDto['status'] }) =>
      apiRequest<GoalDto>(`/api/goals/${encodeURIComponent(id)}`, { method: 'PUT', body: payload }),
    remove: (id: string) => apiRequest<void>(`/api/goals/${encodeURIComponent(id)}`, { method: 'DELETE' }),
    measure: (id: string, payload: GoalMeasurement) =>
      apiRequest<GoalDto>(`/api/goals/${encodeURIComponent(id)}/measurements`, { method: 'POST', body: payload }),
    measurements: (id: string) => apiRequest<(GoalMeasurement & { id: string })[]>(`/api/goals/${encodeURIComponent(id)}/measurements`),
    milestones: (id: string) => apiRequest<MilestoneDto[]>(`/api/goals/${encodeURIComponent(id)}/milestones`),
    addMilestone: (id: string, payload: { title: string; target_value: number; current_value?: number; due_date?: string | null }) =>
      apiRequest<MilestoneDto>(`/api/goals/${encodeURIComponent(id)}/milestones`, { method: 'POST', body: payload }),
    updateMilestone: (id: string, milestoneId: string, payload: { current_value: number }) =>
      apiRequest<MilestoneDto>(`/api/goals/${encodeURIComponent(id)}/milestones/${encodeURIComponent(milestoneId)}`, { method: 'PUT', body: payload }),
    removeMilestone: (id: string, milestoneId: string) =>
      apiRequest<void>(`/api/goals/${encodeURIComponent(id)}/milestones/${encodeURIComponent(milestoneId)}`, { method: 'DELETE' }),
  },
  content: {
    list: () => apiRequest<ContentAssetDto[]>('/api/content'),
    scanFolder: (path: string) =>
      apiRequest<{ scanned: number }>('/api/content/scan-folder', {
        method: 'POST',
        body: { folder_path: path },
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
