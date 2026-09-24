import { useEffect, useId, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useActiveJobs } from '../../api/hooks/jobs';
import ProgressBar from '../common/ProgressBar';

/** Navbar pill with the user's running/queued jobs (TOP-14 queue visibility). Hidden when idle. */
export default function QueueIndicator() {
  const { t } = useTranslation();
  const jobs = useActiveJobs();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const panelId = useId();
  const list = jobs.data ?? [];

  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (!list.length) return null;
  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={panelId}
        className="flex h-9 items-center gap-1.5 rounded-full border border-accent/50 bg-accent/10 px-3 text-xs font-semibold text-accent"
      >
        <Loader2 size={14} className="animate-spin" aria-hidden="true" />
        {t('jobs.indicator', { count: list.length })}
      </button>
      {open && (
        <div id={panelId} className="absolute right-0 top-11 z-50 w-80 rounded-2xl border border-border/40 bg-background/95 p-4 shadow-glass backdrop-blur-xl">
          <h2 className="mb-3 text-sm font-bold">{t('jobs.panelTitle')}</h2>
          <ul className="flex flex-col gap-3">
            {list.map((j) => {
              const label =
                j.status === 'queued'
                  ? j.queue_position
                    ? t('jobs.queued', { position: j.queue_position })
                    : t('jobs.status.queued')
                  : t(`jobs.stage.${j.stage ?? 'running'}`, { defaultValue: t('jobs.status.running') });
              return (
                <li key={j.id} className="text-xs">
                  <div className="mb-1 flex justify-between gap-2">
                    <span className="font-medium text-textMain">{t(`jobs.type.${j.type}`)}</span>
                    <span className="text-muted">{label}</span>
                  </div>
                  <ProgressBar value={j.status === 'queued' ? null : j.progress} label={label} />
                  {j.topic_id && (
                    <Link to={`/topics/${j.topic_id}`} onClick={() => setOpen(false)} className="mt-1 inline-block text-accent hover:underline">
                      {t('jobs.openTopic')}
                    </Link>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
