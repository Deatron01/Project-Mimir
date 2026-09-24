import { AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ApiError } from '../../api/errors';
import { cn } from '../../utils/cn';

/** Translates any error: ApiError codes map to `errors.<CODE>`, anything else to a generic message. */
export function useErrorText() {
  const { t, i18n } = useTranslation();
  return (error: unknown): string => {
    if (error instanceof ApiError) {
      const vars = { ...(error.details ?? {}), limitMb: typeof error.details?.limit === 'number' ? Math.round(Number(error.details.limit) / 1048576) : undefined };
      return i18n.exists(error.i18nKey) ? t(error.i18nKey, vars) : t('errors.UNKNOWN');
    }
    return t('errors.UNKNOWN');
  };
}

export default function ErrorNotice({ error, className, onRetry }: { error: unknown; className?: string; onRetry?: () => void }) {
  const { t } = useTranslation();
  const text = useErrorText();
  if (!error) return null;
  const requestId = error instanceof ApiError ? error.requestId : undefined;
  return (
    <div role="alert" className={cn('flex items-start gap-3 rounded-2xl border border-danger/40 bg-danger/10 p-4 text-sm text-danger', className)}>
      <AlertTriangle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p>{text(error)}</p>
        {requestId && <p className="mt-1 text-xs opacity-80">{t('errors.requestId', { id: requestId })}</p>}
      </div>
      {onRetry && (
        <button type="button" onClick={onRetry} className="shrink-0 font-semibold underline-offset-2 hover:underline">
          {t('common.retry')}
        </button>
      )}
    </div>
  );
}
