import { useDeferredValue, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, FileText, FolderPlus, Hourglass, Library, Plus, Search, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '../../components/ui/Button';
import EmptyState from '../../components/common/EmptyState';
import ErrorNotice from '../../components/common/ErrorNotice';
import Spinner from '../../components/common/Spinner';
import NewTopicModal from '../../components/topics/NewTopicModal';
import { useTopics } from '../../api/hooks/topics';
import { useMe } from '../../api/hooks/me';
import { DEFAULT_LIMITS, type Topic } from '../../api/types';
import useDocumentTitle from '../../hooks/useDocumentTitle';
import { daysUntil, formatRelative } from '../../utils/format';
import { cn } from '../../utils/cn';

type Sort = 'activity' | 'name' | 'created';
const EXPIRY_WARN_DAYS = 14;

/** Topic Explorer / dashboard (TOP-10). */
export default function TopicExplorer() {
  const { t, i18n } = useTranslation();
  useDocumentTitle('meta.topics');
  const [query, setQuery] = useState('');
  const q = useDeferredValue(query.trim());
  const [sort, setSort] = useState<Sort>('activity');
  const [open, setOpen] = useState(false);
  const topics = useTopics(q);
  const me = useMe();
  const limits = me.data?.limits ?? DEFAULT_LIMITS;
  const total = topics.data?.total ?? 0;
  const atQuota = (me.data?.usage.topics ?? total) >= limits.max_topics;
  const lang = i18n.resolvedLanguage ?? 'hu';

  const items = useMemo(() => {
    const list = [...(topics.data?.items ?? [])];
    if (sort === 'name') list.sort((a, b) => a.name.localeCompare(b.name, lang));
    if (sort === 'created') list.sort((a, b) => b.created_at.localeCompare(a.created_at));
    return list;
  }, [topics.data, sort, lang]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="mb-1 text-3xl font-extrabold tracking-tight md:text-4xl">{t('topics.title')}</h1>
          <p className="text-sm text-muted">{t('topics.subtitle')}</p>
        </div>
        <div className="flex flex-col items-start gap-1 md:items-end">
          <Button onClick={() => setOpen(true)} disabled={atQuota}>
            <Plus size={18} aria-hidden="true" /> {t('topics.new.button')}
          </Button>
          <span className="text-xs text-muted">
            {atQuota ? t('topics.quotaReached', { max: limits.max_topics }) : t('topics.quota', { count: me.data?.usage.topics ?? total, max: limits.max_topics })}
          </span>
        </div>
      </div>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <label htmlFor="topic-search" className="sr-only">
            {t('topics.search')}
          </label>
          <Search size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
          <input
            id="topic-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('topics.search')}
            className="field py-2.5 pl-11"
          />
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="topic-sort" className="text-sm text-muted">
            {t('topics.sort.label')}
          </label>
          <select
            id="topic-sort"
            value={sort}
            onChange={(e) => setSort(e.target.value as Sort)}
            className="rounded-full border border-border/60 bg-surface/60 px-4 py-2 text-sm text-textMain focus:outline-none focus:ring-2 focus:ring-accent/60"
          >
            <option value="activity">{t('topics.sort.activity')}</option>
            <option value="name">{t('topics.sort.name')}</option>
            <option value="created">{t('topics.sort.created')}</option>
          </select>
        </div>
      </div>

      {topics.isPending ? (
        <Spinner className="py-24" />
      ) : topics.isError ? (
        <ErrorNotice error={topics.error} onRetry={() => void topics.refetch()} />
      ) : items.length === 0 ? (
        q ? (
          <EmptyState icon={Search} title={t('topics.noMatch', { q })} />
        ) : (
          <EmptyState
            icon={Library}
            title={t('topics.emptyTitle')}
            description={t('topics.emptyDesc')}
            action={
              <Button size="sm" onClick={() => setOpen(true)}>
                <FolderPlus size={16} aria-hidden="true" /> {t('topics.new.button')}
              </Button>
            }
          />
        )
      ) : (
        <>
          <p className="sr-only" role="status">
            {t('topics.resultCount', { count: items.length })}
          </p>
          <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((topic, i) => (
              <motion.li key={topic.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i, 10) * 0.03 }}>
                <TopicCard topic={topic} lang={lang} />
              </motion.li>
            ))}
          </ul>
        </>
      )}

      <NewTopicModal open={open} onClose={() => setOpen(false)} limits={limits} />
    </div>
  );
}

function TopicCard({ topic, lang }: { topic: Topic; lang: string }) {
  const { t } = useTranslation();
  const days = daysUntil(topic.expires_at);
  const deleting = topic.status === 'deleting';
  return (
    <Link
      to={`/topics/${topic.id}`}
      aria-disabled={deleting || undefined}
      onClick={(e) => deleting && e.preventDefault()}
      className={cn(
        'card group flex h-full flex-col p-5 transition-colors hover:border-accent/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
        deleting && 'pointer-events-none opacity-60',
      )}
    >
      <div className="mb-2 flex items-start justify-between gap-3">
        <h2 className="line-clamp-2 text-lg font-bold leading-snug text-textMain group-hover:text-accent">{topic.name}</h2>
        {deleting && <span className="shrink-0 rounded-full bg-danger/10 px-2 py-0.5 text-[11px] font-semibold text-danger">{t('topics.deleting')}</span>}
      </div>
      <p className="mb-4 line-clamp-2 min-h-[2.5rem] text-sm text-muted">{topic.description || t('topics.noDescription')}</p>
      <dl className="mt-auto grid grid-cols-2 gap-2 text-xs text-muted">
        <div className="flex items-center gap-1.5">
          <FileText size={14} aria-hidden="true" />
          <dt className="sr-only">{t('topics.stats.files')}</dt>
          <dd>{t('topics.stats.filesCount', { count: topic.file_count })}</dd>
        </div>
        <div className="flex items-center gap-1.5">
          <Star size={14} aria-hidden="true" />
          <dt className="sr-only">{t('topics.stats.saved')}</dt>
          <dd>{t('topics.stats.savedCount', { count: topic.saved_test_count })}</dd>
        </div>
        <div className="col-span-2 flex items-center gap-1.5">
          <Clock size={14} aria-hidden="true" />
          <dt className="sr-only">{t('topics.stats.lastActivity')}</dt>
          <dd>{t('topics.stats.active', { when: formatRelative(topic.last_activity_at, lang) })}</dd>
        </div>
        {days <= EXPIRY_WARN_DAYS && (
          <div className="col-span-2 flex items-center gap-1.5 font-medium text-warning">
            <Hourglass size={14} aria-hidden="true" />
            <dt className="sr-only">{t('topics.stats.expires')}</dt>
            <dd>{t('topics.expiresSoon', { count: Math.max(days, 0) })}</dd>
          </div>
        )}
      </dl>
    </Link>
  );
}
