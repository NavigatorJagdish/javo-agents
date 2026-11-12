import React, { useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Sun, Moon, ArrowLeft } from 'lucide-react';
import { Logo, Button } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

export const SETUP_STEPS = [
  { path: '/setup/welcome', label: 'Welcome' },
  { path: '/setup/hardware', label: 'Hardware' },
  { path: '/setup/ai', label: 'AI Setup' },
  { path: '/setup/folder', label: 'Content Folder' },
  { path: '/setup/social', label: 'Social Accounts' },
  { path: '/setup/brand', label: 'Brand Profile' },
  { path: '/setup/autopilot', label: 'Autopilot' },
  { path: '/setup/telegram', label: 'Telegram' },
  { path: '/setup/voice', label: 'Voice' },
  { path: '/setup/privacy', label: 'Privacy' },
  { path: '/setup/diagnostics', label: 'Diagnostics' },
  { path: '/setup/complete', label: 'Complete' },
];

export const AuthLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useAppStore();

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  const currentIdx = Math.max(
    0,
    SETUP_STEPS.findIndex((s) => location.pathname === s.path)
  );
  const pct = Math.round(((currentIdx + 1) / SETUP_STEPS.length) * 100);

  return (
    <div className="min-h-screen flex flex-col bg-[#F4F7FB] dark:bg-[#0B1026] text-slate-900 dark:text-[#E2E6F0]">
      <header className="h-16 px-6 flex items-center justify-between border-b border-slate-200 dark:border-white/10 bg-white/80 dark:bg-[#090E22]/80 backdrop-blur-xl">
        <Logo size={34} showText subtitle="Onboarding Wizard" />
        <div className="flex items-center gap-3">
          <Button
            size="sm"
            variant="ghost"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => navigate('/')}
          >
            Dashboard
          </Button>
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="p-2 rounded-xl bg-slate-100 dark:bg-[#131C40] border border-slate-200 dark:border-white/10 cursor-pointer"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-600" />}
          </button>
        </div>
      </header>

      {/* Progress Track */}
      <div className="border-b border-slate-200 dark:border-white/10 bg-white/50 dark:bg-[#0F1736]/60 px-6 py-3">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-semibold text-[#008CA8] dark:text-[#00E5FF]">
              Step {currentIdx + 1} of {SETUP_STEPS.length}: {SETUP_STEPS[currentIdx]?.label}
            </span>
            <span className="text-slate-500 dark:text-slate-400">{pct}% complete</span>
          </div>
          <div className="h-1.5 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[#00E5FF] to-[#8B5CF6] transition-all duration-300"
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="mt-2.5 hidden md:flex items-center justify-between gap-1">
            {SETUP_STEPS.map((step, i) => (
              <button
                key={step.path}
                type="button"
                onClick={() => navigate(step.path)}
                className={`text-[11px] font-medium px-2 py-0.5 rounded-md transition-colors cursor-pointer ${
                  i === currentIdx
                    ? 'bg-[#00E5FF]/15 text-[#008CA8] dark:text-[#00E5FF]'
                    : i < currentIdx
                      ? 'text-emerald-600 dark:text-emerald-400 hover:bg-white/5'
                      : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
                }`}
              >
                {step.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <main className="flex-1 flex items-center justify-center p-4 sm:p-8">
        <div className="w-full max-w-3xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
