import React from 'react';
import Link from 'next/link';
import { Github, ShieldCheck } from 'lucide-react';
import { JavoLogo } from './JavoLogo';
import { FOOTER_COLUMNS, SITE_CONFIG } from '@/data/site';

export function Footer() {
  return (
    <footer className="border-t border-slate-200/80 bg-slate-50 dark:border-white/10 dark:bg-[#080C1D]">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <JavoLogo size={38} showWordmark animated={false} />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/75">
              {SITE_CONFIG.tagline}. Local-first AI automation for Windows &amp; Android, running 29 specialist agents on your own hardware with Supervised Autopilot.
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 font-medium text-emerald-700 dark:text-emerald-300">
                <ShieldCheck className="h-3.5 w-3.5" />
                {SITE_CONFIG.version} · {SITE_CONFIG.license} Open Source
              </span>
              <a
                href={SITE_CONFIG.githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-300 px-3 py-1 font-medium text-slate-700 transition hover:border-[#00E5FF] dark:border-white/15 dark:text-[#E2E6F0]"
              >
                <Github className="h-3.5 w-3.5" />
                Source on GitHub
              </a>
            </div>
          </div>

          {FOOTER_COLUMNS.map((column) => (
            <div key={column.title}>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
                {column.title}
              </h3>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-slate-600 transition hover:text-[#008BA3] dark:text-[#E2E6F0]/75 dark:hover:text-[#00E5FF]"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-start justify-between gap-4 border-t border-slate-200/80 pt-8 text-xs text-slate-500 dark:border-white/10 dark:text-[#94A3B8] sm:flex-row sm:items-center">
          <p>
            Javo Agents · Initial Release Free ($0/month) · MIT License · Local-First Architecture
          </p>
          <p>
            Interactive demos on this site are clearly labeled simulations running in your browser.
          </p>
        </div>
      </div>
    </footer>
  );
}
