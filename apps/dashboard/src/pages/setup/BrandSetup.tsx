import React, { useState } from 'react';
import { Palette } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const BrandSetup: React.FC = () => {
  const [brandName, setBrandName] = useState('Javo Tech Studio');
  const [niche, setNiche] = useState('Local AI, Automation & Creator Engineering');

  return (
    <SetupStepCard
      title="Brand Voice & Identity"
      subtitle="Brand Manager (#06) uses these guidelines to write captions and replies."
      icon={<Palette className="h-6 w-6" />}
      prevPath="/setup/social"
      nextPath="/setup/autopilot"
    >
      <div>
        <label className="block text-xs font-medium mb-1">Studio / Creator Name</label>
        <input
          value={brandName}
          onChange={(e) => setBrandName(e.target.value)}
          className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
        />
      </div>
      <div>
        <label className="block text-xs font-medium mb-1">Core Niche & Audience</label>
        <input
          value={niche}
          onChange={(e) => setNiche(e.target.value)}
          className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
        />
      </div>
    </SetupStepCard>
  );
};
