import React from 'react';
import { Link } from 'react-router-dom';
import { Mic } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const VoiceSetup: React.FC = () => <SetupStepCard title="Companion and audio availability" subtitle="The text companion is available; microphone and speech engines are not integrated." icon={<Mic className="h-6 w-6" />} prevPath="/setup/telegram" nextPath="/setup/privacy">
  <p className="text-sm">The companion accepts typed English, Hindi and Hinglish messages. Supported runtime commands use the real control handlers; AI text requires an available configured model and a resumed runtime.</p>
  <p className="text-sm text-slate-500">Speech recognition, speech synthesis and wake-word support remain unavailable. This guide does not request microphone access or simulate a microphone test.</p>
  <Link to="/voice" className="text-cyan-600 dark:text-cyan-300 underline">Open text companion</Link>
</SetupStepCard>;
