/** Locale-aware formatting helpers (HU uses space-separated thousands and 24h time). */
export function formatBytes(bytes: number, lang = 'hu'): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let v = bytes;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${new Intl.NumberFormat(lang, { maximumFractionDigits: i === 0 ? 0 : 1 }).format(v)} ${units[i]}`;
}

export function formatDate(iso: string, lang = 'hu', opts: Intl.DateTimeFormatOptions = { dateStyle: 'medium', timeStyle: 'short' }): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : new Intl.DateTimeFormat(lang, opts).format(d);
}

/** "3 days ago" / "in 2 months" using Intl.RelativeTimeFormat. */
export function formatRelative(iso: string, lang = 'hu', now = Date.now()): string {
  const diff = (Date.parse(iso) - now) / 1000;
  const rtf = new Intl.RelativeTimeFormat(lang, { numeric: 'auto' });
  const abs = Math.abs(diff);
  if (abs < 60) return rtf.format(Math.round(diff), 'second');
  if (abs < 3600) return rtf.format(Math.round(diff / 60), 'minute');
  if (abs < 86_400) return rtf.format(Math.round(diff / 3600), 'hour');
  if (abs < 86_400 * 30) return rtf.format(Math.round(diff / 86_400), 'day');
  if (abs < 86_400 * 365) return rtf.format(Math.round(diff / (86_400 * 30)), 'month');
  return rtf.format(Math.round(diff / (86_400 * 365)), 'year');
}

export const daysUntil = (iso: string, now = Date.now()): number => Math.ceil((Date.parse(iso) - now) / 86_400_000);

/**
 * Minutes and seconds for a wait estimate; above a minute rounded to 5 s so the text does not jitter.
 * Format with the `progress.duration.*` translations.
 */
export function splitDuration(seconds: number): { m: number; s: number } {
  const total = Math.max(0, Math.round(seconds));
  const rounded = total < 60 ? total : Math.round(total / 5) * 5;
  return { m: Math.floor(rounded / 60), s: rounded % 60 };
}

/** Stopwatch style, e.g. "1:05". */
export function formatClock(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
}
