import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { AlertTriangle, BookOpen, Bot, Check, FileWarning, MessageSquarePlus, Pencil, RotateCcw, Send, Settings2, Trash2, User, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Button from '../ui/Button';
import SegmentedControl from '../ui/SegmentedControl';
import ConfirmDialog from '../common/ConfirmDialog';
import ErrorNotice, { useErrorText } from '../common/ErrorNotice';
import Spinner from '../common/Spinner';
import { useToast } from '../common/Toaster';
import JobProgress from './JobProgress';
import GenerationOptionsForm, { loadOptions, storeOptions } from './GenerationOptionsForm';
import { useQueryClient } from '@tanstack/react-query';
import { postMessageTo, useCreateSession, useDeleteSession, useMessages, usePostMessage, useRenameSession, useSessions } from '../../api/hooks/sessions';
import { qk } from '../../api/keys';
import { useFiles } from '../../api/hooks/files';
import type { ChatSession, GenerationOptions, Message, Topic } from '../../api/types';
import { formatDate } from '../../utils/format';
import { cn } from '../../utils/cn';

type Intent = 'generate' | 'ask';

/** Chat pane (TOP-14 + FE-05): sessions scoped to the topic, generation options, live job progress. */
export default function ChatPane({ topic }: { topic: Topic }) {
  const { t } = useTranslation();
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const sessions = useSessions(topic.id);

  // Open the most recent session when none is selected.
  useEffect(() => {
    if (!sessionId && sessions.data?.length) navigate(`/topics/${topic.id}/chat/${sessions.data[0].id}`, { replace: true });
  }, [sessionId, sessions.data, navigate, topic.id]);

  return (
    <div className="grid gap-4 lg:h-[min(80vh,54rem)] lg:grid-cols-[16rem_minmax(0,1fr)]">
      <SessionList topicId={topic.id} sessions={sessions.data ?? []} loading={sessions.isPending} activeId={sessionId} />
      <section aria-label={t('chat.v1.conversation')} className="card flex h-[80vh] min-h-[28rem] flex-col overflow-hidden lg:h-auto">
        {sessions.isError ? (
          <ErrorNotice className="m-4" error={sessions.error} onRetry={() => void sessions.refetch()} />
        ) : (
          <Conversation key={sessionId ?? 'new'} topic={topic} sessionId={sessionId} />
        )}
      </section>
    </div>
  );
}

function SessionList({ topicId, sessions, loading, activeId }: { topicId: string; sessions: ChatSession[]; loading: boolean; activeId?: string }) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const toast = useToast();
  const errorText = useErrorText();
  const create = useCreateSession(topicId);
  const rename = useRenameSession(topicId);
  const del = useDeleteSession(topicId);
  const [editing, setEditing] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [toDelete, setToDelete] = useState<ChatSession | null>(null);

  const newChat = async () => {
    try {
      const s = await create.mutateAsync(undefined);
      navigate(`/topics/${topicId}/chat/${s.id}`);
    } catch (e) {
      toast(errorText(e), 'error');
    }
  };
  const saveTitle = async (id: string) => {
    if (title.trim()) {
      try {
        await rename.mutateAsync({ sessionId: id, title: title.trim() });
      } catch (e) {
        toast(errorText(e), 'error');
      }
    }
    setEditing(null);
  };
  const confirmDelete = async () => {
    if (!toDelete) return;
    try {
      await del.mutateAsync(toDelete.id);
      toast(t('chat.v1.sessionDeleted'));
      if (toDelete.id === activeId) navigate(`/topics/${topicId}/chat`, { replace: true });
    } catch (e) {
      toast(errorText(e), 'error');
    }
    setToDelete(null);
  };

  return (
    <aside aria-label={t('chat.v1.sessions')} className="card flex max-h-64 flex-col p-3 lg:max-h-none">
      <Button size="sm" variant="outline" className="mb-3 w-full" onClick={() => void newChat()} isLoading={create.isPending}>
        <MessageSquarePlus size={16} aria-hidden="true" /> {t('chat.v1.newChat')}
      </Button>
      {loading ? (
        <Spinner className="py-6" />
      ) : sessions.length === 0 ? (
        <p className="px-2 py-4 text-center text-xs text-muted">{t('chat.v1.noSessions')}</p>
      ) : (
        <ul className="-mx-1 flex flex-col gap-1 overflow-y-auto px-1">
          {sessions.map((s) => (
            <li key={s.id}>
              {editing === s.id ? (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void saveTitle(s.id);
                  }}
                  className="flex items-center gap-1"
                >
                  <label htmlFor={`rename-${s.id}`} className="sr-only">
                    {t('chat.v1.renameLabel')}
                  </label>
                  <input
                    id={`rename-${s.id}`}
                    value={title}
                    maxLength={120}
                    onChange={(e) => setTitle(e.target.value)}
                    onKeyDown={(e) => e.key === 'Escape' && setEditing(null)}
                    className="field min-w-0 flex-1 px-3 py-1.5 text-sm"
                    // eslint-disable-next-line jsx-a11y/no-autofocus -- opened by the rename button
                    autoFocus
                  />
                  <button type="submit" aria-label={t('common.save')} className="rounded-full p-1.5 text-success hover:bg-success/10">
                    <Check size={14} aria-hidden="true" />
                  </button>
                  <button type="button" onClick={() => setEditing(null)} aria-label={t('common.cancel')} className="rounded-full p-1.5 text-muted hover:bg-surface">
                    <X size={14} aria-hidden="true" />
                  </button>
                </form>
              ) : (
                <div
                  className={cn(
                    'group flex items-center gap-1 rounded-xl pr-1 transition-colors',
                    s.id === activeId ? 'bg-primary/15 text-textMain' : 'text-muted hover:bg-surface/60 hover:text-textMain',
                  )}
                >
                  <Link
                    to={`/topics/${topicId}/chat/${s.id}`}
                    aria-current={s.id === activeId ? 'page' : undefined}
                    className="min-w-0 flex-1 px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  >
                    <span className="block truncate text-sm font-medium">{s.title}</span>
                    <span className="block text-[11px] opacity-80">{formatDate(s.updated_at, i18n.resolvedLanguage)}</span>
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      setTitle(s.title);
                      setEditing(s.id);
                    }}
                    aria-label={t('chat.v1.rename', { title: s.title })}
                    className="rounded-full p-1.5 opacity-60 hover:bg-surface hover:opacity-100 focus-visible:opacity-100"
                  >
                    <Pencil size={13} aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setToDelete(s)}
                    aria-label={t('chat.v1.deleteSession', { title: s.title })}
                    className="rounded-full p-1.5 opacity-60 hover:bg-danger/10 hover:text-danger hover:opacity-100 focus-visible:opacity-100"
                  >
                    <Trash2 size={13} aria-hidden="true" />
                  </button>
                </div>
              )}
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
        title={t('chat.v1.deleteSessionTitle')}
        confirmLabel={t('common.delete')}
        body={<p>{t('chat.v1.deleteSessionBody')}</p>}
      />
    </aside>
  );
}

function Conversation({ topic, sessionId }: { topic: Topic; sessionId?: string }) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const uiLang = i18n.resolvedLanguage === 'en' ? 'en' : 'hu';
  const messages = useMessages(topic.id, sessionId);
  const files = useFiles(topic.id);
  const createSession = useCreateSession(topic.id);
  const post = usePostMessage(topic.id, sessionId ?? '');
  const [intent, setIntent] = useState<Intent>('generate');
  const [text, setText] = useState('');
  const [options, setOptions] = useState<GenerationOptions>(() => loadOptions(uiLang));
  const [showOptions, setShowOptions] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const readyFiles = useMemo(() => (files.data ?? []).filter((f) => f.status === 'ready'), [files.data]);
  const processing = (files.data ?? []).some((f) => f.status !== 'ready' && f.status !== 'failed');
  const fileNames = useMemo(() => Object.fromEntries((files.data ?? []).map((f) => [f.id, f.filename])), [files.data]);

  // Oldest first for display.
  const list = useMemo(() => (messages.data?.pages.flatMap((p) => p.items) ?? []).slice().reverse(), [messages.data]);
  const answered = useMemo(() => new Set(list.filter((m) => m.role === 'assistant' && m.job_id).map((m) => m.job_id)), [list]);
  const pending = list.filter((m) => m.role === 'user' && m.job_id && !answered.has(m.job_id));

  useEffect(() => {
    const el = logRef.current;
    el?.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [list.length, pending.length]);

  const canSend = readyFiles.length > 0 && !post.isPending && !createSession.isPending && (intent === 'generate' || text.trim().length > 0);

  const send = async (content: string, sendIntent: Intent, opts?: GenerationOptions) => {
    setError(null);
    let sid = sessionId;
    try {
      if (!sid) {
        const s = await createSession.mutateAsync(content.trim().slice(0, 60) || undefined);
        sid = s.id;
      }
      const body = { content, intent: sendIntent, options: sendIntent === 'generate' ? opts : undefined };
      if (sid === sessionId) await post.mutateAsync(body);
      else {
        // New session: post directly, then switch the URL (the new Conversation will load the messages).
        await postMessageTo(topic.id, sid, body);
        void qc.invalidateQueries({ queryKey: qk.activeJobs });
        navigate(`/topics/${topic.id}/chat/${sid}`);
      }
      if (sendIntent === 'generate' && opts) storeOptions(opts);
      setText('');
    } catch (e) {
      setError(e);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSend) return;
    void send(text, intent, intent === 'generate' ? options : undefined);
  };

  const retry = (assistant: Message) => {
    const original = list.find((m) => m.role === 'user' && m.job_id === assistant.job_id);
    if (original) void send(original.content, original.options ? 'generate' : 'ask', original.options);
  };

  return (
    <>
      <div ref={logRef} role="log" aria-live="polite" aria-relevant="additions" aria-label={t('chat.v1.messages')} className="flex-1 space-y-5 overflow-y-auto p-4 md:p-6">
        {messages.hasNextPage && (
          <div className="text-center">
            <Button size="sm" variant="ghost" onClick={() => void messages.fetchNextPage()} isLoading={messages.isFetchingNextPage}>
              {t('chat.v1.loadOlder')}
            </Button>
          </div>
        )}
        {sessionId && messages.isPending ? (
          <Spinner className="py-10" />
        ) : messages.isError ? (
          <ErrorNotice error={messages.error} onRetry={() => void messages.refetch()} />
        ) : list.length === 0 ? (
          <Welcome topic={topic} />
        ) : (
          list.map((m) => <MessageBubble key={m.id} message={m} topicId={topic.id} fileNames={fileNames} onRetry={() => retry(m)} />)
        )}
        {pending.map((m) => (
          <div key={`job-${m.id}`} className="flex gap-3">
            <Avatar who="assistant" />
            <div className="w-full max-w-lg rounded-2xl rounded-tl-none border border-border/50 bg-surface/50 p-4">
              <JobProgress jobId={m.job_id!} />
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-border/40 bg-background/40 p-3 md:p-4">
        {!files.isPending && readyFiles.length === 0 && (
          <div className="mb-3 flex items-start gap-2 rounded-xl border border-warning/50 bg-warning/10 p-3 text-sm text-textMain">
            <FileWarning size={16} className="mt-0.5 shrink-0 text-warning" aria-hidden="true" />
            <p>
              {processing ? t('chat.v1.filesProcessing') : t('chat.v1.noFiles')}{' '}
              <Link to={`/topics/${topic.id}/files`} className="font-semibold text-accent hover:underline">
                {t('chat.v1.goToFiles')}
              </Link>
            </p>
          </div>
        )}
        {error ? <ErrorNotice className="mb-3" error={error} /> : null}

        <form onSubmit={onSubmit} className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <SegmentedControl
              label={t('chat.v1.intent')}
              value={intent}
              onChange={setIntent}
              options={[
                { value: 'generate', label: t('chat.v1.intents.generate') },
                { value: 'ask', label: t('chat.v1.intents.ask') },
              ]}
              className="w-full max-w-xs"
            />
            {intent === 'generate' && (
              <button
                type="button"
                onClick={() => setShowOptions((v) => !v)}
                aria-expanded={showOptions}
                aria-controls="gen-options"
                className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium text-muted hover:bg-surface/60 hover:text-textMain"
              >
                <Settings2 size={14} aria-hidden="true" />
                {t('chat.v1.optionsSummary', {
                  count: options.count,
                  difficulty: t(`editor.difficulty.${options.difficulty}`).toLowerCase(),
                  lang: options.exam_language.toUpperCase(),
                })}
              </button>
            )}
          </div>

          {intent === 'generate' && showOptions && (
            <div id="gen-options">
              <GenerationOptionsForm value={options} onChange={setOptions} readyFiles={readyFiles} disabled={post.isPending} />
            </div>
          )}

          <div className="flex items-end gap-2 rounded-3xl border border-border/80 bg-background/60 p-1.5 pl-4 focus-within:border-accent/60">
            <label htmlFor="chat-input" className="sr-only">
              {intent === 'generate' ? t('chat.v1.placeholderGenerate') : t('chat.v1.placeholderAsk')}
            </label>
            <textarea
              id="chat-input"
              value={text}
              maxLength={4000}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (canSend) void send(text, intent, intent === 'generate' ? options : undefined);
                }
              }}
              placeholder={intent === 'generate' ? t('chat.v1.placeholderGenerate') : t('chat.v1.placeholderAsk')}
              rows={2}
              className="max-h-40 min-h-[44px] flex-1 resize-none border-none bg-transparent py-2 text-[15px] text-textMain outline-none placeholder:text-muted"
            />
            <button
              type="submit"
              disabled={!canSend}
              aria-label={intent === 'generate' ? t('chat.v1.sendGenerate') : t('chat.v1.sendAsk')}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary text-onPrimary transition-colors hover:bg-primary/85 disabled:opacity-40"
            >
              <Send size={18} aria-hidden="true" />
            </button>
          </div>
          <p className="text-center text-[11px] tracking-wide text-muted">{t('chat.disclaimer')}</p>
        </form>
      </div>
    </>
  );
}

function Welcome({ topic }: { topic: Topic }) {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-md py-10 text-center">
      <Bot size={40} className="mx-auto mb-3 text-accent" aria-hidden="true" />
      <h2 className="mb-1 text-lg font-semibold">{t('chat.v1.welcomeTitle', { name: topic.name })}</h2>
      <p className="text-sm text-muted">{t('chat.v1.welcomeBody')}</p>
    </div>
  );
}

function Avatar({ who }: { who: Message['role'] }) {
  const { t } = useTranslation();
  const user = who === 'user';
  return (
    <div
      className={cn(
        'flex h-9 w-9 shrink-0 items-center justify-center rounded-full',
        user ? 'border border-border bg-surface text-textMain' : 'border border-primary/30 bg-primary/20 text-accent',
      )}
    >
      {user ? <User size={18} aria-hidden="true" /> : <Bot size={18} aria-hidden="true" />}
      <span className="sr-only">{user ? t('chat.you') : t('chat.assistant')}</span>
    </div>
  );
}

function MessageBubble({ message: m, topicId, fileNames, onRetry }: { message: Message; topicId: string; fileNames: Record<string, string>; onRetry: () => void }) {
  const { t, i18n } = useTranslation();
  const user = m.role === 'user';
  const failed = Boolean(m.error_code);
  return (
    <article className={cn('flex gap-3', user && 'flex-row-reverse')} aria-label={user ? t('chat.you') : t('chat.assistant')}>
      <Avatar who={m.role} />
      <div
        className={cn(
          'max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed shadow-sm md:text-[15px]',
          user
            ? 'rounded-tr-none border border-border/50 bg-surface text-textMain'
            : failed
              ? 'rounded-tl-none border border-danger/40 bg-danger/10 text-textMain'
              : 'rounded-tl-none border border-border/50 bg-surface/50',
        )}
      >
        {failed ? (
          <div className="flex items-start gap-2">
            <AlertTriangle size={16} className="mt-0.5 shrink-0 text-danger" aria-hidden="true" />
            <div>
              <p>{t(`errors.${m.error_code}`, { defaultValue: t('errors.UNKNOWN') })}</p>
              <button type="button" onClick={onRetry} className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-accent hover:underline">
                <RotateCcw size={12} aria-hidden="true" /> {t('common.retry')}
              </button>
            </div>
          </div>
        ) : (
          m.content && <p className="whitespace-pre-wrap">{m.content}</p>
        )}
        {user && m.options && (
          <p className="mt-2 text-xs text-muted">
            {t('chat.v1.optionsSummary', {
              count: m.options.count,
              difficulty: t(`editor.difficulty.${m.options.difficulty}`).toLowerCase(),
              lang: m.options.exam_language.toUpperCase(),
            })}
          </p>
        )}
        {m.test_id && (
          <Link
            to={`/topics/${topicId}/tests/${m.test_id}`}
            className="mt-3 inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-onPrimary hover:bg-primary/85"
          >
            {t('chat.v1.reviewTest')}
          </Link>
        )}
        {m.citations && m.citations.length > 0 && (
          <details className="mt-3 text-xs text-muted">
            <summary className="flex cursor-pointer list-none items-center gap-1 font-medium text-textMain/90">
              <BookOpen size={12} aria-hidden="true" /> {t('editor.sources', { count: m.citations.length })}
            </summary>
            <ul className="mt-1 space-y-1">
              {m.citations.map((c) => (
                <li key={c.chunk_id}>
                  {fileNames[c.file_id] ?? c.filename}
                  {c.page ? ` · ${t('editor.page', { page: c.page })}` : ''}
                </li>
              ))}
            </ul>
          </details>
        )}
        <time dateTime={m.created_at} className="mt-2 block text-[11px] text-muted">
          {formatDate(m.created_at, i18n.resolvedLanguage, new Date(m.created_at).toDateString() === new Date().toDateString() ? { timeStyle: 'short' } : { dateStyle: 'medium', timeStyle: 'short' })}
        </time>
      </div>
    </article>
  );
}
