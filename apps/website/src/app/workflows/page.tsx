import type { Metadata } from 'next';
import Link from 'next/link';
import { PageHeader } from '@/components/PageHeader';
import { InteractiveWorkflowDemo } from '@/components/InteractiveWorkflowDemo';

export const metadata: Metadata = {
  title: 'Workflow Automation',
  description:
    'Visual 16-node workflow automation with Folder Watcher, AI Prompt, Condition, Approval Gate, Retry, and Publish nodes.',
};

const NODE_TYPES = [
  { name: 'Trigger', group: 'Entry', desc: 'Manual or API-triggered workflow start.' },
  { name: 'Schedule', group: 'Entry', desc: 'Persistent APScheduler cron or interval trigger.' },
  { name: 'Folder Watcher', group: 'Entry', desc: 'Fires when new media enters watched local directories.' },
  { name: 'Account Event', group: 'Entry', desc: 'Reacts to new comments or verified channel updates.' },
  { name: 'Content Analyzer', group: 'AI & Data', desc: 'Extracts duration, format, and metadata locally.' },
  { name: 'AI Prompt', group: 'AI & Data', desc: 'Runs routed Ollama or sanitized Gemini prompt step.' },
  { name: 'Condition', group: 'Logic', desc: 'Deterministic branching based on scores or tags.' },
  { name: 'Approval', group: 'Safety', desc: 'Pauses workflow until human approves on Desktop/Android/Telegram.' },
  { name: 'Publish', group: 'Action', desc: 'Executes approved upload/post to connected channel.' },
  { name: 'Comment Reply', group: 'Action', desc: 'Posts approved reply via official platform connector.' },
  { name: 'Notification', group: 'Action', desc: 'Sends structured summary to Dashboard, Android, or Telegram.' },
  { name: 'Analytics', group: 'AI & Data', desc: 'Reads verified local platform snapshots without guessing.' },
  { name: 'Delay', group: 'Flow', desc: 'Enforces cooldown spacing between consecutive actions.' },
  { name: 'Retry', group: 'Resilience', desc: 'Bounded exponential backoff for transient network errors.' },
  { name: 'Error Handler', group: 'Resilience', desc: 'Routes failures cleanly to Recovery Agent (Agent 20).' },
  { name: 'End', group: 'Flow', desc: 'Finalizes execution and seals local SQLite audit trail.' },
];

export default function WorkflowsPage() {
  return (
    <div>
      <PageHeader
        badge="16-Node Visual DAG Engine"
        title="Workflow"
        highlight="Automation"
        subtitle="Combine local folder triggers, deterministic policy checks, AI drafting, and human approval gates inside a persistent DAG engine."
      >
        <Link href="/features" className="btn-primary">
          Explore Supervised Autopilot
        </Link>
        <Link href="/agents" className="btn-secondary">
          Meet Agent 24 (Workflow Automation)
        </Link>
      </PageHeader>

      <section className="mx-auto max-w-7xl space-y-12 px-4 py-14 sm:px-6 lg:px-8">
        <InteractiveWorkflowDemo />

        <div>
          <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">
            All 16 Supported Workflow Node Types
          </h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
            Defined in <code className="font-mono">packages/workflow-schema</code> and executed by Workflow Automation (Agent 24).
          </p>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {NODE_TYPES.map((node) => (
              <div key={node.name} className="glass-card p-4">
                <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
                  {node.group}
                </span>
                <h3 className="mt-1 font-display text-base font-bold text-slate-900 dark:text-white">
                  {node.name}
                </h3>
                <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                  {node.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
