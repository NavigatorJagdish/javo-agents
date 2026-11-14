import { useState, type FormEvent } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest, ApiError } from '../api/client';
type Asset = { id: string; title: string; asset_type: string; user_id: string };
type Account = { id: string; username: string; platform: string; user_id: string };
type Schedule = { id: string; asset_id: string; account_id: string; status: string; caption: string | null; scheduled_at: string };
type Preview = { schedule_id: string; fingerprint: string; snapshot: Record<string, unknown> };
type Receipt = { status: string; message: string; platform_post_id: string | null };
const inputStyle = 'w-full rounded border border-slate-400 bg-white dark:bg-slate-900 p-2';
const buttonStyle = 'rounded bg-cyan-700 text-white px-4 py-2 disabled:opacity-40';
export function Content() {
  const qc = useQueryClient();
  const [folder, setFolder] = useState('');
  const [asset, setAsset] = useState('');
  const [account, setAccount] = useState('');
  const [caption, setCaption] = useState('');
  const [when, setWhen] = useState('');
  const [preview, setPreview] = useState<Preview | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const assets = useQuery({ queryKey: ['content'], queryFn: () => apiRequest<Asset[]>('/api/content/'), retry: false });
  const accounts = useQuery({ queryKey: ['accounts'], queryFn: () => apiRequest<Account[]>('/api/accounts/'), retry: false });
  const schedules = useQuery({ queryKey: ['schedules'], queryFn: () => apiRequest<Schedule[]>('/api/content/schedule'), retry: false });
  async function act(work: () => Promise<void>) {
    setBusy(true); setError(''); setNotice('');
    try { await work(); }
    catch (e) {
      const detail = e instanceof ApiError ? (e.detail as { detail?: unknown })?.detail : null;
      setError(typeof detail === 'string' ? detail : e instanceof Error ? e.message : 'Action failed');
    } finally { setBusy(false); }
  }
  async function scan(e: FormEvent) {
    e.preventDefault();
    await act(async () => {
      const result = await apiRequest<{ discovered_files: number; imported_assets: Asset[] }>('/api/content/scan-folder', { method: 'POST', body: { folder_path: folder, recursive: true } });
      await qc.invalidateQueries({ queryKey: ['content'] });
      setNotice(result.discovered_files + ' files discovered; ' + result.imported_assets.length + ' imported.');
    });
  }
  async function schedule(e: FormEvent) {
    e.preventDefault();
    await act(async () => {
      const date = new Date(when + ':00+05:30');
      if (!Number.isFinite(date.getTime()) || date.getTime() <= Date.now()) throw new Error('Choose a future date and time in India Standard Time.');
      await apiRequest('/api/content/schedule', { method: 'POST', body: { asset_id: asset, account_id: account, caption, scheduled_at: date.toISOString() } });
      await qc.invalidateQueries({ queryKey: ['schedules'] });
      setNotice('Schedule saved. Review and approve separately. Automatic timed dispatch is not enabled yet.');
    });
  }
  return <section className="space-y-6 text-slate-900 dark:text-slate-100">
    <h1 className="text-3xl font-semibold">Content workflow</h1>
    <p>Import local files, prepare a schedule and review the exact content before simulating dispatch. No social post will be sent.</p>
    {error && <p role="alert" className="border border-red-500 rounded p-3">{error}</p>}
    {notice && <p role="status" className="border border-cyan-600 rounded p-3">{notice}</p>}
    {(assets.isError || accounts.isError || schedules.isError) && <p role="alert">Runtime data unavailable. Reconnect and refresh; no demo records are substituted.</p>}
    <form onSubmit={scan} className="space-y-3 rounded-xl border border-slate-400 p-5">
      <h2 className="text-xl font-semibold">1. Import</h2>
      <label className="block">Local folder path<input className={inputStyle} value={folder} onChange={e => setFolder(e.target.value)} required /></label>
      <button className={buttonStyle} disabled={busy}>Scan folder</button>
      <p>{assets.data?.length ?? 0} assets loaded (first 50).</p>
    </form>
    <form onSubmit={schedule} className="space-y-3 rounded-xl border border-slate-400 p-5">
      <h2 className="text-xl font-semibold">2. Prepare schedule</h2>
      <label className="block" htmlFor="content-asset">Asset</label>
      <select id="content-asset" className={inputStyle} required value={asset} onChange={e => setAsset(e.target.value)}><option value="">Choose asset</option>{assets.data?.map(a => <option key={a.id} value={a.id}>{a.title} ({a.asset_type})</option>)}</select>
      <label className="block" htmlFor="content-destination">Destination</label>
      <select id="content-destination" className={inputStyle} required value={account} onChange={e => setAccount(e.target.value)}><option value="">Choose destination</option>{accounts.data?.map(a => <option key={a.id} value={a.id}>{a.username} ({a.platform})</option>)}</select>
      <button type="button" disabled={busy} className={buttonStyle} onClick={() => act(async () => {
        const created = await apiRequest<Account>('/api/accounts/', { method: 'POST', body: { platform: 'other', username: 'Local simulation', metadata: { simulation_only: true } } });
        await qc.invalidateQueries({ queryKey: ['accounts'] }); setAccount(created.id); setNotice('Disconnected simulation destination created. No OAuth or remote account connected.');
      })}>Add local simulation destination</button>
      <label className="block">Caption<textarea className={inputStyle} value={caption} onChange={e => setCaption(e.target.value)} /></label>
      <label className="block">Planned time — IST (UTC+05:30)<input className={inputStyle} type="datetime-local" required value={when} onChange={e => setWhen(e.target.value)} /></label>
      <button className={buttonStyle} disabled={busy || !asset || !account}>Save schedule</button>
    </form>
    <section className="space-y-3 rounded-xl border border-slate-400 p-5">
      <h2 className="text-xl font-semibold">3. Review and simulate</h2>
      {schedules.data?.length === 0 && <p>No schedules yet.</p>}
      {schedules.data?.map(item => <article key={item.id} className="border-b border-slate-500 py-3 space-y-2">
        <p className="break-all">{item.id} · {item.status}</p><p>{item.caption || '(No caption)'}</p>
        <p>Planned UTC: {item.scheduled_at}</p>
        <div className="flex flex-wrap gap-2">
          <button disabled={busy} className={buttonStyle} onClick={() => act(async () => { setReceipt(null); setPreview(await apiRequest<Preview>('/api/content/schedule/' + item.id + '/preview')); })}>Review preview</button>
          <button disabled={busy} className={buttonStyle} onClick={() => act(async () => { setReceipt(await apiRequest<Receipt>('/api/content/schedule/' + item.id + '/receipt')); })}>Load saved receipt</button>
        </div>
      </article>)}
      {preview && <article className="rounded border border-cyan-600 p-4 space-y-3">
        <h3 className="text-lg font-semibold">Exact review snapshot</h3>
        <pre className="whitespace-pre-wrap break-all text-sm">{JSON.stringify(preview.snapshot, null, 2)}</pre>
        <button disabled={busy} className={buttonStyle} onClick={() => act(async () => {
          await apiRequest('/api/content/schedule/' + preview.schedule_id + '/approve', { method: 'POST', body: { mode: 'mock', fingerprint: preview.fingerprint } });
          await qc.invalidateQueries({ queryKey: ['schedules'] }); setNotice('This exact snapshot is approved for simulation. Use Simulate now to dispatch.');
        })}>Approve this snapshot for simulation</button>
        <button disabled={busy} className={buttonStyle} onClick={() => act(async () => {
          setReceipt(await apiRequest<Receipt>('/api/content/schedule/' + preview.schedule_id + '/publish', { method: 'POST' }));
          await qc.invalidateQueries({ queryKey: ['schedules'] });
        })}>Simulate now</button>
        <p className="text-sm">Manual simulation runs now, regardless of planned time. Approval is checked again by the runtime.</p>
      </article>}
      {receipt && <article role="status" className="rounded border border-cyan-600 p-4"><h3>Receipt: {receipt.status}</h3><p>{receipt.message}</p><p className="break-all">{receipt.platform_post_id}</p></article>}
    </section>
  </section>;
}
