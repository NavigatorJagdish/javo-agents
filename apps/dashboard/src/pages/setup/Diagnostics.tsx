import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity } from 'lucide-react';
import { Badge, Button } from '@javo/design-system';
import { apiRequest } from '../../api/client';
import { SetupStepCard } from './SetupStepCard';

type DiagnosticsResult = { overall: string; checks: { name: string; status: string; message: string | null }[] };
export const Diagnostics: React.FC = () => {
  const checks = useQuery({ queryKey: ['setup-diagnostics'], queryFn: () => apiRequest<DiagnosticsResult>('/api/health/diagnostics'), retry: false });
  return <SetupStepCard title="Runtime service diagnostics" subtitle="Results from the runtime computer; no sample pass marks." icon={<Activity className="h-6 w-6" />} prevPath="/setup/privacy" nextPath="/setup/complete" nextLabel="Finish guide">
    {checks.isPending && <p>Checking runtime services…</p>}
    {checks.isError && <p role="alert">Diagnostics could not be loaded. Reconnect and retry.</p>}
    {checks.data && <div className="space-y-3"><p>Runtime service status: {checks.data.overall}</p>{checks.data.checks.map(check => <div key={check.name} className="rounded-xl border border-slate-300 dark:border-white/20 p-3"><div className="flex flex-wrap justify-between gap-2"><span>{check.name}</span><Badge status={check.status === 'ok' ? 'active' : 'warning'}>{check.status}</Badge></div>{check.message && <p className="text-sm mt-1">{check.message}</p>}</div>)}</div>}
    <p className="text-sm text-slate-500">These checks do not verify whole-database encryption, model generation, platform access, audio engines, release signing or every specialist.</p>
    <Button variant="secondary" disabled={checks.isFetching} onClick={() => checks.refetch()}>Run diagnostics again</Button>
  </SetupStepCard>;
};
