import React, { useState } from 'react';
import { Github, GitBranch, RefreshCw, Download, CheckCircle2 } from 'lucide-react';
import { Card, Badge, Button } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

const REPOS = [
  {
    id: 'repo-1',
    name: 'javo-ai/javo-agents-core',
    branch: 'main',
    commit: 'a8f31c9',
    status: 'synced',
    description: 'Core runtime, 29 specialist agents, and signed Windows desktop builds.',
    updateAvailable: false,
  },
  {
    id: 'repo-2',
    name: 'javo-ai/javo-skills-registry',
    branch: 'verified-v2',
    commit: '42d90b1',
    status: 'update',
    description: 'Signed community & first-party creator skills with capability manifests.',
    updateAvailable: true,
  },
  {
    id: 'repo-3',
    name: 'creator-studio/brand-templates',
    branch: 'main',
    commit: '91e77c4',
    status: 'synced',
    description: 'Private thumbnail presets, LUTs, and caption style prompts.',
    updateAvailable: false,
  },
];

export const GitHub: React.FC = () => {
  const [repos, setRepos] = useState(REPOS);
  const addToast = useAppStore((s) => s.addToast);

  const handleSync = (id: string) => {
    setRepos((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'synced', updateAvailable: false } : r))
    );
    addToast('Repository Synced', 'Verified commit SHA256 signature via Release Agent (#26).', 'success');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            GitHub & Release Registry
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Connected repositories, signed skill registries, and Release Agent (#26) update verification.
          </p>
        </div>
        <Button
          variant="secondary"
          leftIcon={<RefreshCw className="h-4 w-4" />}
          onClick={() => addToast('Checked GitHub Releases', 'Javo Agents v2.4.0 is up to date.', 'info')}
        >
          Check All Releases
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {repos.map((repo) => (
          <Card key={repo.id} variant="status" glow="cyan" className="flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <Github className="h-5 w-5 text-[#00E5FF]" />
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                    {repo.name}
                  </h3>
                </div>
                <Badge status={repo.updateAvailable ? 'warning' : 'active'} size="sm">
                  {repo.updateAvailable ? 'Update Ready' : 'Synced'}
                </Badge>
              </div>
              <p className="mt-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {repo.description}
              </p>
              <div className="mt-3 flex items-center gap-3 text-xs font-mono text-slate-400">
                <span className="flex items-center gap-1">
                  <GitBranch className="h-3.5 w-3.5 text-[#8B5CF6]" /> {repo.branch}
                </span>
                <span>#{repo.commit}</span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-white/10 flex items-center justify-between">
              <span className="text-xs text-emerald-500 flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> GPG Verified
              </span>
              <Button
                size="sm"
                variant={repo.updateAvailable ? 'primary' : 'ghost'}
                leftIcon={<Download className="h-3.5 w-3.5" />}
                onClick={() => handleSync(repo.id)}
              >
                {repo.updateAvailable ? 'Pull & Verify' : 'Re-sync'}
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
