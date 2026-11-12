import React from 'react';

export interface ChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label?: string;
  icon?: React.ReactNode;
  selected?: boolean;
  variant?: 'cyan' | 'violet' | 'neutral';
  removable?: boolean;
  onRemove?: () => void;
}

export const Chip: React.FC<ChipProps> = ({
  label,
  children,
  icon,
  selected = false,
  variant = 'cyan',
  removable = false,
  onRemove,
  className = '',
  type = 'button',
  ...props
}) => {
  const variantStyles = {
    cyan: selected
      ? 'bg-[#00E5FF]/20 border-[#00E5FF] text-[#0099B8] dark:text-[#00E5FF] shadow-[0_0_14px_rgba(0,229,255,0.2)]'
      : 'bg-slate-100 dark:bg-[#131C40]/90 border-slate-200 dark:border-white/10 text-slate-700 dark:text-[#E2E6F0] hover:border-[#00E5FF]/50',
    violet: selected
      ? 'bg-[#8B5CF6]/20 border-[#8B5CF6] text-[#7C3AED] dark:text-[#A78BFA] shadow-[0_0_14px_rgba(139,92,246,0.22)]'
      : 'bg-slate-100 dark:bg-[#131C40]/90 border-slate-200 dark:border-white/10 text-slate-700 dark:text-[#E2E6F0] hover:border-[#8B5CF6]/50',
    neutral: selected
      ? 'bg-slate-900 dark:bg-white/15 border-slate-900 dark:border-white/40 text-white'
      : 'bg-slate-100 dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-700 dark:text-slate-300 hover:bg-slate-200/70 dark:hover:bg-white/10',
  };

  return (
    <button
      type={type}
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E5FF] cursor-pointer ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {icon && <span className="shrink-0 opacity-90">{icon}</span>}
      <span>{label ?? children}</span>
      {removable && onRemove && (
        <span
          role="button"
          tabIndex={0}
          aria-label="Remove"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              e.stopPropagation();
              onRemove();
            }
          }}
          className="ml-0.5 rounded-full p-0.5 hover:bg-black/10 dark:hover:bg-white/15"
        >
          ×
        </span>
      )}
    </button>
  );
};
