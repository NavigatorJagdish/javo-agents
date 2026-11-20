import React from 'react';
import { Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const PrivacyControls: React.FC = () => <SetupStepCard title="Privacy and recovery boundaries" subtitle="Review the protections that are implemented and what still needs work." icon={<Shield className="h-6 w-6" />} prevPath="/setup/voice" nextPath="/setup/diagnostics">
  <p className="text-sm">The local runtime requires its owner credential. AI requests pass through the existing privacy checks; paid cloud execution is disabled. Provider and migrated social credentials use encrypted storage.</p>
  <p className="text-sm">Account names, brand rules, content and other database records are not covered by whole-database encryption. Unknown legacy text may still contain sensitive data. Avoid putting secrets in captions, brand rules or prompts.</p>
  <p className="text-sm text-slate-500">Database snapshots omit separate credential stores, keys, usage accounting and media. Complete encrypted profile recovery and export/deletion tools still need implementation. This guide does not change privacy settings.</p>
  <Link to="/settings" className="text-cyan-600 dark:text-cyan-300 underline">Open provider and backup settings</Link>
</SetupStepCard>;
