import React from 'react';
import { Badge, type BadgeStatus } from './Badge';

export type CardVariant = 'default' | 'status' | 'feature' | 'metric' | 'glass';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  glow?: 'none' | 'cyan' | 'violet';
  interactive?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const variantClasses: Record<CardVariant, string> = {
  default:
    'bg-white dark:bg-[#131C40]/90 border border-slate-200 dark:border-white/10 shadow-sm dark:shadow-none',
  status:
    'bg-gradient-to-br from-white to-slate-50 dark:from-[#1A2552]/90 dark:to-[#0F1736]/95 border border-slate-200 dark:border-[#00E5FF]/20',
  feature:
    'bg-gradient-to-br from-white via-slate-50 to-indigo-50/40 dark:from-[#16204A] dark:via-[#11193A] dark:to-[#1B1645] border border-slate-200 dark:border-[#8B5CF6]/25',
  metric:
    'bg-white dark:bg-gradient-to-b dark:from-[#162049] dark:to-[#0F1736] border border-slate-200 dark:border-white/10',
  glass:
    'bg-white/80 dark:bg-[#0F1736]/75 backdrop-blur-xl border border-slate-200/80 dark:border-white/15',
};

const glowClasses = {
  none: '',
  cyan: 'hover:border-[#00E5FF]/50 hover:shadow-[0_0_28px_rgba(0,229,255,0.14)]',
  violet: 'hover:border-[#8B5CF6]/50 hover:shadow-[0_0_28px_rgba(139,92,246,0.18)]',
};

const paddingClasses = {
  none: 'p-0',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
};

export const Card: React.FC<CardProps> = ({
  variant = 'default',
  glow = 'none',
  interactive = false,
  padding = 'md',
  className = '',
  children,
  ...props
}) => {
  return (
    <div
      className={`rounded-2xl transition-all duration-200 ${variantClasses[variant]} ${glowClasses[glow]} ${paddingClasses[padding]} ${
        interactive ? 'cursor-pointer hover:-translate-y-0.5' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  accent?: 'cyan' | 'violet' | 'emerald' | 'amber';
  className?: string;
}

const accentIconMap = {
  cyan: 'bg-[#00E5FF]/15 text-[#00A8C6] dark:text-[#00E5FF] border-[#00E5FF]/30',
  violet: 'bg-[#8B5CF6]/15 text-[#7C3AED] dark:text-[#A78BFA] border-[#8B5CF6]/30',
  emerald: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
  amber: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendDirection = 'up',
  icon,
  accent = 'cyan',
  className = '',
}) => {
  const trendColor =
    trendDirection === 'up'
      ? 'text-emerald-500 dark:text-emerald-400'
      : trendDirection === 'down'
        ? 'text-red-500 dark:text-red-400'
        : 'text-slate-500 dark:text-slate-400';

  return (
    <Card variant="metric" glow={accent === 'violet' ? 'violet' : 'cyan'} className={className}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {title}
          </p>
          <p className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            {value}
          </p>
        </div>
        {icon && (
          <div className={`p-2.5 rounded-xl border ${accentIconMap[accent]}`}>{icon}</div>
        )}
      </div>
      {(trend || subtitle) && (
        <div className="mt-3 flex items-center gap-2 text-xs">
          {trend && <span className={`font-semibold ${trendColor}`}>{trend}</span>}
          {subtitle && <span className="text-slate-500 dark:text-slate-400">{subtitle}</span>}
        </div>
      )}
    </Card>
  );
};

export interface StatusCardProps {
  title: string;
  description?: string;
  status: BadgeStatus;
  statusLabel: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  description,
  status,
  statusLabel,
  icon,
  action,
  footer,
  className = '',
}) => (
  <Card variant="status" glow="cyan" className={className}>
    <div className="flex items-start justify-between gap-3">
      <div className="flex items-center gap-3 min-w-0">
        {icon && (
          <div className="h-10 w-10 rounded-xl bg-[#00E5FF]/10 border border-[#00E5FF]/25 flex items-center justify-center text-[#00A8C6] dark:text-[#00E5FF] shrink-0">
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white truncate">{title}</h3>
          {description && (
            <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mt-0.5">
              {description}
            </p>
          )}
        </div>
      </div>
      <Badge status={status} pulse={status === 'active'} size="sm">
        {statusLabel}
      </Badge>
    </div>
    {(action || footer) && (
      <div className="mt-4 pt-3 border-t border-slate-200 dark:border-white/10 flex items-center justify-between gap-2">
        <div className="text-xs text-slate-500 dark:text-slate-400">{footer}</div>
        {action}
      </div>
    )}
  </Card>
);

export interface FeatureCardProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  badge?: string;
  children?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  title,
  description,
  icon,
  badge,
  children,
  onClick,
  className = '',
}) => (
  <Card
    variant="feature"
    glow="violet"
    interactive={Boolean(onClick)}
    onClick={onClick}
    className={className}
  >
    <div className="flex items-start justify-between gap-3">
      {icon && (
        <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-[#00E5FF]/20 to-[#8B5CF6]/20 border border-[#8B5CF6]/30 flex items-center justify-center text-[#00A8C6] dark:text-[#00E5FF]">
          {icon}
        </div>
      )}
      {badge && (
        <Badge status="violet" dot={false} size="sm">
          {badge}
        </Badge>
      )}
    </div>
    <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">{title}</h3>
    <p className="mt-1.5 text-sm text-slate-600 dark:text-[#E2E6F0]/80 leading-relaxed">
      {description}
    </p>
    {children && <div className="mt-4">{children}</div>}
  </Card>
);
