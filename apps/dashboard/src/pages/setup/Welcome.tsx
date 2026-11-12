import React from 'react';
import { Sparkles, Shield, Bot, Cpu } from 'lucide-react';
import { Logo, Badge } from '@javo/design-system';
import { SetupStepCard } from './SetupStepCard';

export const Welcome: React.FC = () => (
  <SetupStepCard
    title="Welcome to Javo Agents"
    subtitle="Your local-first autonomous studio with 29 coordinated specialist AI agents."
    icon={<Sparkles className="h-6 w-6" />}
    nextPath="/setup/hardware"
    nextLabel="Start Setup"
  >
    <div className="p-5 rounded-2xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10 flex flex-col sm:flex-row items-center gap-5">
      <Logo size={64} />
      <div className="space-y-2 text-center sm:text-left">
        <div className="flex flex-wrap justify-center sm:justify-start gap-2">
          <Badge status="info">Windows Desktop</Badge>
          <Badge status="violet">29 AI Specialists</Badge>
          <Badge status="active">Zero Lock-In</Badge>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          This 2-minute wizard verifies your hardware, configures Ollama & Gemini routing, connects your content folders, and secures your privacy firewall.
        </p>
      </div>
    </div>

    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
      <div className="p-3.5 rounded-xl bg-white/70 dark:bg-[#131C40] border border-slate-200 dark:border-white/10">
        <Cpu className="h-4 w-4 text-[#00E5FF] mb-2" />
        <p className="font-semibold">Local AI First</p>
        <p className="text-slate-400 mt-0.5">Runs Qwen & Whisper on your workstation.</p>
      </div>
      <div className="p-3.5 rounded-xl bg-white/70 dark:bg-[#131C40] border border-slate-200 dark:border-white/10">
        <Bot className="h-4 w-4 text-[#8B5CF6] mb-2" />
        <p className="font-semibold">Human-in-the-Loop</p>
        <p className="text-slate-400 mt-0.5">Approve sensitive actions via Telegram or Inbox.</p>
      </div>
      <div className="p-3.5 rounded-xl bg-white/70 dark:bg-[#131C40] border border-slate-200 dark:border-white/10">
        <Shield className="h-4 w-4 text-emerald-400 mb-2" />
        <p className="font-semibold">Encrypted Vault</p>
        <p className="text-slate-400 mt-0.5">All tokens stay encrypted on your machine.</p>
      </div>
    </div>
  </SetupStepCard>
);
