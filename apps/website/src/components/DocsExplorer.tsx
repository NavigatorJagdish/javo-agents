'use client';

import React, { useMemo, useState } from 'react';
import { BookOpen, Check, Copy, Search } from 'lucide-react';
import { DOC_SECTIONS, type DocSection } from '@/data/docs';

const CATEGORIES: Array<'All' | DocSection['category']> = [
  'All',
  'Getting Started',
  'AI & Voice',
  'Channels & Content',
  'Security & Operations',
];

export function DocsExplorer() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<'All' | DocSection['category']>('All');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return DOC_SECTIONS.filter((doc) => {
      const catMatch = category === 'All' || doc.category === category;
      const queryMatch =
        !q ||
        doc.title.toLowerCase().includes(q) ||
        doc.summary.toLowerCase().includes(q) ||
        doc.steps.some((s) => s.toLowerCase().includes(q)) ||
        doc.notes.some((n) => n.toLowerCase().includes(q));
      return catMatch && queryMatch;
    });
  }, [query, category]);

  const handleCopy = async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 1800);
    } catch {
      // Clipboard unavailable in restricted browser context
    }
  };

  return (
    <div className="grid gap-8 lg:grid-cols-12">
      {/* Sidebar TOC */}
      <aside className="lg:col-span-4">
        <div className="glass-card sticky top-24 p-5">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search 12 documentation guides..."
              aria-label="Search documentation"
              className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#00E5FF] focus:outline-none dark:border-white/15 dark:bg-[#0B1026] dark:text-white"
            />
          </div>

          <div className="mt-4 flex flex-wrap gap-1.5">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition ${
                  category === cat
                    ? 'bg-[#00E5FF]/20 text-[#007B8F] ring-1 ring-[#00E5FF]/40 dark:text-[#00E5FF]'
                    : 'bg-slate-100 text-slate-600 hover:text-slate-900 dark:bg-white/5 dark:text-[#94A3B8] dark:hover:text-white'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <nav aria-label="Documentation topics" className="mt-5 space-y-1">
            {DOC_SECTIONS.map((doc) => (
              <a
                key={doc.id}
                href={`#${doc.id}`}
                className="flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 dark:text-[#E2E6F0]/80 dark:hover:bg-white/5 dark:hover:text-[#00E5FF]"
              >
                <BookOpen className="h-3.5 w-3.5 shrink-0 text-[#00E5FF]" />
                <span>{doc.title}</span>
              </a>
            ))}
          </nav>
        </div>
      </aside>

      {/* Main Guides */}
      <div className="space-y-6 lg:col-span-8">
        {filtered.length === 0 ? (
          <div className="glass-card p-8 text-center">
            <p className="text-sm font-medium text-slate-700 dark:text-[#E2E6F0]">
              No documentation guides matched &ldquo;{query}&rdquo;.
            </p>
            <button
              type="button"
              onClick={() => {
                setQuery('');
                setCategory('All');
              }}
              className="btn-secondary mt-4"
            >
              Reset Search
            </button>
          </div>
        ) : (
          filtered.map((doc) => (
            <article key={doc.id} id={doc.id} className="glass-card scroll-mt-24 p-6 sm:p-7">
              <span className="font-mono text-xs font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
                {doc.category}
              </span>
              <h2 className="mt-1.5 font-display text-2xl font-bold text-slate-900 dark:text-white">
                {doc.title}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/85">
                {doc.summary}
              </p>

              <ol className="mt-5 space-y-2.5 text-sm text-slate-700 dark:text-[#E2E6F0]/90">
                {doc.steps.map((step, index) => (
                  <li key={step} className="flex items-start gap-3">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#00E5FF]/15 font-mono text-xs font-bold text-[#007B8F] dark:text-[#00E5FF]">
                      {index + 1}
                    </span>
                    <span className="pt-0.5 leading-relaxed">{step}</span>
                  </li>
                ))}
              </ol>

              {doc.codeSnippet && (
                <div className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-slate-950 dark:border-white/10">
                  <div className="flex items-center justify-between border-b border-white/10 px-4 py-2 text-xs text-slate-300">
                    <span className="font-mono">{doc.codeSnippet.label}</span>
                    <button
                      type="button"
                      onClick={() => handleCopy(doc.id, doc.codeSnippet!.code)}
                      className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs hover:bg-white/10"
                    >
                      {copiedId === doc.id ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-400" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" />
                          Copy
                        </>
                      )}
                    </button>
                  </div>
                  <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-slate-100">
                    {doc.codeSnippet.code}
                  </pre>
                </div>
              )}

              {doc.notes.length > 0 && (
                <div className="mt-5 rounded-xl border border-[#8B5CF6]/30 bg-[#8B5CF6]/5 p-4 text-xs text-slate-700 dark:text-[#E2E6F0]/85">
                  <ul className="space-y-1">
                    {doc.notes.map((note) => (
                      <li key={note}>• {note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </article>
          ))
        )}
      </div>
    </div>
  );
}
