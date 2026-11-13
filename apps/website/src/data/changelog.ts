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
    version: '0.1.1-alpha',
    date: '2026-11-13',
    status: 'Alpha / Source Available',
    summary:
      'Complete Android Real Functionality Rebuild based on physical device audit. Purged demonstration data from production UI, added isolated opt-in Demo Mode, native Android SpeechRecognizer with Hindi/Hinglish/English support, conversational Gemini Direct API routing, full-lifecycle Content Studio, and repaired Windows pairing contract.',
    highlights: [
      {
        area: 'Truthful Mobile Baseline & Safe Migration',
        details: [
          'Fresh install baseline verified: 0 tasks, 0 approvals, 0 drafts, 0 connected accounts, 0 active executions',
          'Safe one-time migration purges legacy hardcoded sample IDs while preserving all real user data',
          'Opt-in Isolated Demo Mode in Settings with load and clear controls',
          'Truthful Home Dashboard waveform: idle when idle, executing only during real background task execution',
        ],
      },
      {
        area: 'Native Speech Recognition & Direct AI Routing',
        details: [
          'Integrated native Android SpeechRecognizer supporting Hindi, Hinglish, and English with live RMS volume waveform reactivity',
          'Real-time partial and final transcript streaming with zero prompt substitution',
          'Direct Google Gemini API fallback when configured in Keystore without requiring active Windows connection',
          'Honest unconfigured provider guidance for general conversational queries',
        ],
      },
      {
        area: 'Content Studio & Approval Inbox',
        details: [
          'Full-lifecycle draft management: Create, Edit, Delete, Platform filter, Search, and Sync',
          'Rebuilt Approval Inbox with Pending vs Decided tabs and immutable status pills on decided items',
        ],
      },
      {
        area: 'Windows Pairing & API Alignment',
        details: [
          'Unauthenticated pairing challenge confirmation allows new mobile devices to exchange 6-digit codes for device-bound tokens',
          'Aligned Retrofit and FastAPI request/response schemas for pairing and delta sync',
        ],
      },
    ],
  },
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
