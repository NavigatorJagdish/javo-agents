import type { Metadata } from 'next';
import Link from 'next/link';
import { AlertTriangle, ExternalLink, Lock, ShieldCheck } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { SITE_CONFIG } from '@/data/site';

export const metadata: Metadata = {
  title: 'Vulnerability Disclosure & Security Reporting',
  description:
    'Coordinated vulnerability disclosure policy, in-scope components, and safe-harbor guidelines for Javo Agents.',
};

export default function SecurityReportingPage() {
  return (
    <div>
      <PageHeader
        badge="Coordinated Vulnerability Disclosure"
        title="Security"
        highlight="Reporting"
        subtitle="Help keep Javo Agents safe for local-first creators. Report suspected vulnerabilities privately before public disclosure."
      />

      <section className="mx-auto max-w-4xl space-y-6 px-4 py-14 sm:px-6 lg:px-8">
        <div className="rounded-2xl border border-amber-500/35 bg-amber-500/10 p-5 text-sm text-slate-800 dark:text-[#E2E6F0]">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">
                Do Not Open Public GitHub Issues for Security Bugs
              </p>
              <p className="mt-1 text-xs leading-relaxed text-slate-700 dark:text-[#E2E6F0]/85">
                Use GitHub&apos;s private Security Advisory workflow (<code className="font-mono">/security/advisories/new</code>) so maintainers can verify and patch the issue before details become public.
              </p>
            </div>
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
            <Lock className="h-4 w-4 text-[#00E5FF]" />
            In-Scope Components
          </div>
          <ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-[#E2E6F0]/85">
            <li>• <code className="font-mono">services/local-runtime</code> — FastAPI auth, Privacy Firewall, SQLite encryption, and OAuth callbacks</li>
            <li>• <code className="font-mono">skills/sandbox</code> — AST sandbox escaping, secret environment leakage, or Plugin Trust bypasses</li>
            <li>• <code className="font-mono">apps/android</code> — Keystore token handling, LAN pairing verification, and WorkManager sync</li>
            <li>• <code className="font-mono">apps/windows</code> &amp; <code className="font-mono">apps/dashboard</code> — Electron preload IPC boundaries and XSS vectors</li>
          </ul>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
            <ShieldCheck className="h-4 w-4 text-[#8B5CF6]" />
            What to Include in a Report
          </div>
          <ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-[#E2E6F0]/85">
            <li>1. Affected component, version (<code className="font-mono">0.1.0-alpha</code>), and OS environment.</li>
            <li>2. Clear step-by-step reproduction or minimal proof-of-concept without accessing other users&apos; accounts.</li>
            <li>3. Assessment of impact (e.g., credential exposure, sandbox escape, unapproved publish bypass).</li>
          </ul>
          <p className="mt-4 text-xs text-slate-500 dark:text-[#94A3B8]">
            Good-faith security research adhering to this policy and avoiding destructive testing against third-party APIs will not face legal action from Javo Agents maintainers.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <a
            href={`${SITE_CONFIG.githubUrl}/security/advisories/new`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
          >
            Submit Private GitHub Advisory
            <ExternalLink className="h-4 w-4" />
          </a>
          <Link href="/security" className="btn-secondary">
            Security Architecture
          </Link>
        </div>
      </section>
    </div>
  );
}
