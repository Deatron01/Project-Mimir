import { Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { formatClock, splitDuration } from '../../utils/format';

/**
 * "Elapsed 0:42 · about 1 min 20 sec left". Visual only (no live region), so screen readers are not
 * interrupted every second; the surrounding progress region announces stage changes.
 */
export default function TimeEstimate({
  elapsedS,
  remainingS,
  overdue = false,
}: {
  elapsedS: number;
  /** null = no estimate yet */
  remainingS: number | null;
  /** Taking longer than usual: say so instead of promising a number. */
  overdue?: boolean;
}) {
  const { t } = useTranslation();
  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted" data-testid="time-estimate">
      <Clock size={12} aria-hidden="true" />
      <span>{t('progress.elapsed', { time: formatClock(elapsedS) })}</span>
      <span aria-hidden="true">·</span>
      <span className="text-textMain">
        {overdue
          ? t('progress.overdue')
          : remainingS === null
            ? t('progress.estimating')
            : t('progress.remaining', { time: durationText(t, remainingS) })}
      </span>
    </p>
  );
}

export function durationText(t: (key: string, o?: Record<string, unknown>) => string, seconds: number): string {
  const { m, s } = splitDuration(seconds);
  if (!m) return t('progress.duration.s', { s });
  return s ? t('progress.duration.ms', { m, s }) : t('progress.duration.m', { m });
}
