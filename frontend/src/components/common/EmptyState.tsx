import type { LucideIcon } from 'lucide-react';
import { cn } from '../../utils/cn';

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-col items-center justify-center rounded-3xl border border-dashed border-border/50 bg-surface/10 px-6 py-14 text-center', className)}>
      <Icon size={44} className="mb-4 text-muted" aria-hidden="true" />
      <h2 className="mb-1 text-lg font-semibold text-textMain">{title}</h2>
      {description && <p className="mb-6 max-w-sm text-sm text-muted">{description}</p>}
      {action}
    </div>
  );
}
