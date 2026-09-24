import type { LucideIcon } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
  icon?: LucideIcon;
}
interface Props<T extends string> {
  label: string;
  options: SegmentOption<T>[];
  value: T;
  onChange: (v: T) => void;
  className?: string;
}

/** Accessible radio-group styled as a segmented switch. */
export default function SegmentedControl<T extends string>({ label, options, value, onChange, className }: Props<T>) {
  return (
    <div role="radiogroup" aria-label={label} className={cn('flex rounded-full border border-border/50 bg-background/40 p-1', className)}>
      {options.map((opt) => {
        const active = opt.value === value;
        const Icon = opt.icon;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt.value)}
            className={cn(
              'flex flex-1 items-center justify-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors',
              active ? 'bg-primary text-onPrimary shadow-sm' : 'text-muted hover:text-textMain hover:bg-surface/60',
            )}
          >
            {Icon && <Icon size={14} aria-hidden="true" />}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
