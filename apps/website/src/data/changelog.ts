export interface ChangelogEntry {
  version: string;
  date: string;
  status: 'Alpha / Source Available' | 'Preview';
  summary: string;
  highlights: {
    area: string;
    details: string[];
  }[];
}

export const CHANGELOG_ENTRIES: ChangelogEntry[] = [
  {
    version: '0.1.0-alpha',
    date: '2026-11-12',
    status: 'Alpha / Source Available',
    summary:
      'Initial public source-available milestone establishing the local-first monorepo, 29-agent orchestration framework, Windows desktop runtime, Android companion app, and official website.',
    highlights: [
      {
        area: 'Local Runtime & 29 Specialist Agents',
        details: [
          'FastAPI local runtime with SQLite persistence, APScheduler job reconciliation, and WebSocket live events',
          'Master Orchestrator + 29 specialist agent modules with explicit permission scopes and retry/cost budgets',
          'AI Router supporting local Ollama (with 8GB RAM sequential scheduling) and optional Gemini fallback',
          'Privacy Firewall data classification and secret redaction prior to external requests',
        ],
      },
      {
        area: 'Desktop Dashboard & Workflows',
        details: [
          'Midnight Navy dark-first React + TypeScript dashboard with light mode toggle and 12-step setup wizard',
          '16-node visual workflow builder with Folder Watcher, Condition, Approval, Delay, Retry, and Publish nodes',
          'Supervised Autopilot Approval Inbox and global Emergency Stop control',
        ],
      },
      {
        area: 'Android Companion & Voice Mode',
        details: [
          'Jetpack Compose Android companion with Keystore AES-GCM token protection, Room offline cache, and QR LAN pairing',
          'Cyan-violet waveform visualizer with Idle, Listening, Thinking, Executing, and Finished states',
          'Local whisper.cpp + Piper TTS voice pipeline supporting English, Hindi, and Hinglish commands',
        ],
      },
      {
        area: 'Integrations & Security',
        details: [
          'Supported: Ollama, Google Gemini Developer API, Telegram Bot, GitHub, whisper.cpp + Piper TTS',
          'Beta: YouTube Data API v3, Facebook Pages Graph API, Instagram Professional Graph API',
          'AST-checked Python skill sandbox and Plugin Trust verification scoring',
        ],
      },
    ],
  },
];
