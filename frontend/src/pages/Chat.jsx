import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Send, Paperclip, Loader2, FileText, Download, Bot, User, X, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { cn } from '../utils/cn';
import { useAuth } from '../context/AuthContext';
import { endpoints } from '../config';
import QuestionEditor from '../components/editor/QuestionEditor';
import useDocumentTitle from '../hooks/useDocumentTitle';

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS = 10 * 60 * 1000;

/** Error that carries a translation key, so messages follow the UI language. */
class ChatError extends Error {
  constructor(key, detail) {
    super(detail || key);
    this.key = key;
  }
}

const postJson = (url, body) =>
  fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export default function Chat() {
  const { t } = useTranslation();
  useDocumentTitle('meta.chat');
  const { user } = useAuth();
  // AI messages store translation keys (not text) so switching language re-renders them.
  const [messages, setMessages] = useState([{ id: 1, role: 'ai', key: 'chat.welcome' }]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [statusKey, setStatusKey] = useState('');
  // GDPR: explicit confirmation before a document is uploaded (reset for every new file).
  const [consent, setConsent] = useState(false);
  const [consentError, setConsentError] = useState(false);
  const chatContainerRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    const el = chatContainerRef.current;
    el?.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages, isLoading, statusKey]);

  const addMessage = (msg) => setMessages((prev) => [...prev, { id: Date.now() + Math.random(), ...msg }]);

  const errorText = (err, prefixKey = 'common.errorPrefix') =>
    t(prefixKey, { message: err instanceof ChatError && err.key.includes('.') ? t(err.key) : err.message });

  const clearFile = () => {
    setFile(null);
    setConsent(false);
    setConsentError(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSend = async (e) => {
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

    try {
      if (!file) throw new ChatError('chat.errors.noFile');

      setStatusKey('chat.status.extracting');
      const formData = new FormData();
      formData.append('file', file);
      const wellRes = await fetch(endpoints.extract, { method: 'POST', body: formData });
      if (!wellRes.ok) throw new ChatError('chat.errors.extract');
      const wellData = await wellRes.json();

      setStatusKey('chat.status.chunking');
      const runeRes = await postJson(endpoints.chunk, {
        filename: file.name,
        extension: file.name.split('.').pop(),
        content: wellData.content,
      });
      if (!runeRes.ok) throw new ChatError('chat.errors.chunk');
      const runeData = await runeRes.json();

      setStatusKey('chat.status.indexing');
      const ingestRes = await postJson(endpoints.ingest, { chunks: runeData.chunks });
      if (!ingestRes.ok) throw new ChatError('chat.errors.ingest');

      setStatusKey('chat.status.generating');
      const genRes = await postJson(endpoints.generate, { query: prompt, limit: 3 });
      if (!genRes.ok) throw new ChatError('chat.errors.start');
      const { job_id: jobId } = await genRes.json();

      // Poll the job until it completes, fails or times out.
      const started = Date.now();
      let result = null;
      while (!result) {
        if (Date.now() - started > POLL_TIMEOUT_MS) throw new ChatError('chat.errors.generate');
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
        const statusRes = await fetch(endpoints.status(jobId));
        if (!statusRes.ok) continue;
        const statusData = await statusRes.json();
        if (statusData.status === 'completed') result = statusData.data;
        else if (statusData.status === 'failed') throw new ChatError('chat.errors.generate', statusData.error);
      }

      // Human-in-the-loop review before export (EU AI Act art. 14).
      addMessage({ role: 'ai', key: 'chat.ready', needsReview: true, resultData: result });
      clearFile();
    } catch (err) {
      addMessage({ role: 'ai', content: errorText(err), isError: true });
    } finally {
      setIsLoading(false);
      setStatusKey('');
    }
  };

  const handleApprove = async (messageId, editedData, { save = false } = {}) => {
    setIsLoading(true);
    setStatusKey('chat.status.exporting');
    try {
      const skaldRes = await postJson(endpoints.exportPdf, { ...editedData, user_id: user?.email, save });
      if (!skaldRes.ok) throw new ChatError('chat.errors.export');
      const pdfUrl = URL.createObjectURL(await skaldRes.blob());
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, needsReview: false, key: 'chat.approved', resultData: editedData, pdfUrl } : msg,
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

                {msg.needsReview && (
                  <QuestionEditor
                    initialData={msg.resultData}
                    disabled={isLoading}
                    canSave={Boolean(user?.email)}
                    onApprove={(data, opts) => handleApprove(msg.id, data, opts)}
                  />
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

        {isLoading && (
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
                {t('chat.consent.details')}{' '}
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
                setFile(e.target.files[0] ?? null);
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
            rows="1"
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
