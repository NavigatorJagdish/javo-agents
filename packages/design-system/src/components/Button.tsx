import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'violet';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-gradient-to-r from-[#00E5FF] via-[#0EA5E9] to-[#38BDF8] text-[#0B1026] font-semibold shadow-[0_0_20px_rgba(0,229,255,0.28)] hover:shadow-[0_0_28px_rgba(0,229,255,0.45)] hover:brightness-105 active:scale-[0.98]',
  violet:
    'bg-gradient-to-r from-[#8B5CF6] to-[#6366F1] text-white font-semibold shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_26px_rgba(139,92,246,0.45)] hover:brightness-110 active:scale-[0.98]',
  secondary:
    'border border-[#00E5FF]/40 bg-[#00E5FF]/5 text-[#00A8C6] dark:text-[#00E5FF] hover:bg-[#00E5FF]/15 hover:border-[#00E5FF]/70 active:scale-[0.98]',
  ghost:
    'bg-transparent text-slate-700 dark:text-[#E2E6F0] hover:bg-slate-200/70 dark:hover:bg-white/10 active:scale-[0.98]',
  danger:
    'bg-red-500/15 border border-red-500/40 text-red-600 dark:text-red-400 hover:bg-red-500/25 hover:border-red-500/70 active:scale-[0.98]',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-xs rounded-lg gap-1.5',
  md: 'h-10 px-4 text-sm rounded-xl gap-2',
  lg: 'h-12 px-6 text-base rounded-xl gap-2.5',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className = '',
      disabled,
      children,
      type = 'button',
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || isLoading}
        className={`inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E5FF] focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-[#0B1026] disabled:opacity-50 disabled:pointer-events-none cursor-pointer ${variantClasses[variant]} ${sizeClasses[size]} ${fullWidth ? 'w-full' : ''} ${className}`}
        {...props}
      >
        {isLoading ? (
          <svg
            className="animate-spin h-4 w-4 shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
            <path
              className="opacity-85"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z"
            />
          </svg>
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        {children && <span>{children}</span>}
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
