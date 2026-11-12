import React, { useState } from 'react';
import { Zap, Plus, Clock, FolderOpen, MessageSquare, Power } from 'lucide-react';
import { Card, Badge, Button, Chip, Modal } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

interface AutomationRule {
  id: string;
  name: string;
  trigger: string;
  condition: string;
  action: string;
  enabled: boolean;
  runs: number;
  lastTriggered: string;
}

const INITIAL_RULES: AutomationRule[] = [
  {
    id: 'rule-1',
    name: 'Auto-Prepare New Reels Drop',
    trigger: 'Folder Watcher: D:/CreatorContent/Ready',
    condition: 'duration <= 60s AND qa_score >= 85',
    action: 'Generate caption + Queue Approval',
    enabled: true,
    runs: 48,
    lastTriggered: '22m ago',
  },
  {
    id: 'rule-2',
    name: 'High-Priority Comment Triage',
    trigger: 'Account Event: YouTube New Comment',
    condition: 'sentiment == "question" OR follower_count > 5000',
    action: 'Draft reply with Brand Manager #06 + Telegram Ping',
    enabled: true,
    runs: 193,
    lastTriggered: '6m ago',
  },
  {
    id: 'rule-3',
    name: 'Weekly Executive Digest',
    trigger: 'Schedule: Every Sunday 19:00',
    condition: 'always',
    action: 'Compile analytics report + Send Telegram summary',
    enabled: true,
    runs: 12,
    lastTriggered: '2d ago',
  },
  {
    id: 'rule-4',
    name: 'Evergreen Top-Clip Recycler',
    trigger: 'Schedule: Every Wednesday 10:00',
    condition: 'views_30d > 25000 AND age_days > 45',
    action: 'Create carousel variant via Content Recycler #17',
    enabled: false,
    runs: 9,
    lastTriggered: '1w ago',
  },
];

export const Automation: React.FC = () => {
  const [rules, setRules] = useState<AutomationRule[]>(INITIAL_RULES);
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [trigger, setTrigger] = useState('Folder Watcher: D:/CreatorContent/Ready');
  const [condition, setCondition] = useState('qa_score >= 85');
  const [action, setAction] = useState('Queue for Telegram Approval');
  const addToast = useAppStore((s) => s.addToast);

  const toggleRule = (id: string) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r))
    );
  };

  const handleAddRule = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setRules((prev) => [
      {
        id: `rule-${Date.now()}`,
        name,
        trigger,
        condition,
        action,
        enabled: true,
        runs: 0,
        lastTriggered: 'Never',
      },
      ...prev,
    ]);
    addToast('Automation Rule Added', `"${name}" is now active.`, 'success');
    setName('');
    setModalOpen(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Automation Rules Engine
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Event-driven triggers, policy conditions, and autonomous actions managed by Workflow Automation (#24).
          </p>
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>
          New Rule
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {rules.map((rule) => (
          <Card key={rule.id} variant="status" glow={rule.enabled ? 'cyan' : 'none'}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-[#00E5FF]/15 border border-[#00E5FF]/30 flex items-center justify-center text-[#00E5FF]">
                  <Zap className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                    {rule.name}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {rule.runs} executions • Last: {rule.lastTriggered}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge status={rule.enabled ? 'active' : 'inactive'} size="sm" pulse={rule.enabled}>
                  {rule.enabled ? 'Active' : 'Paused'}
                </Badge>
                <button
                  type="button"
                  aria-label={`Toggle ${rule.name}`}
                  onClick={() => toggleRule(rule.id)}
                  className={`p-2 rounded-lg border cursor-pointer ${
                    rule.enabled
                      ? 'bg-emerald-500/15 border-emerald-500/35 text-emerald-400'
                      : 'bg-slate-200 dark:bg-white/5 border-slate-300 dark:border-white/10 text-slate-400'
                  }`}
                >
                  <Power className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="mt-4 space-y-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10 flex items-center gap-2">
                <Clock className="h-3.5 w-3.5 text-[#00E5FF] shrink-0" />
                <span className="text-slate-400">WHEN:</span>
                <span className="font-mono text-slate-800 dark:text-white truncate">{rule.trigger}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10 flex items-center gap-2">
                <FolderOpen className="h-3.5 w-3.5 text-[#8B5CF6] shrink-0" />
                <span className="text-slate-400">IF:</span>
                <span className="font-mono text-slate-800 dark:text-white truncate">{rule.condition}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10 flex items-center gap-2">
                <MessageSquare className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                <span className="text-slate-400">THEN:</span>
                <span className="font-medium text-slate-800 dark:text-white truncate">{rule.action}</span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Create Automation Rule">
        <form onSubmit={handleAddRule} className="space-y-4">
          <div>
            <label className="block text-xs font-medium mb-1">Rule Name</label>
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Auto-Publish Approved Shorts"
              className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Trigger</label>
            <input
              value={trigger}
              onChange={(e) => setTrigger(e.target.value)}
              className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Condition</label>
            <input
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Action</label>
            <input
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create Rule</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
