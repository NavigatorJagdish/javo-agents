import React, { useState } from 'react';
import { Mic } from 'lucide-react';
import { WaveformVisualizer, Button } from '@javo/design-system';
import { SetupStepCard } from './SetupStepCard';

export const VoiceSetup: React.FC = () => {
  const [testing, setTesting] = useState(false);

  return (
    <SetupStepCard
      title="Voice Mode & Whisper STT"
      subtitle="Verify your studio microphone and neural TTS output."
      icon={<Mic className="h-6 w-6" />}
      prevPath="/setup/telegram"
      nextPath="/setup/privacy"
    >
      <div className="p-5 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10 flex flex-col items-center gap-4">
        <WaveformVisualizer active={testing} bars={24} height={48} />
        <Button size="sm" variant="secondary" onClick={() => setTesting(!testing)}>
          {testing ? 'Stop Mic Test' : 'Test Microphone Input'}
        </Button>
      </div>
    </SetupStepCard>
  );
};
