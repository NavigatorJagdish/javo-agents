import React, { useState } from 'react';
import { Shield } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const PrivacyControls: React.FC = () => {
  const [redactPii, setRedactPii] = useState(true);
  const [localOnlyMedia, setLocalOnlyMedia] = useState(true);

  return (
    <SetupStepCard
      title="Privacy Firewall Controls"
      subtitle="Configure data classification and external egress boundaries."
      icon={<Shield className="h-6 w-6" />}
      prevPath="/setup/voice"
      nextPath="/setup/diagnostics"
    >
      <label className="flex items-center justify-between p-4 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10 cursor-pointer">
        <div>
          <p className="text-sm font-semibold">Auto-Redact PII Before Cloud Calls</p>
          <p className="text-xs text-slate-400">Strips emails, phone numbers, and tokens before Gemini calls.</p>
        </div>
        <input
          type="checkbox"
          checked={redactPii}
          onChange={(e) => setRedactPii(e.target.checked)}
          className="h-4 w-4 accent-[#00E5FF]"
        />
      </label>

      <label className="flex items-center justify-between p-4 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10 cursor-pointer">
        <div>
          <p className="text-sm font-semibold">Keep Raw Media Local Only</p>
          <p className="text-xs text-slate-400">Video analysis runs exclusively on local Whisper + Qwen VL.</p>
        </div>
        <input
          type="checkbox"
          checked={localOnlyMedia}
          onChange={(e) => setLocalOnlyMedia(e.target.checked)}
          className="h-4 w-4 accent-[#00E5FF]"
        />
      </label>
    </SetupStepCard>
  );
};
