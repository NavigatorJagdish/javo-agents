import React, { useState } from 'react';
import { Sun, Moon, Cpu, Database, Download, Info } from 'lucide-react';
import { Card, Button, Badge } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

export const Settings: React.FC = () => {
  const { theme, setTheme, addToast } = useAppStore();
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [defaultLocalModel, setDefaultLocalModel] = useState('qwen2.5:14b');
  const [dailyBudget, setDailyBudget] = useState('0.00');
  const [geminiKey, setGeminiKey] = useState('••••••••••••••••••••');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    addToast('Settings Saved', 'AI Router and local runtime configuration updated.', 'success');
  };

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

      {/* AI Providers */}
      <Card variant="default">
        <form onSubmit={handleSave} className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <Cpu className="h-4 w-4 text-[#00E5FF]" /> AI Providers & Budget Cap
            </h2>
            <Badge status="active" size="sm">Local First</Badge>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium mb-1">Ollama Endpoint</label>
              <input
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                className="w-full h-10 px-3 rounded-xl text-sm font-mono bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Default Local Model</label>
              <input
                value={defaultLocalModel}
                onChange={(e) => setDefaultLocalModel(e.target.value)}
                className="w-full h-10 px-3 rounded-xl text-sm font-mono bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Gemini API Key (Encrypted)</label>
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                className="w-full h-10 px-3 rounded-xl text-sm font-mono bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Daily Cloud Spend Cap ($ USD)</label>
              <input
                value={dailyBudget}
                onChange={(e) => setDailyBudget(e.target.value)}
                className="w-full h-10 px-3 rounded-xl text-sm font-mono bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <Button type="submit">Save Provider Config</Button>
          </div>
        </form>
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
            Export SQLite memory, workflows, and encrypted vault keys as a portable `.javobak` bundle.
          </p>
          <Button
            size="sm"
            variant="secondary"
            leftIcon={<Download className="h-4 w-4" />}
            onClick={() => addToast('Backup Exported', 'Saved javo-backup-2026-11-12.javobak.', 'success')}
          >
            Export Snapshot
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
            Dashboard v0.1.0-alpha • Windows Desktop Edition
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            29 Specialist Agents • FastAPI Runtime (localhost:8000)
          </p>
        </Card>
      </div>
    </div>
  );
};
