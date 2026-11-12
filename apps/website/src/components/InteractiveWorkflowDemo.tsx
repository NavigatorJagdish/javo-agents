'use client';

import React, { useState } from 'react';
import {
  CheckCircle2,
  ChevronRight,
  FolderOpen,
  Play,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Send,
} from 'lucide-react';

interface WorkflowNodeStep {
  id: string;
  nodeType: string;
  label: string;
  agent: string;
  privacyRule: string;
  outputPreview: string;
  requiresApproval?: boolean;
}

interface WorkflowPreset {
  id: string;
  title: string;
  description: string;
  nodes: WorkflowNodeStep[];
}

const WORKFLOW_PRESETS: WorkflowPreset[] = [
  {
    id: 'content-folder-pipeline',
    title: 'Folder-to-Publish Pipeline',
    description:
      'Watches local Content Folder → drafts caption via Ollama → runs Quality & Brand checks → pauses at Approval Gate.',
    nodes: [
      {
        id: 'n1',
        nodeType: 'Folder Watcher',
        label: 'Detect New Reel',
        agent: '24 Workflow Automation',
        privacyRule: 'Local Disk Only',
        outputPreview: 'Detected: D:\\CreatorContent\\inbox\\launch-clip.mp4 (42s, 1080x1920)',
      },
      {
        id: 'n2',
        nodeType: 'AI Prompt',
        label: 'Draft Caption & Hook',
        agent: '02 Content Factory',
        privacyRule: 'Ollama Local (8GB Profile)',
        outputPreview: 'Drafted 3 Hinglish + English hook variations and 5 niche hashtags locally.',
      },
      {
        id: 'n3',
        nodeType: 'Condition',
        label: 'Quality & Brand Audit',
        agent: '13 Quality Inspector',
        privacyRule: 'Zero External Egress',
        outputPreview: 'Passed: No placeholders, tone matches Brand Profile, length within Instagram Reels limit.',
      },
      {
        id: 'n4',
        nodeType: 'Approval',
        label: 'Supervised Autopilot Gate',
        agent: '15 Approval Manager',
        privacyRule: 'Human Sign-Off Required',
        requiresApproval: true,
        outputPreview: 'Paused for owner approval on Desktop, Android Companion, or Telegram Bot.',
      },
      {
        id: 'n5',
        nodeType: 'Publish',
        label: 'Scheduled Publish',
        agent: '09 Content Publisher',
        privacyRule: 'OAuth Token (OS Encrypted)',
        outputPreview: 'Executes only after approval signature is recorded in local SQLite audit log.',
      },
    ],
  },
  {
    id: 'comment-triage',
    title: 'Comment Triage & Reply',
    description:
      'Polls verified channel comments → drafts contextual replies → validates policy compliance → holds for approval.',
    nodes: [
      {
        id: 'c1',
        nodeType: 'Account Event',
        label: 'Fetch New Comments',
        agent: '08 API Integration',
        privacyRule: 'Official Graph/Data API',
        outputPreview: 'Fetched 4 unread comments from connected YouTube & Instagram Professional channels.',
      },
      {
        id: 'c2',
        nodeType: 'AI Prompt',
        label: 'Draft Helpful Replies',
        agent: '10 Community Manager',
        privacyRule: 'Privacy Firewall Filtered',
        outputPreview: 'Generated concise replies matching your English/Hinglish creator tone.',
      },
      {
        id: 'c3',
        nodeType: 'Condition',
        label: 'Compliance & Rate Check',
        agent: '29 Compliance Agent',
        privacyRule: 'Anti-Spam Guardrail',
        outputPreview: 'Verified zero duplicate replies and safe Account Guardian cooldown spacing.',
      },
      {
        id: 'c4',
        nodeType: 'Approval',
        label: 'Batch Reply Approval',
        agent: '15 Approval Manager',
        privacyRule: 'Human Sign-Off Required',
        requiresApproval: true,
        outputPreview: 'Queued 4 reply drafts in Approval Inbox for one-tap review.',
      },
    ],
  },
  {
    id: 'weekly-digest',
    title: 'Weekly Growth Digest',
    description:
      'Reads verified local snapshots → compiles honest Markdown report → delivers digest to Telegram.',
    nodes: [
      {
        id: 'w1',
        nodeType: 'Schedule',
        label: 'Sunday 9:00 AM Trigger',
        agent: '24 Workflow Automation',
        privacyRule: 'APScheduler Persistent',
        outputPreview: 'Scheduled trigger fired cleanly with persistent SQLite job tracking.',
      },
      {
        id: 'w2',
        nodeType: 'Analytics',
        label: 'Compile Verified Snapshot',
        agent: '19 Weekly Analyst',
        privacyRule: 'No Fabricated Metrics',
        outputPreview: 'Summarizes synced YouTube/Meta metrics; disconnected platforms explicitly labeled Unavailable.',
      },
      {
        id: 'w3',
        nodeType: 'AI Prompt',
        label: 'Propose Next Experiment',
        agent: '01 Growth Scientist',
        privacyRule: 'Ollama / Sanitized Gemini',
        outputPreview: 'Suggests 2 retention hook tests for upcoming week based on historical snapshots.',
      },
      {
        id: 'w4',
        nodeType: 'Notification',
        label: 'Send Telegram Digest',
        agent: '05 Telegram Agent',
        privacyRule: 'Allowlisted Chat ID Only',
        outputPreview: 'Delivers private Markdown summary directly to your verified Telegram Chat ID.',
      },
    ],
  },
];

export function InteractiveWorkflowDemo() {
  const [presetIndex, setPresetIndex] = useState(0);
  const [activeStep, setActiveStep] = useState(0);
  const [approvedGate, setApprovedGate] = useState(false);

  const preset = WORKFLOW_PRESETS[presetIndex];
  const currentNode = preset.nodes[activeStep];

  const handleSelectPreset = (index: number) => {
    setPresetIndex(index);
    setActiveStep(0);
    setApprovedGate(false);
  };

  const handleNextStep = () => {
    if (currentNode.requiresApproval && !approvedGate) {
      return;
    }
    if (activeStep < preset.nodes.length - 1) {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleReset = () => {
    setActiveStep(0);
    setApprovedGate(false);
  };

  return (
    <div className="glass-card overflow-hidden p-6 sm:p-8">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 dark:border-white/10 md:flex-row md:items-center">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[#8B5CF6]/40 bg-[#8B5CF6]/10 px-3 py-1 text-xs font-semibold text-[#6D28D9] dark:text-[#A78BFA]">
            <Sparkles className="h-3.5 w-3.5" />
            Interactive Demonstration (Simulated Browser Preview)
          </div>
          <h3 className="mt-2 font-display text-xl font-bold text-slate-900 dark:text-white">
            Supervised Autopilot Workflow Explorer
          </h3>
          <p className="mt-1 text-sm text-slate-600 dark:text-[#E2E6F0]/75">
            Select a workflow template and step through how Javo Agents enforces local-first privacy and human approval gates.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {WORKFLOW_PRESETS.map((item, idx) => (
            <button
              key={item.id}
              type="button"
              onClick={() => handleSelectPreset(idx)}
              className={`rounded-xl px-3.5 py-2 text-xs font-semibold transition ${
                idx === presetIndex
                  ? 'bg-gradient-to-r from-[#00E5FF] to-[#8B5CF6] text-[#0B1026]'
                  : 'border border-slate-300 bg-white text-slate-700 hover:border-[#00E5FF] dark:border-white/15 dark:bg-white/5 dark:text-[#E2E6F0]'
              }`}
            >
              {item.title}
            </button>
          ))}
        </div>
      </div>

      {/* Node Graph Strip */}
      <div className="mt-6 flex flex-col gap-3 lg:flex-row lg:items-center">
        {preset.nodes.map((node, idx) => {
          const isCurrent = idx === activeStep;
          const isCompleted = idx < activeStep;

          return (
            <React.Fragment key={node.id}>
              <button
                type="button"
                onClick={() => setActiveStep(idx)}
                className={`flex-1 rounded-xl border p-3.5 text-left transition-all ${
                  isCurrent
                    ? 'border-[#00E5FF] bg-[#00E5FF]/10 shadow-glow'
                    : isCompleted
                      ? 'border-emerald-500/40 bg-emerald-500/10'
                      : 'border-slate-200 bg-slate-50/70 hover:border-slate-300 dark:border-white/10 dark:bg-[#0B1026]/70 dark:hover:border-white/25'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
                    {node.nodeType}
                  </span>
                  {isCompleted ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  ) : node.requiresApproval ? (
                    <ShieldAlert className="h-4 w-4 text-amber-400" />
                  ) : (
                    <FolderOpen className="h-3.5 w-3.5 text-slate-400" />
                  )}
                </div>
                <p className="mt-1.5 text-sm font-semibold text-slate-900 dark:text-white">
                  {node.label}
                </p>
                <p className="mt-0.5 text-xs text-slate-500 dark:text-[#94A3B8]">
                  Agent {node.agent}
                </p>
              </button>
              {idx < preset.nodes.length - 1 && (
                <ChevronRight className="hidden h-5 w-5 shrink-0 text-slate-400 lg:block" />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Inspector Panel */}
      <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-[#0B1026]/80">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-md bg-[#00E5FF]/15 px-2.5 py-0.5 font-mono text-xs font-semibold text-[#007B8F] dark:text-[#00E5FF]">
                Step {activeStep + 1} / {preset.nodes.length}: {currentNode.nodeType}
              </span>
              <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300">
                <ShieldCheck className="h-3.5 w-3.5" />
                {currentNode.privacyRule}
              </span>
            </div>
            <h4 className="mt-2 text-base font-bold text-slate-900 dark:text-white">
              {currentNode.label} — Agent {currentNode.agent}
            </h4>
            <p className="mt-1.5 font-mono text-xs leading-relaxed text-slate-700 dark:text-[#E2E6F0]/90">
              {currentNode.outputPreview}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {currentNode.requiresApproval && !approvedGate && (
              <button
                type="button"
                onClick={() => setApprovedGate(true)}
                className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500 px-4 py-2 text-xs font-semibold text-[#0B1026] transition hover:bg-emerald-400"
              >
                <Send className="h-3.5 w-3.5" />
                Simulate Approve
              </button>
            )}
            {activeStep < preset.nodes.length - 1 && (
              <button
                type="button"
                disabled={Boolean(currentNode.requiresApproval && !approvedGate)}
                onClick={handleNextStep}
                className="btn-primary px-4 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-45"
              >
                <Play className="h-3.5 w-3.5" />
                {currentNode.requiresApproval && !approvedGate
                  ? 'Waiting for Approval'
                  : 'Next Simulated Step'}
              </button>
            )}
            <button
              type="button"
              onClick={handleReset}
              className="btn-secondary px-3.5 py-2 text-xs"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Reset
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
