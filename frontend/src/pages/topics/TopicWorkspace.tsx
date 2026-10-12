import { NavLink, Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { FileText, ListChecks, MessageSquare } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TopicStreamProvider } from '../../api/TopicStream';
import { useTopic } from '../../api/hooks/topics';
import { ApiError } from '../../api/errors';
import EmptyState from '../../components/common/EmptyState';
import ErrorNotice from '../../components/common/ErrorNotice';
import { PageLoader } from '../../components/common/Spinner';
import ButtonLink from '../../components/ui/ButtonLink';
import HelpTip from '../../components/ui/HelpTip';
import { useToast } from '../../components/common/Toaster';
import TopicHeader from '../../components/workspace/TopicHeader';
import ChatPane from '../../components/workspace/ChatPane';
import FilesPane from '../../components/workspace/FilesPane';
import TestsPane from '../../components/workspace/TestsPane';
import TestDetail from '../../components/workspace/TestDetail';
import { ClassSidebar, MobileClassSwitcher, useCurrentTab } from '../../components/workspace/ClassSwitcher';
import useDocumentTitle from '../../hooks/useDocumentTitle';
import { cn } from '../../utils/cn';

/** Class workspace (TOP-12): class switcher + header + Chat / Documents / Tests, all scoped to one class (topic). */
export default function TopicWorkspace() {
  const { topicId = '' } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const toast = useToast();
  const topic = useTopic(topicId);
  const tab = useCurrentTab();
  const location = useLocation();
  useDocumentTitle('meta.topics');

  if (topic.isPending) return <PageLoader />;
  if (topic.isError) {
    const notFound = topic.error instanceof ApiError && topic.error.code === 'TOPIC_NOT_FOUND';
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 md:px-6">
        {notFound ? (
          <EmptyState
            mascot="thinking"
            title={t('workspace.notFoundTitle')}
            description={t('workspace.notFoundDesc')}
            action={
              <ButtonLink to="/topics" size="sm">
                {t('workspace.backToTopics')}
              </ButtonLink>
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
  // Animate between tabs, but not between e.g. two conversations inside the chat tab.
  const paneKey = location.pathname.split('/')[4] && tab === 'tests' ? 'test-detail' : tab;

  return (
    <TopicStreamProvider
      topicId={topicId}
      onTopicDeleted={() => {
        toast(t('workspace.deletedElsewhere'), 'info');
        navigate('/topics', { replace: true });
      }}
    >
      <div className="mx-auto flex max-w-[90rem] gap-6 px-4 pb-10 pt-4 md:px-6 md:pt-6">
        <ClassSidebar currentId={topicId} />

        <div className="flex min-w-0 flex-1 flex-col">
          <MobileClassSwitcher current={topic.data} />
          <TopicHeader topic={topic.data} />

          {/* Tabs: inline under the header from md up, a fixed bottom bar on phones. */}
          <div className="mb-4 flex items-center gap-2 md:mb-5 md:mt-5 md:border-b md:border-border/40">
            <nav
              aria-label={t('workspace.sections')}
              className={cn(
                'fixed inset-x-0 bottom-0 z-40 flex border-t border-border/50 bg-background/95 px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-1.5 shadow-[0_-8px_24px_rgb(0_0_0/0.12)] backdrop-blur-md',
                'md:static md:z-auto md:gap-1 md:border-0 md:bg-transparent md:p-0 md:shadow-none md:backdrop-blur-none',
              )}
            >
              {tabs.map(({ to, label, icon: Icon, badge }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    cn(
                      'relative flex flex-1 flex-col items-center justify-center gap-0.5 rounded-xl px-3 py-1.5 text-[11px] font-semibold transition-colors md:-mb-px md:flex-none md:flex-row md:gap-2 md:rounded-none md:px-4 md:py-3 md:text-sm',
                      isActive ? 'text-accent' : 'text-muted hover:text-textMain',
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <motion.span
                          layoutId="workspace-tab"
                          className="absolute inset-0 rounded-xl bg-primary/15 md:inset-x-0 md:bottom-0 md:top-auto md:h-0.5 md:rounded-full md:bg-accent"
                          transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                          aria-hidden="true"
                        />
                      )}
                      <span className="relative">
                        <Icon size={20} className="md:h-4 md:w-4" aria-hidden="true" />
                        {badge !== undefined && (
                          <span className="absolute -right-3 -top-1.5 min-w-[1.1rem] rounded-full bg-primary px-1 text-center text-[10px] font-bold leading-4 text-onPrimary md:hidden">
                            {badge}
                          </span>
                        )}
                      </span>
                      <span className="relative">{label}</span>
                      {badge !== undefined && (
                        <span className="relative hidden rounded-full bg-surface px-1.5 py-0.5 text-[11px] font-semibold text-textMain md:inline">{badge}</span>
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </nav>
            <HelpTip label={t('workspace.sections')} className="ml-auto hidden md:inline-flex">
              {t('help.tabs')}
            </HelpTip>
          </div>

          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={paneKey}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.16, ease: 'easeOut' }}
            >
              {/* The exiting pane keeps its own location so it doesn't flash the next route while fading out. */}
              <Routes location={location}>
                <Route index element={<Navigate to="chat" replace />} />
                <Route path="chat" element={<ChatPane topic={topic.data} />} />
                <Route path="chat/:sessionId" element={<ChatPane topic={topic.data} />} />
                <Route path="files" element={<FilesPane topic={topic.data} />} />
                <Route path="tests" element={<TestsPane topic={topic.data} />} />
                <Route path="tests/:testId" element={<TestDetail topic={topic.data} />} />
                <Route path="*" element={<Navigate to="chat" replace />} />
              </Routes>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </TopicStreamProvider>
  );
}
