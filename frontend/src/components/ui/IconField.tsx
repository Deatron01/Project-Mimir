import type React from 'react';
import type { LucideIcon } from 'lucide-react';

interface IconFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: React.ReactNode;
  icon?: LucideIcon;
  hint?: React.ReactNode;
}

/** Labelled input with a leading icon. */
export default function IconField({ id, label, icon: Icon, className = '', hint, ...inputProps }: IconFieldProps) {
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-2 ml-1 block text-sm font-medium text-textMain">
        {label}
      </label>
      <div className="relative">
        {Icon && <Icon size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />}
        <input
          id={id}
          className={`field ${Icon ? 'pl-11' : ''}`}
          aria-describedby={hint ? `${id}-hint` : undefined}
          {...inputProps}
        />
      </div>
      {hint && (
        <p id={`${id}-hint`} className="ml-1 mt-1.5 text-xs text-muted">
          {hint}
        </p>
      )}
    </div>
  );
}
