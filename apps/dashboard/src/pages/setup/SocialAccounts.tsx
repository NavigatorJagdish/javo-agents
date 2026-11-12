import React, { useState } from 'react';
import { Share2, Check } from 'lucide-react';
import { Button } from '@javo/design-system';
import { SetupStepCard } from './SetupStepCard';

export const SocialAccounts: React.FC = () => {
  const [connected, setConnected] = useState<string[]>(['YouTube', 'Instagram']);

  const toggle = (name: string) => {
    setConnected((prev) =>
      prev.includes(name) ? prev.filter((p) => p !== name) : [...prev, name]
    );
  };

  return (
    <SetupStepCard
      title="Connect Social Channels"
      subtitle="Authorize your publishing destinations using local PKCE OAuth."
      icon={<Share2 className="h-6 w-6" />}
      prevPath="/setup/folder"
      nextPath="/setup/brand"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {['YouTube', 'Instagram', 'Facebook', 'X'].map((p) => {
          const isConn = connected.includes(p);
          return (
            <div
              key={p}
              className="flex items-center justify-between p-4 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10"
            >
              <span className="font-semibold text-sm">{p}</span>
              <Button
                size="sm"
                variant={isConn ? 'secondary' : 'primary'}
                leftIcon={isConn ? <Check className="h-3.5 w-3.5" /> : undefined}
                onClick={() => toggle(p)}
              >
                {isConn ? 'Connected' : 'Connect'}
              </Button>
            </div>
          );
        })}
      </div>
    </SetupStepCard>
  );
};
