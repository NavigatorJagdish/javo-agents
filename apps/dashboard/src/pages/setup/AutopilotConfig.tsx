import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Zap } from 'lucide-react';
import { apiRequest } from '../../api/client';
import { SetupStepCard } from './SetupStepCard';

export const AutopilotConfig: React.FC = () => {
  const control = useQuery({ queryKey: ['setup-control'], queryFn: () => apiRequest<{ paused: boolean; emergency_stopped: boolean }>('/api/security/autopilot-status'), retry: false });
  return <SetupStepCard title="Runtime controls and approval" subtitle="Review the saved pause state; sensitive actions need separate review." icon={<Zap className="h-6 w-6" />} prevPath="/setup/brand" nextPath="/setup/telegram">
    {control.isPending && <p>Reading runtime state…</p>}
    {control.isError && <p role="alert">Runtime control state is unavailable.</p>}
    {control.data && <p>Runtime state: {control.data.emergency_stopped ? 'Emergency stopped' : control.data.paused ? 'Paused' : 'Resumed'}.</p>}
    <p className="text-sm">Use the dashboard's pause, resume and emergency-stop controls. Resuming permits supported local jobs; it does not approve content, activate paid AI or enable live publishing. Review each content snapshot separately.</p>
    <p className="text-sm text-slate-500">Automatic community replies and unrestricted workflow execution are not implemented. Continuing this guide does not change permissions or resume the runtime.</p>
    <Link to="/" className="text-cyan-600 dark:text-cyan-300 underline">Open runtime controls</Link>
  </SetupStepCard>;
};
