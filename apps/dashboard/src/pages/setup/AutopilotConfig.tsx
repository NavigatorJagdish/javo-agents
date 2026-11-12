import React, { useState } from 'react';
import { Zap } from 'lucide-react';
import { Chip } from '@javo/design-system';
import { SetupStepCard } from './SetupStepCard';

export const AutopilotConfig: React.FC = () => {
  const [level, setLevel] = useState<'assisted' | 'balanced' | 'autonomous'>('balanced');

  return (
    <SetupStepCard
      title="Autopilot Guardrails"
      subtitle="Control which actions execute automatically vs waiting for human sign-off."
      icon={<Zap className="h-6 w-6" />}
      prevPath="/setup/brand"
      nextPath="/setup/telegram"
    >
      <div className="flex flex-wrap gap-2">
        <Chip label="Assisted (All Approvals)" selected={level === 'assisted'} onClick={() => setLevel('assisted')} />
        <Chip label="Balanced (Recommended)" selected={level === 'balanced'} onClick={() => setLevel('balanced')} />
        <Chip label="Full Autopilot" selected={level === 'autonomous'} variant="violet" onClick={() => setLevel('autonomous')} />
      </div>
      <div className="p-4 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10 text-xs text-slate-600 dark:text-slate-300">
        {level === 'assisted' && 'Every publish, comment reply, and skill update requires manual approval.'}
        {level === 'balanced' && 'Low-risk FAQ replies and content drafts run automatically; publishing & skill installs require approval.'}
        {level === 'autonomous' && 'All QA-passing (>=85) workflows publish automatically within Budget & Account Guardian caps.'}
      </div>
    </SetupStepCard>
  );
};
