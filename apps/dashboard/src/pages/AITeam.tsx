import React, { useMemo, useState } from 'react';
import { Bot, Play, Power, Search, ShieldCheck, Cpu } from 'lucide-react';
import { Card, Badge, Button, Chip, Modal, type BadgeStatus } from '@javo/design-system';
import { useAgentStore, type AgentItem, type AgentStatus } from '../store/useAgentStore';
import { useRunAgentMutation, useToggleAgentMutation } from '../api/hooks';
import { useAppStore } from '../store/useAppStore';

const CATEGORIES = ['All', 'Growth', 'Content', 'Operations', 'Security', 'Infrastructure'] as const;

const statusToBadge: Record<AgentStatus, { status: BadgeStatus; label: string }> = {
  active: { status: 'active', label: 'Active' },
  running: { status: 'info', label: 'Running' },
  idle: { status: 'violet', label: 'Standby' },
  error: { status: 'error', label: 'Error' },
  disabled: { status: 'inactive', label: 'Disabled' },
};

export const AITeam: React.FC = () => {
  const agents = useAgentStore((s) => s.agents);
  const toggleMutation = useToggleAgentMutation();
  const runMutation = useRunAgentMutation();
  const addToast = useAppStore((s) => s.addToast);

  const [category, setCategory] = useState<(typeof CATEGORIES)[number]>('All');
  const [search, setSearch] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<AgentItem | null>(null);

  const filtered = useMemo(() => {
    return agents.filter((a) => {
      const catOk = category === 'All' || a.category === category;
      const q = search.trim().toLowerCase();
      const searchOk =
        !q ||
        a.name.toLowerCase().includes(q) ||
        a.role.toLowerCase().includes(q) ||
        a.description.toLowerCase().includes(q);
      return catOk && searchOk;
    });
  }, [agents, category, search]);

  const enabledCount = agents.filter((a) => a.enabled).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            AI Team Roster ({agents.length} Specialists)
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            {enabledCount} enabled • Coordinated by MasterAgent Orchestrator with strict permission boundaries.
          </p>
        </div>

        <div className="relative w-full md:w-72">
          <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter 29 agents..."
            aria-label="Filter AI agents"
            className="w-full h-10 pl-9 pr-3 rounded-xl text-sm bg-white dark:bg-[#131C40] border border-slate-200 dark:border-white/10 focus:outline-none focus:border-[#00E5FF]"
          />
        </div>
      </div>

      {/* Category chips */}
      <div className="flex flex-wrap items-center gap-2">
        {CATEGORIES.map((cat) => (
          <Chip
            key={cat}
            label={cat}
            selected={category === cat}
            variant={cat === 'Security' ? 'violet' : 'cyan'}
            onClick={() => setCategory(cat)}
          />
        ))}
      </div>

      {/* 29 Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((agent) => {
          const badge = statusToBadge[agent.status];
          return (
            <Card
              key={agent.id}
              variant="status"
              glow={agent.enabled ? 'cyan' : 'none'}
              className={`flex flex-col justify-between ${!agent.enabled ? 'opacity-65' : ''}`}
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-[#00E5FF]/20 to-[#8B5CF6]/20 border border-[#00E5FF]/30 flex items-center justify-center text-xs font-mono font-bold text-[#008CA8] dark:text-[#00E5FF] shrink-0">
                      #{String(agent.number).padStart(2, '0')}
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                        {agent.name}
                      </h3>
                      <p className="text-xs text-[#7C3AED] dark:text-[#A78BFA] truncate">
                        {agent.role}
                      </p>
                    </div>
                  </div>
                  <Badge
                    status={badge.status}
                    pulse={agent.status === 'running' || agent.status === 'active'}
                    size="sm"
                  >
                    {badge.label}
                  </Badge>
                </div>

                <p className="mt-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {agent.description}
                </p>

                <div className="mt-3 flex flex-wrap items-center gap-1.5">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-300">
                    <Cpu className="h-3 w-3 text-[#00E5FF]" />
                    {agent.model}
                  </span>
                  <span className="px-2 py-0.5 rounded-md text-[11px] bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-300">
                    {agent.tasksCompleted} tasks • {agent.successRate}%
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200 dark:border-white/10 flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedAgent(agent)}
                  className="text-xs font-medium text-[#008CA8] dark:text-[#00E5FF] hover:underline cursor-pointer"
                >
                  Inspect Agent
                </button>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={!agent.enabled || agent.status === 'running'}
                    onClick={() => {
                      runMutation.mutate(agent.id);
                      addToast(`Triggered ${agent.name}`, 'Task dispatched to local runtime.', 'info');
                    }}
                    leftIcon={<Play className="h-3.5 w-3.5" />}
                  >
                    Run
                  </Button>
                  <button
                    type="button"
                    aria-label={agent.enabled ? `Disable ${agent.name}` : `Enable ${agent.name}`}
                    onClick={() => toggleMutation.mutate({ id: agent.id, enabled: !agent.enabled })}
                    className={`p-2 rounded-lg border transition-colors cursor-pointer ${
                      agent.enabled
                        ? 'bg-emerald-500/15 border-emerald-500/35 text-emerald-500 hover:bg-emerald-500/25'
                        : 'bg-slate-200 dark:bg-white/5 border-slate-300 dark:border-white/10 text-slate-500 hover:text-white'
                    }`}
                  >
                    <Power className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Agent Detail Modal */}
      <Modal
        open={Boolean(selectedAgent)}
        onClose={() => setSelectedAgent(null)}
        title={
          selectedAgent
            ? `Agent #${String(selectedAgent.number).padStart(2, '0')} — ${selectedAgent.name}`
            : ''
        }
        description={selectedAgent?.role}
        footer={
          selectedAgent && (
            <>
              <Button variant="ghost" onClick={() => setSelectedAgent(null)}>
                Close
              </Button>
              <Button
                variant="primary"
                leftIcon={<Play className="h-4 w-4" />}
                onClick={() => {
                  runMutation.mutate(selectedAgent.id);
                  addToast(`Dispatched ${selectedAgent.name}`, 'Execution started.', 'success');
                  setSelectedAgent(null);
                }}
              >
                Execute Now
              </Button>
            </>
          )
        }
      >
        {selectedAgent && (
          <div className="space-y-4 text-sm">
            <p className="text-slate-600 dark:text-slate-300">{selectedAgent.description}</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10">
                <p className="text-xs text-slate-500">Assigned Model</p>
                <p className="mt-1 font-semibold">{selectedAgent.model}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10">
                <p className="text-xs text-slate-500">Last Execution</p>
                <p className="mt-1 font-semibold">{selectedAgent.lastRun}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10">
                <p className="text-xs text-slate-500">Tasks Completed</p>
                <p className="mt-1 font-semibold">{selectedAgent.tasksCompleted}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10">
                <p className="text-xs text-slate-500">Success Rate</p>
                <p className="mt-1 font-semibold text-emerald-500">{selectedAgent.successRate}%</p>
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-[#00E5FF]" /> Permission Boundaries
              </p>
              <div className="flex flex-wrap gap-2">
                {selectedAgent.permissions.map((perm) => (
                  <Chip key={perm} label={perm} variant="violet" selected />
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
