import React from 'react';
import type { IntegrationStatus } from '@/data/integrations';

const STATUS_STYLES: Record<IntegrationStatus, string> = {
  Supported:
    'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  Beta:
    'border-[#00E5FF]/40 bg-[#00E5FF]/10 text-[#007B8F] dark:text-[#00E5FF]',
  Planned:
    'border-[#8B5CF6]/40 bg-[#8B5CF6]/10 text-[#6D28D9] dark:text-[#A78BFA]',
  Unavailable:
    'border-amber-500/35 bg-amber-500/10 text-amber-700 dark:text-amber-300',
};

export function StatusBadge({ status }: { status: IntegrationStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${STATUS_STYLES[status]}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          status === 'Supported'
            ? 'bg-emerald-400'
            : status === 'Beta'
              ? 'bg-[#00E5FF]'
              : status === 'Planned'
                ? 'bg-[#8B5CF6]'
                : 'bg-amber-400'
        }`}
      />
      {status}
    </span>
  );
}
