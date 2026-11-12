'use client';

import React, { useMemo, useState } from 'react';
import { Search, Shield } from 'lucide-react';
import {
  AGENT_CATEGORIES,
  MASTER_ORCHESTRATOR,
  SPECIALIST_AGENTS,
  type AgentCategory,
  type AgentSpec,
} from '@/data/agents';

export function AgentsExplorer() {
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'All' | AgentCategory>('All');
  const [selectedAgent, setSelectedAgent] = useState<AgentSpec>(SPECIALIST_AGENTS[0]);

  const filteredAgents = useMemo(() => {
    const q = query.trim().toLowerCase();
    return SPECIALIST_AGENTS.filter((agent) => {
      const matchesCat =
        selectedCategory === 'All' || agent.category === selectedCategory;
      const matchesQuery =
        !q ||
        agent.name.toLowerCase().includes(q) ||
        agent.role.toLowerCase().includes(q) ||
        agent.summary.toLowerCase().includes(q) ||
        agent.number.includes(q);
      return matchesCat && matchesQuery;
    });
  }, [query, selectedCategory]);

  return (
    <div className="space-y-8">
      {/* Master Orchestrator Banner */}
      <div className="glass-card border-[#00E5FF]/40 p-6">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div>
            <span className="font-mono text-xs font-bold text-[#007B8F] dark:text-[#00E5FF]">
              CORE COORDINATOR · AGENT {MASTER_ORCHESTRATOR.number}
            </span>
            <h2 className="mt-1 font-display text-2xl font-bold text-slate-900 dark:text-white">
              {MASTER_ORCHESTRATOR.name}
            </h2>
            <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-[#E2E6F0]/85">
              {MASTER_ORCHESTRATOR.summary}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setSelectedAgent(MASTER_ORCHESTRATOR)}
            className="btn-secondary shrink-0"
          >
            Inspect Orchestrator Scopes
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative w-full lg:max-w-sm">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search 29 agents by name, number, or role..."
            aria-label="Search specialist agents"
            className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#00E5FF] focus:outline-none dark:border-white/15 dark:bg-[#111836] dark:text-white"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {(['All', ...AGENT_CATEGORIES] as const).map((category) => (
            <button
              key={category}
              type="button"
              onClick={() => setSelectedCategory(category)}
              className={`rounded-xl px-3.5 py-2 text-xs font-semibold transition ${
                selectedCategory === category
                  ? 'bg-gradient-to-r from-[#00E5FF] to-[#8B5CF6] text-[#0B1026]'
                  : 'border border-slate-300 bg-white text-slate-700 hover:border-[#00E5FF] dark:border-white/15 dark:bg-white/5 dark:text-[#E2E6F0]'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Selected Agent Detail Panel */}
      <div className="glass-card border-[#8B5CF6]/40 p-6">
        <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 dark:border-white/10 md:flex-row md:items-center">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs font-bold text-[#007B8F] dark:text-[#00E5FF]">
                AGENT {selectedAgent.number}
              </span>
              <span className="rounded-full bg-[#8B5CF6]/15 px-2.5 py-0.5 text-xs font-medium text-[#6D28D9] dark:text-[#A78BFA]">
                {selectedAgent.category}
              </span>
              <span className="rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-medium text-slate-700 dark:bg-white/10 dark:text-[#E2E6F0]">
                {selectedAgent.ramProfile}
              </span>
            </div>
            <h3 className="mt-2 font-display text-2xl font-bold text-slate-900 dark:text-white">
              {selectedAgent.name} — {selectedAgent.role}
            </h3>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
            <Shield className="h-3.5 w-3.5" />
            Default: {selectedAgent.defaultMode}
          </span>
        </div>

        <div className="mt-5 grid gap-6 md:grid-cols-3">
          <div className="md:col-span-2">
            <p className="text-sm leading-relaxed text-slate-700 dark:text-[#E2E6F0]/90">
              {selectedAgent.summary}
            </p>
            <h4 className="mt-4 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-[#94A3B8]">
              Core Responsibilities
            </h4>
            <ul className="mt-2 space-y-1.5 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
              {selectedAgent.responsibilities.map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#00E5FF]" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-[#0B1026]/80">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-[#94A3B8]">
              Permission Boundaries
            </h4>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {selectedAgent.permissions.map((perm) => (
                <code
                  key={perm}
                  className="rounded-md bg-[#00E5FF]/10 px-2 py-1 font-mono text-xs text-[#007B8F] dark:text-[#00E5FF]"
                >
                  {perm}
                </code>
              ))}
            </div>
            <p className="mt-4 text-xs text-slate-500 dark:text-[#94A3B8]">
              Every specialist can be toggled individually in the Desktop Dashboard and halted globally via Emergency Stop.
            </p>
          </div>
        </div>
      </div>

      {/* Grid of All Filtered Specialist Agents */}
      <div>
        <p className="mb-4 text-xs font-medium text-slate-500 dark:text-[#94A3B8]">
          Showing {filteredAgents.length} of {SPECIALIST_AGENTS.length} specialist agents
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredAgents.map((agent) => {
            const isSelected = selectedAgent.id === agent.id;
            return (
              <button
                key={agent.id}
                type="button"
                onClick={() => setSelectedAgent(agent)}
                className={`glass-card p-5 text-left transition ${
                  isSelected
                    ? 'border-[#00E5FF] ring-1 ring-[#00E5FF]/50'
                    : 'hover:border-[#00E5FF]/40'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-bold text-[#007B8F] dark:text-[#00E5FF]">
                    #{agent.number} · {agent.category}
                  </span>
                </div>
                <h3 className="mt-2 font-display text-lg font-bold text-slate-900 dark:text-white">
                  {agent.name}
                </h3>
                <p className="text-xs font-medium text-[#6D28D9] dark:text-[#A78BFA]">
                  {agent.role}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                  {agent.summary}
                </p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {agent.permissions.map((perm) => (
                    <span
                      key={perm}
                      className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-600 dark:bg-white/5 dark:text-[#94A3B8]"
                    >
                      {perm}
                    </span>
                  ))}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
