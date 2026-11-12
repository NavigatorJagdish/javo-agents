import { create } from 'zustand';

export type AgentStatus = 'active' | 'idle' | 'running' | 'error' | 'disabled';

export interface AgentItem {
  id: string;
  number: number;
  name: string;
  role: string;
  category: 'Growth' | 'Content' | 'Operations' | 'Security' | 'Infrastructure';
  description: string;
  enabled: boolean;
  status: AgentStatus;
  tasksCompleted: number;
  successRate: number;
  model: string;
  lastRun: string;
  permissions: string[];
}

const INITIAL_AGENTS: AgentItem[] = [
  { id: 'growth_scientist', number: 1, name: 'Growth Scientist', role: 'Experimentation & Retention', category: 'Growth', description: 'Designs A/B content experiments and tracks follower velocity.', enabled: true, status: 'active', tasksCompleted: 142, successRate: 97.2, model: 'Gemini 2.5 Pro', lastRun: '4m ago', permissions: ['analytics:read', 'experiments:write'] },
  { id: 'content_factory', number: 2, name: 'Content Factory', role: 'Multi-Format Generation', category: 'Content', description: 'Produces hooks, captions, carousels, and short-form scripts.', enabled: true, status: 'running', tasksCompleted: 318, successRate: 98.4, model: 'Qwen 2.5 14B (Local)', lastRun: 'Running now', permissions: ['content:write', 'media:read'] },
  { id: 'smart_memory', number: 3, name: 'Smart Memory', role: 'Vector Context & Recall', category: 'Operations', description: 'Maintains brand preferences, past wins, and long-term memory.', enabled: true, status: 'active', tasksCompleted: 509, successRate: 99.6, model: 'Nomic Embed + Qwen', lastRun: '2m ago', permissions: ['memory:read', 'memory:write'] },
  { id: 'self_upgrading_engineer', number: 4, name: 'Self-Upgrading Engineer', role: 'Skill Synthesis & Patches', category: 'Infrastructure', description: 'Generates and tests new skills in isolated sandboxes.', enabled: true, status: 'idle', tasksCompleted: 37, successRate: 94.5, model: 'Gemini 2.5 Pro', lastRun: '1h ago', permissions: ['sandbox:exec', 'skills:write'] },
  { id: 'telegram_agent', number: 5, name: 'Telegram Agent', role: 'Mobile Command Bridge', category: 'Operations', description: 'Handles remote approvals, voice notes, and status pings via Telegram.', enabled: true, status: 'active', tasksCompleted: 214, successRate: 99.1, model: 'Llama 3.2 8B', lastRun: '11m ago', permissions: ['telegram:send', 'approvals:trigger'] },
  { id: 'brand_manager', number: 6, name: 'Brand Manager', role: 'Tone & Visual Consistency', category: 'Content', description: 'Enforces brand voice guidelines across every platform.', enabled: true, status: 'active', tasksCompleted: 186, successRate: 98.0, model: 'Gemini 2.5 Flash', lastRun: '9m ago', permissions: ['brand:read', 'content:review'] },
  { id: 'voice_agent', number: 7, name: 'Voice Agent', role: 'STT / TTS & Command Parsing', category: 'Operations', description: 'Processes push-to-talk commands with Whisper and neural TTS.', enabled: true, status: 'idle', tasksCompleted: 93, successRate: 96.8, model: 'Whisper Large v3', lastRun: '25m ago', permissions: ['audio:capture', 'voice:speak'] },
  { id: 'api_integration', number: 8, name: 'API Integration', role: 'Connector & Webhook Bridge', category: 'Infrastructure', description: 'Manages OAuth tokens, rate limits, and third-party API health.', enabled: true, status: 'active', tasksCompleted: 412, successRate: 98.9, model: 'Local Router', lastRun: '3m ago', permissions: ['oauth:refresh', 'webhooks:manage'] },
  { id: 'content_publisher', number: 9, name: 'Content Publisher', role: 'Multi-Channel Dispatcher', category: 'Content', description: 'Publishes scheduled reels, shorts, and posts across connected accounts.', enabled: true, status: 'active', tasksCompleted: 274, successRate: 99.3, model: 'Local Worker', lastRun: '18m ago', permissions: ['social:publish', 'schedule:read'] },
  { id: 'community_manager', number: 10, name: 'Community Manager', role: 'Comment & DM Triage', category: 'Growth', description: 'Drafts personalized replies and flags high-value creator DMs.', enabled: true, status: 'active', tasksCompleted: 361, successRate: 97.5, model: 'Gemini 2.5 Flash', lastRun: '6m ago', permissions: ['comments:read', 'comments:reply'] },
  { id: 'account_guardian', number: 11, name: 'Account Guardian', role: 'Rate Limit & Policy Shield', category: 'Security', description: 'Prevents shadowbans and enforces safe publishing cadence.', enabled: true, status: 'active', tasksCompleted: 198, successRate: 100.0, model: 'Policy Engine', lastRun: '1m ago', permissions: ['accounts:monitor', 'limits:enforce'] },
  { id: 'resource_optimizer', number: 12, name: 'Resource Optimizer', role: 'VRAM & CPU Scheduler', category: 'Infrastructure', description: 'Loads and unloads local models cleanly to stay under RAM budgets.', enabled: true, status: 'active', tasksCompleted: 620, successRate: 99.8, model: 'System Monitor', lastRun: '30s ago', permissions: ['system:metrics', 'models:manage'] },
  { id: 'quality_inspector', number: 13, name: 'Quality Inspector', role: 'Pre-Publish QA Gate', category: 'Content', description: 'Scores resolution, audio levels, hook strength, and aspect ratios.', enabled: true, status: 'active', tasksCompleted: 245, successRate: 98.7, model: 'Qwen 2.5 VL', lastRun: '14m ago', permissions: ['media:inspect', 'approvals:flag'] },
  { id: 'niche_radar', number: 14, name: 'Niche Radar', role: 'Trend & Competitor Intel', category: 'Growth', description: 'Surfaces breakout topics and audio trends in your niche daily.', enabled: true, status: 'idle', tasksCompleted: 129, successRate: 95.3, model: 'Gemini 2.5 Flash', lastRun: '42m ago', permissions: ['trends:read', 'memory:write'] },
  { id: 'approval_manager', number: 15, name: 'Approval Manager', role: 'Human-in-the-Loop Queue', category: 'Operations', description: 'Routes sensitive posts and actions to dashboard and Telegram.', enabled: true, status: 'active', tasksCompleted: 176, successRate: 100.0, model: 'Policy Engine', lastRun: '5m ago', permissions: ['approvals:read', 'approvals:write'] },
  { id: 'budget_guardian', number: 16, name: 'Budget Guardian', role: 'Token & Spend Caps', category: 'Security', description: 'Tracks cloud API costs and enforces daily/monthly hard limits.', enabled: true, status: 'active', tasksCompleted: 488, successRate: 100.0, model: 'Metering Core', lastRun: '1m ago', permissions: ['billing:read', 'router:throttle'] },
  { id: 'content_recycler', number: 17, name: 'Content Recycler', role: 'Evergreen Repurposing', category: 'Content', description: 'Turns top-performing long videos into fresh clips and threads.', enabled: true, status: 'idle', tasksCompleted: 88, successRate: 96.4, model: 'Qwen 2.5 14B', lastRun: '2h ago', permissions: ['content:read', 'content:write'] },
  { id: 'brand_studio', number: 18, name: 'Brand Studio', role: 'Thumbnails & Visual Kits', category: 'Content', description: 'Generates thumbnail variants, overlays, and color-matched assets.', enabled: true, status: 'idle', tasksCompleted: 112, successRate: 95.9, model: 'Imagen / Local', lastRun: '1h ago', permissions: ['media:write', 'brand:read'] },
  { id: 'weekly_analyst', number: 19, name: 'Weekly Analyst', role: 'Executive Digests', category: 'Growth', description: 'Compiles Sunday performance reports and strategic next steps.', enabled: true, status: 'idle', tasksCompleted: 24, successRate: 100.0, model: 'Gemini 2.5 Pro', lastRun: '2d ago', permissions: ['analytics:read', 'reports:write'] },
  { id: 'recovery_agent', number: 20, name: 'Recovery Agent', role: 'Self-Healing & Retries', category: 'Infrastructure', description: 'Recovers stalled jobs and reconciles schedules after restarts.', enabled: true, status: 'active', tasksCompleted: 64, successRate: 98.4, model: 'Runtime Core', lastRun: '12m ago', permissions: ['jobs:recover', 'logs:read'] },
  { id: 'plugin_trust', number: 21, name: 'Plugin Trust', role: 'Skill Signature & Audit', category: 'Security', description: 'Verifies hashes, manifests, and capability scopes for skills.', enabled: true, status: 'active', tasksCompleted: 91, successRate: 100.0, model: 'Trust Verifier', lastRun: '33m ago', permissions: ['skills:audit', 'sandbox:policy'] },
  { id: 'security_guardian', number: 22, name: 'Security Guardian', role: 'Egress & Intrusion Shield', category: 'Security', description: 'Monitors privacy firewall rules, device pairing, and anomaly alerts.', enabled: true, status: 'active', tasksCompleted: 530, successRate: 100.0, model: 'Firewall Core', lastRun: '15s ago', permissions: ['security:admin', 'sessions:revoke'] },
  { id: 'goal_persistence', number: 23, name: 'Goal Persistence', role: 'Milestone Orchestration', category: 'Growth', description: 'Breaks long-term KPIs into daily agent tasks and verifies drift.', enabled: true, status: 'active', tasksCompleted: 157, successRate: 97.9, model: 'Gemini 2.5 Pro', lastRun: '19m ago', permissions: ['goals:write', 'tasks:dispatch'] },
  { id: 'workflow_automation', number: 24, name: 'Workflow Automation', role: 'DAG Execution Engine', category: 'Operations', description: 'Executes visual node workflows triggered by folders or cron.', enabled: true, status: 'running', tasksCompleted: 304, successRate: 98.6, model: 'DAG Runner', lastRun: 'Running now', permissions: ['workflows:exec', 'triggers:listen'] },
  { id: 'reporting_agent', number: 25, name: 'Reporting Agent', role: 'CSV / PDF Exports', category: 'Operations', description: 'Packages client and creator analytics exports on demand.', enabled: false, status: 'disabled', tasksCompleted: 41, successRate: 97.5, model: 'Local Worker', lastRun: '5d ago', permissions: ['analytics:read', 'files:export'] },
  { id: 'release_agent', number: 26, name: 'Release Agent', role: 'Signed App Updates', category: 'Infrastructure', description: 'Checks GitHub releases and verifies signed Windows installers.', enabled: true, status: 'idle', tasksCompleted: 19, successRate: 100.0, model: 'Updater Core', lastRun: '6h ago', permissions: ['github:read', 'updates:verify'] },
  { id: 'device_sync_agent', number: 27, name: 'Device Sync Agent', role: 'Desktop & Android Sync', category: 'Infrastructure', description: 'Keeps paired Windows and Android companion clients synchronized.', enabled: true, status: 'active', tasksCompleted: 267, successRate: 99.2, model: 'Sync Mesh', lastRun: '3m ago', permissions: ['devices:sync', 'state:push'] },
  { id: 'ux_assistant', number: 28, name: 'UX Assistant', role: 'Contextual Onboarding Help', category: 'Operations', description: 'Guides configuration steps and explains system diagnostics clearly.', enabled: true, status: 'idle', tasksCompleted: 74, successRate: 98.6, model: 'Llama 3.2 8B', lastRun: '45m ago', permissions: ['ui:assist', 'docs:read'] },
  { id: 'compliance_agent', number: 29, name: 'Compliance Agent', role: 'Disclosure & Platform Rules', category: 'Security', description: 'Checks sponsored tags, copyright safety, and AI disclosure rules.', enabled: true, status: 'active', tasksCompleted: 149, successRate: 99.3, model: 'Policy Engine', lastRun: '8m ago', permissions: ['content:audit', 'compliance:tag'] },
];

interface AgentStoreState {
  agents: AgentItem[];
  toggleAgent: (id: string) => void;
  setAgentStatus: (id: string, status: AgentStatus) => void;
  emergencyStopAll: () => void;
  enableCoreAgents: () => void;
}

export const useAgentStore = create<AgentStoreState>((set) => ({
  agents: INITIAL_AGENTS,
  toggleAgent: (id) =>
    set((state) => ({
      agents: state.agents.map((a) =>
        a.id === id
          ? {
              ...a,
              enabled: !a.enabled,
              status: !a.enabled ? 'active' : 'disabled',
            }
          : a
      ),
    })),
  setAgentStatus: (id, status) =>
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, status } : a)),
    })),
  emergencyStopAll: () =>
    set((state) => ({
      agents: state.agents.map((a) => ({
        ...a,
        enabled: false,
        status: 'disabled',
      })),
    })),
  enableCoreAgents: () =>
    set((state) => ({
      agents: state.agents.map((a) => ({
        ...a,
        enabled: true,
        status: a.number <= 15 ? 'active' : 'idle',
      })),
    })),
}));
