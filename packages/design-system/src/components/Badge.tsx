import React from 'react';

export type BadgeStatus = 'active' | 'inactive' | 'error' | 'warning' | 'info' | 'violet';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status?: BadgeStatus;
  dot?: boolean;
  pulse?: boolean;
  size?: 'sm' | 'md';
}

const statusClasses: Record<BadgeStatus, string> = {
  active:
    'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
  inactive:
    'bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-500/30',
  error:
    'bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/30',
  warning:
    'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
  info:
    'bg-[#00E5FF]/15 text-[#0099B8] dark:text-[#00E5FF] border-[#00E5FF]/35',
  violet:
    'bg-[#8B5CF6]/15 text-[#7C3AED] dark:text-[#A78BFA] border-[#8B5CF6]/35',
};

const dotClasses: Record<BadgeStatus, string> = {
  active: 'bg-emerald-400',
  inactive: 'bg-slate-400',
  error: 'bg-red-400',
  warning: 'bg-amber-400',
  info: 'bg-[#00E5FF]',
  violet: 'bg-[#8B5CF6]',
};

export const Badge: React.FC<BadgeProps> = ({
  status = 'info',
  dot = true,
  pulse = false,
  size = 'md',
  className = '',
  children,
  ...props
}) => {
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border backdrop-blur-sm ${statusClasses[status]} ${sizeClass} ${className}`}
      {...props}
    >
      {dot && (
        <span className="relative flex h-2 w-2">
          {pulse && (
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${dotClasses[status]}`}
            />
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${dotClasses[status]}`} />
        </span>
      )}
      {children}
    </span>
  );
};
