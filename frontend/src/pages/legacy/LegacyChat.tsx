import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Send, Paperclip, Loader2, FileText, Download, Bot, User, X, ShieldCheck, Cloud, HardDrive } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';
import { useAuth } from '../../context/AuthContext';
import { legacyEndpoints as endpoints } from '../../config/legacyEndpoints';
import TestEditor, { type EditableExam } from '../../components/tests/TestEditor';
import type { Exam } from '../../api/types';
import useDocumentTitle from '../../hooks/useDocumentTitle';
import GenerationProgress, { type GenerationPhase, type ServerJobStatus } from '../../components/generation/GenerationProgress';
import ModelSelect, { AUTO_MODEL, loadModel, locationOf, storeModel, validModel, type ModelList } from '../../components/generation/ModelSelect';

const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 10 * 60 * 1000;
/** Used until the backend has timed a few jobs (or when it is too old to report estimates). */
const DEFAULT_GENERATION_S = 60;

/** Error that carries a translation key, so messages follow the UI language. */
class ChatError extends Error {
  key: string;
  constructor(key: string, detail?: string) {
    super(detail || key);
    this.key = key;
  }
}

const postJson = (url: string, body: unknown) =>
  fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

/** Legacy result metadata (model, date, AI disclosure); passed through to the PDF export. */
type ExamMetadata = Record<string, unknown> & { model_used?: string; processing_location?: 'external' | 'local'; is_fallback?: boolean };
type LegacyExam = EditableExam & { metadata?: ExamMetadata };

interface ChatMessage {
  id: number;
  role: 'user' | 'ai';
  key?: string;
  content?: string;
  attachedFile?: string | null;
  isError?: boolean;
  isInfo?: boolean;
  needsReview?: boolean;
  resultData?: LegacyExam;
  pdfUrl?: string;
}

/** Models offered by the backend (GET /models). Older backends without it: no selector, default behaviour. */
function useLegacyModels() {
  return useQuery({
    queryKey: ['legacy-models'],
    queryFn: async (): Promise<ModelList> => {
      const res = await fetch(endpoints.models());
      if (!res.ok) throw new Error(String(res.status));
      return (await res.json()) as ModelList;
    },
    retry: false,
    staleTime: 60_000,
  });
}

/** Pre-topic chat flow for the old backend (apiMode = 'legacy'). Replaced by the topic workspace in v1 mode. */
export default function LegacyChat() {
  const { t } = useTranslation();
  useDocumentTitle('meta.chat');
  const { user } = useAuth();
  // AI messages store translation keys (not text) so switching language re-renders them.
  const [messages, setMessages] = useState<ChatMessage[]>([{ id: 1, role: 'ai', key: 'chat.welcome' }]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [statusKey, setStatusKey] = useState('');
  // Generation progress (loader with steps and a time estimate).
  const [phase, setPhase] = useState<GenerationPhase | null>(null);
  const [serverJob, setServerJob] = useState<ServerJobStatus | null>(null);
  const [startedAt, setStartedAt] = useState(0);
  const [expectedGenS, setExpectedGenS] = useState(DEFAULT_GENERATION_S);
  const cancelRef = useRef(false);
  const models = useLegacyModels();
  const [model, setModel] = useState(loadModel);
  const chosenModel = validModel(models.data, model);
  const where = locationOf(models.data, chosenModel);
  // GDPR: explicit confirmation before a document is uploaded (reset for every new file).
  const [consent, setConsent] = useState(false);
  const [consentError, setConsentError] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = chatContainerRef.current;
    el?.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages, isLoading, statusKey, phase]);

  // Finished while the user was in another tab: say so in the tab title until they come back.
  const notifyIfHidden = () => {
    if (!document.hidden) return;
    const previous = document.title;
    document.title = t('progress.readyTitle');
    const back = () => {
      if (!document.hidden) {
        document.title = previous;
        document.removeEventListener('visibilitychange', back);
      }
    };
    document.addEventListener('visibilitychange', back);
  };

  const addMessage = (msg: Omit<ChatMessage, 'id'>) => setMessages((prev) => [...prev, { id: Date.now() + Math.random(), ...msg }]);

  const errorText = (err: unknown, prefixKey = 'common.errorPrefix') =>
    t(prefixKey, { message: err instanceof ChatError && err.key.includes('.') ? t(err.key) : err instanceof Error ? err.message : String(err) });

  const clearFile = () => {
    setFile(null);
    setConsent(false);
    setConsentError(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSend = async (e: React.FormEvent | React.KeyboardEvent) => {
    e.preventDefault();
    if (isLoading || (!input.trim() && !file)) return;
    if (file && !consent) {
      setConsentError(true);
      return;
    }

    const prompt = input;
    addMessage({ role: 'user', content: prompt, attachedFile: file?.name ?? null });
    setInput('');
    setIsLoading(true);
    cancelRef.current = false;
    setServerJob(null);
    setStartedAt(Date.now());
    setExpectedGenS(models.data?.estimates_s?.[where ?? 'external'] ?? DEFAULT_GENERATION_S);
    const stopIfCancelled = () => {
      if (cancelRef.current) throw new ChatError('chat.errors.cancelled');
    };

    try {
      if (!file) throw new ChatError('chat.errors.noFile');

      setPhase('extracting');
      const formData = new FormData();
      formData.append('file', file);
      const wellRes = await fetch(endpoints.extract(), { method: 'POST', body: formData });
      if (!wellRes.ok) throw new ChatError('chat.errors.extract');
      const wellData = await wellRes.json();
      stopIfCancelled();

      setPhase('chunking');
      const runeRes = await postJson(endpoints.chunk(), {
        filename: file.name,
        extension: file.name.split('.').pop(),
        content: wellData.content,
      });
      if (!runeRes.ok) throw new ChatError('chat.errors.chunk');
      const runeData = await runeRes.json();
      stopIfCancelled();

      setPhase('indexing');
      const ingestRes = await postJson(endpoints.ingest(), { chunks: runeData.chunks });
      if (!ingestRes.ok) throw new ChatError('chat.errors.ingest');
      stopIfCancelled();

      setPhase('generating');
      const genRes = await postJson(endpoints.generate(), {
        query: prompt,
        limit: 3,
        ...(models.data && chosenModel !== AUTO_MODEL ? { model: chosenModel } : {}),
      });
      if (!genRes.ok) throw new ChatError('chat.errors.start');
      const gen = (await genRes.json()) as { job_id: string; expected_total_s?: number };
      if (gen.expected_total_s) setExpectedGenS(gen.expected_total_s);

      // Poll the job until it completes, fails or times out; every answer refreshes the estimate.
      const started = Date.now();
      let result: LegacyExam | null = null;
      while (!result) {
        if (Date.now() - started > POLL_TIMEOUT_MS) throw new ChatError('chat.errors.generate');
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
        stopIfCancelled();
        const statusRes = await fetch(endpoints.status(gen.job_id));
        if (!statusRes.ok) continue;
        const statusData = await statusRes.json();
        setServerJob({ ...statusData, receivedAt: Date.now() });
        if (statusData.status === 'completed') result = statusData.data;
        else if (statusData.status === 'failed') throw new ChatError('chat.errors.generate', statusData.error);
      }

      // Human-in-the-loop review before export (EU AI Act art. 14).
      addMessage({ role: 'ai', key: 'chat.ready', needsReview: true, resultData: result });
      clearFile();
      notifyIfHidden();
    } catch (err) {
      if (err instanceof ChatError && err.key === 'chat.errors.cancelled') addMessage({ role: 'ai', key: err.key, isInfo: true });
      else addMessage({ role: 'ai', content: errorText(err), isError: true });
    } finally {
      setIsLoading(false);
      setStatusKey('');
      setPhase(null);
      setServerJob(null);
    }
  };

  const changeModel = (id: string) => {
    setModel(id);
    storeModel(id);
  };

  const handleApprove = async (messageId: number, editedData: Exam, { save = false }: { save?: boolean } = {}) => {
    setIsLoading(true);
    setStatusKey('chat.status.exporting');
    try {
      // Keep the generation metadata: the PDF prints it as the AI disclosure (AI Act art. 50).
      const metadata = messages.find((m) => m.id === messageId)?.resultData?.metadata;
      const skaldRes = await postJson(endpoints.exportPdf(), { ...editedData, metadata, user_id: user?.email, save });
      if (!skaldRes.ok) throw new ChatError('chat.errors.export');
      const pdfUrl = URL.createObjectURL(await skaldRes.blob());
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, needsReview: false, key: 'chat.approved', resultData: { ...editedData, metadata }, pdfUrl } : msg,
        ),
      );
    } catch (err) {
      addMessage({ role: 'ai', content: errorText(err, 'chat.errors.exportPrefix'), isError: true });
    } finally {
      setIsLoading(false);
      setStatusKey('');
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-80px)] max-w-4xl flex-col px-4 py-6 md:px-6">
      <h1 className="sr-only">{t('meta.chat')}</h1>

      <div
        ref={chatContainerRef}
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        className="mb-4 flex-1 space-y-6 overflow-y-auto pr-2"
      >
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn('flex gap-4', isUser ? 'ml-auto max-w-[85%] flex-row-reverse' : 'flex-col md:flex-row', msg.needsReview ? 'max-w-full' : 'max-w-[85%]')}
            >
              <div
                className={cn(
                  'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full shadow-sm',
                  isUser ? 'border border-border bg-surface text-textMain' : 'border border-primary/30 bg-primary/20 text-accent',
                )}
              >
                {isUser ? <User size={20} aria-hidden="true" /> : <Bot size={20} aria-hidden="true" />}
                <span className="sr-only">{isUser ? t('chat.you') : t('chat.assistant')}</span>
              </div>

              <div
                className={cn(
                  'w-full rounded-2xl p-4 shadow-md',
                  isUser
                    ? 'rounded-tr-none border border-border/50 bg-surface text-textMain'
                    : msg.isError
                      ? 'rounded-tl-none border border-danger/40 bg-danger/10 text-danger'
                      : 'rounded-tl-none border border-border/50 bg-surface/50 backdrop-blur-md',
                )}
              >
                {msg.attachedFile && (
                  <div className="mb-3 flex w-max max-w-full items-center gap-2 rounded-lg border border-border/50 bg-background/60 p-2 text-xs text-textMain/80">
                    <FileText size={14} className="shrink-0 text-accent" aria-hidden="true" /> <span className="truncate">{msg.attachedFile}</span>
                  </div>
                )}

                <p className="whitespace-pre-wrap text-sm leading-relaxed md:text-base">{msg.key ? t(msg.key) : msg.content}</p>

                {msg.resultData?.metadata?.model_used && !msg.resultData.metadata.is_fallback && (
                  <p className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-border/50 bg-background/50 px-2.5 py-1 text-xs text-muted">
                    {msg.resultData.metadata.processing_location === 'local' ? (
                      <HardDrive size={12} aria-hidden="true" />
                    ) : (
                      <Cloud size={12} aria-hidden="true" />
                    )}
                    {t('models.madeWith', { model: msg.resultData.metadata.model_used })}
                  </p>
                )}

                {msg.needsReview && (
                  <div className="mt-4">
                    <TestEditor
                      initial={msg.resultData ?? {}}
                      disabled={isLoading}
                      canSave={Boolean(user?.email)}
                      onSubmit={(data, opts) => handleApprove(msg.id, data, opts)}
                    />
                  </div>
                )}

                {msg.pdfUrl && (
                  <div className="mt-4 border-t border-border/30 pt-4">
                    <a
                      href={msg.pdfUrl}
                      download="mimir_vizsga.pdf"
                      className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-onPrimary shadow-lg shadow-accent/20 transition-colors hover:bg-primary/85"
                    >
                      <Download size={16} aria-hidden="true" /> {t('chat.downloadPdf')}
                    </a>
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}

        {isLoading && phase && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex w-full max-w-xl gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-primary/30 bg-primary/20 text-accent">
              <Bot size={20} aria-hidden="true" />
            </div>
            <div className="w-full rounded-2xl rounded-tl-none border border-border/50 bg-surface/50 p-4 shadow-md backdrop-blur-md">
              <GenerationProgress
                phase={phase}
                job={serverJob}
                startedAt={startedAt}
                expectedGenS={expectedGenS}
                onCancel={() => {
                  cancelRef.current = true;
                }}
              />
            </div>
          </motion.div>
        )}

        {isLoading && !phase && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex max-w-[85%] gap-4" role="status">
            <div className="flex h-10 w-10 items-center justify-center rounded-full border border-primary/30 bg-primary/20 text-accent">
              <Loader2 size={20} className="animate-spin" aria-hidden="true" />
            </div>
            <div className="flex items-center gap-3 rounded-2xl rounded-tl-none border border-border/50 bg-surface/50 p-4 shadow-md backdrop-blur-md">
              <span className="animate-pulse text-sm text-muted">{statusKey ? t(statusKey) : t('chat.thinking')}</span>
            </div>
          </motion.div>
        )}
      </div>

      <div className="mt-2 flex w-full shrink-0 flex-col items-center gap-3">
        {file && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="ml-2 inline-flex items-center gap-2 self-start rounded-xl border border-border/60 bg-surface/80 px-3 py-1.5 text-sm shadow-sm backdrop-blur-md"
          >
            <FileText size={14} className="text-accent" aria-hidden="true" />
            <span className="max-w-[200px] truncate font-medium text-textMain/90">{file.name}</span>
            <button type="button" onClick={clearFile} aria-label={t('chat.removeFile')} className="ml-1 text-muted transition-colors hover:text-danger">
              <X size={14} aria-hidden="true" />
            </button>
          </motion.div>
        )}

        {file && (
          <div
            className={cn(
              'w-full rounded-2xl border bg-surface/70 p-3 text-xs text-muted backdrop-blur-md',
              consentError ? 'border-danger/60' : 'border-border/50',
            )}
          >
            <label className="flex cursor-pointer items-start gap-2">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => {
                  setConsent(e.target.checked);
                  setConsentError(false);
                }}
                aria-describedby="consent-details"
                className="mt-0.5 h-4 w-4 shrink-0 accent-[rgb(var(--c-primary))]"
              />
              <span className="text-sm text-textMain">{t('chat.consent.label')}</span>
            </label>
            <p id="consent-details" className="mt-2 flex items-start gap-2 pl-6">
              <ShieldCheck size={14} className="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
              <span>
                {where === 'local'
                  ? t('chat.consent.detailsLocal')
                  : where === 'external'
                    ? t('chat.consent.detailsExternal')
                    : t('chat.consent.details')}{' '}
                <Link to="/privacy" className="font-medium text-accent underline-offset-2 hover:underline">
                  {t('chat.consent.more')}
                </Link>
              </span>
            </p>
            {consentError && (
              <p role="alert" className="mt-2 pl-6 font-medium text-danger">
                {t('chat.consent.required')}
              </p>
            )}
          </div>
        )}

        {models.data && (
          <div className="w-full px-2">
            <ModelSelect list={models.data} value={chosenModel} onChange={changeModel} disabled={isLoading} id="legacy-model" />
          </div>
        )}

        <form
          onSubmit={handleSend}
          className="flex w-full items-center gap-2 rounded-full border border-border/80 bg-background/40 py-1.5 pl-2 pr-2 shadow-sm backdrop-blur-md transition-colors focus-within:border-accent/60"
        >
          <label
            className="flex h-10 w-10 shrink-0 cursor-pointer items-center justify-center rounded-full text-muted transition-colors focus-within:ring-2 focus-within:ring-accent hover:bg-surface/50 hover:text-accent"
            title={t('chat.attach')}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="sr-only"
              accept=".pdf,.txt,.md"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setConsent(false);
                setConsentError(false);
              }}
              disabled={isLoading}
              aria-label={t('chat.attach')}
            />
            <Paperclip size={20} aria-hidden="true" />
          </label>

          <label htmlFor="chat-input" className="sr-only">
            {t('chat.placeholder')}
          </label>
          <textarea
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(e);
              }
            }}
            placeholder={t('chat.placeholder')}
            className="flex-1 resize-none border-none bg-transparent px-2 py-2.5 text-[15px] text-textMain outline-none placeholder:text-muted focus:ring-0"
            rows={1}
            style={{ minHeight: '44px', maxHeight: '120px' }}
            disabled={isLoading}
          />

          <button
            type="submit"
            disabled={isLoading || (!input.trim() && !file)}
            aria-label={t('chat.send')}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-onPrimary transition-all hover:bg-primary/85 disabled:opacity-40"
          >
            {isLoading ? <Loader2 size={18} className="animate-spin" aria-hidden="true" /> : <Send size={18} aria-hidden="true" />}
          </button>
        </form>

        <p className="text-center text-[11px] tracking-wide text-muted">{t('chat.disclaimer')}</p>
      </div>
    </div>
  );
}
