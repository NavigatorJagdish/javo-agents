import React from 'react';

interface PageHeaderProps {
  badge: string;
  title: string;
  highlight?: string;
  subtitle: string;
  children?: React.ReactNode;
}

export function PageHeader({ badge, title, highlight, subtitle, children }: PageHeaderProps) {
  return (
    <section className="relative overflow-hidden border-b border-slate-200/80 bg-grid-pattern py-16 dark:border-white/10 sm:py-20">
      <div className="pointer-events-none absolute -top-24 left-1/2 h-72 w-[36rem] -translate-x-1/2 rounded-full bg-gradient-to-r from-[#00E5FF]/15 via-[#8B5CF6]/15 to-transparent blur-3xl" />
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-[#00E5FF]/35 bg-[#00E5FF]/10 px-3.5 py-1 text-xs font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
            {badge}
          </span>
          <h1 className="mt-4 font-display text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-5xl">
            {title}{' '}
            {highlight && <span className="text-gradient">{highlight}</span>}
          </h1>
          <p className="mt-4 text-base leading-relaxed text-slate-600 dark:text-[#E2E6F0]/85 sm:text-lg">
            {subtitle}
          </p>
          {children && <div className="mt-7 flex flex-wrap items-center gap-3">{children}</div>}
        </div>
      </div>
    </section>
  );
}
