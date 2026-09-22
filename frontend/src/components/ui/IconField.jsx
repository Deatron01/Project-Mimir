import React from 'react';

/** Labelled input with a leading icon. */
export default function IconField({ id, label, icon: Icon, className = '', ...inputProps }) {
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-2 ml-1 block text-sm font-medium text-textMain">
        {label}
      </label>
      <div className="relative">
        {Icon && <Icon size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />}
        <input id={id} className={`field ${Icon ? 'pl-11' : ''}`} {...inputProps} />
      </div>
    </div>
  );
}
