import type { Metadata } from 'next';
import Link from 'next/link';
import {
  AlertTriangle,
  Database,
  FileWarning,
  KeyRound,
  Lock,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';

export const metadata: Metadata = {
  title: 'Privacy & Security',
  description:
    'Local-first security architecture: Encrypted SQLite, OS Keystore/DPAPI secrets, Privacy Firewall, AST skill sandboxing, and Threat Model summary.',
};

const THREAT_MITIGATIONS = [
  {
    threat: 'Unintended Cloud Data Leak',
    mitigation:
      'Privacy Firewall classifies local records (Public / Internal / Confidential) and strips tokens, local paths, and PII before any optional Gemini call.',
  },
  {
    threat: 'Unapproved Social Posting',
    mitigation:
      'Supervised Autopilot enforces human Approval Manager sign-off prior to Content Publisher or Comment Reply execution.',
  },
  {
    threat: 'Malicious or Buggy Local Skill',
    mitigation:
      'Plugin Trust audits Python AST imports, executes skills in a constrained subprocess without credential env vars, and enforces timeouts.',
  },
  {
    threat: 'Unauthorized Telegram or LAN Access',
    mitigation:
      'Telegram Bot restricts commands to allowlisted owner Chat IDs; Android pairing uses short-lived QR tokens with per-device revocation.',
  },
  {
    threat: 'Runaway Loops or Quota Exhaustion',
    mitigation:
      'Master Orchestrator & Budget Guardian enforce strict retry caps, cooldowns, daily token budgets, and instant Emergency Stop.',
  },
  {
    threat: 'Plaintext Token Exposure',
    mitigation:
      'OAuth tokens and API keys are stored via Windows DPAPI / Android Keystore AES-GCM and excluded from logs and diagnostics.',
  },
];

export default function SecurityPage() {
  return (
    <div>
      <PageHeader
        badge="Defense-in-Depth Local Security"
        title="Privacy &"
        highlight="Security Architecture"
        subtitle="Built on the principle that your drafts, credentials, and audience analytics belong on your own machine—protected by encryption, firewalls, and explicit human consent."
      >
        <Link href="/security-reporting" className="btn-primary">
          Report a Vulnerability
        </Link>
        <Link href="/privacy" className="btn-secondary">
          Privacy Policy
        </Link>
      </PageHeader>

      <section className="mx-auto max-w-7xl space-y-12 px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {[
            {
              icon: Database,
              title: 'Local Encrypted SQLite',
              body: 'All tasks, goals, memory vaults, and audit trails persist locally on your Windows drive.',
            },
            {
              icon: KeyRound,
              title: 'OS Credential Vaults',
              body: 'Secrets are protected via Windows DPAPI and Android Hardware-backed Keystore AES-256-GCM.',
            },
            {
              icon: Lock,
              title: 'Privacy Firewall',
              body: 'Enforces Strict Local-Only mode or redacts confidential fields before optional cloud fallback.',
            },
            {
              icon: ShieldAlert,
              title: 'Global Emergency Stop',
              body: 'Immediately halts scheduled jobs, active agents, and outbound connectors from any surface.',
            },
          ].map((pillar) => (
            <div key={pillar.title} className="glass-card p-6">
              <pillar.icon className="h-6 w-6 text-[#00E5FF]" />
              <h2 className="mt-3 font-display text-lg font-bold text-slate-900 dark:text-white">
                {pillar.title}
              </h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-[#E2E6F0]/80">{pillar.body}</p>
            </div>
          ))}
        </div>

        {/* Threat Model Summary */}
        <div className="glass-card p-6 sm:p-8">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#6D28D9] dark:text-[#A78BFA]">
            <ShieldCheck className="h-4 w-4" />
            Threat Model Summary
          </div>
          <h2 className="mt-2 font-display text-2xl font-bold text-slate-900 dark:text-white">
            Key Risks &amp; Architectural Mitigations
          </h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
            The full 20-threat security analysis lives in <code className="font-mono">docs/architecture/THREAT_MODEL.md</code> in the repository.
          </p>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {THREAT_MITIGATIONS.map((row) => (
              <div
                key={row.threat}
                className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-[#0B1026]/80"
              >
                <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
                  <FileWarning className="h-4 w-4 text-amber-400" />
                  {row.threat}
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                  {row.mitigation}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5 text-sm text-slate-800 dark:text-[#E2E6F0]">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">
                Alpha Security Notice
              </p>
              <p className="mt-1 text-xs leading-relaxed text-slate-700 dark:text-[#E2E6F0]/85">
                v0.1.0-alpha is a pre-release milestone undergoing community review. Keep Privacy Firewall in Strict Local mode for highly sensitive workloads, back up your recovery key offline, and report any suspected security issues responsibly via our{' '}
                <Link href="/security-reporting" className="underline">
                  Security Reporting policy
                </Link>.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
