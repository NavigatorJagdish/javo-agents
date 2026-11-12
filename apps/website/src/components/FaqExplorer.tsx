'use client';

import React, { useMemo, useState } from 'react';
import { ChevronDown, Search } from 'lucide-react';
import { FAQ_ITEMS, type FaqItem } from '@/data/faq';

const CATEGORIES: Array<'All' | FaqItem['category']> = [
  'All',
  'General',
  'Pricing & Open Source',
  'Privacy & Hardware',
  'Social & Voice',
];

export function FaqExplorer() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<'All' | FaqItem['category']>('All');
  const [openId, setOpenId] = useState<string | null>(FAQ_ITEMS[0].id);

  const items = useMemo(() => {
    const q = query.trim().toLowerCase();
    return FAQ_ITEMS.filter((item) => {
      const catMatch = category === 'All' || item.category === category;
      const qMatch =
        !q ||
        item.question.toLowerCase().includes(q) ||
        item.answer.toLowerCase().includes(q);
      return catMatch && qMatch;
    });
  }, [query, category]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="relative w-full md:max-w-sm">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search FAQs..."
            aria-label="Search FAQs"
            className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pl-10 pr-4 text-sm text-slate-900 focus:border-[#00E5FF] focus:outline-none dark:border-white/15 dark:bg-[#111836] dark:text-white"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setCategory(cat)}
              className={`rounded-xl px-3 py-2 text-xs font-semibold transition ${
                category === cat
                  ? 'bg-gradient-to-r from-[#00E5FF] to-[#8B5CF6] text-[#0B1026]'
                  : 'border border-slate-300 bg-white text-slate-700 dark:border-white/15 dark:bg-white/5 dark:text-[#E2E6F0]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item) => {
          const isOpen = openId === item.id;
          return (
            <div key={item.id} className="glass-card overflow-hidden">
              <button
                type="button"
                aria-expanded={isOpen}
                onClick={() => setOpenId(isOpen ? null : item.id)}
                className="flex w-full items-center justify-between gap-4 p-5 text-left"
              >
                <div>
                  <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
                    {item.category}
                  </span>
                  <h2 className="mt-1 font-display text-base font-bold text-slate-900 dark:text-white sm:text-lg">
                    {item.question}
                  </h2>
                </div>
                <ChevronDown
                  className={`h-5 w-5 shrink-0 text-slate-400 transition-transform ${
                    isOpen ? 'rotate-180 text-[#00E5FF]' : ''
                  }`}
                />
              </button>
              {isOpen && (
                <div className="border-t border-slate-200 px-5 pb-5 pt-4 text-sm leading-relaxed text-slate-600 dark:border-white/10 dark:text-[#E2E6F0]/85">
                  {item.answer}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
