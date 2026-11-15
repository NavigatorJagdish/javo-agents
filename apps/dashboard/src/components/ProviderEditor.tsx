import { useState, type FormEvent } from 'react';
import { Button } from '@javo/design-system';
import { apiRequest, ApiError } from '../api/client';

export type ProviderInfo = { name: string; model: string; base_url: string | null; enabled: boolean; has_api_key: boolean };
const inputStyle = 'w-full rounded border border-slate-400 bg-white dark:bg-slate-900 p-2';

export function ProviderEditor({ provider, available, onSaved }: {
  provider: ProviderInfo; available: boolean; onSaved: () => Promise<void>;
}) {
  const [model, setModel] = useState(provider.model);
  const [endpoint, setEndpoint] = useState(provider.base_url ?? '');
  const [enabled, setEnabled] = useState(provider.enabled);
  const [key, setKey] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  async function run(work: () => Promise<void>) {
    setBusy(true); setError(''); setNotice('');
    try { await work(); }
    catch (failure) {
      const detail = failure instanceof ApiError ? (failure.detail as { detail?: unknown })?.detail : null;
      setError(typeof detail === 'string' ? detail : 'Provider configuration could not be saved.');
    } finally { setBusy(false); }
  }
  function save(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      await apiRequest('/api/settings/ai-providers/' + provider.name, { method: 'PUT', body: {
        model, enabled, ...(provider.name !== 'gemini' ? { base_url: endpoint } : {}),
        ...(key ? { api_key: key } : {}),
      } });
      setKey(''); await onSaved(); setNotice('Saved encrypted provider configuration. Connection has not been tested.');
    });
  }
  return <form onSubmit={save} className="border-b border-slate-500 py-4 space-y-3">
    <h3 className="font-semibold">{provider.name}</h3>
    {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    <label className="block">{provider.name} model
      <input className={inputStyle} value={model} required maxLength={128} disabled={!available || busy} onChange={event => setModel(event.target.value)} />
    </label>
    {provider.name !== 'gemini' && <label className="block">{provider.name} endpoint
      <input className={inputStyle} value={endpoint} required disabled={!available || busy} onChange={event => setEndpoint(event.target.value)} />
    </label>}
    <label className="flex gap-2 items-center"><input type="checkbox" checked={enabled} disabled={!available || busy} onChange={event => setEnabled(event.target.checked)} />Enable {provider.name}</label>
    {provider.name !== 'ollama' && <>
      <p>Saved key: {provider.has_api_key ? 'Configured' : 'Not configured'}</p>
      <label className="block">{provider.name} replacement API key
        <input type="password" autoComplete="off" className={inputStyle} value={key} disabled={!available || busy} onChange={event => setKey(event.target.value)} />
      </label>
      <p className="text-sm">Leave blank to keep the current key. Removing a key disables this provider; it does not revoke the key at its issuer.</p>
    </>}
    <div className="flex flex-wrap gap-2">
      <Button type="submit" disabled={!available || busy}>Save {provider.name}</Button>
      {provider.name !== 'ollama' && <Button variant="danger" disabled={!available || busy || !provider.has_api_key} onClick={() => { void run(async () => {
        await apiRequest('/api/settings/ai-providers/' + provider.name + '/credentials', { method: 'DELETE' });
        setKey(''); setEnabled(false); await onSaved(); setNotice('Saved credentials removed and provider disabled.');
      }); }}>Remove {provider.name} credentials</Button>}
    </div>
  </form>;
}
