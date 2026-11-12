import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Rocket, CheckCircle2 } from 'lucide-react';
import { Button, Badge } from '@javo/design-system';
import { SetupStepCard } from './SetupStepCard';
import { useAppStore } from '../../store/useAppStore';

export const Complete: React.FC = () => {
  const navigate = useNavigate();
  const { setSetupCompleted, addToast } = useAppStore();

  const handleFinish = () => {
    setSetupCompleted(true);
    addToast('Setup Complete', 'Javo Agents Mission Control is ready.', 'success');
    navigate('/');
  };

  return (
    <SetupStepCard
      title="Your Autonomous Studio is Ready"
      subtitle="All 29 agents, local models, and security guardrails are initialized."
      icon={<Rocket className="h-6 w-6" />}
      prevPath="/setup/diagnostics"
    >
      <div className="p-6 rounded-2xl bg-gradient-to-br from-[#00E5FF]/15 to-[#8B5CF6]/15 border border-[#00E5FF]/30 text-center space-y-4">
        <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto" />
        <div className="flex justify-center gap-2">
          <Badge status="active" pulse>Swarm Online</Badge>
          <Badge status="violet">Privacy Locked</Badge>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-300 max-w-md mx-auto">
          Head to Mission Control to monitor live agent activity, build visual node workflows, or test Voice Mode.
        </p>
        <Button size="lg" variant="primary" onClick={handleFinish}>
          Enter Mission Control
        </Button>
      </div>
    </SetupStepCard>
  );
};
