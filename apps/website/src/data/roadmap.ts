export interface RoadmapStage {
  phase: string;
  horizon: string;
  status: 'In Progress (Current)' | 'Near-Term' | 'Planned' | 'Future Exploration';
  description: string;
  items: string[];
}

export const ROADMAP_STAGES: RoadmapStage[] = [
  {
    phase: 'v0.1.0-alpha — Local-First Foundation',
    horizon: 'Current Release',
    status: 'In Progress (Current)',
    description:
      'Core Windows Local Runtime, 29 specialist agents, visual 16-node workflows, Android LAN companion, and honest Beta social connectors.',
    items: [
      'Zero-cost local operation via Ollama + whisper.cpp + Piper TTS',
      'Supervised Autopilot Approval Inbox across Desktop, Android, and Telegram',
      '8GB RAM Resource Optimizer & Privacy Firewall egress controls',
      'Signed/checksummed Windows NSIS installer packaging pipeline',
    ],
  },
  {
    phase: 'v0.2 — Hardened Connectors & Packaging',
    horizon: 'Near-Term',
    status: 'Near-Term',
    description:
      'Streamlined one-click installer, richer media previews, and expanded OAuth onboarding diagnostics.',
    items: [
      'One-click Windows installer with bundled Ollama & whisper.cpp detection',
      'Direct Android APK sideload & Google Play Store internal testing track',
      'Expanded YouTube Shorts & Instagram Reels container status polling',
      'Automated encrypted backup scheduling to local external drives',
    ],
  },
  {
    phase: 'v0.3 — Multi-Channel & Community Workflows',
    horizon: 'Planned',
    status: 'Planned',
    description:
      'Additional platform connectors, shared workflow templates, and deeper multilingual voice tuning.',
    items: [
      'LinkedIn Pages & Profile OAuth publishing adapter',
      'TikTok Content Posting API evaluation & adapter',
      'Shareable signed workflow templates with Plugin Trust verification',
      'Improved regional Hindi/Hinglish acoustic tuning for noisy rooms',
    ],
  },
  {
    phase: 'Future — Optional Cloud Sync & Team Editions',
    horizon: 'Future Exploration',
    status: 'Future Exploration',
    description:
      'Optional end-to-end encrypted relay and multi-seat collaboration for studios that want remote sync without abandoning local-first control.',
    items: [
      'Optional E2EE relay for Windows ↔ Android sync outside home Wi-Fi',
      'Multi-brand studio workspaces with role-based approval policies',
      'Enterprise audit export & managed compliance packs (clearly optional; core stays MIT free)',
    ],
  },
];
