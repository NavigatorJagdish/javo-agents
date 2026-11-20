import { useEffect, useState, type ReactNode, type FormEvent } from 'react';
import { apiRequest, setOwnerToken } from '../api/client';
export function OwnerAccess({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [token, setToken] = useState('');
  const [message, setMessage] = useState('Connecting to local runtime…');
  const [busy, setBusy] = useState(false);
  async function connect(event?: FormEvent) {
    event?.preventDefault(); setBusy(true);
    if (event) setOwnerToken(token.trim());
    try { await apiRequest('/api/health/'); setToken(''); setReady(true); }
    catch { setOwnerToken(''); setMessage('Runtime unavailable or authorization required. Start the desktop app, or enter the owner token configured for your local runtime.'); }
    finally { setBusy(false); }
  }
  useEffect(() => { void connect(); }, []);
  if (ready) return <>{children}</>;
  return <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
    <form onSubmit={connect} className="max-w-lg w-full space-y-4">
      <h1 className="text-2xl font-semibold">Javo Agents · Local access</h1>
      <p role="status">{message}</p>
      <label className="block" htmlFor="owner-token">Owner access token</label>
      <input id="owner-token" type="password" autoComplete="off" value={token}
        onChange={event => setToken(event.target.value)} className="w-full rounded bg-slate-800 p-3" />
      <button disabled={busy} className="rounded bg-cyan-700 px-4 py-2" type="submit">{busy ? 'Connecting…' : 'Connect / retry'}</button>
      <p className="text-sm text-slate-400">Token stays in memory for this tab only. The desktop app supplies its credential automatically.</p>
    </form>
  </main>;
}
