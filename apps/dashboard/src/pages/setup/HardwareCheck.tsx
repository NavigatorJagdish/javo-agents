import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Cpu } from 'lucide-react';
import { Button } from '@javo/design-system';
import { apiRequest } from '../../api/client';
import { SetupStepCard } from './SetupStepCard';

type SystemInfo = { cpu_count: number; cpu_percent: number; ram_total_mb: number; ram_used_mb: number; ram_percent: number; disk_total_gb: number; disk_used_gb: number; resource_profile: { name?: string; max_concurrent_agents?: number; memory_headroom_mb?: number } };
export const HardwareCheck: React.FC = () => {
  const system = useQuery({ queryKey: ['setup-system'], queryFn: () => apiRequest<SystemInfo>('/api/health/system'), retry: false });
  return <SetupStepCard title="Hardware and runtime check" subtitle="Current measurements from the runtime computer." icon={<Cpu className="h-6 w-6" />} prevPath="/setup/welcome" nextPath="/setup/ai">
    {system.isPending && <p>Reading system measurements…</p>}
    {system.isError && <p role="alert">System measurements are unavailable. Reconnect to the local runtime.</p>}
    {system.data && <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
      <div><dt>CPU threads</dt><dd>{system.data.cpu_count}</dd></div>
      <div><dt>CPU usage</dt><dd>{system.data.cpu_percent.toFixed(1)}%</dd></div>
      <div><dt>System memory</dt><dd>{(system.data.ram_total_mb / 1024).toFixed(1)} GiB total; {(system.data.ram_used_mb / 1024).toFixed(1)} GiB used</dd></div>
      <div><dt>System drive free space</dt><dd>{(system.data.disk_total_gb - system.data.disk_used_gb).toFixed(1)} GiB</dd></div>
      <div><dt>Selected resource profile</dt><dd>{system.data.resource_profile.name ?? 'Unavailable'}</dd></div>
      <div><dt>Worker concurrency limit</dt><dd>{system.data.resource_profile.max_concurrent_agents ?? 'Unavailable'}</dd></div>
    </dl>}
    <p className="text-sm text-slate-500">These readings are not a model benchmark. GPU/VRAM and instruction-set support have not been checked here. The 8GB baseline and larger hardware profiles still require workload testing.</p>
    <Button variant="secondary" disabled={system.isFetching} onClick={() => system.refetch()}>Re-scan hardware</Button>
  </SetupStepCard>;
};
