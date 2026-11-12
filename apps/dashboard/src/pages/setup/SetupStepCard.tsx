import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Card, Button } from '@javo/design-system';

export interface SetupStepCardProps {
  title: string;
  subtitle: string;
  icon?: React.ReactNode;
  prevPath?: string;
  nextPath?: string;
  nextLabel?: string;
  onNext?: () => void;
  children: React.ReactNode;
}

export const SetupStepCard: React.FC<SetupStepCardProps> = ({
  title,
  subtitle,
  icon,
  prevPath,
  nextPath,
  nextLabel = 'Continue',
  onNext,
  children,
}) => {
  const navigate = useNavigate();

  const handleNext = () => {
    onNext?.();
    if (nextPath) {
      navigate(nextPath);
    }
  };

  return (
    <Card variant="feature" glow="cyan" padding="lg">
      <div className="flex items-start gap-4 mb-6">
        {icon && (
          <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[#00E5FF]/20 to-[#8B5CF6]/20 border border-[#00E5FF]/35 flex items-center justify-center text-[#00E5FF] shrink-0">
            {icon}
          </div>
        )}
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">
            {title}
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{subtitle}</p>
        </div>
      </div>

      <div className="space-y-4">{children}</div>

      <div className="mt-8 pt-5 border-t border-slate-200 dark:border-white/10 flex items-center justify-between gap-3">
        {prevPath ? (
          <Button
            variant="ghost"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => navigate(prevPath)}
          >
            Back
          </Button>
        ) : (
          <div />
        )}
        {nextPath && (
          <Button
            variant="primary"
            rightIcon={<ArrowRight className="h-4 w-4" />}
            onClick={handleNext}
          >
            {nextLabel}
          </Button>
        )}
      </div>
    </Card>
  );
};
