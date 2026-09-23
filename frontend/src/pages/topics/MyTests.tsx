import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Download, FolderOpen, Inbox, Trash2 } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import ButtonLink from '../../components/ui/ButtonLink';
import Button from '../../components/ui/Button';
import ConfirmDialog from '../../components/common/ConfirmDialog';
import EmptyState from '../../components/common/EmptyState';
import ErrorNotice, { useErrorText } from '../../components/common/ErrorNotice';
import { PageLoader } from '../../components/common/Spinner';
import { useToast } from '../../components/common/Toaster';
import ExportDialog from '../../components/tests/ExportDialog';
import { useSavedTests } from '../../api/hooks/tests';
import { api } from '../../api/client';
import { unwrap } from '../../api/errors';
import { qk } from '../../api/keys';
import type { TestSummary } from '../../api/types';
import useDocumentTitle from '../../hooks/useDocumentTitle';
import { formatDate } from '../../utils/format';

/** "My tests": every saved test, grouped by topic (TOP-14). */
export default function MyTests() {
  const { t, i18n } = useTranslation();
  useDocumentTitle('meta.tests');
  const groups = useSavedTests();
  const qc = useQueryClient();
  const toast = useToast();
  const errorText = useErrorText();
  const [exporting, setExporting] = useState<TestSummary | null>(null);
  const [toDelete, setToDelete] = useState<TestSummary | null>(null);
  const [deleting, setDeleting] = useState(false);

  const confirmDelete = async () => {
    if (!toDelete) return;
    setDeleting(true);
    try {
      unwrap(await api().DELETE('/topics/{topicId}/tests/{testId}', { params: { path: { topicId: toDelete.topic_id, testId: toDelete.id } } }));
      toast(t('tests.deleted'));
      void qc.invalidateQueries({ queryKey: qk.savedTests });
      void qc.invalidateQueries({ queryKey: qk.topic(toDelete.topic_id) });
    } catch (e) {
      toast(errorText(e), 'error');
    }
    setDeleting(false);
    setToDelete(null);
  };

  if (groups.isPending) return <PageLoader />;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-10">
        <h1 className="mb-2 text-3xl font-extrabold tracking-tight">{t('tests.title')}</h1>
        <p className="text-sm text-muted">{t('tests.v1.subtitle')}</p>
        <p className="mt-1 text-xs text-muted">{t('tests.v1.retention')}</p>
      </div>

      {groups.isError ? (
        <ErrorNotice error={groups.error} onRetry={() => void groups.refetch()} />
      ) : !groups.data.length ? (
        <EmptyState
          icon={Inbox}
          title={t('tests.emptyTitle')}
          description={t('tests.v1.emptyDesc')}
          action={
            <ButtonLink to="/topics" size="sm">{t('tests.v1.goToTopics')}</ButtonLink>
          }
        />
      ) : (
        <div className="space-y-8">
          {groups.data.map((g) => (
            <section key={g.topic.id} aria-labelledby={`grp-${g.topic.id}`}>
              <h2 id={`grp-${g.topic.id}`} className="mb-3 flex items-center gap-2 text-lg font-bold">
                <FolderOpen size={18} className="text-accent" aria-hidden="true" />
                <Link to={`/topics/${g.topic.id}`} className="hover:text-accent">
                  {g.topic.name}
                </Link>
                <span className="text-sm font-normal text-muted">({g.tests.length})</span>
              </h2>
              <ul className="divide-y divide-border/30 overflow-hidden rounded-2xl border border-border/40 bg-surface/10">
                {g.tests.map((x) => (
                  <li key={x.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
                    <div className="min-w-0 flex-1">
                      <Link to={`/topics/${g.topic.id}/tests/${x.id}`} className="block truncate font-medium text-textMain hover:text-accent">
                        {x.title}
                      </Link>
                      <p className="text-xs text-muted">{t('workspace.tests.meta', { count: x.question_count, date: formatDate(x.updated_at, i18n.resolvedLanguage) })}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => setExporting(x)}>
                        <Download size={14} aria-hidden="true" /> {t('export.button')}
                      </Button>
                      <Button size="sm" variant="danger" onClick={() => setToDelete(x)} aria-label={t('workspace.tests.deleteLabel', { title: x.title })}>
                        <Trash2 size={14} aria-hidden="true" /> {t('common.delete')}
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}

      {exporting && <ExportDialog open onClose={() => setExporting(null)} topicId={exporting.topic_id} test={exporting} />}
      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={confirmDelete}
        busy={deleting}
        danger
        title={t('tests.deleteTitle')}
        confirmLabel={t('common.delete')}
        body={<p>{t('tests.deleteBody', { title: toDelete?.title ?? '' })}</p>}
      />
    </div>
  );
}
