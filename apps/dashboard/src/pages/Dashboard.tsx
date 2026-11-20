import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '../api/client';
import { useHealthQuery } from '../api/hooks';
type SystemInfo = { cpu_percent: number; ram_percent: number; ram_total_mb: number;
  resource_profile: { name: string; max_concurrent_agents: number; memory_headroom_mb: number; basis: string } };
export function Dashboard() {
  const health = useHealthQuery();
  const system = useQuery({ queryKey: ['system'], queryFn: () => apiRequest<SystemInfo>('/api/health/system'), refetchInterval: 15000, retry: false });
  const schedules = useQuery({ queryKey: ['schedules'], queryFn: () => apiRequest<Array<{ id: string; status: string; scheduled_at: string }>>('/api/content/schedule'), retry: false });
  return <section className="space-y-6 text-slate-900 dark:text-slate-100">
    <header><h1 className="text-3xl font-semibold">Local runtime</h1><p className="mt-2 text-slate-500">Measured runtime status. Live social publishing is not enabled.</p></header>
    {(health.isError || system.isError || schedules.isError) && <p role="alert" className="rounded border border-red-500 p-4">Some data could not be loaded. Check the runtime and authorization.</p>}
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[
        ['Runtime', health.data?.status ?? 'Unavailable'], ['Database', health.data?.database ?? 'Unavailable'],
        ['CPU', system.data ? system.data.cpu_percent + '%' : 'Unavailable'],
        ['RAM', system.data ? system.data.ram_percent + '%' : 'Unavailable'],
      ].map(([label, value]) => <article key={label} className="rounded-xl border border-slate-300 dark:border-slate-700 p-5"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-xl font-semibold">{value}</p></article>)}
    </div>
    <article className="rounded-xl border border-slate-300 dark:border-slate-700 p-5">
      <h2 className="text-xl font-semibold">Resource profile</h2>
      {system.data ? <div className="mt-3 space-y-2">
        <p>{system.data.resource_profile.name} · {Math.round(system.data.ram_total_mb / 1024)} GB detected · {system.data.resource_profile.max_concurrent_agents} worker slots</p>
        <p>{system.data.resource_profile.memory_headroom_mb} MB reserved headroom</p>
        <p className="text-sm text-slate-500">{system.data.resource_profile.basis}. 8GB is the baseline target; larger machines can use larger profiles.</p>
      </div> : <p>Resource data unavailable.</p>}
    </article>
    <article className="rounded-xl border border-slate-300 dark:border-slate-700 p-5">
      <h2 className="text-xl font-semibold">Persisted schedules</h2>
      {schedules.isPending ? <p>Loading…</p> : schedules.data?.length === 0 ? <p className="mt-3">No schedules created yet.</p> :
        <ul className="mt-3 space-y-2">{schedules.data?.map(item => <li key={item.id} className="break-all">{item.id} · {item.status} · {item.scheduled_at}</li>)}</ul>}
      <p className="mt-4 text-sm text-slate-500">Approval is bound to content and destination. Mock dispatch creates an explicitly simulated receipt.</p>
    </article>
  </section>;
}
