import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronsUpDown, LayoutGrid, Plus, Search } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Dialog from '../common/Dialog';
import Spinner from '../common/Spinner';
import HelpTip from '../ui/HelpTip';
import ClassAvatar from '../topics/ClassAvatar';
import NewTopicModal from '../topics/NewTopicModal';
import { useTopics } from '../../api/hooks/topics';
import { useMe } from '../../api/hooks/me';
import { DEFAULT_LIMITS, type Topic } from '../../api/types';
import { cn } from '../../utils/cn';

export type WorkspaceTab = 'chat' | 'files' | 'tests';

/** The tab the user is on, so switching class keeps it (an open test or conversation falls back to its list/chat). */
export function useCurrentTab(): WorkspaceTab {
  const { pathname } = useLocation();
  const seg = pathname.split('/')[3];
  return seg === 'files' || seg === 'tests' ? seg : 'chat';
}

const SEARCH_FROM = 6;

/** Class list shared by the desktop sidebar and the phone sheet. */
function ClassList({ currentId, onNavigate, onNew }: { currentId: string; onNavigate?: () => void; onNew: () => void }) {
  const { t } = useTranslation();
  const tab = useCurrentTab();
  const topics = useTopics();
  const [query, setQuery] = useState('');
  const me = useMe();
  const limits = me.data?.limits ?? DEFAULT_LIMITS;
  const all = useMemo(() => (topics.data?.items ?? []).filter((x) => x.status !== 'deleting'), [topics.data]);
  const atQuota = (me.data?.usage.topics ?? all.length) >= limits.max_topics;
  const q = query.trim().toLocaleLowerCase();
  const list = q ? all.filter((x) => x.name.toLocaleLowerCase().includes(q)) : all;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-2">
      {all.length >= SEARCH_FROM && (
        <div className="relative">
          <label htmlFor={`class-search-${onNavigate ? 'sheet' : 'side'}`} className="sr-only">
            {t('workspace.switcher.search')}
          </label>
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
          <input
            id={`class-search-${onNavigate ? 'sheet' : 'side'}`}
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('workspace.switcher.search')}
            className="field rounded-full py-2 pl-9 text-sm"
          />
        </div>
      )}
      {topics.isPending ? (
        <Spinner className="py-6" />
      ) : (
        <ul className="-mx-1 flex min-h-0 flex-col gap-1 overflow-y-auto px-1 py-1">
          {list.map((x) => (
            <ClassRow key={x.id} topic={x} active={x.id === currentId} to={`/topics/${x.id}/${tab}`} onNavigate={onNavigate} />
          ))}
          {!list.length && <li className="px-3 py-4 text-center text-xs text-muted">{t('workspace.switcher.noMatch')}</li>}
        </ul>
      )}
      <div className="mt-auto flex flex-col gap-1 border-t border-border/30 pt-2">
        <button
          type="button"
          onClick={onNew}
          disabled={atQuota}
          className="flex min-h-[2.75rem] items-center gap-2 rounded-xl px-3 text-sm font-semibold text-accent transition-colors hover:bg-surface/60 disabled:opacity-50"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg border-2 border-dashed border-accent/60">
            <Plus size={16} aria-hidden="true" />
          </span>
          {t('workspace.switcher.new')}
        </button>
        <Link
          to="/topics"
          onClick={onNavigate}
          className="flex min-h-[2.75rem] items-center gap-2 rounded-xl px-3 text-sm font-medium text-muted transition-colors hover:bg-surface/60 hover:text-textMain"
        >
          <span className="flex h-8 w-8 items-center justify-center">
            <LayoutGrid size={16} aria-hidden="true" />
          </span>
          {t('workspace.switcher.all')}
        </Link>
      </div>
    </div>
  );
}

function ClassRow({ topic, active, to, onNavigate }: { topic: Topic; active: boolean; to: string; onNavigate?: () => void }) {
  const { t } = useTranslation();
  return (
    <li className="relative">
      {active && (
        <motion.span
          layoutId={onNavigate ? 'class-active-sheet' : 'class-active'}
          className="absolute inset-0 rounded-xl bg-surface ring-1 ring-accent/50"
          transition={{ type: 'spring', stiffness: 500, damping: 40 }}
          aria-hidden="true"
        />
      )}
      <Link
        to={to}
        onClick={onNavigate}
        aria-current={active ? 'page' : undefined}
        className={cn(
          'relative flex items-center gap-3 rounded-xl px-2 py-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
          active ? 'text-textMain' : 'text-textMain/90 hover:bg-surface/50',
        )}
      >
        <ClassAvatar name={topic.name} size="sm" />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold">{topic.name}</span>
          <span className="block truncate text-[11px] text-muted">
            {t('workspace.switcher.counts', { files: topic.file_count, saved: topic.saved_test_count })}
          </span>
        </span>
      </Link>
    </li>
  );
}

/** Desktop: the class list as a sticky sidebar next to the workspace. */
export function ClassSidebar({ currentId }: { currentId: string }) {
  const { t } = useTranslation();
  const me = useMe();
  const [creating, setCreating] = useState(false);
  return (
    <aside aria-label={t('workspace.switcher.title')} className="hidden w-64 shrink-0 lg:block">
      <div className="card sticky top-20 flex max-h-[calc(100vh-6rem)] flex-col p-3">
        <div className="mb-2 flex items-center gap-1 px-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-muted">{t('workspace.switcher.title')}</h2>
          <HelpTip label={t('workspace.switcher.title')} size={13}>
            {t('help.switcher')}
          </HelpTip>
        </div>
        <ClassList currentId={currentId} onNew={() => setCreating(true)} />
      </div>
      <NewTopicModal open={creating} onClose={() => setCreating(false)} limits={me.data?.limits} />
    </aside>
  );
}

/** Phones and tablets: a "current class ▾" button that opens the class list in a bottom sheet. */
export function MobileClassSwitcher({ current }: { current: Topic }) {
  const { t } = useTranslation();
  const me = useMe();
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  return (
    <div className="mb-4 flex items-center gap-1 lg:hidden">
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        className="flex min-h-[3rem] min-w-0 flex-1 items-center gap-3 rounded-2xl border border-border/50 bg-surface/40 px-3 py-2 text-left transition-colors hover:border-accent/60 active:scale-[0.99]"
      >
        <ClassAvatar name={current.name} size="sm" />
        <span className="min-w-0 flex-1">
          <span className="block text-[11px] font-semibold uppercase tracking-wider text-muted">{t('workspace.switcher.label')}</span>
          <span className="block truncate text-sm font-bold text-textMain">{current.name}</span>
        </span>
        <ChevronsUpDown size={18} className="shrink-0 text-muted" aria-hidden="true" />
      </button>
      <HelpTip label={t('workspace.switcher.label')}>{t('help.switcher')}</HelpTip>
      <Dialog open={open} onClose={() => setOpen(false)} title={t('workspace.switcher.title')} size="sm">
        <div className="flex max-h-[60vh] flex-col">
          <ClassList
            currentId={current.id}
            onNavigate={() => setOpen(false)}
            onNew={() => {
              setOpen(false);
              setCreating(true);
            }}
          />
        </div>
      </Dialog>
      <NewTopicModal open={creating} onClose={() => setCreating(false)} limits={me.data?.limits} />
    </div>
  );
}
