import { Loader2, XCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import ProgressBar from '../common/ProgressBar';
import { useCancelJob, useJob } from '../../api/hooks/jobs';
import { useErrorText } from '../common/ErrorNotice';
import { useToast } from '../common/Toaster';

/** Live status of one job: queue position, stage and progress, with cancel. */
export default function JobProgress({ jobId, compact }: { jobId: string; compact?: boolean }) {
  const { t } = useTranslation();
  const job = useJob(jobId);
  const cancel = useCancelJob();
  const toast = useToast();
  const errorText = useErrorText();
  const j = job.data;
  if (!j || j.status === 'succeeded') return null;
  if (j.status === 'cancelled' || j.status === 'failed') {
    return (
      <p className="flex items-center gap-2 text-sm text-muted">
        <XCircle size={16} aria-hidden="true" /> {t(`jobs.status.${j.status}`)}
      </p>
    );
  }
  const label =
    j.status === 'queued'
      ? j.queue_position
        ? t('jobs.queued', { position: j.queue_position })
        : t('jobs.status.queued')
      : t(`jobs.stage.${j.stage ?? 'running'}`, { defaultValue: t('jobs.status.running') });
  return (
    <div className="flex flex-col gap-2" role="status" aria-live="polite">
      <div className="flex items-center justify-between gap-3">
        <span className="flex items-center gap-2 text-sm text-textMain">
          <Loader2 size={16} className="animate-spin text-accent" aria-hidden="true" />
          {label}
        </span>
        {!compact && (
          <button
            type="button"
            onClick={() => cancel.mutate(j.id, { onError: (e) => toast(errorText(e), 'error') })}
            disabled={cancel.isPending}
            className="text-xs font-medium text-muted underline-offset-2 hover:text-danger hover:underline"
          >
            {t('common.cancel')}
          </button>
        )}
      </div>
      <ProgressBar value={j.status === 'queued' ? null : j.progress} label={label} />
    </div>
  );
}
