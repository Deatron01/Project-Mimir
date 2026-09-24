import { useId, useRef, useState } from 'react';
import { FileText, ShieldCheck, UploadCloud, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';
import { formatBytes } from '../../utils/format';
import { DEFAULT_LIMITS, type Limits } from '../../api/types';

export interface RejectedFile {
  name: string;
  reason: 'type' | 'size' | 'count' | 'storage' | 'duplicate';
}

export function validateFiles(
  incoming: File[],
  current: File[],
  opts: { limits?: Limits; existingCount?: number; existingBytes?: number } = {},
): { accepted: File[]; rejected: RejectedFile[] } {
  const limits = opts.limits ?? DEFAULT_LIMITS;
  const accepted: File[] = [];
  const rejected: RejectedFile[] = [];
  let count = (opts.existingCount ?? 0) + current.length;
  let bytes = (opts.existingBytes ?? 0) + current.reduce((s, f) => s + f.size, 0);
  let batch = current.length;
  for (const f of incoming) {
    const ext = f.name.split('.').pop()?.toLowerCase() ?? '';
    if (!limits.allowed_types.includes(ext)) rejected.push({ name: f.name, reason: 'type' });
    else if (f.size > limits.max_file_bytes) rejected.push({ name: f.name, reason: 'size' });
    else if ([...current, ...accepted].some((c) => c.name === f.name && c.size === f.size)) rejected.push({ name: f.name, reason: 'duplicate' });
    else if (count + 1 > limits.max_files_per_topic || batch + 1 > limits.max_files_per_upload) rejected.push({ name: f.name, reason: 'count' });
    else if (bytes + f.size > limits.max_topic_bytes) rejected.push({ name: f.name, reason: 'storage' });
    else {
      accepted.push(f);
      count += 1;
      batch += 1;
      bytes += f.size;
    }
  }
  return { accepted, rejected };
}

interface Props {
  files: File[];
  onFilesChange: (files: File[]) => void;
  consent: boolean;
  onConsentChange: (v: boolean) => void;
  consentError?: boolean;
  limits?: Limits;
  existingCount?: number;
  existingBytes?: number;
  disabled?: boolean;
  compact?: boolean;
}

/**
 * Drag-and-drop / click-to-browse file picker with client-side limit checks and the GDPR upload consent.
 * The consent box resets whenever the selection is emptied.
 */
export default function Dropzone({
  files,
  onFilesChange,
  consent,
  onConsentChange,
  consentError,
  limits = DEFAULT_LIMITS,
  existingCount = 0,
  existingBytes = 0,
  disabled,
  compact,
}: Props) {
  const { t, i18n } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [rejected, setRejected] = useState<RejectedFile[]>([]);
  const hintId = useId();
  const consentId = useId();
  const lang = i18n.resolvedLanguage ?? 'hu';

  const add = (list: FileList | null) => {
    if (!list?.length) return;
    const { accepted, rejected: rej } = validateFiles([...list], files, { limits, existingCount, existingBytes });
    setRejected(rej);
    if (accepted.length) onFilesChange([...files, ...accepted]);
  };
  const remove = (idx: number) => {
    const next = files.filter((_, i) => i !== idx);
    onFilesChange(next);
    if (!next.length) onConsentChange(false);
  };

  const accept = limits.allowed_types.map((x) => `.${x}`).join(',');

  return (
    <div className="flex flex-col gap-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          if (!disabled) add(e.dataTransfer.files);
        }}
        className={cn(
          'relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed text-center transition-colors',
          compact ? 'px-4 py-5' : 'px-6 py-8',
          over ? 'border-accent bg-accent/10' : 'border-border/60 bg-surface/20',
          disabled && 'opacity-50',
        )}
      >
        <UploadCloud size={compact ? 24 : 32} className="mb-2 text-accent" aria-hidden="true" />
        <p className="text-sm font-medium text-textMain">
          {t('upload.drop')}{' '}
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={disabled}
            aria-describedby={hintId}
            className="font-semibold text-accent underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {t('upload.browse')}
          </button>
        </p>
        <p id={hintId} className="mt-1 text-xs text-muted">
          {t('upload.limits', {
            types: limits.allowed_types.map((x) => x.toUpperCase()).join(', '),
            fileMb: Math.round(limits.max_file_bytes / 1048576),
            perUpload: limits.max_files_per_upload,
            perTopic: limits.max_files_per_topic,
            topicMb: Math.round(limits.max_topic_bytes / 1048576),
          })}
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={accept}
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
          onChange={(e) => {
            add(e.target.files);
            e.target.value = '';
          }}
        />
      </div>

      {rejected.length > 0 && (
        <ul role="alert" className="space-y-1 rounded-xl border border-danger/40 bg-danger/10 p-3 text-xs text-danger">
          {rejected.map((r) => (
            <li key={r.name + r.reason}>{t(`upload.rejected.${r.reason}`, { name: r.name })}</li>
          ))}
        </ul>
      )}

      {files.length > 0 && (
        <>
          <ul aria-label={t('upload.selected')} className="flex flex-col gap-1.5">
            {files.map((f, i) => (
              <li key={`${f.name}-${f.size}`} className="flex items-center gap-2 rounded-xl border border-border/40 bg-background/50 px-3 py-2 text-sm">
                <FileText size={16} className="shrink-0 text-accent" aria-hidden="true" />
                <span className="min-w-0 flex-1 truncate">{f.name}</span>
                <span className="shrink-0 text-xs text-muted">{formatBytes(f.size, lang)}</span>
                <button
                  type="button"
                  onClick={() => remove(i)}
                  disabled={disabled}
                  aria-label={t('upload.remove', { name: f.name })}
                  className="rounded-full p-1 text-muted hover:bg-danger/10 hover:text-danger"
                >
                  <X size={14} aria-hidden="true" />
                </button>
              </li>
            ))}
          </ul>

          <div className={cn('rounded-2xl border bg-surface/40 p-3 text-xs text-muted', consentError ? 'border-danger/60' : 'border-border/40')}>
            <label className="flex cursor-pointer items-start gap-2">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => onConsentChange(e.target.checked)}
                disabled={disabled}
                aria-describedby={consentId}
                aria-invalid={consentError || undefined}
                className="mt-0.5 h-4 w-4 shrink-0 accent-[rgb(var(--c-primary))]"
              />
              <span className="text-sm text-textMain">{t('upload.consent.label')}</span>
            </label>
            <p id={consentId} className="mt-2 flex items-start gap-2 pl-6">
              <ShieldCheck size={14} className="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
              <span>
                {t('upload.consent.details')}{' '}
                <Link to="/privacy" className="font-medium text-accent underline-offset-2 hover:underline">
                  {t('upload.consent.more')}
                </Link>
              </span>
            </p>
            {consentError && (
              <p role="alert" className="mt-2 pl-6 font-medium text-danger">
                {t('upload.consent.required')}
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
