import React, { useState } from 'react';
import { BrainCircuit } from 'lucide-react';
import { Chip } from '@javo/design-system';
import { SetupStepCard } from './SetupStepCard';

export const AISetup: React.FC = () => {
  const [mode, setMode] = useState<'hybrid' | 'local'>('hybrid');
  const [localModel, setLocalModel] = useState('qwen2.5:14b');

  return (
    <SetupStepCard
      title="AI Provider Routing"
      subtitle="Choose between 100% offline local inference or hybrid local + Gemini fallback."
      icon={<BrainCircuit className="h-6 w-6" />}
      prevPath="/setup/hardware"
      nextPath="/setup/folder"
    >
      <div className="flex gap-2">
        <Chip
          label="Hybrid (Local + Gemini)"
          selected={mode === 'hybrid'}
          onClick={() => setMode('hybrid')}
        />
        <Chip
          label="100% Local Ollama"
          selected={mode === 'local'}
          variant="violet"
          onClick={() => setMode('local')}
        />
      </div>

      <div>
        <label className="block text-xs font-medium mb-1">Primary Local Model</label>
        <select
          value={localModel}
          onChange={(e) => setLocalModel(e.target.value)}
          className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
        >
          <option value="qwen2.5:14b">qwen2.5:14b (Recommended for 12GB VRAM)</option>
          <option value="llama3.2:8b">llama3.2:8b (Fastest)</option>
          <option value="mistral-nemo:12b">mistral-nemo:12b</option>
        </select>
      </div>

      {mode === 'hybrid' && (
        <div>
          <label className="block text-xs font-medium mb-1">Gemini API Key (Optional)</label>
          <input
            type="password"
            placeholder="AIzaSy..."
            className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm font-mono"
          />
        </div>
      )}
    </SetupStepCard>
  );
};
