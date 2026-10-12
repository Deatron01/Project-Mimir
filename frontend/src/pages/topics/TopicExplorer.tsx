import { useDeferredValue, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Clock, FileText, Hourglass, Plus, Search, Star, UploadCloud } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '../../components/ui/Button';
import HelpTip from '../../components/ui/HelpTip';
import EmptyState from '../../components/common/EmptyState';
import ErrorNotice from '../../components/common/ErrorNotice';
import HowItWorks from '../../components/common/HowItWorks';
import Spinner from '../../components/common/Spinner';
import Mascot from '../../components/mascot/Mascot';
import ClassAvatar from '../../components/topics/ClassAvatar';
import NewTopicModal from '../../components/topics/NewTopicModal';
import { useTopics } from '../../api/hooks/topics';
import { useMe } from '../../api/hooks/me';
import { DEFAULT_LIMITS, type Topic } from '../../api/types';
import useDocumentTitle from '../../hooks/useDocumentTitle';
import { daysUntil, formatRelative } from '../../utils/format';
import { cn } from '../../utils/cn';

type Sort = 'activity' | 'name' | 'created';
const EXPIRY_WARN_DAYS = 14;

/** "My classes" dashboard (TOP-10): every class (topic) the user created, one per subject. */
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
  const hasAny = total > 0 || Boolean(q);

  const items = useMemo(() => {
    const list = [...(topics.data?.items ?? [])];
    if (sort === 'name') list.sort((a, b) => a.name.localeCompare(b.name, lang));
    if (sort === 'created') list.sort((a, b) => b.created_at.localeCompare(a.created_at));
    return list;
  }, [topics.data, sort, lang]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10">
      <div className="mb-8 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div className="flex items-end gap-4">
          <Mascot mood="wave" size={84} className="hidden sm:inline-flex" />
          <div>
            <p className="mb-1 text-sm font-semibold text-accent">{t('topics.greeting')}</p>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-extrabold tracking-tight md:text-4xl">{t('topics.title')}</h1>
              <HelpTip label={t('topics.title')} size={18}>
                {t('help.class')}
              </HelpTip>
            </div>
            <p className="mt-1 max-w-xl text-sm text-muted">{t('topics.subtitle')}</p>
          </div>
        </div>
        <div className="flex flex-col items-stretch gap-1 sm:items-end">
          <Button onClick={() => setOpen(true)} disabled={atQuota}>
            <Plus size={18} aria-hidden="true" /> {t('topics.new.button')}
          </Button>
          <span className="flex items-center justify-center gap-0.5 text-xs text-muted sm:justify-end">
            {atQuota ? t('topics.quotaReached', { max: limits.max_topics }) : t('topics.quota', { count: me.data?.usage.topics ?? total, max: limits.max_topics })}
            <HelpTip label={t('topics.quotaLabel')} size={13}>
              {t('help.quota')}
            </HelpTip>
          </span>
        </div>
      </div>

      {(!hasAny || total <= 1) && !topics.isPending && <HowItWorks compact headingLevel={2} className="mb-8" />}

      {hasAny && (
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
              className="min-h-[2.75rem] flex-1 rounded-full border border-border/60 bg-surface/60 px-4 py-2 text-sm text-textMain focus:outline-none focus:ring-2 focus:ring-accent/60 sm:flex-none"
            >
              <option value="activity">{t('topics.sort.activity')}</option>
              <option value="name">{t('topics.sort.name')}</option>
              <option value="created">{t('topics.sort.created')}</option>
            </select>
            <HelpTip label={t('topics.sort.label')}>{t('help.sort')}</HelpTip>
          </div>
        </div>
      )}

      {topics.isPending ? (
        <Spinner className="py-24" />
      ) : topics.isError ? (
        <ErrorNotice error={topics.error} onRetry={() => void topics.refetch()} />
      ) : items.length === 0 ? (
        q ? (
          <EmptyState icon={Search} title={t('topics.noMatch', { q })} />
        ) : (
          <EmptyState
            mascot="wave"
            title={t('topics.emptyTitle')}
            description={t('topics.emptyDesc')}
            action={
              <Button onClick={() => setOpen(true)} disabled={atQuota}>
                <Plus size={18} aria-hidden="true" /> {t('topics.new.button')}
              </Button>
            }
          />
        )
      ) : (
        <>
          <p className="sr-only" role="status">
            {t('topics.resultCount', { count: items.length })}
          </p>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((topic, i) => (
              <motion.li key={topic.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i, 10) * 0.04 }}>
                <ClassCard topic={topic} lang={lang} />
              </motion.li>
            ))}
            {!q && !atQuota && (
              <motion.li initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: Math.min(items.length, 10) * 0.04 }}>
                <button
                  type="button"
                  onClick={() => setOpen(true)}
                  className="group flex h-full min-h-[11rem] w-full flex-col items-center justify-center gap-2 rounded-3xl border-2 border-dashed border-border/50 p-5 text-muted transition-colors hover:border-accent/70 hover:bg-surface/20 hover:text-accent"
                >
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface/60 transition-transform group-hover:scale-110 group-hover:rotate-90">
                    <Plus size={22} aria-hidden="true" />
                  </span>
                  <span className="text-sm font-semibold">{t('topics.new.button')}</span>
                </button>
              </motion.li>
            )}
          </ul>
        </>
      )}

      <NewTopicModal open={open} onClose={() => setOpen(false)} limits={limits} />
    </div>
  );
}

function ClassCard({ topic, lang }: { topic: Topic; lang: string }) {
  const { t } = useTranslation();
  const days = daysUntil(topic.expires_at);
  const deleting = topic.status === 'deleting';
  const empty = topic.file_count === 0;
  return (
    <motion.div whileHover={deleting ? undefined : { y: -4 }} transition={{ type: 'spring', stiffness: 400, damping: 25 }} className="h-full">
      <Link
        to={`/topics/${topic.id}${empty ? '/files' : ''}`}
        aria-disabled={deleting || undefined}
        onClick={(e) => deleting && e.preventDefault()}
        className={cn(
          'card group flex h-full flex-col p-5 transition-colors hover:border-accent/60 hover:shadow-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
          deleting && 'pointer-events-none opacity-60',
        )}
      >
        <div className="mb-3 flex items-start gap-3">
          <ClassAvatar name={topic.name} />
          <div className="min-w-0 flex-1">
            <h2 className="line-clamp-2 text-lg font-bold leading-snug text-textMain group-hover:text-accent">{topic.name}</h2>
            <p className="line-clamp-1 text-sm text-muted">{topic.description || t('topics.noDescription')}</p>
          </div>
          {deleting ? (
            <span className="shrink-0 rounded-full bg-danger/10 px-2 py-0.5 text-[11px] font-semibold text-danger">{t('topics.deleting')}</span>
          ) : (
            <ArrowRight size={18} className="mt-1 shrink-0 text-muted transition-transform group-hover:translate-x-1 group-hover:text-accent" aria-hidden="true" />
          )}
        </div>
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
        {empty && !deleting && (
          <p className="mt-3 flex items-center gap-1.5 rounded-xl bg-surface/60 px-3 py-2 text-xs font-semibold text-textMain">
            <UploadCloud size={14} className="text-accent" aria-hidden="true" /> {t('topics.card.addDocs')}
          </p>
        )}
      </Link>
    </motion.div>
  );
}
