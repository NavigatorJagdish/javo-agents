import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Logo } from './Logo';

export interface SidebarNavItem {
  id: string;
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: string | number;
  section?: 'core' | 'operations' | 'system';
}

export interface SidebarProps {
  items: SidebarNavItem[];
  activePath: string;
  onNavigate: (path: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  footer?: React.ReactNode;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  items,
  activePath,
  onNavigate,
  collapsed = false,
  onToggleCollapse,
  footer,
  mobileOpen = false,
  onCloseMobile,
}) => {
  const isActive = (path: string) =>
    path === '/' ? activePath === '/' : activePath === path || activePath.startsWith(`${path}/`);

  const navContent = (
    <div className="flex flex-col h-full bg-white dark:bg-[#090E22] border-r border-slate-200 dark:border-white/10">
      {/* Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-slate-200 dark:border-white/10 shrink-0">
        <button
          type="button"
          onClick={() => onNavigate('/')}
          className="flex items-center gap-2.5 focus:outline-none cursor-pointer"
        >
          <Logo size={34} showText={!collapsed} subtitle="Autonomous Studio" />
        </button>
        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="hidden lg:inline-flex p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        )}
      </div>

      {/* Navigation list */}
      <nav aria-label="Main navigation" className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {items.map((item) => {
          const active = isActive(item.path);
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                onNavigate(item.path);
                onCloseMobile?.();
              }}
              aria-current={active ? 'page' : undefined}
              title={collapsed ? item.label : undefined}
              className={`group w-full flex items-center ${
                collapsed ? 'justify-center px-2' : 'justify-between px-3'
              } py-2.5 rounded-xl text-sm font-medium transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E5FF] cursor-pointer ${
                active
                  ? 'bg-gradient-to-r from-[#00E5FF]/18 via-[#00E5FF]/10 to-[#8B5CF6]/10 text-[#008CA8] dark:text-[#00E5FF] border border-[#00E5FF]/35 shadow-[0_0_16px_rgba(0,229,255,0.12)]'
                  : 'text-slate-600 dark:text-[#E2E6F0]/75 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white border border-transparent'
              }`}
            >
              <span className="flex items-center gap-3 min-w-0">
                <span
                  className={`shrink-0 transition-colors ${
                    active
                      ? 'text-[#0099B8] dark:text-[#00E5FF]'
                      : 'text-slate-400 dark:text-slate-400 group-hover:text-slate-700 dark:group-hover:text-white'
                  }`}
                >
                  {item.icon}
                </span>
                {!collapsed && <span className="truncate">{item.label}</span>}
              </span>
              {!collapsed && item.badge !== undefined && (
                <span
                  className={`ml-2 px-2 py-0.5 text-[11px] font-semibold rounded-full ${
                    active
                      ? 'bg-[#00E5FF]/20 text-[#0099B8] dark:text-[#00E5FF]'
                      : 'bg-[#8B5CF6]/15 text-[#7C3AED] dark:text-[#A78BFA]'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      {footer && (
        <div className="p-3 border-t border-slate-200 dark:border-white/10 shrink-0">{footer}</div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`hidden lg:block shrink-0 transition-all duration-200 ${
          collapsed ? 'w-[76px]' : 'w-[260px]'
        }`}
      >
        <div className="sticky top-0 h-screen">{navContent}</div>
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <aside className="relative z-10 w-[260px] max-w-[85vw] h-full">{navContent}</aside>
        </div>
      )}
    </>
  );
};
