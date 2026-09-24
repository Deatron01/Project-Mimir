import { cn } from '../../utils/cn';

export default function ProgressBar({ value, label, className }: { value: number | null; label: string; className?: string }) {
  const pct = value === null ? null : Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct ?? undefined}
      className={cn('h-1.5 w-full overflow-hidden rounded-full bg-border/30', className)}
    >
      <div
        className={cn('h-full rounded-full bg-accent transition-[width] duration-300', pct === null && 'w-1/3 animate-pulse')}
        style={pct === null ? undefined : { width: `${pct}%` }}
      />
    </div>
  );
}
