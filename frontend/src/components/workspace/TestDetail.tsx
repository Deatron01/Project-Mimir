import { useCallback, useMemo, useRef, useState } from 'react';
import { Link, useBlocker, useParams } from 'react-router-dom';
import { ArrowLeft, Download, ShieldAlert, Star } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import Button from '../ui/Button';
import ConfirmDialog from '../common/ConfirmDialog';
import ErrorNotice, { useErrorText } from '../common/ErrorNotice';
import { PageLoader } from '../common/Spinner';
import { useToast } from '../common/Toaster';
import TestEditor, { type TestEditorHandle } from '../tests/TestEditor';
import ExportDialog from '../tests/ExportDialog';
import { useRegenerateQuestion, useSaveTest, useTest, useUpdateTest } from '../../api/hooks/tests';
import { useFiles } from '../../api/hooks/files';
import { useJob } from '../../api/hooks/jobs';
import { api } from '../../api/client';
import { unwrap } from '../../api/errors';
import { qk } from '../../api/keys';
import type { Exam, Job, Topic } from '../../api/types';

/** Test review & edit (FE-06): drag reorder, per-question regenerate, citations, opt-in save and export. */
export default function TestDetail({ topic }: { topic: Topic }) {
  const { testId = '' } = useParams();
  const { t } = useTranslation();
  const toast = useToast();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const test = useTest(topic.id, testId);
  const files = useFiles(topic.id);
  const update = useUpdateTest(topic.id, testId);
  const saveTest = useSaveTest(topic.id);
  const regen = useRegenerateQuestion(topic.id, testId);
  const editor = useRef<TestEditorHandle>(null);
  const [dirty, setDirty] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [regenerating, setRegenerating] = useState<Record<string, string>>({}); // questionId → jobId
  const fileNames = useMemo(() => Object.fromEntries((files.data ?? []).map((f) => [f.id, f.filename])), [files.data]);
  const regenIds = useMemo(() => new Set(Object.keys(regenerating)), [regenerating]);

  // Warn before leaving with unsaved edits (in-app navigation).
  const blocker = useBlocker(({ currentLocation, nextLocation }) => dirty && currentLocation.pathname !== nextLocation.pathname);

  const submit = async (exam: Exam, { save }: { save: boolean }) => {
    try {
      await update.mutateAsync(exam);
      if (save) await saveTest.mutateAsync(testId);
      toast(save ? t('workspace.test.savedToLibrary') : t('workspace.test.changesSaved'));
    } catch (e) {
      toast(errorText(e), 'error');
      throw e;
    }
  };

  const startRegenerate = (questionId: string) => {
    regen.mutate(questionId, {
      onSuccess: ({ job_id }) => setRegenerating((m) => ({ ...m, [questionId]: job_id })),
      onError: (e) => toast(errorText(e), 'error'),
    });
  };

  const onRegenDone = useCallback(
    async (questionId: string, job: Job) => {
      setRegenerating(({ [questionId]: _done, ...rest }) => rest);
      if (job.status !== 'succeeded') {
        toast(job.error_code ? t(`errors.${job.error_code}`) : t('jobs.status.failed'), 'error');
        return;
      }
      const fresh = unwrap(await api().GET('/topics/{topicId}/tests/{testId}', { params: { path: { topicId: topic.id, testId } } }));
      const q = fresh.exam.questions.find((x) => x.id === questionId);
      if (q) editor.current?.replaceQuestion(q);
      qc.setQueryData(qk.test(topic.id, testId), fresh);
      toast(t('workspace.test.regenerated'));
    },
    [qc, t, testId, toast, topic.id],
  );

  if (test.isPending) return <PageLoader />;
  if (test.isError)
    return (
      <div className="space-y-4">
        <ErrorNotice error={test.error} />
        <Link to={`/topics/${topic.id}/tests`} className="text-sm font-semibold text-accent hover:underline">
          {t('workspace.test.back')}
        </Link>
      </div>
    );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to={`/topics/${topic.id}/tests`} className="inline-flex items-center gap-1 text-sm font-medium text-muted hover:text-accent">
          <ArrowLeft size={16} aria-hidden="true" /> {t('workspace.test.back')}
        </Link>
        {test.data.saved && (
          <span className="inline-flex items-center gap-1 rounded-full border border-success/50 bg-success/10 px-3 py-1 text-xs font-semibold text-success">
            <Star size={12} aria-hidden="true" /> {t('workspace.tests.savedBadge')}
          </span>
        )}
      </div>

      <p className="flex items-start gap-2 rounded-2xl border border-border/40 bg-surface/30 p-3 text-xs text-muted">
        <ShieldAlert size={16} className="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
        {t('workspace.test.aiActNotice')}
      </p>

      {Object.entries(regenerating).map(([qid, jobId]) => (
        <RegenWatcher key={jobId} jobId={jobId} onDone={(job) => void onRegenDone(qid, job)} />
      ))}

      <TestEditor
        ref={editor}
        key={test.data.id}
        initial={test.data.exam}
        onSubmit={submit}
        submitLabel={t('workspace.test.saveChanges')}
        disabled={update.isPending || saveTest.isPending}
        canSave={!test.data.saved}
        onRegenerate={startRegenerate}
        regeneratingIds={regenIds}
        fileNames={fileNames}
        onDirtyChange={setDirty}
        actions={
          <Button size="sm" variant="outline" onClick={() => setExportOpen(true)} disabled={dirty} title={dirty ? t('workspace.test.saveBeforeExport') : undefined}>
            <Download size={14} aria-hidden="true" /> {t('export.button')}
          </Button>
        }
      />
      {dirty && <p className="text-right text-xs text-muted">{t('workspace.test.saveBeforeExport')}</p>}

      <ExportDialog open={exportOpen} onClose={() => setExportOpen(false)} topicId={topic.id} test={test.data} />
      <ConfirmDialog
        open={blocker.state === 'blocked'}
        onClose={() => blocker.reset?.()}
        onConfirm={() => blocker.proceed?.()}
        title={t('workspace.test.leaveTitle')}
        confirmLabel={t('workspace.test.leaveConfirm')}
        danger
        body={<p>{t('workspace.test.leaveBody')}</p>}
      />
    </div>
  );
}

function RegenWatcher({ jobId, onDone }: { jobId: string; onDone: (job: Job) => void }) {
  const job = useJob(jobId, 1500);
  const fired = useRef(false);
  const j = job.data;
  if (j && !fired.current && (j.status === 'succeeded' || j.status === 'failed' || j.status === 'cancelled')) {
    fired.current = true;
    queueMicrotask(() => onDone(j));
  }
  return null;
}
