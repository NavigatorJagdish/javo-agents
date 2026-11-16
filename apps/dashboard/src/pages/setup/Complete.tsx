import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Rocket, Info } from 'lucide-react';
import { Button, Badge } from '@javo/design-system';
import { SetupStepCard } from './SetupStepCard';
import { useAppStore } from '../../store/useAppStore';

export const Complete: React.FC = () => {
  const navigate = useNavigate();
  const { setSetupCompleted, addToast } = useAppStore();

  const handleFinish = () => {
    setSetupCompleted(true);
    addToast('Guide finished', 'Open the dashboard to review available runtime controls.', 'success');
    navigate('/');
  };

  return (
    <SetupStepCard
      title="Development setup guide finished"
      subtitle="Review availability in the dashboard before starting work."
      icon={<Rocket className="h-6 w-6" />}
      prevPath="/setup/diagnostics"
    >
      <div className="p-6 rounded-2xl bg-gradient-to-br from-[#00E5FF]/15 to-[#8B5CF6]/15 border border-[#00E5FF]/30 text-center space-y-4">
        <Info className="h-12 w-12 text-cyan-400 mx-auto" />
        <div className="flex justify-center gap-2">
          <Badge status="warning">Unfinished build</Badge>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-300 max-w-md mx-auto">
          This guide does not verify installed models, platform connections, audio engines or every specialist. Saved records and runtime controls are available; other features still require implementation and verification.
        </p>
        <Button size="lg" variant="primary" onClick={handleFinish}>
          Enter Mission Control
        </Button>
      </div>
    </SetupStepCard>
  );
};
