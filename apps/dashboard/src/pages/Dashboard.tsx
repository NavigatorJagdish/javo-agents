import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bot,
  CalendarClock,
  CheckCircle2,
  Target,
  Share2,
  Zap,
  Play,
  GitBranch,
  Mic,
  Cpu,
  HardDrive,
  ArrowUpRight,
  Sparkles,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { MetricCard, Card, Badge, Button, Chip, WaveformVisualizer } from '@javo/design-system';
import { useAgentStore } from '../store/useAgentStore';
import { useGoalStore } from '../store/useGoalStore';
import { useAppStore } from '../store/useAppStore';
import { useHealthQuery } from '../api/hooks';

const throughputData = [
  { day: 'Mon', tasks: 42, posts: 6 },
  { day: 'Tue', tasks: 58, posts: 8 },
  { day: 'Wed', tasks: 51, posts: 7 },
  { day: 'Thu', tasks: 76, posts: 11 },
  { day: 'Fri', tasks: 84, posts: 12 },
  { day: 'Sat', tasks: 67, posts: 9 },
  { day: 'Sun', tasks: 93, posts: 14 },
];

const activityFeed = [
  {
    id: 'act-1',
    agent: 'Content Factory (#02)',
    action: 'Generated 3 viral hook variants for "Local AI Workflows"',
    time: '2 mins ago',
    status: 'active' as const,
  },
  {
    id: 'act-2',
    agent: 'Quality Inspector (#13)',
    action: 'Scored reel_048.mp4 at 94/100 and approved audio loudness (-14 LUFS)',
    time: '11 mins ago',
    status: 'info' as const,
  },
  {
    id: 'act-3',
    agent: 'Approval Manager (#15)',
    action: 'Queued 4 community replies for human sign-off via Telegram',
    time: '24 mins ago',
    status: 'warning' as const,
  },
  {
    id: 'act-4',
    agent: 'Growth Scientist (#01)',
    action: 'Concluded Experiment #1: Question hooks outperformed by +22.4%',
    time: '1 hr ago',
    status: 'violet' as const,
  },
  {
    id: 'act-5',
    agent: 'Account Guardian (#11)',
    action: 'Verified YouTube & Instagram OAuth tokens refreshed cleanly',
    time: '2 hrs ago',
    status: 'active' as const,
  },
];

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const agents = useAgentStore((s) => s.agents);
  const goals = useGoalStore((s) => s.goals);
  const addToast = useAppStore((s) => s.addToast);
  const { data: health } = useHealthQuery();

  const activeAgents = agents.filter((a) => a.enabled).length;
  const totalTasks = agents.reduce((acc, a) => acc + a.tasksCompleted, 0);
  const avgGoalProgress = Math.round(
    goals.reduce((acc, g) => acc + g.progress, 0) / Math.max(1, goals.length)
  );

  return (
    <div className="space-y-6">
      {/* Hero header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Mission Control
            </h1>
            <Badge status="info" pulse>
              Swarm v2.4
            </Badge>
          </div>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Real-time telemetry across your 29 local-first autonomous agents, content pipeline, and growth goals.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Mic className="h-4 w-4" />}
            onClick={() => navigate('/voice')}
          >
            Voice Command
          </Button>
          <Button
            variant="violet"
            size="sm"
            leftIcon={<GitBranch className="h-4 w-4" />}
            onClick={() => navigate('/workflows')}
          >
            Open Workflow Builder
          </Button>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Play className="h-4 w-4" />}
            onClick={() =>
              addToast('Swarm Cycle Started', 'Content Factory & Growth Scientist triggered.', 'success')
            }
          >
            Run Daily Cycle
          </Button>
        </div>
      </div>

      {/* 5 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
        <MetricCard
          title="Active Agents"
          value={`${activeAgents}/29`}
          trend="+3 running"
          subtitle="zero errors"
          accent="cyan"
          icon={<Bot className="h-5 w-5" />}
        />
        <MetricCard
          title="Scheduled Jobs"
          value={18}
          trend="Next in 22m"
          subtitle="APScheduler WAL"
          accent="violet"
          icon={<CalendarClock className="h-5 w-5" />}
        />
        <MetricCard
          title="Tasks Completed"
          value={totalTasks.toLocaleString()}
          trend="+18.4%"
          subtitle="vs last 7 days"
          accent="emerald"
          icon={<CheckCircle2 className="h-5 w-5" />}
        />
        <MetricCard
          title="Goal Progress"
          value={`${avgGoalProgress}%`}
          trend={`${goals.length} active`}
          subtitle="on track"
          accent="cyan"
          icon={<Target className="h-5 w-5" />}
        />
        <MetricCard
          title="Connected Platforms"
          value={5}
          trend="All healthy"
          subtitle="YT • IG • FB • X • TG"
          accent="violet"
          icon={<Share2 className="h-5 w-5" />}
        />
      </div>

      {/* Main Grid: Chart + Resource Usage */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card variant="default" className="xl:col-span-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-5">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Autonomous Execution Throughput
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Agent tasks executed and content assets published over the last 7 days
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Chip label="Tasks" selected variant="cyan" />
              <Chip label="Published" variant="violet" />
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={throughputData} margin={{ top: 10, right: 12, left: -16, bottom: 0 }}>
                <defs>
                  <linearGradient id="cyanArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00E5FF" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#00E5FF" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="violetArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
                <XAxis dataKey="day" stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F1736',
                    borderColor: 'rgba(0,229,255,0.3)',
                    borderRadius: '12px',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="tasks"
                  stroke="#00E5FF"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#cyanArea)"
                />
                <Area
                  type="monotone"
                  dataKey="posts"
                  stroke="#8B5CF6"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#violetArea)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Resource Usage & Voice Pulse */}
        <Card variant="status" glow="cyan" className="flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Local Hardware & AI Router
              </h2>
              <Badge status="active" size="sm" pulse>
                Optimal
              </Badge>
            </div>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Resource Optimizer (#12) managing Ollama & Whisper memory slots
            </p>

            <div className="mt-5 space-y-4">
              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-200">
                    <Cpu className="h-3.5 w-3.5 text-[#00E5FF]" /> CPU Utilization
                  </span>
                  <span className="font-mono font-semibold text-[#008CA8] dark:text-[#00E5FF]">
                    {health?.cpu_percent ?? 24}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-[#00E5FF] to-[#38BDF8]"
                    style={{ width: `${health?.cpu_percent ?? 24}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-200">
                    <HardDrive className="h-3.5 w-3.5 text-[#8B5CF6]" /> Unified RAM (32 GB)
                  </span>
                  <span className="font-mono font-semibold text-[#7C3AED] dark:text-[#A78BFA]">
                    {health?.memory_percent ?? 42}% (13.4 GB)
                  </span>
                </div>
                <div className="h-2 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-[#8B5CF6] to-[#C084FC]"
                    style={{ width: `${health?.memory_percent ?? 42}%` }}
                  />
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10">
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    Voice & Neural Bus
                  </span>
                  <span className="text-[11px] text-emerald-500 font-medium">Whisper Ready</span>
                </div>
                <div className="flex justify-center">
                  <WaveformVisualizer active bars={20} height={36} intensity={0.85} />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-200 dark:border-white/10 flex items-center justify-between text-xs">
            <span className="text-slate-500 dark:text-slate-400">Daily Cloud Budget</span>
            <span className="font-mono font-semibold text-slate-900 dark:text-white">$1.42 / $10.00</span>
          </div>
        </Card>
      </div>

      {/* Bottom Grid: Activity Feed + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card variant="default" className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              Live Swarm Activity Feed
            </h2>
            <Button size="sm" variant="ghost" onClick={() => navigate('/ai-team')}>
              View all 29 agents <ArrowUpRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </div>
          <div className="space-y-3">
            {activityFeed.map((item) => (
              <div
                key={item.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3.5 rounded-xl bg-slate-50 dark:bg-[#0B1026]/65 border border-slate-200 dark:border-white/10"
              >
                <div className="flex items-start gap-3">
                  <Badge status={item.status} size="sm" pulse={item.status === 'active'}>
                    {item.agent}
                  </Badge>
                  <p className="text-sm text-slate-700 dark:text-[#E2E6F0]">{item.action}</p>
                </div>
                <span className="text-xs text-slate-400 shrink-0">{item.time}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card variant="feature" glow="violet">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <Zap className="h-4 w-4 text-[#00E5FF]" /> Quick Actions
          </h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Common autonomous creator commands
          </p>

          <div className="mt-4 space-y-2.5">
            {[
              { label: 'Inspect 4 Pending Approvals', to: '/approvals', tag: '4 waiting' },
              { label: 'Scan Local Content Folder', to: '/content', tag: 'Watcher active' },
              { label: 'Create Visual Automation Flow', to: '/workflows', tag: '16 nodes' },
              { label: 'Review Skill Trust & Sandbox', to: '/skills', tag: '100% signed' },
              { label: 'Run Hardware & API Diagnostics', to: '/setup/diagnostics', tag: 'Healthy' },
            ].map((action) => (
              <button
                key={action.label}
                type="button"
                onClick={() => navigate(action.to)}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-white/80 dark:bg-[#0B1026]/70 border border-slate-200 dark:border-white/10 hover:border-[#00E5FF]/50 transition-all text-left cursor-pointer group"
              >
                <span className="text-sm font-medium text-slate-800 dark:text-white group-hover:text-[#008CA8] dark:group-hover:text-[#00E5FF]">
                  {action.label}
                </span>
                <span className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                  <Sparkles className="h-3 w-3 text-[#8B5CF6]" />
                  {action.tag}
                </span>
              </button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
