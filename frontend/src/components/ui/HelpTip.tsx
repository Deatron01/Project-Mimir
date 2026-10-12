import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { HelpCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';

const WIDTH = 256;
const GAP = 8;
const MARGIN = 12;

interface Props {
  /** The explanation, in one or two plain sentences. */
  children: React.ReactNode;
  /** What is being explained; used for the button's accessible name ("Help: …"). */
  label: string;
  className?: string;
  size?: number;
}

/**
 * The little "?" next to anything that needs explaining. A toggletip: opens on hover, keyboard focus or tap,
 * closes on Escape, outside click or when the pointer leaves. Rendered in a portal so scrolling or
 * `overflow: hidden` containers never clip it. Must not be placed inside a <label> (a button is labelable).
 */
export default function HelpTip({ children, label, className, size = 15 }: Props) {
  const { t } = useTranslation();
  const id = useId();
  const btn = useRef<HTMLButtonElement>(null);
  const tip = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false); // opened by click/tap: stays until dismissed
  const [pos, setPos] = useState<{ top: number; left: number; arrow: number; below: boolean } | null>(null);
  const hoverTimer = useRef<number>();

  const close = useCallback(() => {
    setOpen(false);
    setPinned(false);
  }, []);

  const place = useCallback(() => {
    const b = btn.current?.getBoundingClientRect();
    if (!b) return;
    const width = Math.min(WIDTH, window.innerWidth - MARGIN * 2);
    const center = b.left + b.width / 2;
    const left = Math.max(MARGIN, Math.min(center - width / 2, window.innerWidth - width - MARGIN));
    const height = tip.current?.offsetHeight ?? 80;
    const below = b.top - height - GAP < MARGIN;
    setPos({ top: below ? b.bottom + GAP : b.top - height - GAP, left, arrow: center - left, below });
  }, []);

  useLayoutEffect(() => {
    if (open) place();
  }, [open, place]);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        close();
        btn.current?.focus();
      }
    };
    const onDown = (e: PointerEvent) => {
      const target = e.target as Node;
      if (!btn.current?.contains(target) && !tip.current?.contains(target)) close();
    };
    window.addEventListener('keydown', onKey, true);
    document.addEventListener('pointerdown', onDown);
    window.addEventListener('resize', place);
    window.addEventListener('scroll', place, true);
    return () => {
      window.removeEventListener('keydown', onKey, true);
      document.removeEventListener('pointerdown', onDown);
      window.removeEventListener('resize', place);
      window.removeEventListener('scroll', place, true);
    };
  }, [open, close, place]);

  useEffect(() => () => window.clearTimeout(hoverTimer.current), []);

  const hoverIn = (e: React.PointerEvent) => {
    if (e.pointerType !== 'mouse') return;
    window.clearTimeout(hoverTimer.current);
    hoverTimer.current = window.setTimeout(() => setOpen(true), 120);
  };
  const hoverOut = (e: React.PointerEvent) => {
    if (e.pointerType !== 'mouse') return;
    window.clearTimeout(hoverTimer.current);
    if (!pinned) hoverTimer.current = window.setTimeout(() => setOpen(false), 150);
  };

  return (
    // Positioned wrapper: keeps the sr-only live region inside any scroll container the tip sits in.
    <span className={cn('relative inline-flex shrink-0', className)}>
      <button
        ref={btn}
        type="button"
        aria-label={t('help.label', { topic: label })}
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        onClick={() => {
          if (open && pinned) close();
          else {
            setOpen(true);
            setPinned(true);
          }
        }}
        onPointerEnter={hoverIn}
        onPointerLeave={hoverOut}
        onBlur={(e) => {
          if (!tip.current?.contains(e.relatedTarget as Node)) close();
        }}
        className={cn(
          'relative inline-flex shrink-0 items-center justify-center rounded-full align-middle text-muted transition-colors hover:text-accent focus-visible:text-accent',
          // Small icon, comfortable touch target.
          'h-6 w-6 before:absolute before:-inset-2.5',
          open && 'text-accent',
        )}
      >
        <HelpCircle size={size} aria-hidden="true" />
      </button>
      {/* Toggletip: the text is announced when it opens; the floating copy below is visual only. */}
      <span className="sr-only" aria-live="polite">
        {open ? children : ''}
      </span>
      {createPortal(
        <AnimatePresence>
          {open && (
            <motion.div
              ref={tip}
              id={id}
              aria-hidden="true"
              initial={{ opacity: 0, y: pos?.below ? -4 : 4, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97, transition: { duration: 0.1 } }}
              transition={{ duration: 0.14, ease: 'easeOut' }}
              onPointerEnter={() => window.clearTimeout(hoverTimer.current)}
              onPointerLeave={hoverOut}
              style={{ top: pos?.top ?? -9999, left: pos?.left ?? -9999, width: Math.min(WIDTH, window.innerWidth - MARGIN * 2) }}
              className="fixed z-[200] rounded-2xl border border-border/50 bg-background px-3.5 py-2.5 text-left text-xs font-normal normal-case leading-relaxed tracking-normal text-textMain shadow-glass"
            >
              {children}
              <span
                aria-hidden="true"
                style={{ left: (pos?.arrow ?? 0) - 5 }}
                className={cn(
                  'absolute h-2.5 w-2.5 rotate-45 border-border/50 bg-background',
                  pos?.below ? '-top-[6px] border-l border-t' : '-bottom-[6px] border-b border-r',
                )}
              />
            </motion.div>
          )}
        </AnimatePresence>,
        document.body,
      )}
    </span>
  );
}
