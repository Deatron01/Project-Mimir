import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, Info, X, XCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';

type Tone = 'success' | 'error' | 'info';
interface Toast {
  id: number;
  tone: Tone;
  text: string;
}
const ToastCtx = createContext<(text: string, tone?: Tone) => void>(() => undefined);

/** Short confirmations ("Saved", "Topic deleted"). Announced politely; errors assertively. */
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const [toasts, setToasts] = useState<Toast[]>([]);
  const seq = useRef(0);
  const dismiss = useCallback((id: number) => setToasts((l) => l.filter((x) => x.id !== id)), []);
  const push = useCallback(
    (text: string, tone: Tone = 'success') => {
      seq.current += 1;
      const id = seq.current;
      setToasts((l) => [...l.slice(-3), { id, tone, text }]);
      setTimeout(() => dismiss(id), tone === 'error' ? 8000 : 4000);
    },
    [dismiss],
  );
  const value = useMemo(() => push, [push]);
  const Icon = { success: CheckCircle2, error: XCircle, info: Info };
  return (
    <ToastCtx.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-[90] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2">
        <div aria-live="polite" className="sr-only">
          {toasts.filter((x) => x.tone !== 'error').map((x) => x.text).join('. ')}
        </div>
        <div aria-live="assertive" className="sr-only">
          {toasts.filter((x) => x.tone === 'error').map((x) => x.text).join('. ')}
        </div>
        <AnimatePresence>
          {toasts.map((x) => {
            const I = Icon[x.tone];
            return (
              <motion.div
                key={x.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 12 }}
                className={cn(
                  'pointer-events-auto flex items-start gap-3 rounded-2xl border bg-background/95 p-4 text-sm shadow-xl backdrop-blur-md',
                  x.tone === 'success' && 'border-success/50 text-textMain',
                  x.tone === 'error' && 'border-danger/50 text-textMain',
                  x.tone === 'info' && 'border-border/50 text-textMain',
                )}
              >
                <I size={18} className={cn('mt-0.5 shrink-0', x.tone === 'success' ? 'text-success' : x.tone === 'error' ? 'text-danger' : 'text-accent')} aria-hidden="true" />
                <p className="flex-1">{x.text}</p>
                <button type="button" onClick={() => dismiss(x.id)} aria-label={t('common.close')} className="text-muted hover:text-textMain">
                  <X size={16} aria-hidden="true" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);
