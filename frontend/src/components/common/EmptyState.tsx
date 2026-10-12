import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import Mascot from '../mascot/Mascot';
import type { MascotMood } from '../../theme/mascots';
import { cn } from '../../utils/cn';

/** Friendly "nothing here yet" panel: what is missing and the one thing to do next. Shows the mascot when `mascot` is set. */
export default function EmptyState({
  icon: Icon,
  mascot,
  title,
  description,
  action,
  className,
  children,
}: {
  icon?: LucideIcon;
  mascot?: MascotMood;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={cn('flex flex-col items-center justify-center rounded-3xl border border-dashed border-border/50 bg-surface/10 px-6 py-12 text-center', className)}
    >
      {mascot ? (
        <Mascot mood={mascot} size={112} className="mb-4" />
      ) : (
        Icon && <Icon size={44} className="mb-4 text-muted" aria-hidden="true" />
      )}
      <h2 className="mb-1 text-lg font-bold text-textMain">{title}</h2>
      {description && <p className="mb-6 max-w-sm text-sm text-muted">{description}</p>}
      {action}
      {children}
    </motion.div>
  );
}
