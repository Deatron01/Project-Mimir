import React, { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, HardDrive, Mail, Server, ShieldCheck, Trash2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { endpoints, PRIVACY_EMAIL } from '../config';
import useDocumentTitle from '../hooks/useDocumentTitle';

// Every key Mimir writes to browser storage. Keep in sync with the privacy notice.
const STORAGE_KEYS = ['mimir-theme', 'mimir-lang', 'mimir_user'];

const readStorage = () =>
  STORAGE_KEYS.map((key) => {
    let value = null;
    try {
      value = localStorage.getItem(key);
    } catch {
      /* storage unavailable */
    }
    return { key, value };
  }).filter((x) => x.value !== null);

/** "Your data" page: what is stored, export, deletion (GDPR Art. 15, 17, 20). */
export default function YourData() {
  const { t } = useTranslation();
  useDocumentTitle('meta.data');
  const { user, logout } = useAuth();
  const { setPaletteId, setMode } = useTheme();
  const navigate = useNavigate();
  const [stored, setStored] = useState(readStorage);
  const [confirmClear, setConfirmClear] = useState(false);
  const [notice, setNotice] = useState('');
  const [exporting, setExporting] = useState(false);

  const mailto = useMemo(() => {
    if (!PRIVACY_EMAIL) return '';
    const subject = encodeURIComponent(t('dataPage.mailSubject'));
    const body = encodeURIComponent(t('dataPage.mailBody', { email: user?.email ?? '' }));
    return `mailto:${PRIVACY_EMAIL}?subject=${subject}&body=${body}`;
  }, [t, user]);

  const handleExport = async () => {
    setExporting(true);
    const data = {
      exportedAt: new Date().toISOString(),
      browserStorage: Object.fromEntries(stored.map(({ key, value }) => [key, value])),
    };
    if (user?.email) {
      try {
        const res = await fetch(endpoints.tests(user.email));
        if (res.ok) data.savedTests = await res.json();
      } catch {
        /* export what we have */
      }
    }
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mimir-my-data.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setExporting(false);
  };

  const handleClear = () => {
    if (!confirmClear) {
      setConfirmClear(true);
      return;
    }
    logout();
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

  const serverItems = t('dataPage.serverItems', { returnObjects: true });

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
            <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
              {Array.isArray(serverItems) && serverItems.map((item) => <li key={item}>{item}</li>)}
            </ul>
            {user && (
              <Link to="/tests" className="mt-4 inline-block text-sm font-medium text-accent hover:underline">
                {t('dataPage.savedTests')}
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
                    <dd className="mt-1 break-all font-mono text-xs text-muted">{value}</dd>
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
          <p className="mb-6 text-sm text-muted">{t('dataPage.rightsDesc')}</p>

          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <Button variant="outline" size="sm" onClick={handleExport} isLoading={exporting}>
              {!exporting && <Download size={14} aria-hidden="true" />} {t('dataPage.export')}
            </Button>
            <Button variant="danger" size="sm" onClick={handleClear} onBlur={() => setConfirmClear(false)}>
              <Trash2 size={14} aria-hidden="true" /> {confirmClear ? t('dataPage.clearConfirm') : t('dataPage.clear')}
            </Button>
            {mailto ? (
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
          <p className="mt-3 text-xs text-muted">{t('dataPage.exportHint')}</p>
          {!PRIVACY_EMAIL && <p className="mt-1 text-xs text-muted">{t('dataPage.noEmail')}</p>}

          <Link to="/privacy" className="mt-6 inline-block text-sm font-medium text-accent hover:underline">
            {t('dataPage.readNotice')}
          </Link>
        </section>
      </motion.div>
    </div>
  );
}
