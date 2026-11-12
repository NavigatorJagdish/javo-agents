import type { Metadata } from 'next';
import Link from 'next/link';
import { CheckCircle2, Compass } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { ROADMAP_STAGES } from '@/data/roadmap';

export const metadata: Metadata = {
  title: 'Public Roadmap',
  description:
    'Transparent public roadmap for Javo Agents from v0.1.0-alpha local-first foundation to hardened connectors and optional E2EE cloud sync.',
};

export default function RoadmapPage() {
  return (
    <div>
      <PageHeader
        badge="Public Direction"
        title="Javo Agents"
        highlight="Roadmap"
        subtitle="Where Javo Agents stands today and what is planned next—with zero fabricated ship dates or overpromised integrations."
      />

      <section className="mx-auto max-w-5xl space-y-6 px-4 py-14 sm:px-6 lg:px-8">
        {ROADMAP_STAGES.map((stage) => (
          <div key={stage.phase} className="glass-card p-6 sm:p-7">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#007B8F] dark:text-[#00E5FF]">
                <Compass className="h-4 w-4" />
                {stage.horizon}
              </span>
              <span
                className={`rounded-full px-3 py-0.5 text-xs font-semibold ${
                  stage.status === 'In Progress (Current)'
                    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                    : 'bg-[#8B5CF6]/15 text-[#6D28D9] dark:text-[#A78BFA]'
                }`}
              >
                {stage.status}
              </span>
            </div>

            <h2 className="mt-2 font-display text-xl font-bold text-slate-900 dark:text-white">
              {stage.phase}
            </h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-[#E2E6F0]/85">
              {stage.description}
            </p>

            <ul className="mt-4 grid gap-2.5 sm:grid-cols-2">
              {stage.items.map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700 dark:border-white/10 dark:bg-[#0B1026]/80 dark:text-[#E2E6F0]/90"
                >
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#00E5FF]" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}

        <div className="flex flex-wrap gap-3 pt-2">
          <Link href="/integrations" className="btn-primary">
            Check Connector Status Matrix
          </Link>
          <Link href="/contact" className="btn-secondary">
            Propose Features on GitHub
          </Link>
        </div>
      </section>
    </div>
  );
}
