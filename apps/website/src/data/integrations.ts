export type IntegrationStatus = 'Supported' | 'Beta' | 'Planned' | 'Unavailable';

export interface IntegrationItem {
  id: string;
  name: string;
  category: 'AI Providers' | 'Social Platforms' | 'Messaging & Dev' | 'Voice & Local Media';
  status: IntegrationStatus;
  authMethod: string;
  costModel: string;
  summary: string;
  capabilities: string[];
  limitations: string;
}

export const INTEGRATIONS: IntegrationItem[] = [
  {
    id: 'ollama',
    name: 'Ollama (Local AI)',
    category: 'AI Providers',
    status: 'Supported',
    authMethod: 'Localhost HTTP (127.0.0.1:11434)',
    costModel: '$0 — Runs 100% on your PC',
    summary:
      'Primary zero-cost local inference engine with automatic RAM-aware model sizing for 8GB, 16GB, and 32GB+ Windows systems.',
    capabilities: [
      'Offline caption drafting, summaries, and agent reasoning',
      'Automatic model unloading on 8GB RAM machines via Resource Optimizer',
      'Zero external data egress under Privacy Firewall Strict mode',
    ],
    limitations: 'Requires local Ollama installation; inference speed depends on CPU/GPU.',
  },
  {
    id: 'gemini',
    name: 'Google Gemini (Developer API)',
    category: 'AI Providers',
    status: 'Supported',
    authMethod: 'User-supplied API Key (OS Keystore encrypted)',
    costModel: 'Google AI Studio Free Tier / User Key',
    summary:
      'Optional cloud reasoning fallback routed through the Privacy Firewall so only sanitized non-sensitive prompts leave your machine.',
    capabilities: [
      'Optional escalation for complex multi-step planning or long-context synthesis',
      'Privacy Firewall strips tokens, local file paths, and private PII before egress',
      'Budget Guardian tracks daily requests to avoid surprise quota limits',
    ],
    limitations: 'Requires your own API key and internet connection; subject to Google API terms.',
  },
  {
    id: 'telegram',
    name: 'Telegram Bot',
    category: 'Messaging & Dev',
    status: 'Supported',
    authMethod: 'Bot Token + Allowlisted Owner Chat ID',
    costModel: '$0 — Official Telegram Bot API',
    summary:
      'Remote command center and mobile approval inbox to approve drafts, pause workflows, or trigger Emergency Stop from anywhere.',
    capabilities: [
      'Interactive Approve / Edit / Reject / Pause notifications',
      'Strict owner Chat ID allowlist rejects unknown senders',
      'Supports text and voice-note command forwarding',
    ],
    limitations: 'Requires creating a free bot via @BotFather and supplying your Chat ID.',
  },
  {
    id: 'github',
    name: 'GitHub',
    category: 'Messaging & Dev',
    status: 'Supported',
    authMethod: 'Personal Access Token / Public API',
    costModel: '$0 — GitHub API',
    summary:
      'Checks official Javo Agents releases with SHA-256 verification and syncs auditable skill manifests.',
    capabilities: [
      'Release version checks and SHA-256 verification prompts',
      'Read-only skill repository inspection via Plugin Trust',
      'Developer workflow triggers for repo release announcements',
    ],
    limitations: 'Skill execution always remains sandboxed and requires local approval.',
  },
  {
    id: 'whisper-piper',
    name: 'whisper.cpp + Piper TTS',
    category: 'Voice & Local Media',
    status: 'Supported',
    authMethod: 'Local Binary / Offline Models',
    costModel: '$0 — Local CPU Inference',
    summary:
      'Local speech-to-text and neural text-to-speech powering "Javo" wake-word commands in English, Hindi, and Hinglish.',
    capabilities: [
      '100% offline transcription with no third-party audio upload',
      'Push-to-talk and wake-word mode on Windows and Android companion',
      'Automatic model unload when idle to preserve 8GB RAM headroom',
    ],
    limitations: 'Large Whisper models need more RAM; small/base quantized models are recommended for 8GB PCs.',
  },
  {
    id: 'youtube',
    name: 'YouTube Data API v3',
    category: 'Social Platforms',
    status: 'Beta',
    authMethod: 'OAuth 2.0 (User Google Cloud Project)',
    costModel: 'YouTube Data API Free Daily Quota',
    summary:
      'Supports scheduled video metadata/uploads after approval, comment fetching, and verified channel analytics snapshots.',
    capabilities: [
      'Draft video title, description, tags, and upload queue after approval',
      'Comment triage and approved reply posting',
      'Channel statistics sync into Weekly Analyst',
    ],
    limitations: 'Beta: requires configuring your own Google Cloud OAuth consent screen for unverified personal projects.',
  },
  {
    id: 'facebook-pages',
    name: 'Facebook Pages (Meta Graph API)',
    category: 'Social Platforms',
    status: 'Beta',
    authMethod: 'Meta OAuth 2.0 Page Access Token',
    costModel: 'Meta Graph API (App Review required for public apps)',
    summary:
      'Connects managed Facebook Pages for approved post publishing, scheduling, and Page comment moderation.',
    capabilities: [
      'Publish approved text, image, and video posts to managed Pages',
      'Read Page post comments for Community Manager drafting',
      'Account Guardian rate-limit protection',
    ],
    limitations: 'Beta: personal profiles are not supported by Meta API; requires a managed Facebook Page and Meta Developer App.',
  },
  {
    id: 'instagram-pro',
    name: 'Instagram Professional (Graph API)',
    category: 'Social Platforms',
    status: 'Beta',
    authMethod: 'Meta OAuth 2.0 (Business/Creator Account linked to Page)',
    costModel: 'Instagram Graph API',
    summary:
      'Supports Reels/image publishing workflows and comment triage for Instagram Business or Creator accounts.',
    capabilities: [
      'Publish approved media containers to Instagram Professional accounts',
      'Fetch basic media insights and recent comments',
      'Supervised Autopilot approval gate before every post',
    ],
    limitations: 'Beta: personal Instagram accounts are unsupported by Meta Graph API; public media URLs or container upload rules apply.',
  },
  {
    id: 'linkedin',
    name: 'LinkedIn Pages & Profile',
    category: 'Social Platforms',
    status: 'Planned',
    authMethod: 'OAuth 2.0 (Planned)',
    costModel: 'LinkedIn API',
    summary:
      'Planned connector for long-form posts, document carousels, and B2B creator scheduling.',
    capabilities: [
      'Draft generation is already supported offline via Content Factory',
      'Native OAuth publishing adapter scheduled for v0.2+',
    ],
    limitations: 'Not yet wired in v0.1.0-alpha; copy-export from Content Library works today.',
  },
  {
    id: 'x-twitter',
    name: 'X (Twitter) API',
    category: 'Social Platforms',
    status: 'Unavailable',
    authMethod: 'OAuth 2.0 (Paid API tier required by X)',
    costModel: 'Restricted by X API pricing',
    summary:
      'Marked Unavailable in the zero-cost baseline because X restricts automated posting and read quotas behind paid API tiers.',
    capabilities: [
      'Thread and post drafts can still be generated locally and exported manually',
    ],
    limitations: 'No active automated connector in v0.1.0-alpha due to third-party API paywalls.',
  },
  {
    id: 'tiktok',
    name: 'TikTok Content Posting API',
    category: 'Social Platforms',
    status: 'Planned',
    authMethod: 'OAuth 2.0 (Planned)',
    costModel: 'TikTok Developer API',
    summary:
      'Planned vertical-video draft handoff and publishing adapter pending regional availability and app audit.',
    capabilities: [
      'Vertical short-form scripts and hooks can be generated locally today',
    ],
    limitations: 'Direct API publishing is not active in v0.1.0-alpha.',
  },
];
