import { useEffect, useId, useRef } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';

const FOCUSABLE = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: React.ReactNode;
  description?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  /** Element to focus first; defaults to the first focusable element. */
  initialFocusRef?: React.RefObject<HTMLElement | null>;
  /** Prevents closing by Escape/backdrop while a request runs. */
  busy?: boolean;
  role?: 'dialog' | 'alertdialog';
}

/**
 * Accessible modal: aria-modal, labelled by its title, focus trapped inside, Escape and backdrop close it,
 * focus returns to the opener, background scroll is locked.
 */
export default function Dialog({ open, onClose, title, description, children, footer, size = 'md', initialFocusRef, busy, role = 'dialog' }: DialogProps) {
  const { t } = useTranslation();
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const descId = useId();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const busyRef = useRef(busy);
  busyRef.current = busy;

  useEffect(() => {
    if (!open) return undefined;
    const opener = document.activeElement as HTMLElement | null;
    const { overflow } = document.body.style;
    document.body.style.overflow = 'hidden';
    const focusFirst = () => {
      const target = initialFocusRef?.current ?? panelRef.current?.querySelector<HTMLElement>(FOCUSABLE) ?? panelRef.current;
      target?.focus();
    };
    const raf = requestAnimationFrame(focusFirst);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !busyRef.current) {
        e.stopPropagation();
        closeRef.current();
      }
      if (e.key !== 'Tab' || !panelRef.current) return;
      const items = [...panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE)].filter((el) => el.offsetParent !== null || el === document.activeElement);
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', onKey, true);
    return () => {
      cancelAnimationFrame(raf);
      document.removeEventListener('keydown', onKey, true);
      document.body.style.overflow = overflow;
      opener?.focus?.();
    };
  }, [open, initialFocusRef]);

  return createPortal(
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[80] flex items-end justify-center p-0 sm:items-center sm:p-4">
          <motion.div
            className="absolute inset-0 bg-black/55 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => !busy && onClose()}
            aria-hidden="true"
          />
          <motion.div
            ref={panelRef}
            role={role}
            aria-modal="true"
            aria-labelledby={titleId}
            aria-describedby={description ? descId : undefined}
            tabIndex={-1}
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            className={cn(
              'relative flex max-h-[92vh] w-full flex-col overflow-hidden rounded-t-3xl border border-border/40 bg-background shadow-2xl focus:outline-none sm:rounded-3xl',
              size === 'sm' && 'sm:max-w-md',
              size === 'md' && 'sm:max-w-xl',
              size === 'lg' && 'sm:max-w-3xl',
            )}
          >
            <div className="flex items-start justify-between gap-4 border-b border-border/30 px-6 py-5">
              <div>
                <h2 id={titleId} className="text-xl font-bold tracking-tight text-textMain">
                  {title}
                </h2>
                {description && (
                  <p id={descId} className="mt-1 text-sm text-muted">
                    {description}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={onClose}
                disabled={busy}
                aria-label={t('common.close')}
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-muted hover:bg-surface/60 hover:text-textMain disabled:opacity-40"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
            <div className="overflow-y-auto px-6 py-5">{children}</div>
            {footer && <div className="flex flex-wrap justify-end gap-2 border-t border-border/30 px-6 py-4">{footer}</div>}
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
