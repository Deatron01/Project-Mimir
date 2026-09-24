import { useEffect, useRef } from 'react';
import { Check, Circle, Cloud, HardDrive, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import ProgressBar from '../common/ProgressBar';
import TimeEstimate from '../common/TimeEstimate';
import useNow from '../../hooks/useNow';
import { cn } from '../../utils/cn';

export type GenerationPhase = 'extracting' | 'chunking' | 'indexing' | 'generating';
export const PHASES: GenerationPhase[] = ['extracting', 'chunking', 'indexing', 'generating'];

/** `GET /status/{job_id}` of the legacy backend (Bifrost), plus when the browser received it. */
export interface ServerJobStatus {
  stage?: string;
  progress?: number;
  eta_s?: number;
  elapsed_s?: number;
  expected_total_s?: number;
  model?: string | null;
  location?: 'external' | 'local';
  receivedAt: number;
}

// Share of the whole wait per phase: text extraction, chunking and indexing are quick; the LLM dominates.
const RANGES: Record<GenerationPhase, [number, number]> = {
  extracting: [0, 0.05],
  chunking: [0.05, 0.12],
  indexing: [0.12, 0.2],
  generating: [0.2, 1],
};
/** Typical seconds for extract + chunk + index before the generation job starts. */
export const PREP_SECONDS = 15;
const MIN_REMAINING_S = 3;

export interface Estimate {
  progress: number;
  elapsedS: number;
  remainingS: number;
  overdue: boolean;
}

/**
 * Overall progress and remaining time. Before the job starts: typical prep time + the server's learned
 * average for the chosen model. During generation: the server's own estimate, counted down between polls.
 */
export function estimate(
  phase: GenerationPhase,
  job: ServerJobStatus | null,
  now: number,
  startedAt: number,
  expectedGenS: number,
): Estimate {
  const elapsedS = (now - startedAt) / 1000;
  const [lo, hi] = RANGES[phase];
  if (phase !== 'generating' || !job) {
    const prepLeft = phase === 'generating' ? 0 : Math.max(PREP_SECONDS - elapsedS, MIN_REMAINING_S);
    return { progress: lo, elapsedS, remainingS: prepLeft + expectedGenS, overdue: false };
  }
  const since = (now - job.receivedAt) / 1000;
  const p = Math.max(0, Math.min(1, job.progress ?? 0));
  const remainingS = Math.max((job.eta_s ?? expectedGenS) - since, MIN_REMAINING_S);
  const expected = job.expected_total_s ?? expectedGenS;
  const overdue = (job.elapsed_s ?? 0) + since > expected * 1.5 && p < 0.9;
  return { progress: lo + (hi - lo) * p, elapsedS, remainingS, overdue };
}

/** Loader for the legacy single-document flow: steps, overall bar, elapsed and remaining time. */
export default function GenerationProgress({
  phase,
  job,
  startedAt,
  expectedGenS,
  onCancel,
}: {
  phase: GenerationPhase;
  job: ServerJobStatus | null;
  startedAt: number;
  expectedGenS: number;
  onCancel?: () => void;
}) {
  const { t } = useTranslation();
  const now = useNow(true);
  const est = estimate(phase, job, now, startedAt, expectedGenS);
  const pct = Math.round(est.progress * 100);
  const current = PHASES.indexOf(phase);

  // Percentage in the tab title, so the wait can be followed from another tab.
  const baseTitle = useRef(document.title);
  useEffect(() => {
    document.title = `${pct}% · ${baseTitle.current}`;
  }, [pct]);
  useEffect(() => {
    const base = baseTitle.current;
    return () => {
      document.title = base;
    };
  }, []);

  const stageText =
    phase === 'generating' && job?.stage && job.stage !== 'queued'
      ? t(`jobs.stage.${job.stage}`, { defaultValue: t('jobs.status.running') })
      : t(`progress.phase.${phase}`);

  return (
    <div className="w-full space-y-3" role="status" aria-live="polite" aria-atomic="false" data-testid="generation-progress">
      <div className="flex items-center justify-between gap-3">
        <span className="flex items-center gap-2 text-sm font-medium text-textMain">
          <Loader2 size={16} className="animate-spin text-accent" aria-hidden="true" />
          {stageText}
        </span>
        <span className="text-sm font-semibold tabular-nums text-accent" aria-hidden="true">
          {pct}%
        </span>
      </div>
      <ProgressBar value={est.progress} label={t('progress.label')} />
      <TimeEstimate elapsedS={est.elapsedS} remainingS={est.remainingS} overdue={est.overdue} />

      <ol className="grid gap-1.5 text-xs sm:grid-cols-2">
        {PHASES.map((p, i) => {
          const state = i < current ? 'done' : i === current ? 'active' : 'todo';
          return (
            <li
              key={p}
              className={cn('flex items-center gap-2', state === 'todo' ? 'text-muted' : 'text-textMain', state === 'active' && 'font-semibold')}
            >
              {state === 'done' ? (
                <Check size={14} className="text-success" aria-hidden="true" />
              ) : state === 'active' ? (
                <Loader2 size={14} className="animate-spin text-accent" aria-hidden="true" />
              ) : (
                <Circle size={14} aria-hidden="true" />
              )}
              <span>
                {t(`progress.step.${p}`)}
                <span className="sr-only">{`, ${t(`progress.state.${state}`)}`}</span>
              </span>
            </li>
          );
        })}
      </ol>

      {phase === 'generating' && job?.model && (
        <p className="flex items-center gap-1.5 text-xs text-muted">
          {job.location === 'local' ? <HardDrive size={12} aria-hidden="true" /> : <Cloud size={12} aria-hidden="true" />}
          {t(`progress.location.${job.location ?? 'external'}`, { model: job.model })}
        </p>
      )}

      {onCancel && (
        <button
          type="button"
          onClick={onCancel}
          className="text-xs font-medium text-muted underline-offset-2 hover:text-danger hover:underline"
        >
          {t('progress.stop')}
        </button>
      )}
    </div>
  );
}
