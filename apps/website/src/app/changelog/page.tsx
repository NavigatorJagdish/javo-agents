import type { Metadata } from 'next';
import Link from 'next/link';
import { Tag } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { CHANGELOG_ENTRIES } from '@/data/changelog';

export const metadata: Metadata = {
  title: 'Changelog',
  description:
    'Release changelog for Javo Agents including v0.1.0-alpha local-first runtime, 29 agents, Android companion, and official website.',
};

export default function ChangelogPage() {
  return (
    <div>
      <PageHeader
        badge="Release History"
        title="Javo Agents"
        highlight="Changelog"
        subtitle="Verified release notes documenting implemented modules, connector status, and milestone updates."
      />

      <section className="mx-auto max-w-4xl space-y-8 px-4 py-14 sm:px-6 lg:px-8">
        {CHANGELOG_ENTRIES.map((entry) => (
          <article key={entry.version} className="glass-card p-6 sm:p-8">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4 dark:border-white/10">
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#00E5FF]/15 px-3 py-1 font-mono text-xs font-bold text-[#007B8F] dark:text-[#00E5FF]">
                  <Tag className="h-3.5 w-3.5" />
                  v{entry.version}
                </span>
                <span className="rounded-full border border-[#8B5CF6]/40 bg-[#8B5CF6]/10 px-2.5 py-0.5 text-xs font-medium text-[#6D28D9] dark:text-[#A78BFA]">
                  {entry.status}
                </span>
              </div>
              <time className="font-mono text-xs text-slate-500 dark:text-[#94A3B8]">
                {entry.date}
              </time>
            </div>

            <p className="mt-4 text-sm leading-relaxed text-slate-700 dark:text-[#E2E6F0]/90">
              {entry.summary}
            </p>

            <div className="mt-6 grid gap-5 sm:grid-cols-2">
              {entry.highlights.map((group) => (
                <div
                  key={group.area}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-[#0B1026]/80"
                >
                  <h2 className="font-display text-sm font-bold text-slate-900 dark:text-white">
                    {group.area}
                  </h2>
                  <ul className="mt-2.5 space-y-1.5 text-xs leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                    {group.details.map((detail) => (
                      <li key={detail} className="flex items-start gap-2">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#00E5FF]" />
                        <span>{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </article>
        ))}

        <div className="flex gap-3">
          <Link href="/roadmap" className="btn-primary">
            View Public Roadmap
          </Link>
          <Link href="/download" className="btn-secondary">
            Download v0.1.0-alpha
          </Link>
        </div>
      </section>
    </div>
  );
}
