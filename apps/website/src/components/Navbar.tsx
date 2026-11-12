'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Download, Github, Menu, Moon, Sun, X } from 'lucide-react';
import { JavoLogo } from './JavoLogo';
import { useTheme } from './ThemeProvider';
import { NAV_LINKS, SITE_CONFIG } from '@/data/site';

export function Navbar() {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) =>
    pathname === href || pathname === `${href}/`;

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/85 backdrop-blur-xl dark:border-white/10 dark:bg-[#0B1026]/85">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#00E5FF] rounded-lg">
          <JavoLogo size={36} showWordmark animated />
        </Link>

        <nav aria-label="Main navigation" className="hidden items-center gap-1 lg:flex">
          {NAV_LINKS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive(item.href)
                  ? 'bg-[#00E5FF]/15 text-[#007B8F] dark:text-[#00E5FF]'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-[#E2E6F0]/80 dark:hover:bg-white/5 dark:hover:text-white'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700 transition-colors hover:border-[#00E5FF] dark:border-white/10 dark:bg-white/5 dark:text-[#E2E6F0]"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          <a
            href={SITE_CONFIG.githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Javo Agents GitHub Repository"
            className="hidden h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700 transition-colors hover:border-[#00E5FF] dark:border-white/10 dark:bg-white/5 dark:text-[#E2E6F0] sm:inline-flex"
          >
            <Github className="h-4 w-4" />
          </a>

          <Link
            href="/download"
            className="hidden items-center gap-1.5 rounded-xl bg-gradient-to-r from-[#00E5FF] to-[#8B5CF6] px-4 py-2 text-xs font-semibold text-[#0B1026] shadow-glow transition hover:brightness-110 sm:inline-flex"
          >
            <Download className="h-3.5 w-3.5" />
            Download Alpha
          </Link>

          <button
            type="button"
            onClick={() => setMobileOpen((prev) => !prev)}
            aria-label={mobileOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileOpen}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-700 dark:border-white/10 dark:text-[#E2E6F0] lg:hidden"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="border-t border-slate-200 bg-white px-4 py-4 dark:border-white/10 dark:bg-[#0B1026] lg:hidden">
          <nav aria-label="Mobile navigation" className="grid grid-cols-2 gap-2">
            {NAV_LINKS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`rounded-lg px-3 py-2 text-sm font-medium ${
                  isActive(item.href)
                    ? 'bg-[#00E5FF]/15 text-[#007B8F] dark:text-[#00E5FF]'
                    : 'text-slate-700 hover:bg-slate-100 dark:text-[#E2E6F0] dark:hover:bg-white/5'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-3 flex gap-2">
            <Link
              href="/download"
              onClick={() => setMobileOpen(false)}
              className="btn-primary flex-1 py-2.5 text-xs"
            >
              <Download className="h-4 w-4" />
              Download v0.1.0-alpha
            </Link>
            <a
              href={SITE_CONFIG.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary py-2.5 text-xs"
            >
              <Github className="h-4 w-4" />
              GitHub
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
