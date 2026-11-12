export interface DocSection {
  id: string;
  title: string;
  category: 'Getting Started' | 'AI & Voice' | 'Channels & Content' | 'Security & Operations';
  summary: string;
  steps: string[];
  codeSnippet?: {
    label: string;
    code: string;
  };
  notes: string[];
}

export const DOC_SECTIONS: DocSection[] = [
  {
    id: 'installation',
    title: 'Installation (Windows & Android)',
    category: 'Getting Started',
    summary:
      'Install the Windows Local Runtime, React Dashboard, and optional Android Companion app with zero cloud lock-in.',
    steps: [
      'Verify Windows 10/11 (64-bit) with at least 8 GB RAM and 10 GB free storage.',
      'Install Python 3.11+, Node.js 20+, and Ollama on Windows.',
      'Clone the repository or download the signed/checksummed release archive from GitHub Releases.',
      'Run scripts/setup-windows.ps1 and start the local runtime with scripts/start-windows.ps1.',
      'Open http://localhost:5173 to complete the 12-step local Setup Wizard and optionally pair Android via QR code.',
    ],
    codeSnippet: {
      label: 'PowerShell — Local Setup',
      code: `git clone https://github.com/NavigatorJagdish/javo-agents.git
cd javo-agents
.\\scripts\\setup-windows.ps1
.\\scripts\\start-windows.ps1`,
    },
    notes: [
      'Javo Agents is currently v0.1.0-alpha (Source Available / MIT).',
      'Always verify SHA-256 checksums before running downloaded release binaries.',
    ],
  },
  {
    id: 'local-ai',
    title: 'Local AI (Ollama & 8GB RAM Profiles)',
    category: 'AI & Voice',
    summary:
      'Configure Ollama for 100% offline, $0/month inference tuned for 8GB, 16GB, and 32GB+ Windows machines.',
    steps: [
      'Install Ollama from ollama.com and verify the local service responds on 127.0.0.1:11434.',
      'On 8GB RAM laptops, choose lightweight quantized models (such as qwen2.5:3b or llama3.2:3b) so Windows remains responsive.',
      'Resource Optimizer automatically unloads whisper.cpp before loading an Ollama model on memory-constrained PCs.',
      'Enable "Strict Local-Only" in Privacy Firewall if you want zero prompts leaving localhost.',
    ],
    codeSnippet: {
      label: 'Ollama — Recommended 8GB Profile',
      code: `ollama pull llama3.2:3b
ollama pull qwen2.5:3b
ollama list`,
    },
    notes: [
      '16GB+ RAM systems can comfortably run 7B–8B quantized models alongside background tasks.',
    ],
  },
  {
    id: 'gemini',
    title: 'Google Gemini (Free Developer API)',
    category: 'AI & Voice',
    summary:
      'Optionally add your own Gemini Developer API key for cloud fallback while the Privacy Firewall protects local secrets.',
    steps: [
      'Generate a personal API key in Google AI Studio (free tier available subject to Google quotas).',
      'Paste the key into Settings → AI Providers inside Javo Agents; it is encrypted using OS-backed storage.',
      'Configure AI Router mode: "Local First, Gemini Fallback" or "Gemini for Complex Planning Only".',
      'Budget Guardian tracks daily request counts so you stay within your configured quota cap.',
    ],
    notes: [
      'When Gemini is used, sanitized prompt text is sent to Google APIs under your API key terms.',
      'Local paths, OAuth tokens, and fields tagged Private are stripped by the Privacy Firewall before egress.',
    ],
  },
  {
    id: 'telegram',
    title: 'Telegram Bot & Mobile Approvals',
    category: 'Channels & Content',
    summary:
      'Receive approval cards, daily summaries, and pause/resume controls inside your private Telegram chat.',
    steps: [
      'Message @BotFather on Telegram and run /newbot to receive a bot token.',
      'Find your numeric Telegram User/Chat ID (e.g., via @userinfobot) for strict owner allowlisting.',
      'Enter both values in Settings → Telegram and click Test Connection.',
      'Use /approve, /reject, /pause, or /stop directly from Telegram.',
    ],
    notes: [
      'Any message from a Chat ID not in your allowlist is ignored and logged by Security Guardian.',
    ],
  },
  {
    id: 'facebook',
    title: 'Facebook Pages (Meta Graph API)',
    category: 'Channels & Content',
    summary:
      'Connect managed Facebook Pages via official Meta OAuth for approved post scheduling and comment triage.',
    steps: [
      'Ensure you manage a Facebook Page (Meta APIs do not support personal profiles).',
      'Create a Meta Developer App with pages_manage_posts and pages_read_engagement permissions.',
      'Connect your Page through Accounts → Add Facebook Page and grant consent.',
      'All scheduled Page posts pass through Approval Manager unless explicitly whitelisted.',
    ],
    notes: [
      'Status: Beta. Production multi-user publishing requires Meta App Review for your app credentials.',
    ],
  },
  {
    id: 'instagram',
    title: 'Instagram Professional (Graph API)',
    category: 'Channels & Content',
    summary:
      'Publish approved Reels/posts and triage comments on Instagram Business or Creator accounts.',
    steps: [
      'Switch your Instagram account to Professional (Creator or Business) and link it to your Facebook Page.',
      'Authorize Instagram Graph scopes in Accounts → Connect Instagram Professional.',
      'Review media container previews inside the Approval Inbox before publishing.',
    ],
    notes: [
      'Status: Beta. Personal Instagram accounts cannot be automated via official Meta APIs.',
    ],
  },
  {
    id: 'youtube',
    title: 'YouTube Data API v3',
    category: 'Channels & Content',
    summary:
      'Automate YouTube title/description drafting, comment triage, and verified channel analytics snapshots.',
    steps: [
      'Enable YouTube Data API v3 in a personal Google Cloud project and configure OAuth 2.0 Desktop credentials.',
      'Connect your YouTube channel under Accounts → YouTube.',
      'Drop finished videos into your watched Content Folder to auto-generate title, chapters, and description drafts.',
    ],
    notes: [
      'Status: Beta. Unverified Google Cloud testing apps keep uploads private until OAuth app verification.',
    ],
  },
  {
    id: 'content-folders',
    title: 'Folder-Based Content Pipeline',
    category: 'Channels & Content',
    summary:
      'Organize raw clips, thumbnails, and scripts in local folders that Content Factory automatically turns into platform-ready drafts.',
    steps: [
      'Point Javo Agents to your primary workspace folder (e.g., D:\\CreatorContent).',
      'Drop raw videos or images into /inbox or channel subfolders (/youtube, /reels, /posts).',
      'Folder Watcher detects new files, checks Brand Studio metadata, and creates drafts in /pending-approval.',
      'Once approved and published, assets are archived with publish receipts in local SQLite.',
    ],
    notes: [
      'Zero cloud storage upload is required—media stays on your disk until approved for publishing.',
    ],
  },
  {
    id: 'voice-mode',
    title: 'Voice Mode (Javo Wake Word & Hinglish)',
    category: 'AI & Voice',
    summary:
      'Speak naturally in English, Hindi, or Hinglish using offline whisper.cpp transcription and Piper TTS.',
    steps: [
      'Enable Voice Mode in Settings → Voice and select your microphone input.',
      'Choose Wake Word ("Javo") or Push-to-Talk mode to minimize background CPU usage.',
      'Speak commands like "Javo, aaj ke pending approvals dikhao" or "Pause all scheduled posts".',
      'Pair your Android phone to trigger voice commands from your mobile device over LAN.',
    ],
    notes: [
      'Audio never leaves your local network; whisper.cpp runs offline on your Windows machine.',
    ],
  },
  {
    id: 'security',
    title: 'Security, Encrypted SQLite & Privacy Firewall',
    category: 'Security & Operations',
    summary:
      'Defense-in-depth local architecture with OS-encrypted credentials, SQLite encryption, AST skill sandboxing, and Emergency Stop.',
    steps: [
      'Credentials and OAuth tokens are encrypted via Windows DPAPI / Keystore—never written to plaintext logs.',
      'Privacy Firewall classifies payloads into Public, Internal, and Confidential tiers before any outbound call.',
      'Installed skills run in a constrained subprocess sandbox checked by Plugin Trust.',
      'Use the global Emergency Stop button (Dashboard, Tray, Android, or Telegram) to halt all jobs immediately.',
    ],
    notes: [
      'Review docs/architecture/THREAT_MODEL.md in the repository for all 20 modeled threat vectors.',
    ],
  },
  {
    id: 'backups',
    title: 'Encrypted Backups & Key Recovery',
    category: 'Security & Operations',
    summary:
      'Create portable encrypted archives of your SQLite database, workflows, brand profile, and memory vault.',
    steps: [
      'Open Settings → Backup & Restore and click Export Encrypted Backup.',
      'Save your recovery passphrase offline in a password manager (never inside the repo).',
      'To migrate to a new Windows PC, install Javo Agents and import the encrypted archive.',
    ],
    notes: [
      'OAuth tokens are intentionally excluded or re-bound per device for security; re-authorize channels on a new PC.',
    ],
  },
  {
    id: 'troubleshooting',
    title: 'Troubleshooting Common Issues',
    category: 'Security & Operations',
    summary:
      'Quick fixes for Ollama ports, 8GB RAM slowdowns, Windows Firewall LAN pairing, and OAuth redirect errors.',
    steps: [
      'Ollama unreachable: Run "ollama serve" and verify http://127.0.0.1:11434/api/tags returns JSON.',
      'High RAM usage: Switch Resource Optimizer to "8GB Conservative Mode" so only one model loads at a time.',
      'Android pairing timeout: Ensure Windows and Android share the same Wi-Fi/LAN and allow port 8000 on Private networks only.',
      'OAuth error: Confirm your redirect URI matches http://127.0.0.1:8000/api/accounts/oauth/callback.',
    ],
    notes: [
      'Export sanitized diagnostics from Settings → Diagnostics before opening a GitHub Issue.',
    ],
  },
];
