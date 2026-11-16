import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ProviderEditor, type ProviderInfo } from '../components/ProviderEditor';
import { apiRequest, ApiError } from '../api/client';
import { Sun, Moon, Database, Download, Info } from 'lucide-react';
import { Card, Button } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

interface SavedUsage {
  total_attempts: number;
  total_requests: number;
  total_tokens: number;
  failed_requests: number;
  unresolved_requests: number;
  requests_with_unknown_token_usage: number;
  daily_spend_usd: number;
  monthly_spend_usd: number;
  unresolved_reserved_usd: number;
  coverage_since: string;
  period_timezone: string;
}

export const Settings: React.FC = () => {
  const { theme, setTheme, addToast } = useAppStore();
  const qc = useQueryClient();
  const [defaultProvider, setDefaultProvider] = React.useState<string | null>(null);
  const [savingDefaults, setSavingDefaults] = React.useState(false);
  const settings = useQuery({ queryKey: ['runtime-settings'], queryFn: () => apiRequest<{ app_version: string; default_ai_provider: string; ai_daily_budget: number; ai_monthly_budget: number }>('/api/settings/'), retry: false });
  const providers = useQuery({ queryKey: ['runtime-providers'], queryFn: () => apiRequest<ProviderInfo[]>('/api/settings/ai-providers'), retry: false });
  const storage = useQuery({ queryKey: ['provider-storage'], queryFn: () => apiRequest<{ available: boolean; protection: string }>('/api/settings/provider-storage'), retry: false });
  const usage = useQuery({ queryKey: ['saved-ai-usage'], queryFn: () => apiRequest<SavedUsage>('/api/settings/ai-usage'), retry: false, refetchInterval: 15000 });
  async function refreshProviders() { await qc.invalidateQueries({ queryKey: ['runtime-providers'] }); }
  const budget = (value: unknown) => typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 6 }).format(value) : 'Unavailable';
  const [backingUp, setBackingUp] = React.useState(false);
  async function snapshot() {
    setBackingUp(true);
    try {
      const result = await apiRequest<{ filename: string; encrypted: boolean; size_bytes: number }>('/api/settings/backup', { method: 'POST' });
      if (!result.encrypted || result.size_bytes <= 0) throw new Error('Encrypted snapshot was not confirmed');
      addToast('Snapshot saved', result.filename, 'success');
    } catch (failure) {
      const detail = failure instanceof ApiError ? (failure.detail as { detail?: unknown })?.detail : null;
      addToast('Snapshot failed', typeof detail === 'string' ? detail : 'Runtime did not confirm an encrypted backup.', 'error');
    } finally { setBackingUp(false); }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
          System Settings
        </h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Configure appearance, local/cloud AI routing, encrypted backups, and runtime diagnostics.
        </p>
      </div>

      {/* Theme */}
      <Card variant="default">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-3">
          Appearance & Theme
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setTheme('dark')}
            className={`flex items-center gap-3 p-4 rounded-xl border text-left cursor-pointer ${
              theme === 'dark'
                ? 'bg-[#00E5FF]/15 border-[#00E5FF] text-white'
                : 'bg-slate-100 dark:bg-[#0B1026] border-slate-200 dark:border-white/10'
            }`}
          >
            <Moon className="h-5 w-5 text-[#00E5FF]" />
            <div>
              <p className="text-sm font-semibold">Midnight Navy (Default)</p>
              <p className="text-xs text-slate-400">#0B1026 dark studio aesthetic</p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => setTheme('light')}
            className={`flex items-center gap-3 p-4 rounded-xl border text-left cursor-pointer ${
              theme === 'light'
                ? 'bg-[#00E5FF]/15 border-[#00E5FF] text-slate-900'
                : 'bg-slate-100 dark:bg-[#0B1026] border-slate-200 dark:border-white/10'
            }`}
          >
            <Sun className="h-5 w-5 text-amber-500" />
            <div>
              <p className="text-sm font-semibold">Daylight Studio</p>
              <p className="text-xs text-slate-500">High-contrast clean light mode</p>
            </div>
          </button>
        </div>
      </Card>

      <Card variant="default">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-3">AI Providers & Configured Budgets</h2>
        {(settings.isError || providers.isError || storage.isError) && <p role="alert">Runtime settings unavailable. No example values are substituted.</p>}
        <p>Daily budget: {budget(settings.data?.ai_daily_budget)}</p>
        <p>Monthly budget: {budget(settings.data?.ai_monthly_budget)}</p>
        <p>Saving provider settings does not make an AI request. Cloud execution stays disabled pending verified pricing and explicit spending authorization.</p>
        {!storage.data?.available && <p role="status">Encrypted provider storage is unavailable or locked. Configure a persistent encryption key on this runtime or recover its Windows user profile.</p>}
        <p>Storage protection: {storage.data?.protection ?? 'Unavailable'}</p>
        <label className="block">Default AI provider
          <select className="rounded border border-slate-400 bg-white dark:bg-slate-900 p-2" value={defaultProvider ?? settings.data?.default_ai_provider ?? 'ollama'} disabled={!storage.data?.available || savingDefaults} onChange={event => setDefaultProvider(event.target.value)}>
            <option value="ollama">ollama</option><option value="gemini">gemini</option><option value="openai">openai</option>
          </select>
        </label>
        <Button disabled={!storage.data?.available || savingDefaults || defaultProvider === null} onClick={async () => {
          setSavingDefaults(true);
          try {
            await apiRequest('/api/settings/', { method: 'PUT', body: { default_ai_provider: defaultProvider } });
            await qc.invalidateQueries({ queryKey: ['runtime-settings'] }); setDefaultProvider(null);
            addToast('AI defaults saved', 'The selected default provider is persisted.', 'success');
          } catch { addToast('AI defaults not saved', 'Runtime did not confirm the change.', 'error'); }
          finally { setSavingDefaults(false); }
        }}>Save AI default</Button>
        {providers.data?.map(provider => <ProviderEditor key={provider.name} provider={provider} available={storage.data?.available === true} onSaved={refreshProviders} />)}
      </Card>

      <Card>
        <h2 className="text-base font-semibold mb-3">Saved AI usage</h2>
        {usage.isPending && <p role="status">Loading saved usage…</p>}
        {usage.isError && <p role="alert">Saved usage is unavailable. Totals cannot be confirmed. <Button variant="ghost" onClick={() => void usage.refetch()}>Retry usage</Button></p>}
        {usage.data && <div className="space-y-2 text-sm">
          <p>Completed AI requests: {usage.data.total_requests}</p>
          <p>Reported tokens: {usage.data.total_tokens}</p>
          <p>Requests with unknown token counts: {usage.data.requests_with_unknown_token_usage}</p>
          <p>Attempts: {usage.data.total_attempts} · Failed: {usage.data.failed_requests} · Unresolved: {usage.data.unresolved_requests}</p>
          <p>Recorded API charges today: {budget(usage.data.daily_spend_usd)} · This month: {budget(usage.data.monthly_spend_usd)}</p>
          <p>Unresolved reserved charges: {budget(usage.data.unresolved_reserved_usd)}</p>
          <p className="text-slate-500">Saved since {new Date(usage.data.coverage_since).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST. Accounting periods use {usage.data.period_timezone}. Earlier process-only counters cannot be recovered. Local hardware and electricity costs are not included.</p>
        </div>}
      </Card>

      {/* Backup & About */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card variant="status">
          <div className="flex items-center gap-2 mb-2">
            <Database className="h-4 w-4 text-[#8B5CF6]" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              Encrypted Backup & Restore
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
            Create an encrypted database snapshot on the runtime computer. A persistent backup encryption key must be configured and retained separately. Usage accounting, media folders, AI/social credential vaults and their keys are not included.
          </p>
          <Button
            size="sm"
            variant="secondary"
            leftIcon={<Download className="h-4 w-4" />}
            disabled={backingUp}
            onClick={() => { void snapshot(); }}
          >
            Create encrypted database snapshot
          </Button>
        </Card>

        <Card variant="status">
          <div className="flex items-center gap-2 mb-2">
            <Info className="h-4 w-4 text-[#00E5FF]" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              About Javo Agents
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Runtime version: {settings.data?.app_version ?? 'Unavailable'}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Registered agent definitions; production coverage varies. • FastAPI Runtime (localhost:8000)
          </p>
        </Card>
      </div>
    </div>
  );
};
