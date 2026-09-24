import { AlertCircle, CheckCircle2, Clock, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { FileStatus } from '../../api/types';
import { cn } from '../../utils/cn';

export default function FileStatusBadge({ status }: { status: FileStatus }) {
  const { t } = useTranslation();
  const busy = status === 'extracting' || status === 'chunking' || status === 'indexing';
  const Icon = status === 'ready' ? CheckCircle2 : status === 'failed' ? AlertCircle : busy ? Loader2 : Clock;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold',
        status === 'ready' && 'border-success/50 bg-success/10 text-success',
        status === 'failed' && 'border-danger/50 bg-danger/10 text-danger',
        (busy || status === 'queued') && 'border-border/50 bg-surface/50 text-muted',
      )}
    >
      <Icon size={12} className={cn(busy && 'animate-spin')} aria-hidden="true" />
      {t(`files.status.${status}`)}
    </span>
  );
}
