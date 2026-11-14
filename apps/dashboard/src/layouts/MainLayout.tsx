import { useQuery } from '@tanstack/react-query';
import React, { useEffect, useState } from 'react';
import { RouteContent } from '../components/RouteContent';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  Target,
  FolderKanban,
  GitBranch,
  Zap,
  Users,
  Blocks,
  BarChart3,
  CheckSquare,
  Mic,
  Github,
  Sparkles,
  Shield,
  Settings,
  Sun,
  Moon,
  Menu,
  OctagonAlert,
  Search,
  Wand2,
  Activity,
} from 'lucide-react';
import {
  Sidebar,
  type SidebarNavItem,
  Badge,
  Button,
  ToastContainer,
  Modal,
} from '@javo/design-system';
import { apiRequest } from '../api/client';
import { useAppStore } from '../store/useAppStore';
import { useAgentStore } from '../store/useAgentStore';
import { useEmergencyStopMutation, useHealthQuery } from '../api/hooks';

export const MainLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [stopModalOpen, setStopModalOpen] = useState(false);

  const {
    theme,
    toggleTheme,
    sidebarCollapsed,
    toggleSidebar,
    resetEmergencyStop,
    setAutopilotEnabled,
    toasts,
    dismissToast,
    addToast,
  } = useAppStore();

  const agents = useAgentStore((s) => s.agents);
  const activeAgentCount = agents.filter((a) => a.enabled).length;

  const healthQuery = useHealthQuery();
  const health = healthQuery.data;
  const runtimeOnline = healthQuery.isSuccess && health?.status === 'healthy';
  const control = useQuery({ queryKey: ['runtime-control'], queryFn: () => apiRequest<{ paused: boolean; emergency_stopped: boolean }>('/api/security/autopilot-status'), refetchInterval: 5000, retry: false });
  const emergencyStopped = control.data?.emergency_stopped ?? false;
  const autopilotEnabled = control.isSuccess && !control.data.paused;
  const emergencyStopMutation = useEmergencyStopMutation();

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  const navItems: SidebarNavItem[] = [
    { id: 'dashboard', label: 'Dashboard', path: '/', icon: <LayoutDashboard className="h-4 w-4" /> },
    { id: 'ai-team', label: 'AI Team', path: '/ai-team', icon: <Bot className="h-4 w-4" />, badge: activeAgentCount },
    { id: 'goals', label: 'Goals', path: '/goals', icon: <Target className="h-4 w-4" /> },
    { id: 'content', label: 'Content', path: '/content', icon: <FolderKanban className="h-4 w-4" /> },
    { id: 'workflows', label: 'Workflows', path: '/workflows', icon: <GitBranch className="h-4 w-4" /> },
    { id: 'automation', label: 'Automation', path: '/automation', icon: <Zap className="h-4 w-4" /> },
    { id: 'accounts', label: 'Accounts', path: '/accounts', icon: <Users className="h-4 w-4" /> },
    { id: 'integrations', label: 'Integrations', path: '/integrations', icon: <Blocks className="h-4 w-4" /> },
    { id: 'analytics', label: 'Analytics', path: '/analytics', icon: <BarChart3 className="h-4 w-4" /> },
    { id: 'approvals', label: 'Approvals', path: '/approvals', icon: <CheckSquare className="h-4 w-4" />, badge: 4 },
    { id: 'voice', label: 'Voice', path: '/voice', icon: <Mic className="h-4 w-4" /> },
    { id: 'github', label: 'GitHub', path: '/github', icon: <Github className="h-4 w-4" /> },
    { id: 'skills', label: 'Skills', path: '/skills', icon: <Sparkles className="h-4 w-4" /> },
    { id: 'security', label: 'Security', path: '/security', icon: <Shield className="h-4 w-4" /> },
    { id: 'settings', label: 'Settings', path: '/settings', icon: <Settings className="h-4 w-4" /> },
  ];

  const handleConfirmEmergencyStop = async () => {
    try {
      await emergencyStopMutation.mutateAsync();
      useAppStore.getState().triggerEmergencyStop();
      await control.refetch();
      setStopModalOpen(false);
      addToast('Stop requested', 'Runtime cancelled local work. Remote actions already sent may still complete.', 'info');
    } catch { addToast('Stop failed', 'Runtime did not confirm the request.', 'error'); }
  };
  const handleResumeSystem = async () => {
    try {
      await apiRequest('/api/security/resume', { method: 'POST' });
      await control.refetch();
      resetEmergencyStop();
      addToast('Runtime resumed', 'Resume confirmed by the runtime.', 'success');
    } catch { addToast('Resume failed', 'Runtime did not confirm the request.', 'error'); }
  };
  const handleAutopilot = async () => {
    if (emergencyStopped) return;
    try {
      await apiRequest(autopilotEnabled ? '/api/security/pause' : '/api/security/resume', { method: 'POST' });
      await control.refetch();
      setAutopilotEnabled(!autopilotEnabled);
      addToast('Command confirmed', 'Runtime confirmed pause/resume.', 'info');
    } catch { addToast('Command failed', 'Runtime did not confirm the request.', 'error'); }
  };

  const handleQuickSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const q = searchQuery.trim().toLowerCase();
    if (!q) return;
    const matched = navItems.find((item) => item.label.toLowerCase().includes(q));
    if (matched) {
      navigate(matched.path);
      setSearchQuery('');
    } else {
      addToast('Search', `Filtered results for "${searchQuery}" across workspace`, 'info');
    }
  };

  return (
    <div className="min-h-screen flex bg-[#F4F7FB] dark:bg-[#0B1026] text-slate-900 dark:text-[#E2E6F0] transition-colors">
      <Sidebar
        items={navItems}
        activePath={location.pathname}
        onNavigate={(path) => navigate(path)}
        collapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebar}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
        footer={
          !sidebarCollapsed ? (
            <div className="space-y-2">
              <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-[#131C40] border border-slate-200 dark:border-white/10">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-700 dark:text-slate-300">Local Runtime</span>
                  <Badge status={emergencyStopped || !runtimeOnline ? 'error' : 'active'} size="sm" pulse={runtimeOnline && !emergencyStopped}>
                    {emergencyStopped ? 'Halted' : runtimeOnline ? 'Online' : 'Unavailable'}
                  </Badge>
                </div>
                <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                  CPU {health?.cpu_percent ?? '—'}% • RAM {health?.memory_percent ?? '—'}%
                </p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/setup/welcome')}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-[#008CA8] dark:text-[#00E5FF] bg-[#00E5FF]/10 hover:bg-[#00E5FF]/20 border border-[#00E5FF]/25 transition-colors cursor-pointer"
              >
                <Wand2 className="h-3.5 w-3.5" />
                Launch Setup Wizard
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => navigate('/setup/welcome')}
              title="Launch Setup Wizard"
              aria-label="Launch Setup Wizard"
              className="w-full flex items-center justify-center p-2 rounded-xl text-[#00E5FF] bg-[#00E5FF]/10 hover:bg-[#00E5FF]/20 cursor-pointer"
            >
              <Wand2 className="h-4 w-4" />
            </button>
          )
        }
      />

      {/* Main Content Shell */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 h-16 px-4 sm:px-6 flex items-center justify-between gap-3 bg-white/85 dark:bg-[#0B1026]/85 backdrop-blur-xl border-b border-slate-200 dark:border-white/10">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation menu"
              className="lg:hidden p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/10 cursor-pointer"
            >
              <Menu className="h-5 w-5" />
            </button>

            <form onSubmit={handleQuickSearch} className="relative hidden sm:block max-w-md w-full">
              <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Jump to page or search agents, goals, workflows..."
                aria-label="Search workspace"
                className="w-full h-9 pl-9 pr-3 rounded-xl text-sm bg-slate-100 dark:bg-[#131C40] border border-slate-200 dark:border-white/10 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:border-[#00E5FF]"
              />
            </form>
          </div>

          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            {/* Autopilot pill */}
            <button
              type="button"
                onClick={handleAutopilot}
              className={`hidden md:inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors cursor-pointer ${
                autopilotEnabled && !emergencyStopped
                  ? 'bg-[#00E5FF]/12 border-[#00E5FF]/35 text-[#008CA8] dark:text-[#00E5FF]'
                  : 'bg-slate-100 dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-400'
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
              Autopilot: {control.isError || control.isPending ? 'UNKNOWN' : autopilotEnabled && !emergencyStopped ? 'ON' : 'OFF'}
            </button>

            {/* Theme toggle */}
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              className="p-2 rounded-xl bg-slate-100 dark:bg-[#131C40] border border-slate-200 dark:border-white/10 text-slate-700 dark:text-[#E2E6F0] hover:border-[#00E5FF]/50 transition-colors cursor-pointer"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-600" />}
            </button>

            {/* Emergency Stop or Resume */}
            {emergencyStopped ? (
              <Button size="sm" variant="primary" onClick={handleResumeSystem}>
                Resume Swarm
              </Button>
            ) : (
              <Button
                size="sm"
                variant="danger"
                leftIcon={<OctagonAlert className="h-4 w-4" />}
                onClick={() => setStopModalOpen(true)}
              >
                <span className="hidden sm:inline">Emergency Stop</span>
              </Button>
            )}
          </div>
        </header>

        {/* Emergency Banner */}
        {emergencyStopped && (
          <div className="bg-red-500/15 border-b border-red-500/35 px-6 py-2.5 flex items-center justify-between gap-4">
            <p className="text-xs sm:text-sm font-medium text-red-600 dark:text-red-300">
              EMERGENCY STOP ACTIVE — All autonomous agent execution, publishing, and background triggers are suspended.
            </p>
            <Button size="sm" variant="secondary" onClick={handleResumeSystem}>
              Restore Normal Operation
            </Button>
          </div>
        )}

        {/* Page Outlet */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
          <p role="status" className="mb-4 rounded border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
            Rebuild in progress. Home and Content use runtime data. Other screens still contain prototype data and unfinished controls; charts and activity are not verified account results.
          </p>
          <RouteContent><Outlet /></RouteContent>
        </main>
      </div>

      {/* Emergency Stop Confirmation Modal */}
      <Modal
        open={stopModalOpen}
        onClose={() => setStopModalOpen(false)}
        title="Trigger Emergency Stop?"
        description="This immediately pauses all 29 AI agents, cancels active workflow runs, and locks publishing connectors."
        footer={
          <>
            <Button variant="ghost" onClick={() => setStopModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleConfirmEmergencyStop}>
              Confirm Emergency Stop
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
          No local data or scheduled content drafts will be deleted. You can resume autonomous operations at any time from the top bar or Security center.
        </p>
      </Modal>

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
};
