export type AgentCategory =
  | 'Strategy & Analytics'
  | 'Content & Brand'
  | 'Publishing & Community'
  | 'Operations & Infrastructure'
  | 'Security & Governance';

export interface AgentSpec {
  id: string;
  number: string;
  name: string;
  role: string;
  category: AgentCategory;
  summary: string;
  responsibilities: string[];
  permissions: string[];
  ramProfile: 'Lightweight (<150MB)' | 'Standard (Model Shared)' | 'On-Demand Load';
  defaultMode: 'Supervised' | 'Autonomous (Read-Only)' | 'Approval Required';
}

export const MASTER_ORCHESTRATOR: AgentSpec = {
  id: 'orchestrator',
  number: '00',
  name: 'Master Orchestrator',
  role: 'Central Task Decomposer & Coordinator',
  category: 'Operations & Infrastructure',
  summary:
    'Breaks down high-level creator goals into scoped tasks, routes work across the 29 specialists, enforces retry/cost budgets, and pauses for human approval before external actions.',
  responsibilities: [
    'Decomposes goals into DAG tasks with explicit resource & retry budgets',
    'Selects specialist agents and manages inter-agent handoffs',
    'Coordinates Supervised Autopilot checkpoints via Approval Manager',
    'Triggers fallback recovery paths when local models or APIs time out',
  ],
  permissions: ['task:orchestrate', 'agent:dispatch', 'audit:write'],
  ramProfile: 'Lightweight (<150MB)',
  defaultMode: 'Supervised',
};

export const SPECIALIST_AGENTS: AgentSpec[] = [
  {
    id: 'growth-scientist',
    number: '01',
    name: 'Growth Scientist',
    role: 'Experimentation & Retention Strategist',
    category: 'Strategy & Analytics',
    summary:
      'Designs structured A/B hooks, posting cadence hypotheses, and audience retention experiments grounded in verified platform analytics.',
    responsibilities: [
      'Formulates testable growth hypotheses without fabricating metrics',
      'Evaluates hook retention and watch-time patterns across channels',
      'Recommends schedule adjustments based on real historical snapshots',
    ],
    permissions: ['analytics:read', 'experiments:propose'],
    ramProfile: 'Standard (Model Shared)',
    defaultMode: 'Autonomous (Read-Only)',
  },
  {
    id: 'content-factory',
    number: '02',
    name: 'Content Factory',
    role: 'Multi-Format Draft Generator',
    category: 'Content & Brand',
    summary:
      'Transforms raw media inside your watched content folders into captions, scripts, threads, descriptions, and metadata drafts.',
    responsibilities: [
      'Watches local Content Folders for new video, audio, and image assets',
      'Generates platform-tailored captions, hashtags, and video descriptions',
      'Queues drafts for Brand Studio & Quality Inspector review',
    ],
    permissions: ['content:read', 'drafts:write'],
    ramProfile: 'Standard (Model Shared)',
    defaultMode: 'Supervised',
  },
  {
    id: 'smart-memory',
    number: '03',
    name: 'Smart Memory',
    role: 'Local Encrypted Context & Preference Vault',
    category: 'Operations & Infrastructure',
    summary:
      'Stores creator voice preferences, recurring instructions, and brand facts inside your local encrypted SQLite database.',
    responsibilities: [
      'Indexes user instructions and brand style preferences locally',
      'Retrieves relevant context while stripping sensitive credentials',
      'Allows one-click inspection, export, or deletion of any memory entry',
    ],
    permissions: ['memory:read', 'memory:write'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'self-upgrading-engineer',
    number: '04',
    name: 'Self-Upgrading Engineer',
    role: 'Sandboxed Skill & Prompt Maintainer',
    category: 'Operations & Infrastructure',
    summary:
      'Maintains deterministic skill scripts and prompt templates inside an AST-checked sandbox—never modifying core runtime or bypassing trust gates.',
    responsibilities: [
      'Validates skill manifests and runs local unit tests before activation',
      'Proposes prompt refinements when Quality Inspector flags drift',
      'Requires explicit user approval and Plugin Trust sign-off',
    ],
    permissions: ['skills:propose', 'sandbox:test'],
    ramProfile: 'On-Demand Load',
    defaultMode: 'Approval Required',
  },
  {
    id: 'telegram-agent',
    number: '05',
    name: 'Telegram Agent',
    role: 'Mobile Command & Approval Bridge',
    category: 'Publishing & Community',
    summary:
      'Delivers approval cards, alerts, and daily summaries to your private Telegram bot so you can approve or pause tasks on the go.',
    responsibilities: [
      'Sends formatted approval requests with Approve / Reject / Pause buttons',
      'Validates sender chat ID against allowlisted owner IDs',
      'Forwards voice or text commands to the Master Orchestrator',
    ],
    permissions: ['telegram:send', 'telegram:receive_allowlisted'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'brand-manager',
    number: '06',
    name: 'Brand Manager',
    role: 'Tone, Audience & Guardrail Keeper',
    category: 'Content & Brand',
    summary:
      'Maintains brand voice consistency, banned-phrase guardrails, and language style (English, Hindi, Hinglish) across all outputs.',
    responsibilities: [
      'Enforces creator tone guidelines and prohibited claim rules',
      'Aligns messaging with target audience personas per channel',
      'Flags off-brand drafts before they enter the approval queue',
    ],
    permissions: ['brand:read', 'drafts:review'],
    ramProfile: 'Standard (Model Shared)',
    defaultMode: 'Autonomous (Read-Only)',
  },
  {
    id: 'voice-agent',
    number: '07',
    name: 'Voice Agent',
    role: 'Wake-Word & Multilingual Speech Specialist',
    category: 'Operations & Infrastructure',
    summary:
      'Processes "Javo" wake-word sessions in Hindi, Hinglish, and English using local whisper.cpp STT and Piper TTS.',
    responsibilities: [
      'Runs local speech-to-text via whisper.cpp with zero cloud audio upload',
      'Parses mixed Hindi/Hinglish/English creator commands into structured intents',
      'Synthesizes concise spoken confirmations via Piper TTS',
    ],
    permissions: ['audio:local_process', 'intent:dispatch'],
    ramProfile: 'On-Demand Load',
    defaultMode: 'Supervised',
  },
  {
    id: 'api-integration',
    number: '08',
    name: 'API Integration',
    role: 'Connector Health & OAuth Broker',
    category: 'Operations & Infrastructure',
    summary:
      'Manages official OAuth tokens, rate-limit backoff, and connector health checks for YouTube, Meta Graph API, Telegram, and GitHub.',
    responsibilities: [
      'Refreshes OAuth tokens stored via OS-encrypted credential storage',
      'Monitors API quota headers and applies exponential backoff',
      'Reports real connector availability without mocking disconnected APIs',
    ],
    permissions: ['connectors:status', 'oauth:refresh'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'content-publisher',
    number: '09',
    name: 'Content Publisher',
    role: 'Approved Queue Execution Agent',
    category: 'Publishing & Community',
    summary:
      'Executes scheduled publishing jobs exclusively for items that have passed Supervised Autopilot approval.',
    responsibilities: [
      'Publishes approved posts/videos to YouTube, Facebook Pages, or Instagram',
      'Verifies approval signature and schedule window prior to upload',
      'Records immutable publish receipts and external post IDs',
    ],
    permissions: ['publish:execute_approved', 'audit:write'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Approval Required',
  },
  {
    id: 'community-manager',
    number: '10',
    name: 'Community Manager',
    role: 'Comment Triage & Reply Drafter',
    category: 'Publishing & Community',
    summary:
      'Categorizes incoming comments/questions and drafts helpful replies in your brand voice for one-click approval.',
    responsibilities: [
      'Classifies audience comments into questions, feedback, spam, or priority',
      'Drafts contextual replies in English, Hindi, or Hinglish',
      'Routes replies through Approval Manager unless auto-rule is explicitly enabled',
    ],
    permissions: ['comments:read', 'replies:draft'],
    ramProfile: 'Standard (Model Shared)',
    defaultMode: 'Approval Required',
  },
  {
    id: 'account-guardian',
    number: '11',
    name: 'Account Guardian',
    role: 'Rate-Limit & Platform Policy Protector',
    category: 'Security & Governance',
    summary:
      'Protects connected social accounts from spam-like bursts, duplicate posting, or sudden API quota violations.',
    responsibilities: [
      'Enforces cooldown intervals and daily publish caps per social account',
      'Detects duplicate media hashes or repeated caption patterns',
      'Pauses queue automatically if platform APIs return warning codes',
    ],
    permissions: ['accounts:protect', 'queue:pause'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'resource-optimizer',
    number: '12',
    name: 'Resource Optimizer',
    role: '8GB RAM & CPU/GPU Scheduler',
    category: 'Operations & Infrastructure',
    summary:
      'Monitors Windows RAM/VRAM pressure and dynamically swaps or unloads Ollama and whisper.cpp models so 8GB machines stay responsive.',
    responsibilities: [
      'Enforces sequential heavy-model execution on 8GB RAM systems',
      'Selects quantized model tiers based on live free memory',
      'Throttles background indexing when foreground apps need CPU',
    ],
    permissions: ['system:metrics_read', 'models:manage_local'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'quality-inspector',
    number: '13',
    name: 'Quality Inspector',
    role: 'Accuracy, Formatting & Hallucination Checker',
    category: 'Content & Brand',
    summary:
      'Audits generated captions, scripts, and summaries for broken links, placeholder text, factual drift, and length constraints.',
    responsibilities: [
      'Rejects drafts containing unverified claims, placeholders, or truncation',
      'Checks character limits and aspect/metadata requirements per platform',
      'Scores draft readiness before surfacing to the Approval Inbox',
    ],
    permissions: ['drafts:read', 'quality:score'],
    ramProfile: 'Standard (Model Shared)',
    defaultMode: 'Autonomous (Read-Only)',
  },
  {
    id: 'niche-radar',
    number: '14',
    name: 'Niche Radar',
    role: 'Topic & Trend Signal Analyst',
    category: 'Strategy & Analytics',
    summary:
      'Tracks creator-configured topic feeds and search signals to surface timely content angles aligned with your niche.',
    responsibilities: [
      'Monitors user-selected RSS, YouTube channel, or keyword topics',
      'Produces weekly topic briefs with source citations',
      'Respects Privacy Firewall rules on all outbound fetches',
    ],
    permissions: ['trends:read_configured', 'briefs:write'],
    ramProfile: 'Standard (Model Shared)',
    defaultMode: 'Autonomous (Read-Only)',
  },
  {
    id: 'approval-manager',
    number: '15',
    name: 'Approval Manager',
    role: 'Human-in-the-Loop Gatekeeper',
    category: 'Security & Governance',
    summary:
      'Owns the Approval Inbox across Desktop, Android, and Telegram—ensuring no irreversible action runs without explicit human consent.',
    responsibilities: [
      'Holds drafts, replies, and workflow side-effects in pending state',
      'Supports Approve, Edit, Reject, and Reschedule actions with audit stamps',
      'Enforces instant halt when Emergency Stop is triggered',
    ],
    permissions: ['approvals:manage', 'audit:write'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Approval Required',
  },
  {
    id: 'budget-guardian',
    number: '16',
    name: 'Budget Guardian',
    role: 'Zero-Cost & Cloud Quota Controller',
    category: 'Security & Governance',
    summary:
      'Tracks token and API usage across local Ollama and optional Gemini Developer API keys to prevent unexpected quota exhaustion or paid overruns.',
    responsibilities: [
      'Enforces daily token and request budgets per provider',
      'Automatically routes routine jobs to zero-cost local Ollama models',
      'Alerts user before optional external API free-tier limits are reached',
    ],
    permissions: ['ai_router:budget_enforce', 'usage:read'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'content-recycler',
    number: '17',
    name: 'Content Recycler',
    role: 'Evergreen Repurposing Specialist',
    category: 'Content & Brand',
    summary:
      'Identifies high-performing past assets in your local library and proposes fresh shorts hooks, carousels, or recap posts.',
    responsibilities: [
      'Scans local Content Library for evergreen pieces eligible for remixing',
      'Generates fresh cross-platform angles without repeating identical copy',
      'Queues repurposed suggestions into the Approval Inbox',
    ],
    permissions: ['content:read', 'drafts:write'],
    ramProfile: 'Standard (Model Shared)',
    defaultMode: 'Supervised',
  },
  {
    id: 'brand-studio',
    number: '18',
    name: 'Brand Studio',
    role: 'Visual Metadata & Thumbnail Brief Designer',
    category: 'Content & Brand',
    summary:
      'Prepares structured thumbnail text concepts, color/typography specs, and visual crop metadata aligned with your Brand Profile.',
    responsibilities: [
      'Creates concise thumbnail headline options and layout briefs',
      'Validates aspect ratios and visual asset completeness before scheduling',
      'Maintains consistent Midnight Navy / brand palette presets',
    ],
    permissions: ['brand:read', 'media_meta:write'],
    ramProfile: 'Standard (Model Shared)',
    defaultMode: 'Supervised',
  },
  {
    id: 'weekly-analyst',
    number: '19',
    name: 'Weekly Analyst',
    role: 'Performance Digest Compiler',
    category: 'Strategy & Analytics',
    summary:
      'Generates weekly Markdown & dashboard performance summaries from verified local snapshots—explicitly marking missing platform data as unavailable.',
    responsibilities: [
      'Compiles weekly views, publishing consistency, and approval turnaround',
      'Never interpolates or invents analytics when an account is disconnected',
      'Delivers digest to Dashboard and optional Telegram summary',
    ],
    permissions: ['analytics:read', 'reports:write'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Autonomous (Read-Only)',
  },
  {
    id: 'recovery-agent',
    number: '20',
    name: 'Recovery Agent',
    role: 'Failure Diagnosis & Job Reconciler',
    category: 'Operations & Infrastructure',
    summary:
      'Reconciles interrupted APScheduler jobs after a PC restart, diagnoses failed connector calls, and safely retries idempotent steps.',
    responsibilities: [
      'Detects missed schedule windows on startup and flags stale posts safely',
      'Avoids duplicate publishing by checking idempotency keys first',
      'Provides human-readable root cause explanations in Notifications',
    ],
    permissions: ['scheduler:reconcile', 'tasks:recover'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'plugin-trust',
    number: '21',
    name: 'Plugin Trust',
    role: 'Skill Manifest & Sandbox Auditor',
    category: 'Security & Governance',
    summary:
      'Computes trust scores for local skills, checks AST imports against allowlists, and blocks untrusted network or credential access.',
    responsibilities: [
      'Inspects skill manifests and Python ASTs before execution',
      'Strips secrets from subprocess environment variables',
      'Quarantines skills requesting undeclared filesystem or network scopes',
    ],
    permissions: ['skills:audit', 'sandbox:enforce'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'security-guardian',
    number: '22',
    name: 'Security Guardian',
    role: 'Privacy Firewall & Device Auth Enforcer',
    category: 'Security & Governance',
    summary:
      'Enforces Privacy Firewall egress rules, audits paired Android device sessions, and executes system-wide Emergency Stop.',
    responsibilities: [
      'Blocks classified private data from leaving to external AI providers',
      'Manages paired Android device tokens and one-click session revocation',
      'Halts all active queues and agent runs on Emergency Stop',
    ],
    permissions: ['firewall:enforce', 'devices:revoke', 'system:emergency_stop'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'goal-persistence',
    number: '23',
    name: 'Goal Persistence',
    role: 'Long-Horizon Milestone Tracker',
    category: 'Strategy & Analytics',
    summary:
      'Tracks multi-week creator goals, milestone completion states, and cadence targets across restarts without losing context.',
    responsibilities: [
      'Maintains goal-to-task lineage inside SQLite',
      'Alerts when milestones drift behind target schedule',
      'Adjusts weekly task plans with user confirmation',
    ],
    permissions: ['goals:read', 'goals:update'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'workflow-automation',
    number: '24',
    name: 'Workflow Automation',
    role: 'Visual DAG Runner & Trigger Engine',
    category: 'Operations & Infrastructure',
    summary:
      'Executes visual 16-node workflows triggered by schedules, folder watchers, or manual runs with per-node audit logging.',
    responsibilities: [
      'Validates workflow DAGs for cycles, missing approvals, and timeouts',
      'Executes Folder Watcher, Condition, Delay, Retry, and Publish nodes',
      'Pauses execution cleanly at Approval nodes until human sign-off',
    ],
    permissions: ['workflows:execute', 'audit:write'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'reporting-agent',
    number: '25',
    name: 'Reporting Agent',
    role: 'Audit Export & Transparency Reporter',
    category: 'Strategy & Analytics',
    summary:
      'Generates exportable JSON/Markdown audit trails, AI provider usage breakdowns, and backup verification reports.',
    responsibilities: [
      'Exports local audit logs and task histories on demand',
      'Summarizes local vs cloud AI routing percentages',
      'Verifies encrypted backup archive integrity',
    ],
    permissions: ['audit:read', 'exports:write'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Autonomous (Read-Only)',
  },
  {
    id: 'release-agent',
    number: '26',
    name: 'Release Agent',
    role: 'Local Update & Integrity Verifier',
    category: 'Operations & Infrastructure',
    summary:
      'Checks official GitHub release metadata and verifies SHA-256 checksums for optional app updates—never auto-downloading unverified binaries.',
    responsibilities: [
      'Compares installed version against signed/checksummed GitHub releases',
      'Verifies SHA-256 hashes before prompting user to update',
      'Preserves user database backups prior to version upgrades',
    ],
    permissions: ['updates:check', 'checksum:verify'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Approval Required',
  },
  {
    id: 'device-sync-agent',
    number: '27',
    name: 'Device Sync Agent',
    role: 'Windows ↔ Android Encrypted Sync',
    category: 'Operations & Infrastructure',
    summary:
      'Synchronizes tasks, offline drafts, approval queues, and notifications between your Windows runtime and paired Android device over LAN.',
    responsibilities: [
      'Issues short-lived QR pairing tokens with mutual auth verification',
      'Reconciles offline Android drafts when back on local network',
      'Respects battery and background sync constraints on Android',
    ],
    permissions: ['devices:sync', 'pairing:verify'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
  {
    id: 'ux-assistant',
    number: '28',
    name: 'UX Assistant',
    role: 'Onboarding & Diagnostic Helper',
    category: 'Operations & Infrastructure',
    summary:
      'Guides first-time Windows/Ollama setup, translates technical connector errors into clear next steps, and supports Hinglish help queries.',
    responsibilities: [
      'Assists with 12-step local setup wizard and hardware checks',
      'Explains OAuth, port, or Ollama model issues in plain language',
      'Links directly to relevant local troubleshooting steps',
    ],
    permissions: ['diagnostics:read', 'help:respond'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Autonomous (Read-Only)',
  },
  {
    id: 'compliance-agent',
    number: '29',
    name: 'Compliance Agent',
    role: 'Disclosure, Licensing & Platform Rules Checker',
    category: 'Security & Governance',
    summary:
      'Audits outgoing drafts and workflow templates against platform terms, AI disclosure needs, and open-source model license constraints.',
    responsibilities: [
      'Checks whether AI-generated media requires platform disclosure flags',
      'Validates local model licenses and blocks deceptive automation patterns',
      'Prevents bulk spam or unapproved automated engagement behaviors',
    ],
    permissions: ['compliance:audit', 'publish:veto'],
    ramProfile: 'Lightweight (<150MB)',
    defaultMode: 'Supervised',
  },
];

export const AGENT_CATEGORIES: AgentCategory[] = [
  'Strategy & Analytics',
  'Content & Brand',
  'Publishing & Community',
  'Operations & Infrastructure',
  'Security & Governance',
];
