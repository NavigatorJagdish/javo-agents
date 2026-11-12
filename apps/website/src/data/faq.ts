export interface FaqItem {
  id: string;
  category: 'General' | 'Pricing & Open Source' | 'Privacy & Hardware' | 'Social & Voice';
  question: string;
  answer: string;
}

export const FAQ_ITEMS: FaqItem[] = [
  {
    id: 'what-is-javo',
    category: 'General',
    question: 'What is Javo Agents?',
    answer:
      'Javo Agents is a local-first, open-source AI automation studio for creators and solo teams. It coordinates 29 specialized AI agents (plus a Master Orchestrator) on your own Windows PC with an optional Android companion app and Telegram approval bridge.',
  },
  {
    id: 'is-it-free',
    category: 'Pricing & Open Source',
    question: 'Is Javo Agents really $0/month?',
    answer:
      'Yes. The initial v0.1.0-alpha public release is completely free ($0/month) under the MIT license and runs locally on your own hardware using Ollama and whisper.cpp. If you optionally connect your own Google Gemini Developer API key or social APIs, any third-party provider quotas or terms apply directly between you and that provider.',
  },
  {
    id: 'future-paid-tiers',
    category: 'Pricing & Open Source',
    question: 'Will there be paid Pro or Enterprise plans later?',
    answer:
      'Optional cloud-hosted relay, multi-user team workspaces, or managed enterprise compliance packs may be introduced in future releases. Right now, there is no active billing, no checkout flow, and no features locked behind a paywall.',
  },
  {
    id: 'ram-8gb',
    category: 'Privacy & Hardware',
    question: 'Can Javo Agents run on an 8GB RAM Windows laptop?',
    answer:
      'Yes. Resource Optimizer (Agent 12) is designed specifically for 8GB RAM systems: it queues heavy tasks sequentially, selects quantized 3B Ollama models, and automatically unloads whisper.cpp when text generation runs.',
  },
  {
    id: 'supervised-autopilot',
    category: 'General',
    question: 'What does "Supervised Autopilot" mean?',
    answer:
      'Agents can analyze folders, draft captions, prepare schedules, and triage comments automatically—but irreversible external actions (publishing posts, sending replies, or activating new skills) wait in your Approval Inbox across Desktop, Android, or Telegram unless you explicitly configure safe auto-rules.',
  },
  {
    id: 'privacy-firewall',
    category: 'Privacy & Hardware',
    question: 'Does my content or API key get sent to Javo servers?',
    answer:
      'No. Javo Agents does not operate a central cloud SaaS backend in this release. Your SQLite database, content files, and encrypted credentials stay on your Windows PC. If you opt into Gemini fallback, the Privacy Firewall strips sensitive secrets and local paths before sending prompts to Google.',
  },
  {
    id: 'hindi-hinglish',
    category: 'Social & Voice',
    question: 'Does Voice Mode support Hindi and Hinglish?',
    answer:
      'Yes. Voice Mode uses local whisper.cpp and Piper TTS with intent routing tuned for English, Hindi, and mixed Hinglish commands using the "Javo" wake word or push-to-talk.',
  },
  {
    id: 'social-status',
    category: 'Social & Voice',
    question: 'Which social platforms work today vs. planned?',
    answer:
      'Ollama, Telegram Bot, GitHub, Gemini Developer API, and local whisper.cpp/Piper TTS are Supported. YouTube, Facebook Pages, and Instagram Professional connectors are in Beta (requiring your own OAuth app credentials). LinkedIn and TikTok are Planned, and X (Twitter) is marked Unavailable in the zero-cost baseline due to paid API tiers.',
  },
];
