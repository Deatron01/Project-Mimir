import { Link, NavLink, Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { ChevronRight, FileText, FolderX, MessageSquare, ListChecks } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TopicStreamProvider } from '../../api/TopicStream';
import { useTopic } from '../../api/hooks/topics';
import { ApiError } from '../../api/errors';
import EmptyState from '../../components/common/EmptyState';
import ErrorNotice from '../../components/common/ErrorNotice';
import { PageLoader } from '../../components/common/Spinner';
import ButtonLink from '../../components/ui/ButtonLink';
import { useToast } from '../../components/common/Toaster';
import TopicHeader from '../../components/workspace/TopicHeader';
import ChatPane from '../../components/workspace/ChatPane';
import FilesPane from '../../components/workspace/FilesPane';
import TestsPane from '../../components/workspace/TestsPane';
import TestDetail from '../../components/workspace/TestDetail';
import { cn } from '../../utils/cn';

/** Topic workspace (TOP-12): header + Chat / Files / Tests, all scoped to one topic. */
export default function TopicWorkspace() {
  const { topicId = '' } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const toast = useToast();
  const topic = useTopic(topicId);

  if (topic.isPending) return <PageLoader />;
  if (topic.isError) {
    const notFound = topic.error instanceof ApiError && topic.error.code === 'TOPIC_NOT_FOUND';
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        {notFound ? (
          <EmptyState
            icon={FolderX}
            title={t('workspace.notFoundTitle')}
            description={t('workspace.notFoundDesc')}
            action={
              <ButtonLink to="/topics" size="sm">{t('workspace.backToTopics')}</ButtonLink>
            }
          />
        ) : (
          <ErrorNotice error={topic.error} onRetry={() => void topic.refetch()} />
        )}
      </div>
    );
  }

  const tabs = [
    { to: 'chat', label: t('workspace.tabs.chat'), icon: MessageSquare },
    { to: 'files', label: t('workspace.tabs.files'), icon: FileText, badge: topic.data.file_count },
    { to: 'tests', label: t('workspace.tabs.tests'), icon: ListChecks, badge: topic.data.saved_test_count || undefined },
  ];

  return (
    <TopicStreamProvider
      topicId={topicId}
      onTopicDeleted={() => {
        toast(t('workspace.deletedElsewhere'), 'info');
        navigate('/topics', { replace: true });
      }}
    >
      <div className="mx-auto flex max-w-7xl flex-col px-4 pb-10 pt-6 md:px-6">
        <nav aria-label={t('workspace.breadcrumb')} className="mb-3 flex items-center gap-1 text-sm text-muted">
          <Link to="/topics" className="hover:text-accent">
            {t('topics.title')}
          </Link>
          <ChevronRight size={14} aria-hidden="true" />
          <span aria-current="page" className="truncate text-textMain">
            {topic.data.name}
          </span>
        </nav>

        <TopicHeader topic={topic.data} />

        <nav aria-label={t('workspace.sections')} className="mb-6 mt-6 flex gap-1 overflow-x-auto border-b border-border/40">
          {tabs.map(({ to, label, icon: Icon, badge }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  '-mb-px flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors',
                  isActive ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-textMain',
                )
              }
            >
              <Icon size={16} aria-hidden="true" />
              {label}
              {badge !== undefined && (
                <span className="rounded-full bg-surface px-1.5 py-0.5 text-[11px] font-semibold text-textMain">{badge}</span>
              )}
            </NavLink>
          ))}
        </nav>

        <Routes>
          <Route index element={<Navigate to="chat" replace />} />
          <Route path="chat" element={<ChatPane topic={topic.data} />} />
          <Route path="chat/:sessionId" element={<ChatPane topic={topic.data} />} />
          <Route path="files" element={<FilesPane topic={topic.data} />} />
          <Route path="tests" element={<TestsPane topic={topic.data} />} />
          <Route path="tests/:testId" element={<TestDetail topic={topic.data} />} />
          <Route path="*" element={<Navigate to="chat" replace />} />
        </Routes>
      </div>
    </TopicStreamProvider>
  );
}
