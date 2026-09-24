import { useState } from 'react';
import { FileText, RotateCcw, Trash2, UploadCloud } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Button from '../ui/Button';
import ConfirmDialog from '../common/ConfirmDialog';
import EmptyState from '../common/EmptyState';
import ErrorNotice, { useErrorText } from '../common/ErrorNotice';
import ProgressBar from '../common/ProgressBar';
import Spinner from '../common/Spinner';
import { useToast } from '../common/Toaster';
import Dropzone from '../topics/Dropzone';
import FileStatusBadge from '../topics/FileStatusBadge';
import { useDeleteFile, useFiles, useRetryFile, useUploadFiles } from '../../api/hooks/files';
import { useMe } from '../../api/hooks/me';
import { DEFAULT_LIMITS, type Topic, type TopicFile } from '../../api/types';
import { formatBytes, formatDate } from '../../utils/format';

/** Files pane (TOP-13): upload with byte progress, live ingestion status over SSE, retry and delete. */
export default function FilesPane({ topic }: { topic: Topic }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? 'hu';
  const toast = useToast();
  const errorText = useErrorText();
  const files = useFiles(topic.id);
  const me = useMe();
  const limits = me.data?.limits ?? DEFAULT_LIMITS;
  const upload = useUploadFiles(topic.id);
  const retry = useRetryFile(topic.id);
  const del = useDeleteFile(topic.id);
  const [selected, setSelected] = useState<File[]>([]);
  const [consent, setConsent] = useState(false);
  const [consentError, setConsentError] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [toDelete, setToDelete] = useState<TopicFile | null>(null);

  const list = files.data ?? [];
  const usedBytes = list.reduce((s, f) => s + f.size_bytes, 0);
  const deleting = topic.status === 'deleting';

  const submit = async () => {
    if (!selected.length) return;
    if (!consent) {
      setConsentError(true);
      return;
    }
    setProgress(0);
    try {
      const res = await upload.mutateAsync({ files: selected, onProgress: setProgress });
      toast(t('files.uploaded', { count: res.files.length }));
      setSelected([]);
      setConsent(false);
    } catch {
      /* shown below via upload.error */
    } finally {
      setProgress(null);
    }
  };

  const confirmDelete = async () => {
    if (!toDelete) return;
    try {
      await del.mutateAsync(toDelete.id);
      toast(t('files.deleted', { name: toDelete.filename }));
    } catch (err) {
      toast(errorText(err), 'error');
    }
    setToDelete(null);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
      <section aria-labelledby="upload-title" className="card h-max p-5">
        <h2 id="upload-title" className="mb-3 flex items-center gap-2 text-lg font-bold">
          <UploadCloud size={18} className="text-accent" aria-hidden="true" /> {t('files.uploadTitle')}
        </h2>
        <Dropzone
          files={selected}
          onFilesChange={(f) => {
            setSelected(f);
            upload.reset();
          }}
          consent={consent}
          onConsentChange={(v) => {
            setConsent(v);
            setConsentError(false);
          }}
          consentError={consentError}
          limits={limits}
          existingCount={list.length}
          existingBytes={usedBytes}
          disabled={progress !== null || deleting}
          compact
        />
        {progress !== null && <ProgressBar className="mt-3" value={progress} label={t('upload.progress', { pct: Math.round(progress * 100) })} />}
        {upload.isError && <ErrorNotice className="mt-3" error={upload.error} />}
        {selected.length > 0 && (
          <Button className="mt-4 w-full" size="sm" onClick={() => void submit()} isLoading={progress !== null}>
            {t('files.uploadButton', { count: selected.length })}
          </Button>
        )}
        <div className="mt-5 space-y-2 text-xs text-muted">
          <div className="flex justify-between">
            <span>{t('files.usage.files')}</span>
            <span>
              {list.length} / {limits.max_files_per_topic}
            </span>
          </div>
          <ProgressBar value={list.length / limits.max_files_per_topic} label={t('files.usage.files')} />
          <div className="flex justify-between pt-1">
            <span>{t('files.usage.storage')}</span>
            <span>
              {formatBytes(usedBytes, lang)} / {formatBytes(limits.max_topic_bytes, lang)}
            </span>
          </div>
          <ProgressBar value={usedBytes / limits.max_topic_bytes} label={t('files.usage.storage')} />
        </div>
      </section>

      <section aria-labelledby="files-title">
        <h2 id="files-title" className="mb-3 text-lg font-bold">
          {t('files.listTitle')}
        </h2>
        {files.isPending ? (
          <Spinner className="py-16" />
        ) : files.isError ? (
          <ErrorNotice error={files.error} onRetry={() => void files.refetch()} />
        ) : list.length === 0 ? (
          <EmptyState icon={FileText} title={t('files.emptyTitle')} description={t('files.emptyDesc')} />
        ) : (
          <ul className="flex flex-col gap-2" aria-live="polite" aria-relevant="text">
            {list.map((f) => (
              <li key={f.id} className="card flex flex-col gap-2 p-4 sm:flex-row sm:items-center">
                <div className="flex min-w-0 flex-1 items-start gap-3">
                  <FileText size={20} className="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-textMain" title={f.filename}>
                      {f.filename}
                    </p>
                    <p className="text-xs text-muted">
                      {formatBytes(f.size_bytes, lang)} · {formatDate(f.created_at, lang)}
                      {f.status === 'ready' && ` · ${t('files.chunks', { count: f.chunk_count })}`}
                    </p>
                    {f.status === 'failed' && f.error_code && <p className="mt-1 text-xs text-danger">{t(`errors.${f.error_code}`, { defaultValue: t('errors.UNKNOWN') })}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-2 sm:justify-end">
                  <FileStatusBadge status={f.status} />
                  {f.status === 'failed' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => retry.mutate(f.id, { onError: (e) => toast(errorText(e), 'error') })}
                      disabled={retry.isPending && retry.variables === f.id}
                      aria-label={t('files.retryLabel', { name: f.filename })}
                    >
                      <RotateCcw size={14} aria-hidden="true" /> {t('common.retry')}
                    </Button>
                  )}
                  <button
                    type="button"
                    onClick={() => setToDelete(f)}
                    aria-label={t('files.deleteLabel', { name: f.filename })}
                    className="flex h-9 w-9 items-center justify-center rounded-full text-muted hover:bg-danger/10 hover:text-danger"
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={confirmDelete}
        busy={del.isPending}
        danger
        title={t('files.deleteTitle')}
        confirmLabel={t('common.delete')}
        body={<p>{t('files.deleteBody', { name: toDelete?.filename ?? '' })}</p>}
      />
    </div>
  );
}
