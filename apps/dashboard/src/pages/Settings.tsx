import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiRequest, ApiError } from '../api/client';
import { Sun, Moon, Database, Download, Info } from 'lucide-react';
import { Card, Button } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

export const Settings: React.FC = () => {
  const { theme, setTheme, addToast } = useAppStore();
  const settings = useQuery({ queryKey: ['runtime-settings'], queryFn: () => apiRequest<{ app_version: string; ai_daily_budget: number; ai_monthly_budget: number }>('/api/settings/'), retry: false });
  const providers = useQuery({ queryKey: ['runtime-providers'], queryFn: () => apiRequest<{ name: string; model: string; enabled: boolean; has_api_key: boolean }[]>('/api/settings/ai-providers'), retry: false });
  const budget = (value: unknown) => typeof value === 'number' && Number.isFinite(value) ? '$' + value.toFixed(2) : 'Unavailable';
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
        {(settings.isError || providers.isError) && <p role="alert">Runtime settings unavailable. No example values are substituted.</p>}
        <p>Daily budget: {budget(settings.data?.ai_daily_budget)}</p>
        <p>Monthly budget: {budget(settings.data?.ai_monthly_budget)}</p>
        <p>Provider changes are not available in this build.</p>
        {providers.data?.map(provider => <div key={provider.name} className="border-b border-slate-500 py-3">
          <h3>{provider.name}</h3>
          <p>Configured model: {provider.model}</p>
          <p>{provider.enabled ? 'Enabled' : 'Disabled'}. API key: {provider.has_api_key ? 'Configured' : 'Not configured'}. Connection not tested here.</p>
        </div>)}
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
            Create an encrypted database snapshot on the runtime computer. A persistent backup encryption key must be configured and retained separately. Media folders and vault keys are not included.
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
            Dashboard v2.4.0 • Windows Desktop Edition
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Registered agent definitions; production coverage varies. • FastAPI Runtime (localhost:8000)
          </p>
        </Card>
      </div>
    </div>
  );
};
