import type { AIProviderType, RiskLevel } from "@javo/shared-types";

export type AutopilotMode = "read_only_observer" | "supervised_autopilot" | "paused";

export type PermissionScope =
  | "read:content"
  | "write:draft"
  | "publish:social"
  | "reply:comments"
  | "execute:skill"
  | "network:external"
  | "filesystem:read"
  | "filesystem:write"
  | "secrets:read"
  | "ai:local"
  | "ai:cloud";

export type PolicyActionType =
  | "read_analytics"
  | "scan_folder"
  | "generate_draft"
  | "schedule_post"
  | "publish_post"
  | "reply_comment"
  | "delete_content"
  | "install_skill"
  | "run_skill"
  | "ai_inference"
  | "modify_security";

export interface PolicyContext {
  autopilotMode: AutopilotMode;
  emergencyStopActive: boolean;
  grantedScopes: PermissionScope[];
  aiProvider: AIProviderType;
  dailySpendUsd: number;
  dailyBudgetUsd: number;
  monthlySpendUsd: number;
  monthlyBudgetUsd: number;
  zeroCostOnly: boolean;
  localPrivacyMode: boolean;
  estimatedCostUsd?: number;
}

export interface PolicyEvaluation {
  decision: "allow" | "require_approval" | "deny";
  riskLevel: RiskLevel;
  reasons: string[];
  requiredScopes: PermissionScope[];
  missingScopes: PermissionScope[];
  recommendedProvider?: AIProviderType;
}

const ACTION_SCOPE_MAP: Record<PolicyActionType, PermissionScope[]> = {
  read_analytics: ["read:content"],
  scan_folder: ["filesystem:read", "read:content"],
  generate_draft: ["write:draft", "ai:local"],
  schedule_post: ["write:draft"],
  publish_post: ["publish:social", "network:external"],
  reply_comment: ["reply:comments", "network:external"],
  delete_content: ["filesystem:write"],
  install_skill: ["execute:skill"],
  run_skill: ["execute:skill"],
  ai_inference: ["ai:local"],
  modify_security: ["secrets:read"],
};

const ACTION_RISK_MAP: Record<PolicyActionType, RiskLevel> = {
  read_analytics: "low",
  scan_folder: "low",
  generate_draft: "low",
  ai_inference: "low",
  run_skill: "medium",
  schedule_post: "medium",
  reply_comment: "high",
  publish_post: "high",
  delete_content: "high",
  install_skill: "critical",
  modify_security: "critical",
};

/**
 * Deterministic policy evaluator enforcing:
 * 1. Emergency Stop kill switch (blocks all side-effecting actions)
 * 2. Least-privilege permission scopes
 * 3. Zero-cost & budget guardrails (forces Ollama local when zeroCostOnly=true or budget reached)
 * 4. Strict local privacy firewall (blocks cloud AI egress when localPrivacyMode=true)
 * 5. Supervised Autopilot human approval gates for external/destructive/critical actions
 */
export function evaluatePolicy(action: PolicyActionType, ctx: PolicyContext): PolicyEvaluation {
  const reasons: string[] = [];
  const requiredScopes = [...ACTION_SCOPE_MAP[action]];
  const riskLevel = ACTION_RISK_MAP[action];

  if (action === "ai_inference" && ctx.aiProvider !== "ollama") {
    requiredScopes.push("ai:cloud", "network:external");
  }

  // 1. Emergency stop overrides everything
  if (ctx.emergencyStopActive) {
    return {
      decision: "deny",
      riskLevel,
      reasons: ["Emergency Stop is active. All agent actions are halted until manually resumed."],
      requiredScopes,
      missingScopes: [],
    };
  }

  // 2. Paused or Read-Only Observer checks
  if (ctx.autopilotMode === "paused") {
    return {
      decision: "deny",
      riskLevel,
      reasons: ["Autopilot is currently paused."],
      requiredScopes,
      missingScopes: [],
    };
  }

  if (ctx.autopilotMode === "read_only_observer" && action !== "read_analytics" && action !== "scan_folder") {
    return {
      decision: "deny",
      riskLevel,
      reasons: [`Action "${action}" is blocked in read_only_observer mode.`],
      requiredScopes,
      missingScopes: [],
    };
  }

  // 3. Scope check
  const granted = new Set<PermissionScope>(ctx.grantedScopes);
  const missingScopes = requiredScopes.filter((s) => !granted.has(s));
  if (missingScopes.length > 0) {
    return {
      decision: "deny",
      riskLevel,
      reasons: [`Missing required permission scope(s): ${missingScopes.join(", ")}`],
      requiredScopes,
      missingScopes,
    };
  }

  // 4. Privacy firewall & zero-cost guardrails for AI calls
  let recommendedProvider: AIProviderType = ctx.aiProvider;
  const estCost = ctx.estimatedCostUsd ?? 0;

  if (ctx.localPrivacyMode && ctx.aiProvider !== "ollama") {
    recommendedProvider = "ollama";
    reasons.push("Local-only privacy mode is active; rerouting AI inference to local Ollama.");
    if (action === "ai_inference") {
      return {
        decision: "deny",
        riskLevel,
        reasons: ["Cloud AI egress denied because localPrivacyMode is enabled. Use Ollama."],
        requiredScopes,
        missingScopes: [],
        recommendedProvider: "ollama",
      };
    }
  }

  if (ctx.zeroCostOnly && estCost > 0) {
    return {
      decision: "deny",
      riskLevel,
      reasons: [`Zero-cost guardrail blocked paid action (estimated $${estCost.toFixed(4)}).`],
      requiredScopes,
      missingScopes: [],
      recommendedProvider: "ollama",
    };
  }

  if (
    ctx.dailySpendUsd + estCost > ctx.dailyBudgetUsd ||
    ctx.monthlySpendUsd + estCost > ctx.monthlyBudgetUsd
  ) {
    return {
      decision: "deny",
      riskLevel: "high",
      reasons: ["AI daily or monthly budget cap reached. Falling back to local Ollama only."],
      requiredScopes,
      missingScopes: [],
      recommendedProvider: "ollama",
    };
  }

  // 5. Supervised Autopilot approval gating
  if (
    action === "publish_post" ||
    action === "reply_comment" ||
    action === "delete_content" ||
    action === "install_skill" ||
    action === "modify_security"
  ) {
    reasons.push(`Supervised Autopilot requires explicit human approval for "${action}" (risk: ${riskLevel}).`);
    return {
      decision: "require_approval",
      riskLevel,
      reasons,
      requiredScopes,
      missingScopes: [],
      recommendedProvider,
    };
  }

  return {
    decision: "allow",
    riskLevel,
    reasons: reasons.length > 0 ? reasons : ["Action permitted under Supervised Autopilot policy."],
    requiredScopes,
    missingScopes: [],
    recommendedProvider,
  };
}
