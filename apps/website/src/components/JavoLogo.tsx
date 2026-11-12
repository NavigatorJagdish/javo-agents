import React from 'react';

interface JavoLogoProps {
  size?: number;
  showWordmark?: boolean;
  animated?: boolean;
  className?: string;
}

export function JavoLogo({
  size = 40,
  showWordmark = false,
  animated = true,
  className = '',
}: JavoLogoProps) {
  const uid = React.useId().replace(/:/g, '');
  const gradId = `javo-grad-${uid}`;
  const glowId = `javo-glow-${uid}`;

  return (
    <div className={`inline-flex items-center gap-3 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className="shrink-0"
      >
        <defs>
          <linearGradient id={gradId} x1="8" y1="6" x2="56" y2="58" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#00E5FF" />
            <stop offset="100%" stopColor="#8B5CF6" />
          </linearGradient>
          <filter id={glowId} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Glowing Orbital Ring */}
        <circle
          cx="32"
          cy="32"
          r="27"
          stroke={`url(#${gradId})`}
          strokeOpacity="0.45"
          strokeWidth="1.5"
          strokeDasharray="6 4"
          className={animated ? 'origin-center animate-spin-slow' : ''}
        />
        <circle cx="55.5" cy="18.5" r="2" fill="#00E5FF" filter={`url(#${glowId})`} />

        {/* Hexagonal Shield */}
        <polygon
          points="32,8 52,19 52,43 32,56 12,43 12,19"
          fill="#0B1026"
          fillOpacity="0.95"
          stroke={`url(#${gradId})`}
          strokeWidth="2.5"
          strokeLinejoin="round"
        />

        {/* Inner Connected-Node Graph */}
        <line x1="20" y1="23" x2="32" y2="32" stroke="#00E5FF" strokeWidth="1.4" strokeOpacity="0.8" />
        <line x1="44" y1="23" x2="32" y2="32" stroke="#8B5CF6" strokeWidth="1.4" strokeOpacity="0.8" />
        <line x1="32" y1="46" x2="32" y2="32" stroke={`url(#${gradId})`} strokeWidth="1.4" strokeOpacity="0.8" />

        <circle cx="20" cy="23" r="2.6" fill="#00E5FF" />
        <circle cx="44" cy="23" r="2.6" fill="#8B5CF6" />
        <circle cx="32" cy="46" r="2.6" fill="#00E5FF" />

        {/* Vertical Waveform / Equalizer Bars */}
        <rect x="25.25" y="29" width="2.6" height="8" rx="1.3" fill="#00E5FF" />
        <rect x="30.7" y="24.5" width="2.6" height="15" rx="1.3" fill="#FFFFFF" />
        <rect x="36.15" y="27.5" width="2.6" height="10" rx="1.3" fill="#8B5CF6" />
      </svg>

      {showWordmark && (
        <div className="flex flex-col leading-none">
          <span className="font-display text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            Javo <span className="text-gradient">Agents</span>
          </span>
          <span className="text-[11px] font-medium tracking-wide text-slate-500 dark:text-silver-muted">
            LOCAL-FIRST AI TEAM
          </span>
        </div>
      )}
    </div>
  );
}
