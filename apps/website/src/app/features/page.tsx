import type { Metadata } from 'next';
import Link from 'next/link';
import {
  ArrowRight,
  Cpu,
  FolderKanban,
  Lock,
  ShieldCheck,
  Sliders,
  Zap,
} from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';

export const metadata: Metadata = {
  title: 'Features',
  description:
    'Deep dive into Javo Agents Supervised Autopilot, 8GB RAM optimization, Free AI Router, Privacy Firewall, and Folder-Based Content Pipeline.',
};

const FEATURE_DEEP_DIVES = [
  {
    id: 'supervised-autopilot',
    icon: ShieldCheck,
    badge: 'Human-in-the-Loop Control',
    title: 'Supervised Autopilot',
    summary:
      'Autonomy for preparation; explicit human consent for external impact. Javo Agents never treats your brand accounts like an unchecked black box.',
    points: [
      'Approval Manager (Agent 15) holds outgoing social posts, comment replies, and new skills until you click Approve, Edit, or Reject.',
      'Review approvals from the Windows Desktop Dashboard, Android Companion app, or your allowlisted Telegram Bot.',
      'Deterministic policy engine enforces cooldowns, daily rate caps, and platform disclosure checks before execution.',
      'Global Emergency Stop halts APScheduler jobs, active runs, and outbound queues immediately.',
    ],
  },
  {
    id: 'ram-optimization',
    icon: Cpu,
    badge: 'Hardware-Aware Scheduling',
    title: '8GB RAM Optimization',
    summary:
      'Most AI stacks assume 32GB+ workstations. Resource Optimizer (Agent 12) actively adapts execution for everyday 8GB Windows laptops.',
    points: [
      'Sequential heavy-model queue ensures Ollama text models and whisper.cpp speech models never compete for scarce RAM simultaneously.',
      'Selects quantized 3B model profiles on 8GB machines and unlocks larger 7B–8B models on 16GB/32GB hardware.',
      'Automatic model unloading releases memory back to Windows when the queue is idle.',
      'Lightweight governance agents run as compact Python services under 150MB footprint.',
    ],
  },
  {
    id: 'ai-router',
    icon: Zap,
    badge: 'Zero-Cost First',
    title: 'Free AI Router & Budget Guardian',
    summary:
      'Route routine drafting, classification, and memory lookups to local Ollama at $0 cost—and optionally use your own Gemini Developer API key only when needed.',
    points: [
      'Default provider: Local Ollama (127.0.0.1:11434) with zero subscription fees.',
      'Optional fallback: Google Gemini Developer API using your OS-encrypted personal key.',
      'Budget Guardian (Agent 16) enforces daily token and request caps per provider.',
      'Transparent provider telemetry shows exact local vs. cloud call counts.',
    ],
  },
  {
    id: 'privacy-firewall',
    icon: Lock,
    badge: 'Data Classification & Egress Control',
    title: 'Privacy Firewall',
    summary:
      'Before any prompt leaves your machine to an optional external AI provider, Privacy Firewall classifies data sensitivity and strips secrets.',
    points: [
      'Three classification tiers: Public, Internal, and Confidential.',
      'Automatically redacts API keys, OAuth tokens, local Windows user paths, and personal identifiers.',
      'Strict Local-Only mode blocks all external AI egress with one toggle.',
      'Every outbound request passes through auditable firewall middleware.',
    ],
  },
  {
    id: 'content-pipeline',
    icon: FolderKanban,
    badge: 'Zero Cloud Storage Required',
    title: 'Folder-Based Content Pipeline',
    summary:
      'Work the way creators already work: drop videos, shorts, thumbnails, or notes into local folders and let your agents build the publishing pipeline.',
    points: [
      'Folder Watcher monitors configured directories such as /inbox, /youtube, and /reels.',
      'Content Factory extracts metadata and generates platform-tailored titles, captions, and hashtags.',
      'Brand Manager & Quality Inspector verify tone and completeness prior to entering /pending-approval.',
      'Approved assets publish via Content Publisher and archive cleanly with SQLite audit receipts.',
    ],
  },
];

export default function FeaturesPage() {
  return (
    <div>
      <PageHeader
        badge="Core Platform Capabilities"
        title="Engineered for"
        highlight="Local-First Automation"
        subtitle="Explore how Javo Agents balances 29-agent automation power with 8GB RAM discipline, zero-cost local AI routing, and strict Supervised Autopilot safeguards."
      >
        <Link href="/download" className="btn-primary">
          Get v0.1.0-alpha
        </Link>
        <Link href="/workflows" className="btn-secondary">
          Try Workflow Explorer
        </Link>
      </PageHeader>

      <section className="mx-auto max-w-7xl space-y-8 px-4 py-14 sm:px-6 lg:px-8">
        {FEATURE_DEEP_DIVES.map((feat, idx) => (
          <div key={feat.id} id={feat.id} className="glass-card p-6 sm:p-8">
            <div className="grid gap-8 lg:grid-cols-12 lg:items-center">
              <div className="lg:col-span-5">
                <div className="inline-flex items-center gap-2 rounded-full border border-[#00E5FF]/35 bg-[#00E5FF]/10 px-3 py-1 text-xs font-semibold text-[#007B8F] dark:text-[#00E5FF]">
                  <feat.icon className="h-3.5 w-3.5" />
                  <span>0{idx + 1} · {feat.badge}</span>
                </div>
                <h2 className="mt-3 font-display text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">
                  {feat.title}
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/85">
                  {feat.summary}
                </p>
              </div>

              <div className="lg:col-span-7">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-[#0B1026]/80">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-[#94A3B8]">
                    <Sliders className="h-3.5 w-3.5 text-[#00E5FF]" />
                    How It Works Under the Hood
                  </div>
                  <ul className="mt-3 space-y-2.5 text-sm text-slate-700 dark:text-[#E2E6F0]/90">
                    {feat.points.map((point) => (
                      <li key={point} className="flex items-start gap-2.5">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-gradient-to-r from-[#00E5FF] to-[#8B5CF6]" />
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        ))}

        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#00E5FF]/30 bg-gradient-to-r from-[#00E5FF]/10 to-[#8B5CF6]/10 p-6">
          <div>
            <h3 className="font-display text-xl font-bold text-slate-900 dark:text-white">
              Want to inspect the 29 agents powering these systems?
            </h3>
            <p className="mt-1 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
              Browse every specialist&apos;s responsibilities, permission scopes, and memory tier.
            </p>
          </div>
          <Link href="/agents" className="btn-primary">
            Explore Agent Roster <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
