import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ListChecks, Star, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import SegmentedControl from '../ui/SegmentedControl';
import ConfirmDialog from '../common/ConfirmDialog';
import EmptyState from '../common/EmptyState';
import ErrorNotice, { useErrorText } from '../common/ErrorNotice';
import Spinner from '../common/Spinner';
import { useToast } from '../common/Toaster';
import { useDeleteTest, useTopicTests } from '../../api/hooks/tests';
import type { TestSummary, Topic } from '../../api/types';
import { formatDate } from '../../utils/format';

/** Tests generated in this topic (TOP-14). Unsaved tests are temporary; saving is opt-in. */
export default function TestsPane({ topic }: { topic: Topic }) {
  const { t, i18n } = useTranslation();
  const [filter, setFilter] = useState<'all' | 'saved'>('all');
  const tests = useTopicTests(topic.id, filter === 'saved' ? true : undefined);
  const del = useDeleteTest(topic.id);
  const toast = useToast();
  const errorText = useErrorText();
  const [toDelete, setToDelete] = useState<TestSummary | null>(null);

  const confirmDelete = async () => {
    if (!toDelete) return;
    try {
      await del.mutateAsync(toDelete.id);
      toast(t('tests.deleted'));
    } catch (e) {
      toast(errorText(e), 'error');
    }
    setToDelete(null);
  };

  return (
    <section aria-labelledby="tests-title">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="tests-title" className="text-lg font-bold">
            {t('workspace.tests.title')}
          </h2>
          <p className="text-xs text-muted">{t('workspace.tests.retention')}</p>
        </div>
        <SegmentedControl
          label={t('workspace.tests.filter')}
          value={filter}
          onChange={setFilter}
          options={[
            { value: 'all', label: t('workspace.tests.all') },
            { value: 'saved', label: t('workspace.tests.saved') },
          ]}
          className="w-56"
        />
      </div>
      {tests.isPending ? (
        <Spinner className="py-16" />
      ) : tests.isError ? (
        <ErrorNotice error={tests.error} onRetry={() => void tests.refetch()} />
      ) : !tests.data.length ? (
        <EmptyState
          icon={ListChecks}
          title={filter === 'saved' ? t('workspace.tests.emptySaved') : t('workspace.tests.empty')}
          description={t('workspace.tests.emptyDesc')}
          action={
            <Link to={`/topics/${topic.id}/chat`} className="text-sm font-semibold text-accent hover:underline">
              {t('workspace.tests.goToChat')}
            </Link>
          }
        />
      ) : (
        <ul className="grid gap-3 md:grid-cols-2">
          {tests.data.map((x) => (
            <li key={x.id} className="card flex items-start gap-3 p-4">
              <div className="min-w-0 flex-1">
                <Link to={`/topics/${topic.id}/tests/${x.id}`} className="block truncate font-semibold text-textMain hover:text-accent">
                  {x.title}
                </Link>
                <p className="mt-1 text-xs text-muted">
                  {t('workspace.tests.meta', { count: x.question_count, date: formatDate(x.created_at, i18n.resolvedLanguage) })}
                </p>
                {x.saved ? (
                  <span className="mt-2 inline-flex items-center gap-1 rounded-full border border-success/50 bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
                    <Star size={11} aria-hidden="true" /> {t('workspace.tests.savedBadge')}
                  </span>
                ) : (
                  <span className="mt-2 inline-block rounded-full border border-border/50 px-2 py-0.5 text-[11px] text-muted">{t('workspace.tests.tempBadge')}</span>
                )}
              </div>
              <button
                type="button"
                onClick={() => setToDelete(x)}
                aria-label={t('workspace.tests.deleteLabel', { title: x.title })}
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-muted hover:bg-danger/10 hover:text-danger"
              >
                <Trash2 size={16} aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      )}
      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={confirmDelete}
        busy={del.isPending}
        danger
        title={t('tests.deleteTitle')}
        confirmLabel={t('common.delete')}
        body={<p>{t('tests.deleteBody', { title: toDelete?.title ?? '' })}</p>}
      />
    </section>
  );
}
