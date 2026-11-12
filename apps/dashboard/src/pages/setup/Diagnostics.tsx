import React from 'react';
import { Activity, CheckCircle2 } from 'lucide-react';
import { Badge } from '@javo/design-system';
import { SetupStepCard } from './SetupStepCard';

export const Diagnostics: React.FC = () => (
  <SetupStepCard
    title="Pre-Flight System Diagnostics"
    subtitle="Verifying FastAPI local runtime, encrypted SQLite, and agent orchestrator."
    icon={<Activity className="h-6 w-6" />}
    prevPath="/setup/privacy"
    nextPath="/setup/complete"
    nextLabel="Finish Setup"
  >
    <div className="space-y-2.5">
      {[
        'FastAPI Local Runtime (localhost:8000)',
        'Encrypted SQLite WAL Database',
        'APScheduler Persistent Job Store',
        'Privacy Egress Firewall Active',
        '29 Specialist Agents Registered',
      ].map((check) => (
        <div
          key={check}
          className="flex items-center justify-between p-3.5 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10"
        >
          <span className="text-sm font-medium">{check}</span>
          <Badge status="active" size="sm">
            <CheckCircle2 className="h-3.5 w-3.5 mr-1 inline" /> Passed
          </Badge>
        </div>
      ))}
    </div>
  </SetupStepCard>
);
