import React from 'react';
import { Link } from 'react-router-dom';
import { Palette } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const BrandSetup: React.FC = () => <SetupStepCard title="Brand voice and identity" subtitle="Save separate brand rules for each account." icon={<Palette className="h-6 w-6" />} prevPath="/setup/social" nextPath="/setup/autopilot">
  <p className="text-sm">Open an account's Brand profile to save its name, voice, audience and content pillars. Changes there persist across restarts.</p>
  <Link to="/accounts" className="inline-block text-cyan-600 dark:text-cyan-300 underline">Manage account brand profiles</Link>
  <p className="text-sm text-slate-500">Automatic Brand Manager execution and platform publishing remain under development. Continuing this guide does not save a brand profile.</p>
</SetupStepCard>;
