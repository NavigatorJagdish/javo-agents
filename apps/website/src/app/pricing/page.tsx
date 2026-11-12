import type { Metadata } from 'next';
import Link from 'next/link';
import { CheckCircle2, Clock, Github, Info } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { SITE_CONFIG } from '@/data/site';

export const metadata: Metadata = {
  title: 'Pricing ($0 Free Initial Release)',
  description:
    'Javo Agents initial release is Free ($0/month) local-first and open source (MIT). Transparently view planned future optional cloud and enterprise capabilities with no active billing.',
};

export default function PricingPage() {
  return (
    <div>
      <PageHeader
        badge="Transparent & Truthful Pricing"
        title="Free Local-First"
        highlight="$0 / month"
        subtitle="The v0.1.0-alpha public release of Javo Agents is 100% free and open source (MIT). There is no active billing, no credit card requirement, and no paywalled core agents."
      />

      <section className="mx-auto max-w-7xl space-y-10 px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Active Free Tier */}
          <div className="glass-card flex flex-col justify-between border-[#00E5FF] p-7 shadow-glow">
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                  Available Now
                </span>
                <span className="font-mono text-xs text-slate-500 dark:text-[#94A3B8]">
                  MIT License
                </span>
              </div>

              <h2 className="mt-4 font-display text-2xl font-bold text-slate-900 dark:text-white">
                Starter / Self-Hosted Local
              </h2>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="font-display text-4xl font-bold text-slate-900 dark:text-white">
                  $0
                </span>
                <span className="text-sm text-slate-500 dark:text-[#94A3B8]">/ month forever</span>
              </div>
              <p className="mt-3 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
                Everything in Javo Agents v0.1.0-alpha running directly on your Windows PC and paired Android phone.
              </p>

              <ul className="mt-6 space-y-2.5 text-sm text-slate-700 dark:text-[#E2E6F0]/90">
                {[
                  'All 29 Specialist Agents + Master Orchestrator',
                  '100% Free Local AI via Ollama (8GB RAM optimized)',
                  'Optional personal Gemini Developer API key support',
                  'Local whisper.cpp + Piper TTS Voice Mode (HI/Hinglish/EN)',
                  '16-Node Visual Workflow Engine & Folder Pipelines',
                  'Supervised Autopilot Approval Inbox & Emergency Stop',
                  'Android Companion LAN Pairing & Telegram Bot Bridge',
                ].map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#00E5FF]" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-8 flex flex-col gap-2">
              <Link href="/download" className="btn-primary w-full text-center">
                Download v0.1.0-alpha Free
              </Link>
              <a
                href={SITE_CONFIG.githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary w-full text-center"
              >
                <Github className="h-4 w-4" />
                View MIT Source on GitHub
              </a>
            </div>
          </div>

          {/* Planned Cloud Relay */}
          <div className="glass-card flex flex-col justify-between p-7 opacity-95">
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#8B5CF6]/15 px-3 py-1 text-xs font-semibold text-[#6D28D9] dark:text-[#A78BFA]">
                  <Clock className="h-3.5 w-3.5" />
                  Planned / Coming Soon
                </span>
                <span className="font-mono text-xs text-slate-500 dark:text-[#94A3B8]">
                  Not Active
                </span>
              </div>

              <h2 className="mt-4 font-display text-2xl font-bold text-slate-900 dark:text-white">
                Optional Cloud Sync Relay
              </h2>
              <p className="mt-3 font-display text-xl font-semibold text-slate-500 dark:text-[#94A3B8]">
                Pricing TBD — No active billing
              </p>
              <p className="mt-3 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
                Planned optional add-on for creators who want remote Android-to-Windows sync outside home Wi-Fi without configuring their own VPN.
              </p>

              <ul className="mt-6 space-y-2.5 text-sm text-slate-600 dark:text-[#E2E6F0]/75">
                {[
                  'Planned: End-to-end encrypted relay tunnel',
                  'Planned: Encrypted remote backup snapshot storage',
                  'Planned: Zero-knowledge key ownership retained by user',
                  'Core local-first app remains 100% functional without this',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5">
                    <Clock className="mt-0.5 h-4 w-4 shrink-0 text-[#8B5CF6]" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-8">
              <Link href="/roadmap" className="btn-secondary w-full text-center">
                Track on Public Roadmap
              </Link>
            </div>
          </div>

          {/* Planned Team / Enterprise */}
          <div className="glass-card flex flex-col justify-between p-7 opacity-95">
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#8B5CF6]/15 px-3 py-1 text-xs font-semibold text-[#6D28D9] dark:text-[#A78BFA]">
                  <Clock className="h-3.5 w-3.5" />
                  Planned / Future Exploration
                </span>
                <span className="font-mono text-xs text-slate-500 dark:text-[#94A3B8]">
                  Not Active
                </span>
              </div>

              <h2 className="mt-4 font-display text-2xl font-bold text-slate-900 dark:text-white">
                Studio &amp; Enterprise Edition
              </h2>
              <p className="mt-3 font-display text-xl font-semibold text-slate-500 dark:text-[#94A3B8]">
                Pricing TBD — No checkout flow
              </p>
              <p className="mt-3 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
                Future exploration for multi-seat creator agencies needing shared brand approval queues and centralized compliance packs.
              </p>

              <ul className="mt-6 space-y-2.5 text-sm text-slate-600 dark:text-[#E2E6F0]/75">
                {[
                  'Planned: Multi-seat role-based approval policies',
                  'Planned: Shared brand studio libraries across workstations',
                  'Planned: Enterprise audit archive & SSO options',
                  'Self-hosted MIT edition always stays free for solo creators',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5">
                    <Clock className="mt-0.5 h-4 w-4 shrink-0 text-[#8B5CF6]" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-8">
              <Link href="/contact" className="btn-secondary w-full text-center">
                Share Feedback on GitHub
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-xs text-slate-600 dark:border-white/10 dark:bg-[#111836]/70 dark:text-[#E2E6F0]/80">
          <div className="flex items-start gap-2.5">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-[#00E5FF]" />
            <p>
              <strong>Note on Third-Party APIs:</strong> Javo Agents itself costs $0. If you optionally configure external APIs (such as Google Gemini Developer API, YouTube Data API, or Meta Graph API) using your own credentials, you are responsible for complying with those providers&apos; free-tier quotas and terms.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
