import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, HardDrive, Mail, Server, ShieldCheck, Trash2, UserX } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '../components/ui/Button';
import Dialog from '../components/common/Dialog';
import ErrorNotice, { useErrorText } from '../components/common/ErrorNotice';
import { useToast } from '../components/common/Toaster';
import { LEGACY_USER_KEY, useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { getConfig } from '../config/runtime';
import { legacyEndpoints } from '../config/legacyEndpoints';
import { useDeleteMe, useExportMe, useMe } from '../api/hooks/me';
import { downloadBlob } from '../api/hooks/tests';
import { api, apiUrl, authFetch } from '../api/client';
import { errorFromResponse, unwrap } from '../api/errors';
import { OPTIONS_KEY } from '../components/workspace/GenerationOptionsForm';
import { MOCK_DB_KEY_NAME } from '../mocks/constants';
import useDocumentTitle from '../hooks/useDocumentTitle';
import { formatDate } from '../utils/format';

// Every key Mimir writes to browser storage. Keep in sync with the privacy notice (compliance docs, section "Cookies & storage").
const STORAGE_KEYS = ['mimir-theme', 'mimir-lang', LEGACY_USER_KEY, OPTIONS_KEY, MOCK_DB_KEY_NAME];

const readStorage = () =>
  STORAGE_KEYS.map((key) => {
    let value: string | null = null;
    try {
      value = localStorage.getItem(key);
    } catch {
      /* storage unavailable */
    }
    return { key, value };
  }).filter((x): x is { key: string; value: string } => x.value !== null);

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** "Your data" page: what is stored, export, deletion (GDPR Art. 15, 17, 20). */
export default function YourData() {
  const { t, i18n } = useTranslation();
  useDocumentTitle('meta.data');
  const { user, logout, mode } = useAuth();
  const { setPaletteId, setMode } = useTheme();
  const navigate = useNavigate();
  const toast = useToast();
  const errorText = useErrorText();
  const privacyEmail = getConfig().privacyEmail;
  const v1 = mode === 'v1';
  const me = useMe();
  const exportMe = useExportMe();
  const deleteMe = useDeleteMe();
  const [stored, setStored] = useState(readStorage);
  const [confirmClear, setConfirmClear] = useState(false);
  const [notice, setNotice] = useState('');
  const [exporting, setExporting] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [password, setPassword] = useState('');

  const mailto = useMemo(() => {
    if (!privacyEmail) return '';
    const subject = encodeURIComponent(t('dataPage.mailSubject'));
    const body = encodeURIComponent(t('dataPage.mailBody', { email: user?.email ?? '' }));
    return `mailto:${privacyEmail}?subject=${subject}&body=${body}`;
  }, [t, user, privacyEmail]);

  /** v1: server-side export job (Art. 15/20) – waits for the job, then downloads the archive. */
  const exportServer = async () => {
    setExporting(true);
    try {
      const { job_id } = await exportMe.mutateAsync();
      let url: string | undefined;
      for (let i = 0; i < 120 && !url; i += 1) {
        await sleep(1500);
        const job = unwrap(await api().GET('/jobs/{jobId}', { params: { path: { jobId: job_id } } }));
        if (job.status === 'failed' || job.status === 'cancelled') throw new Error(job.error_code ?? 'failed');
        if (job.status === 'succeeded') url = job.result?.download_url;
      }
      if (!url) throw new Error('timeout');
      const res = await authFetch(new Request(/^https?:/.test(url) ? url : apiUrl(url), { credentials: 'include' }));
      if (!res.ok) throw await errorFromResponse(res);
      downloadBlob(await res.blob(), 'mimir-my-data.json');
      toast(t('dataPage.v1.exportReady'));
    } catch (e) {
      toast(errorText(e), 'error');
    } finally {
      setExporting(false);
    }
  };

  /** Legacy: browser storage + saved-test list from the old backend. */
  const exportLegacy = async () => {
    setExporting(true);
    const data: Record<string, unknown> = {
      exportedAt: new Date().toISOString(),
      browserStorage: Object.fromEntries(stored.map(({ key, value }) => [key, value])),
    };
    if (user?.email) {
      try {
        const res = await fetch(legacyEndpoints.tests(user.email));
        if (res.ok) data.savedTests = await res.json();
      } catch {
        /* export what we have */
      }
    }
    downloadBlob(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }), 'mimir-my-data.json');
    setExporting(false);
  };

  const handleClear = async () => {
    if (!confirmClear) {
      setConfirmClear(true);
      return;
    }
    await logout();
    STORAGE_KEYS.forEach((key) => {
      try {
        localStorage.removeItem(key);
      } catch {
        /* ignore */
      }
    });
    setPaletteId('original');
    setMode('system');
    // ThemeContext re-saves the theme on change; remove it again after that effect.
    setTimeout(() => {
      try {
        localStorage.removeItem('mimir-theme');
      } catch {
        /* ignore */
      }
      setStored(readStorage());
    }, 0);
    setConfirmClear(false);
    setNotice(t('dataPage.cleared'));
  };

  const handleDeleteAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await deleteMe.mutateAsync(password);
      setDeleteOpen(false);
      setPassword('');
      await logout();
      toast(t('dataPage.v1.deleteStarted'));
      navigate('/', { replace: true });
    } catch {
      /* shown in the dialog */
    }
  };

  const serverItems = t(v1 ? 'dataPage.v1.serverItems' : 'dataPage.serverItems', { returnObjects: true }) as unknown;

  return (
    <div className="relative min-h-[80vh] overflow-hidden py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative z-10 mx-auto max-w-4xl px-6">
        <div className="mb-10">
          <h1 className="mb-2 text-3xl font-extrabold tracking-tight md:text-4xl">{t('dataPage.title')}</h1>
          <p className="text-muted">{t('dataPage.subtitle')}</p>
        </div>

        <p role="status" aria-live="polite" className="mb-6 rounded-2xl border border-success/40 bg-success/10 p-4 text-sm text-success empty:hidden">
          {notice}
        </p>

        <div className="grid gap-6 md:grid-cols-2">
          <section className="card p-6" aria-labelledby="data-server">
            <h2 id="data-server" className="mb-4 flex items-center gap-2 text-lg font-bold">
              <Server size={18} className="text-accent" aria-hidden="true" /> {t('dataPage.serverTitle')}
            </h2>
            {v1 && me.data && (
              <dl className="mb-4 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 rounded-xl border border-border/40 bg-background/40 p-3 text-sm">
                <dt className="text-muted">{t('auth.email')}</dt>
                <dd className="break-all text-textMain">{me.data.email}</dd>
                <dt className="text-muted">{t('dataPage.v1.memberSince')}</dt>
                <dd className="text-textMain">{formatDate(me.data.created_at, i18n.resolvedLanguage, { dateStyle: 'medium' })}</dd>
                <dt className="text-muted">{t('dataPage.v1.topics')}</dt>
                <dd className="text-textMain">{me.data.usage.topics}</dd>
                <dt className="text-muted">{t('dataPage.v1.savedTests')}</dt>
                <dd className="text-textMain">{me.data.usage.saved_tests}</dd>
              </dl>
            )}
            <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
              {Array.isArray(serverItems) && (serverItems as string[]).map((item) => <li key={item}>{item}</li>)}
            </ul>
            {user && (
              <Link to={v1 ? '/topics' : '/tests'} className="mt-4 inline-block text-sm font-medium text-accent hover:underline">
                {v1 ? t('dataPage.v1.manageTopics') : t('dataPage.savedTests')}
              </Link>
            )}
          </section>

          <section className="card p-6" aria-labelledby="data-browser">
            <h2 id="data-browser" className="mb-2 flex items-center gap-2 text-lg font-bold">
              <HardDrive size={18} className="text-accent" aria-hidden="true" /> {t('dataPage.browserTitle')}
            </h2>
            <p className="mb-4 text-sm text-muted">{t('dataPage.browserDesc')}</p>
            {stored.length === 0 ? (
              <p className="text-sm text-muted">{t('dataPage.empty')}</p>
            ) : (
              <dl className="space-y-2 text-sm">
                {stored.map(({ key, value }) => (
                  <div key={key} className="rounded-lg border border-border/40 bg-background/40 p-2">
                    <dt className="font-medium text-textMain">
                      {t(`dataPage.keys.${key}`)} <code className="text-xs text-muted">{key}</code>
                    </dt>
                    <dd className="mt-1 line-clamp-3 break-all font-mono text-xs text-muted">{value}</dd>
                  </div>
                ))}
              </dl>
            )}
          </section>
        </div>

        <section className="card mt-6 p-6" aria-labelledby="data-actions">
          <h2 id="data-actions" className="mb-4 flex items-center gap-2 text-lg font-bold">
            <ShieldCheck size={18} className="text-accent" aria-hidden="true" /> {t('dataPage.rightsTitle')}
          </h2>
          <p className="mb-6 text-sm text-muted">{v1 ? t('dataPage.v1.rightsDesc') : t('dataPage.rightsDesc')}</p>

          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <Button variant="outline" size="sm" onClick={() => void (v1 && user ? exportServer() : exportLegacy())} isLoading={exporting}>
              {!exporting && <Download size={14} aria-hidden="true" />} {t('dataPage.export')}
            </Button>
            <Button variant="danger" size="sm" onClick={() => void handleClear()} onBlur={() => setConfirmClear(false)}>
              <Trash2 size={14} aria-hidden="true" /> {confirmClear ? t('dataPage.clearConfirm') : t('dataPage.clear')}
            </Button>
            {v1 && user ? (
              <Button variant="danger" size="sm" onClick={() => setDeleteOpen(true)}>
                <UserX size={14} aria-hidden="true" /> {t('dataPage.v1.deleteAccount')}
              </Button>
            ) : mailto ? (
              <a
                href={mailto}
                className="inline-flex h-9 items-center justify-center gap-2 rounded-full border border-border/70 px-4 text-sm font-medium text-textMain transition-colors hover:bg-surface/60"
              >
                <Mail size={14} aria-hidden="true" /> {t('dataPage.requestErasure')}
              </a>
            ) : (
              <Button variant="outline" size="sm" onClick={() => navigate('/contact')}>
                <Mail size={14} aria-hidden="true" /> {t('dataPage.requestErasure')}
              </Button>
            )}
          </div>
          <p className="mt-3 text-xs text-muted">{v1 && user ? t('dataPage.v1.exportHint') : t('dataPage.exportHint')}</p>
          {!v1 && !privacyEmail && <p className="mt-1 text-xs text-muted">{t('dataPage.noEmail')}</p>}

          <Link to="/privacy" className="mt-6 inline-block text-sm font-medium text-accent hover:underline">
            {t('dataPage.readNotice')}
          </Link>
        </section>
      </motion.div>

      <Dialog
        open={deleteOpen}
        onClose={() => {
          setDeleteOpen(false);
          deleteMe.reset();
        }}
        busy={deleteMe.isPending}
        role="alertdialog"
        size="sm"
        title={t('dataPage.v1.deleteTitle')}
        footer={
          <>
            <Button size="sm" variant="outline" onClick={() => setDeleteOpen(false)} disabled={deleteMe.isPending}>
              {t('common.cancel')}
            </Button>
            <Button size="sm" variant="danger" type="submit" form="delete-account-form" isLoading={deleteMe.isPending} disabled={!password}>
              {t('dataPage.v1.deleteConfirm')}
            </Button>
          </>
        }
      >
        <form id="delete-account-form" onSubmit={handleDeleteAccount} className="space-y-4 text-sm text-muted">
          <p>{t('dataPage.v1.deleteBody')}</p>
          <div>
            <label htmlFor="delete-password" className="mb-1.5 block font-medium text-textMain">
              {t('dataPage.v1.passwordLabel')}
            </label>
            <input
              id="delete-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="field py-2"
              required
            />
          </div>
          {deleteMe.isError && <ErrorNotice error={deleteMe.error} />}
        </form>
      </Dialog>
    </div>
  );
}
