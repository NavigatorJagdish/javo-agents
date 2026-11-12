import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  children: React.ReactNode;
  footer?: React.ReactNode;
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

export const Modal: React.FC<ModalProps> = ({
  open,
  onClose,
  title,
  description,
  size = 'md',
  children,
  footer,
}) => {
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'javo-modal-title' : undefined}
    >
      <div
        className="fixed inset-0 bg-[#050816]/75 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        className={`relative z-10 w-full ${sizeClasses[size]} rounded-2xl bg-white dark:bg-[#0F1736] border border-slate-200 dark:border-[#00E5FF]/25 shadow-2xl dark:shadow-[0_0_48px_rgba(0,229,255,0.14)] overflow-hidden`}
      >
        {(title || description) && (
          <div className="flex items-start justify-between gap-4 px-6 py-4 border-b border-slate-200 dark:border-white/10">
            <div>
              {title && (
                <h2
                  id="javo-modal-title"
                  className="text-lg font-semibold text-slate-900 dark:text-white"
                >
                  {title}
                </h2>
              )}
              {description && (
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close modal"
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/10 transition-colors cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}
        <div className="px-6 py-5 max-h-[75vh] overflow-y-auto text-slate-700 dark:text-[#E2E6F0]">
          {children}
        </div>
        {footer && (
          <div className="px-6 py-4 bg-slate-50 dark:bg-[#0B1026]/60 border-t border-slate-200 dark:border-white/10 flex items-center justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};
