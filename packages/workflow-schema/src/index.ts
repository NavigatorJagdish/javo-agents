import type { NodeType, WorkflowEdge, WorkflowNode } from "@javo/shared-types";

export const WORKFLOW_NODE_TYPES: readonly NodeType[] = [
  "trigger",
  "schedule",
  "folder_watcher",
  "account_event",
  "content_analyzer",
  "ai_prompt",
  "condition",
  "approval",
  "publish",
  "comment_reply",
  "notification",
  "analytics",
  "delay",
  "retry",
  "error_handler",
  "end",
] as const;

export type NodeCategory = "trigger" | "ai" | "logic" | "action" | "control" | "terminal";

export interface NodeConfigFieldSchema {
  key: string;
  type: "string" | "number" | "boolean" | "array" | "object";
  required?: boolean;
  description: string;
  defaultValue?: unknown;
}

export interface NodeTypeDefinition {
  type: NodeType;
  displayName: string;
  category: NodeCategory;
  description: string;
  isEntryCapable: boolean;
  requiresApprovalInAutopilot?: boolean;
  maxOutgoingEdges?: number;
  fields: NodeConfigFieldSchema[];
}

export const NODE_TYPE_REGISTRY: Record<NodeType, NodeTypeDefinition> = {
  trigger: {
    type: "trigger",
    displayName: "Manual / Event Trigger",
    category: "trigger",
    description: "Starts workflow on manual run, webhook, or voice command.",
    isEntryCapable: true,
    fields: [
      { key: "source", type: "string", required: true, description: "manual | voice | webhook | api", defaultValue: "manual" },
      { key: "event_name", type: "string", description: "Optional event identifier" },
    ],
  },
  schedule: {
    type: "schedule",
    displayName: "Schedule (Cron / Interval)",
    category: "trigger",
    description: "Runs workflow on a recurring cron or interval schedule.",
    isEntryCapable: true,
    fields: [
      { key: "cron", type: "string", required: true, description: "Standard 5-field cron expression", defaultValue: "0 9 * * *" },
      { key: "timezone", type: "string", description: "IANA timezone", defaultValue: "Asia/Kolkata" },
    ],
  },
  folder_watcher: {
    type: "folder_watcher",
    displayName: "Folder Watcher",
    category: "trigger",
    description: "Monitors a local folder for newly added videos, images, or scripts.",
    isEntryCapable: true,
    fields: [
      { key: "watch_path", type: "string", required: true, description: "Local folder path inside content root" },
      { key: "extensions", type: "array", description: "Allowed file extensions", defaultValue: [".mp4", ".png", ".jpg"] },
      { key: "recursive", type: "boolean", description: "Watch subfolders", defaultValue: true },
    ],
  },
  account_event: {
    type: "account_event",
    displayName: "Account Event",
    category: "trigger",
    description: "Triggers when a connected social account receives a comment, mention, or milestone.",
    isEntryCapable: true,
    fields: [
      { key: "platform", type: "string", required: true, description: "youtube | instagram | facebook | telegram" },
      { key: "event_type", type: "string", required: true, description: "new_comment | mention | token_expiring" },
    ],
  },
  content_analyzer: {
    type: "content_analyzer",
    displayName: "Content Analyzer",
    category: "ai",
    description: "Extracts media metadata, transcript, duration, and niche tags locally.",
    isEntryCapable: false,
    fields: [
      { key: "extract_audio_transcript", type: "boolean", description: "Transcribe via local whisper.cpp", defaultValue: true },
      { key: "detect_language", type: "boolean", description: "Detect English / Hindi / Hinglish", defaultValue: true },
    ],
  },
  ai_prompt: {
    type: "ai_prompt",
    displayName: "AI Prompt",
    category: "ai",
    description: "Runs a prompt through the AI Router (Ollama local default or Gemini).",
    isEntryCapable: false,
    fields: [
      { key: "prompt_template", type: "string", required: true, description: "Prompt template with {{variable}} placeholders" },
      { key: "provider", type: "string", description: "auto | ollama | gemini | openai", defaultValue: "ollama" },
      { key: "max_tokens", type: "number", description: "Token ceiling", defaultValue: 1024 },
    ],
  },
  condition: {
    type: "condition",
    displayName: "Condition Branch",
    category: "logic",
    description: "Routes execution based on an expression or boolean field.",
    isEntryCapable: false,
    fields: [
      { key: "expression", type: "string", required: true, description: "Safe field comparison expression" },
    ],
  },
  approval: {
    type: "approval",
    displayName: "Human Approval Gate",
    category: "control",
    description: "Pauses execution until approved on Desktop, Android, or Telegram.",
    isEntryCapable: false,
    fields: [
      { key: "channels", type: "array", description: "desktop | android | telegram", defaultValue: ["desktop", "android"] },
      { key: "timeout_hours", type: "number", description: "Auto-expire timeout", defaultValue: 24 },
    ],
  },
  publish: {
    type: "publish",
    displayName: "Publish Content",
    category: "action",
    description: "Publishes content to a connected official platform API.",
    isEntryCapable: false,
    requiresApprovalInAutopilot: true,
    fields: [
      { key: "account_id", type: "string", required: true, description: "Target SocialAccount UUID" },
      { key: "platform", type: "string", required: true, description: "youtube | instagram | facebook" },
      { key: "dry_run", type: "boolean", description: "Simulate without posting", defaultValue: false },
    ],
  },
  comment_reply: {
    type: "comment_reply",
    displayName: "Comment Reply",
    category: "action",
    description: "Drafts or sends replies to audience comments.",
    isEntryCapable: false,
    requiresApprovalInAutopilot: true,
    fields: [
      { key: "account_id", type: "string", required: true, description: "Target SocialAccount UUID" },
      { key: "tone", type: "string", description: "friendly | professional | hinglish", defaultValue: "friendly" },
    ],
  },
  notification: {
    type: "notification",
    displayName: "Send Notification",
    category: "action",
    description: "Sends an alert to Windows Tray, Android, or Telegram.",
    isEntryCapable: false,
    fields: [
      { key: "channel", type: "string", required: true, description: "desktop | android | telegram", defaultValue: "desktop" },
      { key: "message_template", type: "string", required: true, description: "Notification body" },
    ],
  },
  analytics: {
    type: "analytics",
    displayName: "Analytics Snapshot",
    category: "action",
    description: "Fetches official platform metrics and updates Goal progress.",
    isEntryCapable: false,
    fields: [
      { key: "account_id", type: "string", required: true, description: "SocialAccount UUID" },
      { key: "metrics", type: "array", description: "Metrics to collect", defaultValue: ["views", "likes", "comments"] },
    ],
  },
  delay: {
    type: "delay",
    displayName: "Delay / Wait",
    category: "control",
    description: "Waits a bounded duration before continuing to the next node.",
    isEntryCapable: false,
    fields: [
      { key: "seconds", type: "number", required: true, description: "Wait time in seconds", defaultValue: 60 },
    ],
  },
  retry: {
    type: "retry",
    displayName: "Retry Policy",
    category: "control",
    description: "Retries an upstream step with exponential backoff up to max_attempts.",
    isEntryCapable: false,
    fields: [
      { key: "max_attempts", type: "number", required: true, description: "Maximum retries (1-5)", defaultValue: 3 },
      { key: "backoff_seconds", type: "number", description: "Base backoff interval", defaultValue: 5 },
    ],
  },
  error_handler: {
    type: "error_handler",
    displayName: "Error Handler",
    category: "control",
    description: "Catches upstream failures and triggers fallback or alert actions.",
    isEntryCapable: false,
    fields: [
      { key: "fallback_action", type: "string", description: "notify | pause_workflow | ignore", defaultValue: "notify" },
    ],
  },
  end: {
    type: "end",
    displayName: "End Workflow",
    category: "terminal",
    description: "Marks workflow execution complete.",
    isEntryCapable: false,
    maxOutgoingEdges: 0,
    fields: [
      { key: "status", type: "string", description: "completed | archived", defaultValue: "completed" },
    ],
  },
};

export interface WorkflowValidationIssue {
  severity: "error" | "warning";
  code: string;
  message: string;
  nodeId?: string;
  edgeId?: string;
}

export interface WorkflowValidationResult {
  valid: boolean;
  issues: WorkflowValidationIssue[];
}

export interface ValidateWorkflowOptions {
  supervisedAutopilot?: boolean;
}

const VALID_TYPE_SET = new Set<string>(WORKFLOW_NODE_TYPES);

/**
 * Validates a visual workflow graph, checking all 16 node types, required config fields,
 * entry-point existence, edge references, cycle safety, and Supervised Autopilot approval gates.
 */
export function validateWorkflowGraph(
  nodes: WorkflowNode[],
  edges: WorkflowEdge[],
  options: ValidateWorkflowOptions = { supervisedAutopilot: true }
): WorkflowValidationResult {
  const issues: WorkflowValidationIssue[] = [];
  const nodeMap = new Map<string, WorkflowNode>();

  if (nodes.length === 0) {
    issues.push({
      severity: "error",
      code: "EMPTY_WORKFLOW",
      message: "Workflow must contain at least one node.",
    });
    return { valid: false, issues };
  }

  // 1. Validate nodes & configs
  let entryCount = 0;
  for (const node of nodes) {
    if (nodeMap.has(node.id)) {
      issues.push({
        severity: "error",
        code: "DUPLICATE_NODE_ID",
        message: `Duplicate node id "${node.id}".`,
        nodeId: node.id,
      });
      continue;
    }
    nodeMap.set(node.id, node);

    if (!VALID_TYPE_SET.has(node.node_type)) {
      issues.push({
        severity: "error",
        code: "UNKNOWN_NODE_TYPE",
        message: `Unsupported node type "${String(node.node_type)}".`,
        nodeId: node.id,
      });
      continue;
    }

    const def = NODE_TYPE_REGISTRY[node.node_type];
    if (node.is_entry_point || def.isEntryCapable) {
      if (node.is_entry_point && !def.isEntryCapable) {
        issues.push({
          severity: "error",
          code: "INVALID_ENTRY_NODE",
          message: `Node type "${node.node_type}" cannot be marked as an entry point.`,
          nodeId: node.id,
        });
      }
      if (node.is_entry_point) {
        entryCount += 1;
      }
    }

    const cfg = node.config ?? {};
    for (const field of def.fields) {
      if (field.required) {
        const val = cfg[field.key];
        if (val === undefined || val === null || val === "") {
          issues.push({
            severity: "error",
            code: "MISSING_NODE_CONFIG",
            message: `Node "${node.label}" (${node.node_type}) is missing required config "${field.key}".`,
            nodeId: node.id,
          });
        }
      }
    }
  }

  if (entryCount === 0) {
    const hasTrigger = nodes.some((n) => NODE_TYPE_REGISTRY[n.node_type]?.isEntryCapable);
    issues.push({
      severity: hasTrigger ? "warning" : "error",
      code: "NO_ENTRY_POINT",
      message: hasTrigger
        ? "No node has is_entry_point=true; set an explicit entry point."
        : "Workflow must include at least one trigger/schedule/folder_watcher/account_event node.",
    });
  }

  // 2. Validate edges
  const adjacency = new Map<string, string[]>();
  const reverseAdj = new Map<string, string[]>();
  for (const node of nodes) {
    adjacency.set(node.id, []);
    reverseAdj.set(node.id, []);
  }

  for (const edge of edges) {
    if (!nodeMap.has(edge.source_node_id)) {
      issues.push({
        severity: "error",
        code: "ORPHAN_EDGE_SOURCE",
        message: `Edge "${edge.id}" references missing source node "${edge.source_node_id}".`,
        edgeId: edge.id,
      });
      continue;
    }
    if (!nodeMap.has(edge.target_node_id)) {
      issues.push({
        severity: "error",
        code: "ORPHAN_EDGE_TARGET",
        message: `Edge "${edge.id}" references missing target node "${edge.target_node_id}".`,
        edgeId: edge.id,
      });
      continue;
    }
    if (edge.source_node_id === edge.target_node_id) {
      issues.push({
        severity: "error",
        code: "SELF_LOOP",
        message: `Edge "${edge.id}" creates a self-loop on node "${edge.source_node_id}".`,
        edgeId: edge.id,
      });
      continue;
    }

    const srcNode = nodeMap.get(edge.source_node_id)!;
    if (srcNode.node_type === "end") {
      issues.push({
        severity: "error",
        code: "END_NODE_HAS_OUTGOING_EDGE",
        message: `End node "${srcNode.label}" cannot have outgoing edges.`,
        nodeId: srcNode.id,
        edgeId: edge.id,
      });
    }

    adjacency.get(edge.source_node_id)!.push(edge.target_node_id);
    reverseAdj.get(edge.target_node_id)!.push(edge.source_node_id);
  }

  // 3. Cycle detection (DFS 3-color)
  const color = new Map<string, 0 | 1 | 2>();
  for (const id of nodeMap.keys()) color.set(id, 0);

  const dfs = (u: string): void => {
    color.set(u, 1);
    for (const v of adjacency.get(u) ?? []) {
      const c = color.get(v);
      if (c === 1) {
        issues.push({
          severity: "error",
          code: "CYCLE_DETECTED",
          message: `Cycle detected involving node "${nodeMap.get(v)?.label ?? v}". Use a "retry" node instead of cyclic edges.`,
          nodeId: v,
        });
      } else if (c === 0) {
        dfs(v);
      }
    }
    color.set(u, 2);
  };

  for (const id of nodeMap.keys()) {
    if (color.get(id) === 0) dfs(id);
  }

  // 4. Supervised Autopilot check: publish/comment_reply should have an upstream approval node
  if (options.supervisedAutopilot !== false) {
    const hasUpstreamApproval = (startId: string): boolean => {
      const visited = new Set<string>();
      const queue = [...(reverseAdj.get(startId) ?? [])];
      while (queue.length > 0) {
        const cur = queue.shift()!;
        if (visited.has(cur)) continue;
        visited.add(cur);
        if (nodeMap.get(cur)?.node_type === "approval") return true;
        for (const prev of reverseAdj.get(cur) ?? []) {
          if (!visited.has(prev)) queue.push(prev);
        }
      }
      return false;
    };

    for (const node of nodes) {
      const def = NODE_TYPE_REGISTRY[node.node_type];
      if (def?.requiresApprovalInAutopilot && !hasUpstreamApproval(node.id)) {
        issues.push({
          severity: "warning",
          code: "MISSING_APPROVAL_GATE",
          message: `Node "${node.label}" (${node.node_type}) has no upstream "approval" gate; Supervised Autopilot will queue it for manual review at runtime.`,
          nodeId: node.id,
        });
      }
    }
  }

  const hasErrors = issues.some((i) => i.severity === "error");
  return { valid: !hasErrors, issues };
}
