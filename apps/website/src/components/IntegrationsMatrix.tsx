'use client';

import React, { useMemo, useState } from 'react';
import { Check, Info } from 'lucide-react';
import { StatusBadge } from '@/components/StatusBadge';
import { INTEGRATIONS, type IntegrationStatus } from '@/data/integrations';

const STATUS_FILTERS: Array<'All' | IntegrationStatus> = [
  'All',
  'Supported',
  'Beta',
  'Planned',
  'Unavailable',
];

export function IntegrationsMatrix() {
  const [filter, setFilter] = useState<'All' | IntegrationStatus>('All');

  const items = useMemo(() => {
    if (filter === 'All') return INTEGRATIONS;
    return INTEGRATIONS.filter((item) => item.status === filter);
  }, [filter]);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => setFilter(status)}
              className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                filter === status
                  ? 'bg-gradient-to-r from-[#00E5FF] to-[#8B5CF6] text-[#0B1026]'
                  : 'border border-slate-300 bg-white text-slate-700 hover:border-[#00E5FF] dark:border-white/15 dark:bg-white/5 dark:text-[#E2E6F0]'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
        <p className="text-xs text-slate-500 dark:text-[#94A3B8]">
          Showing {items.length} of {INTEGRATIONS.length} connectors
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {items.map((item) => (
          <div key={item.id} className="glass-card flex flex-col justify-between p-6">
            <div>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="text-xs font-medium text-slate-500 dark:text-[#94A3B8]">
                    {item.category}
                  </span>
                  <h2 className="mt-1 font-display text-xl font-bold text-slate-900 dark:text-white">
                    {item.name}
                  </h2>
                </div>
                <StatusBadge status={item.status} />
              </div>

              <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/85">
                {item.summary}
              </p>

              <div className="mt-4 grid gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3.5 text-xs dark:border-white/10 dark:bg-[#0B1026]/80 sm:grid-cols-2">
                <div>
                  <span className="font-semibold text-slate-500 dark:text-[#94A3B8]">Auth:</span>{' '}
                  <span className="text-slate-800 dark:text-white">{item.authMethod}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-500 dark:text-[#94A3B8]">Cost:</span>{' '}
                  <span className="text-slate-800 dark:text-white">{item.costModel}</span>
                </div>
              </div>

              <ul className="mt-4 space-y-1.5 text-xs text-slate-600 dark:text-[#E2E6F0]/85">
                {item.capabilities.map((cap) => (
                  <li key={cap} className="flex items-start gap-2">
                    <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#00E5FF]" />
                    <span>{cap}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-5 flex items-start gap-2 rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-slate-600 dark:text-[#E2E6F0]/80">
              <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" />
              <span>{item.limitations}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
