import React, { useState } from 'react';
import { Check, X, Edit3, CalendarClock, ShieldAlert } from 'lucide-react';
import { Card, Badge, Button, Modal } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

interface ApprovalItem {
  id: string;
  agent: string;
  platform: string;
  type: 'Publish Video' | 'Comment Reply' | 'Skill Install' | 'Ad Experiment';
  title: string;
  preview: string;
  scheduledFor: string;
  risk: 'low' | 'medium';
}

const INITIAL_APPROVALS: ApprovalItem[] = [
  {
    id: 'app-1',
    agent: 'Content Publisher (#09)',
    platform: 'YouTube Shorts',
    type: 'Publish Video',
    title: '5 Local AI Workflows That Save 12 Hours/Week',
    preview: 'Caption: Run 29 specialized agents locally on Windows with zero cloud lock-in. #LocalAI #Automation',
    scheduledFor: '2026-11-13 18:00',
    risk: 'low',
  },
  {
    id: 'app-2',
    agent: 'Community Manager (#10)',
    platform: 'Instagram',
    type: 'Comment Reply',
    title: 'Reply to @dev_maya on "Ollama GPU Setup"',
    preview: 'Thanks Maya! You only need 8GB VRAM for Qwen 2.5 14B Q4_K_M — our Resource Optimizer handles unloading automatically.',
    scheduledFor: 'Immediate',
    risk: 'low',
  },
  {
    id: 'app-3',
    agent: 'Self-Upgrading Engineer (#04)',
    platform: 'Local Sandbox',
    type: 'Skill Install',
    title: 'Approve synthesized skill: youtube_chapter_extractor.py',
    preview: 'Sandbox tests passed (12/12). Read-only transcript access; zero network egress required.',
    scheduledFor: 'Pending Sign-off',
    risk: 'medium',
  },
  {
    id: 'app-4',
    agent: 'Content Recycler (#17)',
    platform: 'X',
    type: 'Publish Video',
    title: 'Thread: Privacy Firewall Architecture Breakdown',
    preview: '1/5 Most AI tools send your raw client files straight to third-party servers. Here is how we fixed that locally...',
    scheduledFor: '2026-11-14 09:30',
    risk: 'low',
  },
];

export const Approvals: React.FC = () => {
  const [items, setItems] = useState(INITIAL_APPROVALS);
  const [editing, setEditing] = useState<ApprovalItem | null>(null);
  const [editText, setEditText] = useState('');
  const [editDate, setEditDate] = useState('');
  const addToast = useAppStore((s) => s.addToast);

  const handleDecision = (item: ApprovalItem, approved: boolean) => {
    setItems((prev) => prev.filter((i) => i.id !== item.id));
    addToast(
      approved ? 'Approved & Dispatched' : 'Rejected',
      `"${item.title}" ${approved ? 'queued for execution' : 'returned to draft'}.`,
      approved ? 'success' : 'warning'
    );
  };

  const openEdit = (item: ApprovalItem) => {
    setEditing(item);
    setEditText(item.preview);
    setEditDate(item.scheduledFor);
  };

  const saveEdit = () => {
    if (!editing) return;
    setItems((prev) =>
      prev.map((i) =>
        i.id === editing.id ? { ...i, preview: editText, scheduledFor: editDate } : i
      )
    );
    addToast('Approval Updated', 'Edited copy and reschedule saved.', 'info');
    setEditing(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Human-in-the-Loop Approval Inbox
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Managed by Approval Manager (#15) — synchronized with your Telegram bot.
          </p>
        </div>
        <Badge status={items.length > 0 ? 'warning' : 'active'}>
          {items.length} Pending
        </Badge>
      </div>

      {items.length === 0 ? (
        <Card variant="status" className="text-center py-12">
          <p className="text-lg font-semibold text-slate-900 dark:text-white">
            All caught up!
          </p>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            No pending items require manual review right now.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <Card key={item.id} variant="status" glow="cyan">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge status="info" size="sm">{item.type}</Badge>
                    <Badge status={item.risk === 'medium' ? 'warning' : 'active'} size="sm">
                      {item.risk === 'medium' ? 'Medium Risk' : 'Low Risk'}
                    </Badge>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {item.agent} • {item.platform}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                    {item.title}
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-[#0B1026]/80 p-3 rounded-xl border border-slate-200 dark:border-white/10">
                    {item.preview}
                  </p>
                  <p className="text-xs text-slate-400 flex items-center gap-1.5">
                    <CalendarClock className="h-3.5 w-3.5 text-[#00E5FF]" />
                    Scheduled: {item.scheduledFor}
                  </p>
                </div>

                <div className="flex flex-wrap lg:flex-col gap-2 shrink-0">
                  <Button
                    size="sm"
                    variant="primary"
                    leftIcon={<Check className="h-4 w-4" />}
                    onClick={() => handleDecision(item, true)}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    leftIcon={<Edit3 className="h-4 w-4" />}
                    onClick={() => openEdit(item)}
                  >
                    Edit / Reschedule
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    leftIcon={<X className="h-4 w-4" />}
                    onClick={() => handleDecision(item, false)}
                  >
                    Reject
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={Boolean(editing)}
        onClose={() => setEditing(null)}
        title="Edit & Reschedule"
        description={editing?.title}
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditing(null)}>Cancel</Button>
            <Button onClick={saveEdit}>Save Changes</Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium mb-1">Payload / Copy</label>
            <textarea
              rows={4}
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Scheduled Time</label>
            <input
              value={editDate}
              onChange={(e) => setEditDate(e.target.value)}
              className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
            />
          </div>
          <p className="text-xs text-slate-400 flex items-center gap-1.5">
            <ShieldAlert className="h-3.5 w-3.5 text-[#8B5CF6]" /> Changes are logged to the Compliance audit trail.
          </p>
        </div>
      </Modal>
    </div>
  );
};
