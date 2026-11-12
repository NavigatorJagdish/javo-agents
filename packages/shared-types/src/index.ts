/**
 * Canonical TypeScript interfaces matching Javo Agents Python backend models
 * in `services/local-runtime/app/models/`.
 */

export type ISODateTime = string;
export type UUID = string;

// ---------------------------------------------------------------------------
// Users & Devices
// ---------------------------------------------------------------------------

export type UserRole = "admin" | "user" | "viewer";

export type DeviceType = "mobile" | "desktop" | "tablet" | "browser" | "other";

export interface User {
  id: UUID;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface DevicePairing {
  id: UUID;
  user_id: UUID;
  device_name: string;
  device_type: DeviceType;
  platform: string | null;
  push_token: string | null;
  last_seen: ISODateTime | null;
  is_trusted: boolean;
  paired_at: ISODateTime;
  pairing_code?: string;
  expires_at?: ISODateTime;
}

// ---------------------------------------------------------------------------
// Tasks, Goals & Milestones
// ---------------------------------------------------------------------------

export type TaskState =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export type TaskPriority = "low" | "normal" | "high" | "critical";

export type GoalStatus = "active" | "paused" | "completed" | "cancelled";

export interface FailureRecord {
  timestamp: ISODateTime;
  error: string;
  agent?: string;
  attempt: number;
  recovered?: boolean;
}

export interface AuditTrailEntry {
  timestamp: ISODateTime;
  actor: string;
  event: string;
  details?: Record<string, unknown>;
}

export interface Task {
  task_id: UUID;
  goal_id: UUID | null;
  account_id: UUID | null;
  assigned_agent: string | null;
  title: string;
  description: string | null;
  inputs: Record<string, unknown> | null;
  outputs: Record<string, unknown> | null;
  permissions: Record<string, unknown> | null;
  state: TaskState;
  priority: TaskPriority;
  deadline: ISODateTime | null;
  retry_budget: number;
  cost_budget: number | null;
  resource_budget: Record<string, unknown> | null;
  failure_history: FailureRecord[] | null;
  audit_trail: AuditTrailEntry[] | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  completed_at: ISODateTime | null;
}

export interface Goal {
  goal_id: UUID;
  title: string;
  description: string | null;
  owner_id: UUID;
  target_metrics: Record<string, unknown> | null;
  progress: number;
  status: GoalStatus;
  deadline: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  milestones?: Milestone[];
}

export interface Milestone {
  id: UUID;
  goal_id: UUID;
  title: string;
  target_value: number;
  current_value: number;
  is_completed: boolean;
  due_date: ISODateTime | null;
}

// ---------------------------------------------------------------------------
// Agents
// ---------------------------------------------------------------------------

export type AgentStatus = "idle" | "running" | "paused" | "error" | "disabled";

export type ExecutionStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "timeout";

export interface AgentConfig {
  id?: UUID;
  agent_id?: UUID;
  ai_provider: string | null;
  ai_model: string | null;
  temperature: number;
  max_tokens: number;
  system_prompt: string | null;
  retry_policy: Record<string, unknown> | null;
  rate_limits: Record<string, unknown> | null;
  custom_settings: Record<string, unknown> | null;
}

export interface AgentDefinition {
  id: UUID;
  agent_key: string;
  name: string;
  description: string | null;
  category: string | null;
  version: string;
  status: AgentStatus;
  capabilities: string[] | null;
  input_schema: Record<string, unknown> | null;
  output_schema: Record<string, unknown> | null;
  tools: string[] | null;
  dependencies: string[] | null;
  trust_score: number;
  is_enabled: boolean;
  config?: AgentConfig | null;
  created_at?: ISODateTime;
  updated_at?: ISODateTime;
}

export interface AgentExecution {
  id: UUID;
  agent_id: UUID;
  task_id: UUID | null;
  status: ExecutionStatus;
  inputs: Record<string, unknown> | null;
  outputs: Record<string, unknown> | null;
  error: string | null;
  tokens_used: number;
  cost: number;
  duration_ms: number | null;
  started_at: ISODateTime | null;
  completed_at: ISODateTime | null;
  created_at: ISODateTime;
}

// ---------------------------------------------------------------------------
// Social Accounts & Brand Profiles
// ---------------------------------------------------------------------------

export type Platform =
  | "instagram"
  | "tiktok"
  | "youtube"
  | "twitter"
  | "facebook"
  | "linkedin"
  | "pinterest"
  | "threads"
  | "telegram"
  | "other";

export type AccountStatus = "connected" | "disconnected" | "expired" | "error";

export interface SocialAccount {
  id: UUID;
  user_id: UUID;
  platform: Platform;
  platform_user_id: string | null;
  username: string;
  display_name: string | null;
  status: AccountStatus;
  token_expires_at: ISODateTime | null;
  metadata: Record<string, unknown> | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface BrandProfile {
  id: UUID;
  account_id: UUID;
  brand_name: string;
  brand_voice: string | null;
  target_audience: string | null;
  content_pillars: string[] | null;
  hashtag_groups: Record<string, string[]> | null;
  color_palette: string[] | null;
  logo_url: string | null;
  guidelines: Record<string, unknown> | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

// ---------------------------------------------------------------------------
// Content & Publishing
// ---------------------------------------------------------------------------

export type AssetType =
  | "image"
  | "video"
  | "audio"
  | "document"
  | "text"
  | "carousel"
  | "story"
  | "reel";

export type AssetStatus =
  | "draft"
  | "ready"
  | "scheduled"
  | "published"
  | "archived"
  | "failed";

export type ScheduleStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "published"
  | "failed"
  | "cancelled";

export type PublishStatus = "success" | "partial" | "failed";

export interface MediaMetadata {
  id: UUID;
  asset_id: UUID;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  file_size_bytes: number | null;
  mime_type: string | null;
  codec: string | null;
  aspect_ratio: string | null;
  checksum_sha256: string | null;
}

export interface ContentAsset {
  id: UUID;
  user_id: UUID;
  title: string;
  description: string | null;
  asset_type: AssetType;
  status: AssetStatus;
  file_path: string | null;
  file_url: string | null;
  content_text: string | null;
  hashtags: string[] | null;
  tags: string[] | null;
  ai_generated: boolean;
  ai_metadata: Record<string, unknown> | null;
  media_metadata?: MediaMetadata | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface ContentSchedule {
  id: UUID;
  asset_id: UUID;
  account_id: UUID;
  scheduled_at: ISODateTime;
  status: ScheduleStatus;
  caption: string | null;
  platform_options: Record<string, unknown> | null;
  approved_by: UUID | null;
  approved_at: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface PublishRecord {
  id: UUID;
  schedule_id: UUID;
  platform: Platform;
  platform_post_id: string | null;
  platform_url: string | null;
  status: PublishStatus;
  error_message: string | null;
  engagement_data: Record<string, unknown> | null;
  published_at: ISODateTime;
}

// ---------------------------------------------------------------------------
// Workflows (16 Node Types)
// ---------------------------------------------------------------------------

export type WorkflowStatus = "draft" | "active" | "paused" | "archived";

export type NodeType =
  | "trigger"
  | "schedule"
  | "folder_watcher"
  | "account_event"
  | "content_analyzer"
  | "ai_prompt"
  | "condition"
  | "approval"
  | "publish"
  | "comment_reply"
  | "notification"
  | "analytics"
  | "delay"
  | "retry"
  | "error_handler"
  | "end";

export type WorkflowExecutionStatus =
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "waiting_approval";

export interface WorkflowNode {
  id: UUID;
  workflow_id?: UUID;
  node_type: NodeType;
  label: string;
  position_x: number;
  position_y: number;
  config: Record<string, unknown> | null;
  is_entry_point: boolean;
}

export interface WorkflowEdge {
  id: UUID;
  workflow_id?: UUID;
  source_node_id: UUID;
  target_node_id: UUID;
  condition: string | null;
  label: string | null;
}

export interface Workflow {
  id: UUID;
  user_id: UUID;
  name: string;
  description: string | null;
  status: WorkflowStatus;
  trigger_config: Record<string, unknown> | null;
  viewport: { x: number; y: number; zoom: number } | null;
  run_count: number;
  last_run_at: ISODateTime | null;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface WorkflowExecution {
  id: UUID;
  workflow_id: UUID;
  status: WorkflowExecutionStatus;
  trigger_data: Record<string, unknown> | null;
  current_node_id: UUID | null;
  execution_log: Array<Record<string, unknown>> | null;
  error: string | null;
  started_at: ISODateTime;
  completed_at: ISODateTime | null;
}

// ---------------------------------------------------------------------------
// Approvals, Security & AI Providers
// ---------------------------------------------------------------------------

export type ApprovalStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "edited"
  | "rescheduled"
  | "expired";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface ApprovalItem {
  id: UUID;
  task_id: UUID | null;
  workflow_execution_id: UUID | null;
  schedule_id: UUID | null;
  agent_key: string;
  action_type: string;
  title: string;
  summary: string;
  platform: Platform | null;
  payload: Record<string, unknown>;
  risk_level: RiskLevel;
  status: ApprovalStatus;
  proposed_scheduled_at: ISODateTime | null;
  reviewed_by: string | null;
  reviewed_at: ISODateTime | null;
  rejection_reason: string | null;
  created_at: ISODateTime;
}

export type AuditAction =
  | "login"
  | "logout"
  | "create"
  | "update"
  | "delete"
  | "execute"
  | "approve"
  | "reject"
  | "publish"
  | "access"
  | "emergency_stop"
  | "config_change"
  | "permission_change";

export type AuditSeverity = "info" | "warning" | "critical";

export interface AuditLog {
  id: UUID;
  user_id: UUID | null;
  agent_id: string | null;
  action: AuditAction;
  severity: AuditSeverity;
  resource_type: string | null;
  resource_id: string | null;
  description: string;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: ISODateTime;
}

export interface SecurityStatus {
  emergency_stop_active: boolean;
  autopilot_mode: "supervised_autopilot" | "manual_only" | "paused";
  encryption_enabled: boolean;
  local_only_privacy_mode: boolean;
  trusted_devices_count: number;
  active_sessions_count: number;
  pending_approvals_count: number;
  blocked_egress_events_24h: number;
  last_key_rotation: ISODateTime | null;
  last_backup_at: ISODateTime | null;
  warnings: string[];
}

export type AIProviderType = "ollama" | "gemini" | "openai";

export interface AIProviderConfig {
  default_ai_provider: AIProviderType;
  ollama_base_url: string;
  ollama_default_model: string;
  gemini_configured: boolean;
  gemini_model: string;
  openai_configured: boolean;
  openai_base_url: string;
  openai_model: string;
  ai_daily_budget: number;
  ai_monthly_budget: number;
  daily_spend_usd: number;
  monthly_spend_usd: number;
  max_tokens_per_request: number;
  privacy_egress_policy: "strict_local" | "sanitized_cloud" | "user_approved";
}

// ---------------------------------------------------------------------------
// Health & System Info
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  uptime_seconds: number;
  database: string;
  timestamp: ISODateTime;
}

export interface SystemInfoResponse {
  cpu_percent: number;
  cpu_count: number;
  ram_total_mb: number;
  ram_used_mb: number;
  ram_percent: number;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_percent: number;
  python_version: string;
  platform: string;
}

export interface ApiError {
  detail: string;
  status_code?: number;
  code?: string;
}
