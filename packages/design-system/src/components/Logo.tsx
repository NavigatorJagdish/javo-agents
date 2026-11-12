import React from 'react';

export interface LogoProps {
  size?: number;
  className?: string;
  showText?: boolean;
  subtitle?: string;
}

export const Logo: React.FC<LogoProps> = ({
  size = 36,
  className = '',
  showText = false,
  subtitle,
}) => {
  const uid = React.useId().replace(/:/g, '');
  const gradId = `javo-grad-${uid}`;
  const glowId = `javo-glow-${uid}`;

  return (
    <div className={`inline-flex items-center gap-3 select-none ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Javo Agents Logo"
        className="shrink-0"
      >
        <defs>
          <linearGradient id={gradId} x1="8" y1="6" x2="56" y2="58" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#00E5FF" />
            <stop offset="55%" stopColor="#38BDF8" />
            <stop offset="100%" stopColor="#8B5CF6" />
          </linearGradient>
          <filter id={glowId} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Outer hexagonal shield */}
        <path
          d="M32 4L56 17V41C56 50.5 45.2 57.6 32 60C18.8 57.6 8 50.5 8 41V17L32 4Z"
          fill="#0F1736"
          stroke={`url(#${gradId})`}
          strokeWidth="2.5"
          strokeLinejoin="round"
        />

        {/* Inner subtle shield outline */}
        <path
          d="M32 10L50 20V39.5C50 46.4 41.8 51.8 32 53.8C22.2 51.8 14 46.4 14 39.5V20L32 10Z"
          stroke={`url(#${gradId})`}
          strokeOpacity="0.28"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />

        {/* Neural mesh connections */}
        <g stroke={`url(#${gradId})`} strokeWidth="1.8" strokeLinecap="round" filter={`url(#${glowId})`}>
          <line x1="32" y1="20" x2="21" y2="30" />
          <line x1="32" y1="20" x2="43" y2="30" />
          <line x1="21" y1="30" x2="32" y2="34" />
          <line x1="43" y1="30" x2="32" y2="34" />
          <line x1="21" y1="30" x2="25" y2="43" />
          <line x1="43" y1="30" x2="39" y2="43" />
          <line x1="32" y1="34" x2="32" y2="45" />
          <line x1="25" y1="43" x2="32" y2="45" />
          <line x1="39" y1="43" x2="32" y2="45" />
        </g>

        {/* Shield neural nodes */}
        <circle cx="32" cy="20" r="3.2" fill="#00E5FF" />
        <circle cx="21" cy="30" r="2.8" fill="#38BDF8" />
        <circle cx="43" cy="30" r="2.8" fill="#8B5CF6" />
        <circle cx="32" cy="34" r="3.6" fill="#FFFFFF" stroke="#00E5FF" strokeWidth="1.5" />
        <circle cx="25" cy="43" r="2.5" fill="#00E5FF" />
        <circle cx="39" cy="43" r="2.5" fill="#8B5CF6" />
        <circle cx="32" cy="45" r="2.8" fill="#A78BFA" />
      </svg>

      {showText && (
        <div className="flex flex-col leading-none">
          <span className="font-display text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            JAVO <span className="text-brand-cyan">AGENTS</span>
          </span>
          {subtitle && (
            <span className="mt-0.5 text-[11px] font-medium tracking-wider uppercase text-slate-500 dark:text-slate-400">
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
