import React from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  Bot,
  Cpu,
  Download,
  FolderKanban,
  Lock,
  Mic,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Workflow,
  Zap,
} from 'lucide-react';
import { JavoLogo } from '@/components/JavoLogo';
import { WaveformGraphic } from '@/components/WaveformGraphic';
import { InteractiveWorkflowDemo } from '@/components/InteractiveWorkflowDemo';
import { VoiceModeDemo } from '@/components/VoiceModeDemo';
import { StatusBadge } from '@/components/StatusBadge';
import { SPECIALIST_AGENTS } from '@/data/agents';
import { INTEGRATIONS } from '@/data/integrations';
import { FAQ_ITEMS } from '@/data/faq';
import { SITE_CONFIG } from '@/data/site';

const CORE_FEATURES = [
  {
    icon: ShieldCheck,
    title: 'Supervised Autopilot',
    description:
      'Agents draft, analyze, and organize automatically—while irreversible publishes, replies, and new skills wait in your Approval Inbox.',
  },
  {
    icon: Cpu,
    title: '8GB RAM Optimization',
    description:
      'Resource Optimizer sequences heavy local models, selects quantized profiles, and unloads whisper.cpp when idle so everyday laptops stay smooth.',
  },
  {
    icon: Zap,
    title: 'Free AI Router',
    description:
      'Defaults to zero-cost local Ollama inference on your PC with optional user-supplied Gemini Developer API fallback governed by Budget Guardian.',
  },
  {
    icon: Lock,
    title: 'Privacy Firewall',
    description:
      'Classifies local data and strips tokens, file paths, and private context before any optional external AI request leaves your machine.',
  },
  {
    icon: FolderKanban,
    title: 'Folder-Based Content Pipeline',
    description:
      'Drop raw videos or assets into watched local folders and let Content Factory, Brand Studio, and Quality Inspector prepare ready-to-approve drafts.',
  },
  {
    icon: Smartphone,
    title: 'Windows + Android LAN Sync',
    description:
      'Pair your Android companion via short-lived QR tokens over your local network for mobile voice commands, offline drafts, and instant approvals.',
  },
];

const HOW_IT_WORKS_STEPS = [
  {
    step: '01',
    title: 'Install Local Runtime on Windows',
    detail:
      'Run the FastAPI Local Runtime, SQLite encrypted store, and Ollama locally on Windows 10/11 (8GB+ RAM). No central SaaS subscription required.',
  },
  {
    step: '02',
    title: 'Connect Folders, Voice & Channels',
    detail:
      'Point Content Factory to your local media folders, enable "Javo" Voice Mode, and optionally link Telegram, YouTube, or Meta Pages.',
  },
  {
    step: '03',
    title: '29 Specialists Collaborate in Workflows',
    detail:
      'Master Orchestrator routes tasks across 29 specialist agents inside a 16-node visual workflow engine with strict permission scopes.',
  },
  {
    step: '04',
    title: 'Approve or Pause from Anywhere',
    detail:
      'Review drafts in Desktop Dashboard, Android Companion, or Telegram—or hit global Emergency Stop at any time.',
  },
];

export default function HomePage() {
  const featuredAgents = SPECIALIST_AGENTS.slice(0, 6);
  const featuredIntegrations = INTEGRATIONS.slice(0, 8);
  const featuredFaqs = FAQ_ITEMS.slice(0, 4);

  return (
    <div>
      {/* HERO SECTION */}
      <section className="relative overflow-hidden border-b border-slate-200/80 bg-grid-pattern py-16 dark:border-white/10 sm:py-24">
        <div className="pointer-events-none absolute -top-24 right-0 h-96 w-96 rounded-full bg-[#00E5FF]/15 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-0 h-80 w-80 rounded-full bg-[#8B5CF6]/15 blur-3xl" />

        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-12 lg:px-8">
          <div className="lg:col-span-7">
            <div className="inline-flex flex-wrap items-center gap-2 rounded-full border border-[#00E5FF]/35 bg-[#00E5FF]/10 px-3.5 py-1.5 text-xs font-semibold text-[#007B8F] dark:text-[#00E5FF]">
              <Sparkles className="h-3.5 w-3.5" />
              <span>{SITE_CONFIG.version} · {SITE_CONFIG.releaseStatus}</span>
              <span className="text-slate-400">•</span>
              <span>Free $0/month (MIT)</span>
            </div>

            <h1 className="mt-5 font-display text-4xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-6xl">
              Javo Agents —{' '}
              <span className="text-gradient">{SITE_CONFIG.tagline}</span>
            </h1>

            <p className="mt-5 max-w-2xl text-base leading-relaxed text-slate-600 dark:text-[#E2E6F0]/85 sm:text-lg">
              Run 29 specialized AI agents on your own Windows PC with an Android companion app. Built around{' '}
              <strong className="font-semibold text-slate-900 dark:text-white">Supervised Autopilot</strong>,{' '}
              <strong className="font-semibold text-slate-900 dark:text-white">8GB RAM optimization</strong>, a{' '}
              <strong className="font-semibold text-slate-900 dark:text-white">Privacy Firewall</strong>, and{' '}
              <strong className="font-semibold text-slate-900 dark:text-white">Hindi / Hinglish / English Voice Mode</strong>.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href="/download" className="btn-primary">
                <Download className="h-4 w-4" />
                Windows Download (v0.1.0-alpha)
              </Link>
              <Link href="/download#android" className="btn-secondary">
                <Smartphone className="h-4 w-4" />
                Android Companion Status
              </Link>
              <Link
                href="/agents"
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-semibold text-[#007B8F] transition hover:underline dark:text-[#00E5FF]"
              >
                Explore 29 Agents <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { label: 'Specialist Agents', value: '29 + Orchestrator' },
                { label: 'Initial Release', value: '$0 / month' },
                { label: 'Minimum RAM', value: '8 GB Windows' },
                { label: 'Control Model', value: 'Supervised' },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-xl border border-slate-200 bg-white/75 p-3 dark:border-white/10 dark:bg-[#111836]/75"
                >
                  <p className="font-display text-sm font-bold text-slate-900 dark:text-white">
                    {stat.value}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500 dark:text-[#94A3B8]">
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Animated AI Ecosystem Graphic */}
          <div className="lg:col-span-5">
            <div className="glass-card relative overflow-hidden p-6 sm:p-8">
              <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-white/10">
                <span className="font-mono text-xs font-semibold text-[#007B8F] dark:text-[#00E5FF]">
                  LOCAL RUNTIME ECOSYSTEM
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  127.0.0.1 Local-First
                </span>
              </div>

              <div className="my-6 flex flex-col items-center justify-center">
                <div className="relative flex h-44 w-44 items-center justify-center">
                  <div className="absolute inset-0 rounded-full border border-dashed border-[#00E5FF]/35 animate-spin-slow" />
                  <div className="absolute inset-4 rounded-full border border-[#8B5CF6]/30 animate-pulse-slow" />
                  <JavoLogo size={104} animated />
                </div>
                <div className="mt-4 w-full">
                  <WaveformGraphic state="Listening" compact />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2.5 text-xs">
                {[
                  { icon: Bot, title: 'Master Orchestrator', sub: '29 Specialist Agents' },
                  { icon: Lock, title: 'Privacy Firewall', sub: 'Zero Silent Egress' },
                  { icon: Mic, title: 'whisper.cpp + Piper', sub: 'HI / Hinglish / EN' },
                  { icon: Workflow, title: '16-Node DAGs', sub: 'Approval Gated' },
                ].map((item) => (
                  <div
                    key={item.title}
                    className="flex items-start gap-2.5 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-white/10 dark:bg-[#0B1026]/80"
                  >
                    <item.icon className="mt-0.5 h-4 w-4 shrink-0 text-[#00E5FF]" />
                    <div>
                      <p className="font-semibold text-slate-900 dark:text-white">{item.title}</p>
                      <p className="text-[11px] text-slate-500 dark:text-[#94A3B8]">{item.sub}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PRODUCT FEATURES */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <p className="font-mono text-xs font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
              Architecture &amp; Capabilities
            </p>
            <h2 className="mt-2 font-display text-3xl font-bold text-slate-900 dark:text-white">
              Built for Real Hardware, Real Privacy, and Human Control
            </h2>
          </div>
          <Link href="/features" className="btn-secondary shrink-0">
            Deep Dive into Features <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {CORE_FEATURES.map((feat) => (
            <div key={feat.title} className="glass-card p-6 transition hover:border-[#00E5FF]/50">
              <div className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[#00E5FF]/20 to-[#8B5CF6]/20 text-[#008BA3] dark:text-[#00E5FF]">
                <feat.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-display text-lg font-bold text-slate-900 dark:text-white">
                {feat.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                {feat.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* AGENT TEAM OVERVIEW */}
      <section className="border-y border-slate-200/80 bg-slate-50/70 py-16 dark:border-white/10 dark:bg-[#080C1D]/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div className="max-w-2xl">
              <p className="font-mono text-xs font-semibold uppercase tracking-wider text-[#6D28D9] dark:text-[#A78BFA]">
                Multi-Agent Specialist Roster
              </p>
              <h2 className="mt-2 font-display text-3xl font-bold text-slate-900 dark:text-white">
                29 Focused Agents Coordinated by One Master Orchestrator
              </h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
                Each agent has explicit input/output schemas, permission boundaries, and enable/disable controls.
              </p>
            </div>
            <Link href="/agents" className="btn-primary shrink-0">
              View All 29 Agents <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {featuredAgents.map((agent) => (
              <div key={agent.id} className="glass-card p-5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[#007B8F] dark:text-[#00E5FF]">
                    AGENT {agent.number}
                  </span>
                  <span className="rounded-full bg-[#8B5CF6]/15 px-2.5 py-0.5 text-[11px] font-medium text-[#6D28D9] dark:text-[#A78BFA]">
                    {agent.defaultMode}
                  </span>
                </div>
                <h3 className="mt-2 font-display text-lg font-bold text-slate-900 dark:text-white">
                  {agent.name}
                </h3>
                <p className="text-xs font-medium text-slate-500 dark:text-[#94A3B8]">
                  {agent.role}
                </p>
                <p className="mt-2.5 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                  {agent.summary}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* INTERACTIVE WORKFLOW DEMO */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <InteractiveWorkflowDemo />
      </section>

      {/* VOICE MODE DEMO */}
      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <VoiceModeDemo />
      </section>

      {/* INTEGRATIONS STRIP */}
      <section className="border-y border-slate-200/80 bg-slate-50/70 py-16 dark:border-white/10 dark:bg-[#080C1D]/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div className="max-w-2xl">
              <p className="font-mono text-xs font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
                Transparent Integration Status
              </p>
              <h2 className="mt-2 font-display text-3xl font-bold text-slate-900 dark:text-white">
                Honest Connector Matrix: Supported, Beta, Planned &amp; Unavailable
              </h2>
            </div>
            <Link href="/integrations" className="btn-secondary shrink-0">
              Full Integration Matrix <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {featuredIntegrations.map((item) => (
              <div key={item.id} className="glass-card p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-slate-500 dark:text-[#94A3B8]">
                    {item.category}
                  </span>
                  <StatusBadge status={item.status} />
                </div>
                <h3 className="mt-2.5 font-display text-base font-bold text-slate-900 dark:text-white">
                  {item.name}
                </h3>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-600 dark:text-[#E2E6F0]/75">
                  {item.summary}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRIVACY HIGHLIGHTS & HOW IT WORKS */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <div className="glass-card h-full p-6 sm:p-8">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                <Lock className="h-3.5 w-3.5" />
                Privacy-First Guarantees
              </span>
              <h2 className="mt-4 font-display text-2xl font-bold text-slate-900 dark:text-white">
                Your Hardware, Your Database, Your Kill Switch
              </h2>
              <ul className="mt-5 space-y-3 text-sm text-slate-600 dark:text-[#E2E6F0]/85">
                <li className="flex items-start gap-2.5">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#00E5FF]" />
                  <span>Encrypted SQLite + OS Keystore/DPAPI token protection</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#00E5FF]" />
                  <span>Privacy Firewall strips credentials and private fields before external API calls</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#00E5FF]" />
                  <span>AST-checked skill sandbox audited by Plugin Trust (Agent 21)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#00E5FF]" />
                  <span>One-click Emergency Stop across Desktop, Android, and Telegram</span>
                </li>
              </ul>
              <Link href="/security" className="btn-secondary mt-6">
                Read Security Architecture <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>

          <div className="lg:col-span-7">
            <p className="font-mono text-xs font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
              How It Works
            </p>
            <h2 className="mt-2 font-display text-3xl font-bold text-slate-900 dark:text-white">
              From Local Folder to Approved Publish in 4 Clear Steps
            </h2>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {HOW_IT_WORKS_STEPS.map((s) => (
                <div key={s.step} className="glass-card p-5">
                  <span className="font-mono text-sm font-bold text-gradient">STEP {s.step}</span>
                  <h3 className="mt-1.5 font-display text-base font-bold text-slate-900 dark:text-white">
                    {s.title}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                    {s.detail}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FAQ PREVIEW & FINAL CTA */}
      <section className="border-t border-slate-200/80 bg-slate-50/70 py-16 dark:border-white/10 dark:bg-[#080C1D]/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <h2 className="font-display text-3xl font-bold text-slate-900 dark:text-white">
                Frequently Asked Questions
              </h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
                Clear answers about pricing ($0/month initial release), 8GB RAM support, and Supervised Autopilot.
              </p>
            </div>
            <Link href="/faq" className="btn-secondary shrink-0">
              All FAQs <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {featuredFaqs.map((faq) => (
              <div key={faq.id} className="glass-card p-5">
                <h3 className="font-display text-base font-bold text-slate-900 dark:text-white">
                  {faq.question}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                  {faq.answer}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
