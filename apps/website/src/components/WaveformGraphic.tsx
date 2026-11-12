'use client';

import React from 'react';

export type WaveformState = 'Idle' | 'Listening' | 'Thinking' | 'Executing' | 'Finished';

const BAR_HEIGHTS = [24, 42, 68, 52, 88, 64, 96, 72, 84, 56, 74, 44, 62, 36, 50, 28];

export function WaveformGraphic({
  state = 'Listening',
  compact = false,
}: {
  state?: WaveformState;
  compact?: boolean;
}) {
  const isAnimated = state === 'Listening' || state === 'Thinking' || state === 'Executing';

  return (
    <div
      className={`flex items-center justify-center gap-1.5 ${
        compact ? 'h-12' : 'h-20'
      }`}
      role="img"
      aria-label={`Cyan-violet AI waveform in ${state} state`}
    >
      {BAR_HEIGHTS.map((height, idx) => {
        const ratio = idx / (BAR_HEIGHTS.length - 1);
        const bg =
          ratio < 0.45
            ? 'from-[#00E5FF] to-[#38BDF8]'
            : ratio < 0.75
              ? 'from-[#38BDF8] to-[#8B5CF6]'
              : 'from-[#8B5CF6] to-[#A78BFA]';

        const activeScale =
          state === 'Idle'
            ? 0.35
            : state === 'Finished'
              ? 0.55
              : height / 100;

        return (
          <span
            key={idx}
            style={{
              height: `${Math.max(18, Math.round(activeScale * 100))}%`,
              animationDelay: `${idx * 90}ms`,
              animationDuration:
                state === 'Executing' ? '0.85s' : state === 'Thinking' ? '1.2s' : '1.5s',
            }}
            className={`w-1.5 rounded-full bg-gradient-to-t ${bg} transition-all duration-300 ${
              isAnimated ? 'animate-wave origin-center' : 'opacity-75'
            }`}
          />
        );
      })}
    </div>
  );
}
