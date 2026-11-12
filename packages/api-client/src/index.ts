import type {
  AIProviderConfig,
  AgentConfig,
  AgentDefinition,
  AgentExecution,
  ApprovalItem,
  AuditLog,
  BrandProfile,
  ContentAsset,
  ContentSchedule,
  DevicePairing,
  Goal,
  HealthResponse,
  Milestone,
  SecurityStatus,
  SocialAccount,
  SystemInfoResponse,
  Task,
  Workflow,
  WorkflowExecution,
} from "@javo/shared-types";

export interface JavoClientOptions {
  baseUrl?: string;
  apiPrefix?: string;
  authToken?: string;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
}

export class JavoApiError extends Error {
  public readonly status: number;
  public readonly body: unknown;

  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.name = "JavoApiError";
    this.status = status;
    this.body = body;
  }
}

export interface WebSocketEvent {
  type: string;
  channel?: string;
  payload: Record<string, unknown>;
  timestamp?: string;
}

export interface WebSocketSubscription {
  close: () => void;
  send: (data: unknown) => void;
}

/**
 * Typed REST + WebSocket client for the Javo Agents FastAPI local runtime.
 * Default endpoint: http://localhost:8000
 */
export class JavoApiClient {
  private baseUrl: string;
  private apiPrefix: string;
  private authToken?: string;
  private timeoutMs: number;
  private fetchImpl: typeof fetch;

  constructor(options: JavoClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? "http://localhost:8000").replace(/\/+$/, "");
    this.apiPrefix = options.apiPrefix ?? "";
    this.authToken = options.authToken;
    this.timeoutMs = options.timeoutMs ?? 15000;
    this.fetchImpl = options.fetchImpl ?? globalThis.fetch.bind(globalThis);
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, "");
  }

  public setAuthToken(token: string | undefined): void {
    this.authToken = token;
  }

  private buildUrl(path: string, query?: Record<string, string | number | boolean | undefined>): string {
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    const url = new URL(`${this.baseUrl}${this.apiPrefix}${cleanPath}`);
    if (query) {
      for (const [k, v] of Object.entries(query)) {
        if (v !== undefined && v !== null) {
          url.searchParams.set(k, String(v));
        }
      }
    }
    return url.toString();
  }

  private async request<T>(
    method: string,
    path: string,
    options?: {
      body?: unknown;
      query?: Record<string, string | number | boolean | undefined>;
      headers?: Record<string, string>;
    }
  ): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    const headers: Record<string, string> = {
      Accept: "application/json",
      ...options?.headers,
    };
    if (this.authToken) {
      headers.Authorization = `Bearer ${this.authToken}`;
    }

    let body: BodyInit | undefined;
    if (options?.body !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(options.body);
    }

    try {
      const response = await this.fetchImpl(this.buildUrl(path, options?.query), {
        method,
        headers,
        body,
        signal: controller.signal,
      });

      const contentType = response.headers.get("content-type") ?? "";
      const parsed = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

      if (!response.ok) {
        const detail =
          typeof parsed === "object" && parsed !== null && "detail" in parsed
            ? String((parsed as { detail: unknown }).detail)
            : `HTTP ${response.status}`;
        throw new JavoApiError(detail, response.status, parsed);
      }

      return parsed as T;
    } finally {
      clearTimeout(timer);
    }
  }

  // -------------------------------------------------------------------------
  // Health & Diagnostics
  // -------------------------------------------------------------------------

  public getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>("GET", "/health/");
  }

  public getSystemInfo(): Promise<SystemInfoResponse> {
    return this.request<SystemInfoResponse>("GET", "/health/system");
  }

  public getDiagnostics(): Promise<{ overall: string; checks: Array<{ name: string; status: string; message?: string }> }> {
    return this.request("GET", "/health/diagnostics");
  }

  // -------------------------------------------------------------------------
  // Agents
  // -------------------------------------------------------------------------

  public listAgents(): Promise<AgentDefinition[]> {
    return this.request<AgentDefinition[]>("GET", "/agents/");
  }

  public getAgent(agentKeyOrId: string): Promise<AgentDefinition> {
    return this.request<AgentDefinition>("GET", `/agents/${encodeURIComponent(agentKeyOrId)}`);
  }

  public runAgent(agentKeyOrId: string, inputs: Record<string, unknown>): Promise<AgentExecution> {
    return this.request<AgentExecution>("POST", `/agents/${encodeURIComponent(agentKeyOrId)}/run`, {
      body: { inputs },
    });
  }

  public updateAgentConfig(agentKeyOrId: string, config: Partial<AgentConfig>): Promise<AgentConfig> {
    return this.request<AgentConfig>("PUT", `/agents/${encodeURIComponent(agentKeyOrId)}/config`, {
      body: config,
    });
  }

  public toggleAgent(agentKeyOrId: string, enabled: boolean): Promise<AgentDefinition> {
    return this.request<AgentDefinition>("POST", `/agents/${encodeURIComponent(agentKeyOrId)}/${enabled ? "enable" : "disable"}`);
  }

  // -------------------------------------------------------------------------
  // Tasks & Goals
  // -------------------------------------------------------------------------

  public listTasks(params?: { state?: string; priority?: string; assigned_agent?: string }): Promise<Task[]> {
    return this.request<Task[]>("GET", "/tasks/", { query: params });
  }

  public createTask(payload: Partial<Task> & { title: string }): Promise<Task> {
    return this.request<Task>("POST", "/tasks/", { body: payload });
  }

  public executeTask(taskId: string): Promise<Task> {
    return this.request<Task>("POST", `/tasks/${encodeURIComponent(taskId)}/execute`);
  }

  public listGoals(status?: string): Promise<Goal[]> {
    return this.request<Goal[]>("GET", "/goals/", { query: { status } });
  }

  public createGoal(payload: Partial<Goal> & { title: string }): Promise<Goal> {
    return this.request<Goal>("POST", "/goals/", { body: payload });
  }

  public addMilestone(goalId: string, payload: Partial<Milestone> & { title: string }): Promise<Milestone> {
    return this.request<Milestone>("POST", `/goals/${encodeURIComponent(goalId)}/milestones`, {
      body: payload,
    });
  }

  // -------------------------------------------------------------------------
  // Social Accounts & Brand Profiles
  // -------------------------------------------------------------------------

  public listAccounts(): Promise<SocialAccount[]> {
    return this.request<SocialAccount[]>("GET", "/accounts/");
  }

  public createAccount(payload: {
    platform: SocialAccount["platform"];
    username: string;
    display_name?: string;
  }): Promise<SocialAccount> {
    return this.request<SocialAccount>("POST", "/accounts/", { body: payload });
  }

  public getBrandProfile(accountId: string): Promise<BrandProfile> {
    return this.request<BrandProfile>("GET", `/accounts/${encodeURIComponent(accountId)}/brand-profile`);
  }

  public upsertBrandProfile(accountId: string, profile: Partial<BrandProfile>): Promise<BrandProfile> {
    return this.request<BrandProfile>("PUT", `/accounts/${encodeURIComponent(accountId)}/brand-profile`, {
      body: profile,
    });
  }

  // -------------------------------------------------------------------------
  // Content & Publishing
  // -------------------------------------------------------------------------

  public listContent(params?: { asset_type?: string; status?: string }): Promise<ContentAsset[]> {
    return this.request<ContentAsset[]>("GET", "/content/", { query: params });
  }

  public scanContentFolder(folderPath?: string, recursive = true): Promise<{ scanned: number; created: number }> {
    return this.request("POST", "/content/scan-folder", {
      body: { folder_path: folderPath, recursive },
    });
  }

  public scheduleContent(payload: {
    asset_id: string;
    account_id: string;
    scheduled_at: string;
    caption?: string;
  }): Promise<ContentSchedule> {
    return this.request<ContentSchedule>("POST", "/content/schedule", { body: payload });
  }

  // -------------------------------------------------------------------------
  // Workflows
  // -------------------------------------------------------------------------

  public listWorkflows(): Promise<Workflow[]> {
    return this.request<Workflow[]>("GET", "/workflows/");
  }

  public getWorkflow(workflowId: string): Promise<Workflow> {
    return this.request<Workflow>("GET", `/workflows/${encodeURIComponent(workflowId)}`);
  }

  public createWorkflow(payload: Partial<Workflow> & { name: string }): Promise<Workflow> {
    return this.request<Workflow>("POST", "/workflows/", { body: payload });
  }

  public executeWorkflow(workflowId: string, triggerData?: Record<string, unknown>): Promise<WorkflowExecution> {
    return this.request<WorkflowExecution>("POST", `/workflows/${encodeURIComponent(workflowId)}/execute`, {
      body: { trigger_data: triggerData ?? {} },
    });
  }

  // -------------------------------------------------------------------------
  // Security, Approvals, Settings & Devices
  // -------------------------------------------------------------------------

  public getSecurityStatus(): Promise<SecurityStatus> {
    return this.request<SecurityStatus>("GET", "/security/dashboard");
  }

  public triggerEmergencyStop(reason = "User activated emergency stop"): Promise<{ stopped_tasks: number; stopped_executions: number; timestamp: string; message: string }> {
    return this.request("POST", "/security/emergency-stop", { body: { reason } });
  }

  public resumeFromEmergencyStop(): Promise<{ active: boolean }> {
    return this.request("POST", "/security/resume");
  }

  public listAuditLogs(limit = 50): Promise<AuditLog[]> {
    return this.request<AuditLog[]>("GET", "/security/audit-log", { query: { limit } });
  }

  public listApprovals(status = "pending"): Promise<ApprovalItem[]> {
    return this.request<ApprovalItem[]>("GET", "/approvals/", { query: { status } });
  }

  public decideApproval(
    approvalId: string,
    decision: "approve" | "reject" | "reschedule",
    options?: { reason?: string; scheduled_at?: string; edited_caption?: string }
  ): Promise<ApprovalItem> {
    return this.request<ApprovalItem>("POST", `/approvals/${encodeURIComponent(approvalId)}/${decision}`, {
      body: options ?? {},
    });
  }

  public getAIProviderConfig(): Promise<AIProviderConfig> {
    return this.request<AIProviderConfig>("GET", "/settings/ai-providers");
  }

  public updateAIProviderConfig(providerName: string, config: Partial<AIProviderConfig>): Promise<AIProviderConfig> {
    return this.request<AIProviderConfig>("PUT", `/settings/ai-providers/${encodeURIComponent(providerName)}`, { body: config });
  }

  public listDevices(): Promise<DevicePairing[]> {
    return this.request<DevicePairing[]>("GET", "/devices/");
  }

  public revokeDevice(deviceId: string): Promise<{ revoked: boolean }> {
    return this.request("DELETE", `/devices/${encodeURIComponent(deviceId)}`);
  }

  // -------------------------------------------------------------------------
  // WebSocket Live Events
  // -------------------------------------------------------------------------

  public connectWebSocket(
    path = "/ws/events",
    handlers: {
      onEvent?: (event: WebSocketEvent) => void;
      onOpen?: () => void;
      onClose?: (code: number, reason: string) => void;
      onError?: (err: unknown) => void;
    } = {},
    reconnect = true
  ): WebSocketSubscription {
    const wsBase = this.baseUrl.replace(/^http/, "ws");
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    const url = new URL(`${wsBase}${this.apiPrefix}${cleanPath}`);
    if (this.authToken) {
      url.searchParams.set("token", this.authToken);
    }

    let ws: WebSocket | null = null;
    let manuallyClosed = false;
    let reconnectAttempt = 0;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      if (typeof WebSocket === "undefined") {
        handlers.onError?.(new Error("WebSocket is not available in this runtime"));
        return;
      }
      ws = new WebSocket(url.toString());

      ws.onopen = () => {
        reconnectAttempt = 0;
        handlers.onOpen?.();
      };

      ws.onmessage = (msg) => {
        try {
          const parsed = JSON.parse(String(msg.data)) as WebSocketEvent;
          handlers.onEvent?.(parsed);
        } catch {
          handlers.onEvent?.({
            type: "raw_message",
            payload: { data: msg.data },
          });
        }
      };

      ws.onerror = (err) => {
        handlers.onError?.(err);
      };

      ws.onclose = (ev) => {
        handlers.onClose?.(ev.code, ev.reason);
        if (reconnect && !manuallyClosed) {
          const backoffMs = Math.min(30000, 1000 * Math.pow(2, reconnectAttempt));
          reconnectAttempt += 1;
          reconnectTimer = setTimeout(connect, backoffMs);
        }
      };
    };

    connect();

    return {
      close: () => {
        manuallyClosed = true;
        if (reconnectTimer) {
          clearTimeout(reconnectTimer);
        }
        ws?.close();
      },
      send: (data: unknown) => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(typeof data === "string" ? data : JSON.stringify(data));
        }
      },
    };
  }
}
