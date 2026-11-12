import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'warning' | 'error' | 'info';

export interface ToastItem {
  id: string;
  title: string;
  message?: string;
  type?: ToastType;
}

export interface ToastProps {
  toast: ToastItem;
  onDismiss: (id: string) => void;
}

const iconMap: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />,
  warning: <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />,
  error: <XCircle className="h-5 w-5 text-red-400 shrink-0" />,
  info: <Info className="h-5 w-5 text-[#00E5FF] shrink-0" />,
};

const borderMap: Record<ToastType, string> = {
  success: 'border-emerald-500/35',
  warning: 'border-amber-500/35',
  error: 'border-red-500/35',
  info: 'border-[#00E5FF]/35',
};

export const Toast: React.FC<ToastProps> = ({ toast, onDismiss }) => {
  const type = toast.type ?? 'info';
  return (
    <div
      role="status"
      className={`flex items-start gap-3 w-full max-w-sm rounded-xl p-4 bg-white dark:bg-[#131C40]/95 backdrop-blur-xl border shadow-xl ${borderMap[type]}`}
    >
      {iconMap[type]}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-900 dark:text-white">{toast.title}</p>
        {toast.message && (
          <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-300">{toast.message}</p>
        )}
      </div>
      <button
        type="button"
        aria-label="Dismiss notification"
        onClick={() => onDismiss(toast.id)}
        className="text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors cursor-pointer"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

export interface ToastContainerProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;
  return (
    <div
      aria-live="polite"
      className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 w-full max-w-sm pointer-events-none"
    >
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <Toast toast={t} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  );
};
