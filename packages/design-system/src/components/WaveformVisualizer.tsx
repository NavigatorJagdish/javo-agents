import React from 'react';

export interface WaveformVisualizerProps {
  active?: boolean;
  bars?: number;
  height?: number;
  className?: string;
  intensity?: number;
}

const DEFAULT_WEIGHTS = [
  0.32, 0.56, 0.84, 0.45, 0.95, 0.66, 0.38, 0.78, 0.92, 0.52,
  0.71, 0.88, 0.42, 0.64, 0.96, 0.58, 0.35, 0.82, 0.49, 0.68,
  0.9, 0.46, 0.75, 0.39,
];

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  active = true,
  bars = 24,
  height = 56,
  className = '',
  intensity = 1,
}) => {
  const items = Array.from({ length: bars }, (_, idx) => {
    const base = DEFAULT_WEIGHTS[idx % DEFAULT_WEIGHTS.length];
    const ratio = Math.min(1, Math.max(0.16, active ? base * intensity : 0.18));
    const delay = (idx % 8) * 110;
    const isViolet = idx % 3 === 2;
    return { idx, ratio, delay, isViolet };
  });

  return (
    <div
      className={`inline-flex items-center justify-center gap-1.5 select-none ${className}`}
      style={{ height }}
      role="img"
      aria-label={active ? 'Active voice waveform' : 'Idle voice waveform'}
    >
      {items.map(({ idx, ratio, delay, isViolet }) => (
        <span
          key={idx}
          className={`w-1.5 rounded-full transition-all duration-300 ${
            active ? 'animate-pulse' : 'opacity-45'
          } ${
            isViolet
              ? 'bg-gradient-to-t from-[#8B5CF6] to-[#C084FC] shadow-[0_0_10px_rgba(139,92,246,0.45)]'
              : 'bg-gradient-to-t from-[#0EA5E9] to-[#00E5FF] shadow-[0_0_10px_rgba(0,229,255,0.45)]'
          }`}
          style={{
            height: `${Math.round(ratio * 100)}%`,
            animationDelay: `${delay}ms`,
            animationDuration: active ? `${650 + (idx % 5) * 140}ms` : undefined,
          }}
        />
      ))}
    </div>
  );
};
