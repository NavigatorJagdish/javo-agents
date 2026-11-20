import React from 'react';
import { Link } from 'react-router-dom';
import { Mic } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const VoiceSetup: React.FC = () => <SetupStepCard title="Companion and local voice setup" subtitle="Select installed local speech models and test a short sample in Voice." icon={<Mic className="h-6 w-6" />} prevPath="/setup/telegram" nextPath="/setup/privacy">
  <p className="text-sm">The companion accepts typed English, Hindi and Hinglish messages. Supported runtime commands use the real control handlers; AI text requires an available configured model and a resumed runtime.</p>
  <p className="text-sm text-slate-500">Voice supports local Kokoro speech presets/effects and Whisper transcript review when their models are installed and selected. Wake word and voice-model training remain unavailable. This guide does not request microphone access or certify language quality.</p>
  <Link to="/voice" className="text-cyan-600 dark:text-cyan-300 underline">Open companion and voice studio</Link>
</SetupStepCard>;
