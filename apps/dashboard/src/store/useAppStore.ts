import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ToastItem, ToastType } from '@javo/design-system';

export type ThemeMode = 'dark' | 'light';

interface AppState {
  theme: ThemeMode;
  sidebarCollapsed: boolean;
  setupCompleted: boolean;
  emergencyStopped: boolean;
  autopilotEnabled: boolean;
  backendConnected: boolean;
  toasts: ToastItem[];
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  setSetupCompleted: (done: boolean) => void;
  triggerEmergencyStop: () => void;
  resetEmergencyStop: () => void;
  setAutopilotEnabled: (enabled: boolean) => void;
  addToast: (title: string, message?: string, type?: ToastType) => void;
  dismissToast: (id: string) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: 'dark',
      sidebarCollapsed: false,
      setupCompleted: true,
      emergencyStopped: false,
      autopilotEnabled: true,
      backendConnected: true,
      toasts: [],
      setTheme: (theme) => set({ theme }),
      toggleTheme: () =>
        set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSetupCompleted: (setupCompleted) => set({ setupCompleted }),
      triggerEmergencyStop: () =>
        set({ emergencyStopped: true, autopilotEnabled: false }),
      resetEmergencyStop: () => set({ emergencyStopped: false }),
      setAutopilotEnabled: (autopilotEnabled) => set({ autopilotEnabled }),
      addToast: (title, message, type = 'info') => {
        const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
        set((state) => ({
          toasts: [...state.toasts.slice(-3), { id, title, message, type }],
        }));
        setTimeout(() => {
          set((state) => ({
            toasts: state.toasts.filter((t) => t.id !== id),
          }));
        }, 4200);
      },
      dismissToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),
    }),
    {
      name: 'javo-app-storage',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        setupCompleted: state.setupCompleted,
        autopilotEnabled: state.autopilotEnabled,
      }),
    }
  )
);
