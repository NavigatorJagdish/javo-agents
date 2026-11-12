import React, { useState } from 'react';
import { Cpu, CheckCircle2, RefreshCw } from 'lucide-react';
import { Badge, Button } from '@javo/design-system';
import { SetupStepCard } from './SetupStepCard';

export const HardwareCheck: React.FC = () => {
  const [checked, setChecked] = useState(true);

  return (
    <SetupStepCard
      title="Hardware & Runtime Check"
      subtitle="Resource Optimizer (#12) inspected your workstation capabilities."
      icon={<Cpu className="h-6 w-6" />}
      prevPath="/setup/welcome"
      nextPath="/setup/ai"
    >
      <div className="space-y-3">
        {[
          { label: 'CPU Cores', value: '16 Threads (AVX2 Supported)', ok: true },
          { label: 'System Memory', value: '32 GB RAM (18.6 GB Free)', ok: true },
          { label: 'GPU Acceleration', value: 'NVIDIA RTX 4070 (12 GB VRAM)', ok: true },
          { label: 'Disk Space', value: '412 GB Available (NVMe SSD)', ok: true },
        ].map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10"
          >
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">{item.label}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">{item.value}</p>
            </div>
            <Badge status={checked ? 'active' : 'info'} size="sm">
              <CheckCircle2 className="h-3.5 w-3.5 mr-1 inline" /> Optimal
            </Badge>
          </div>
        ))}
      </div>
      <Button
        size="sm"
        variant="secondary"
        leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
        onClick={() => setChecked(true)}
      >
        Re-scan Hardware
      </Button>
    </SetupStepCard>
  );
};
