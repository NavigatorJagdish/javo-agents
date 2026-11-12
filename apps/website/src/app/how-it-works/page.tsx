import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight, Cpu, Database, FolderOpen, Layers, Shield, Smartphone } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';

export const metadata: Metadata = {
  title: 'How It Works',
  description:
    'End-to-end local-first architecture of Javo Agents: Windows Local Runtime, Encrypted SQLite, AI Router, Privacy Firewall, and Android Companion.',
};

const ARCHITECTURE_LAYERS = [
  {
    icon: FolderOpen,
    title: '1. Input Triggers & Local Workspace',
    items: [
      'Folder Watcher detects raw videos, audio, and images in your local Content Folder',
      'Voice Mode ("Javo" wake word) captures commands via whisper.cpp offline STT',
      'APScheduler triggers recurring schedules and Goal Persistence milestones',
      'Telegram Bot & Android Companion deliver remote commands and approvals',
    ],
  },
  {
    icon: Cpu,
    title: '2. Master Orchestrator & 29 Specialists',
    items: [
      'Decomposes goals into bounded tasks with retry, cost, and RAM budgets',
      'Routes reasoning through AI Router (Ollama local-first or sanitized Gemini fallback)',
      'Resource Optimizer queues heavy models sequentially on 8GB RAM laptops',
      'Plugin Trust audits any skill script inside an AST-checked sandbox',
    ],
  },
  {
    icon: Shield,
    title: '3. Privacy Firewall & Supervised Autopilot',
    items: [
      'Privacy Firewall classifies payloads and blocks sensitive leaks before external calls',
      'Quality Inspector & Compliance Agent verify formatting and platform rules',
      'Approval Manager pauses external publishes and replies in your Approval Inbox',
      'Global Emergency Stop halts all queues instantaneously when triggered',
    ],
  },
  {
    icon: Database,
    title: '4. Local Encrypted State & Channel Delivery',
    items: [
      'Encrypted SQLite stores tasks, workflows, audit logs, and Smart Memory locally',
      'OS Keystore / Windows DPAPI protects OAuth tokens and optional API keys',
      'Content Publisher executes approved jobs via official YouTube & Meta APIs (Beta)',
      'Device Sync Agent syncs tasks and offline drafts to paired Android devices over LAN',
    ],
  },
];

export default function HowItWorksPage() {
  return (
    <div>
      <PageHeader
        badge="End-to-End Architecture"
        title="How Javo Agents"
        highlight="Works Locally"
        subtitle="No opaque cloud middleware. Every trigger, AI inference call, approval gate, and database write executes transparently on hardware you control."
      />

      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        {/* Visual Flow Diagram */}
        <div className="glass-card p-6 sm:p-8">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
            <Layers className="h-4 w-4" />
            Runtime Topology
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-5">
            {[
              { label: 'Desktop / Android / Voice', sub: 'User Surfaces' },
              { label: 'FastAPI Local Runtime', sub: '127.0.0.1:8000' },
              { label: '29 Agents + DAG Engine', sub: 'Resource Optimized' },
              { label: 'Privacy Firewall + Approval', sub: 'Human Gatekeeper' },
              { label: 'Ollama / Official APIs', sub: 'Zero-Cost Default' },
            ].map((node, i) => (
              <div
                key={node.label}
                className="relative rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-[#0B1026]/80"
              >
                <span className="font-mono text-[11px] font-bold text-[#007B8F] dark:text-[#00E5FF]">
                  STAGE 0{i + 1}
                </span>
                <p className="mt-1 font-display text-sm font-bold text-slate-900 dark:text-white">
                  {node.label}
                </p>
                <p className="mt-0.5 text-xs text-slate-500 dark:text-[#94A3B8]">{node.sub}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Detailed 4 Layers */}
        <div className="mt-10 grid gap-6 md:grid-cols-2">
          {ARCHITECTURE_LAYERS.map((layer) => (
            <div key={layer.title} className="glass-card p-6">
              <div className="flex items-center gap-3">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[#00E5FF]/15 text-[#008BA3] dark:text-[#00E5FF]">
                  <layer.icon className="h-5 w-5" />
                </div>
                <h2 className="font-display text-xl font-bold text-slate-900 dark:text-white">
                  {layer.title}
                </h2>
              </div>
              <ul className="mt-4 space-y-2.5 text-sm text-slate-600 dark:text-[#E2E6F0]/85">
                {layer.items.map((item) => (
                  <li key={item} className="flex items-start gap-2.5">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#8B5CF6]" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-wrap gap-4">
          <Link href="/security" className="btn-primary">
            Explore Security &amp; Threat Model <ArrowRight className="h-4 w-4" />
          </Link>
          <Link href="/download" className="btn-secondary">
            <Smartphone className="h-4 w-4" />
            Install Windows &amp; Android
          </Link>
        </div>
      </section>
    </div>
  );
}
