import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Inbox, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { MockMail } from '../../mocks/db';

/**
 * Mock-mode only: shows the e-mails the mock API "sent" (verification, password reset) so the flows can be
 * tried without a mail server. Never rendered against a real backend.
 */
export default function DevMailbox() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [mails, setMails] = useState<MockMail[]>([]);

  useEffect(() => {
    if (!open) return undefined;
    let alive = true;
    const load = () =>
      import('../../mocks/db').then(({ getDb }) => {
        if (alive) setMails([...getDb().outbox]);
      });
    void load();
    const id = setInterval(() => void load(), 1500);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [open]);

  const reset = async () => {
    const { resetDb } = await import('../../mocks/db');
    resetDb();
    window.location.assign('/');
  };

  return (
    <div className="fixed bottom-4 left-4 z-[70] text-xs">
      {open ? (
        <div className="w-80 rounded-2xl border border-warning/60 bg-background/95 p-4 shadow-2xl backdrop-blur-xl">
          <div className="mb-2 flex items-center justify-between">
            <strong className="text-sm">{t('dev.mailbox')}</strong>
            <button type="button" onClick={() => setOpen(false)} aria-label={t('common.close')} className="text-muted hover:text-textMain">
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <p className="mb-3 text-muted">{t('dev.mockNotice')}</p>
          {mails.length === 0 ? (
            <p className="text-muted">{t('dev.empty')}</p>
          ) : (
            <ul className="mb-3 max-h-60 space-y-2 overflow-y-auto">
              {mails.map((m) => (
                <li key={m.id} className="rounded-lg border border-border/40 p-2">
                  <p className="font-medium text-textMain">{t(`dev.subjects.${m.subject}`)}</p>
                  <p className="text-muted">{m.to}</p>
                  <Link to={m.link} onClick={() => setOpen(false)} className="font-semibold text-accent hover:underline">
                    {t('dev.openLink')}
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <p className="mb-2 text-muted">{t('dev.demoAccount')}</p>
          <button type="button" onClick={() => void reset()} className="font-semibold text-danger hover:underline">
            {t('dev.reset')}
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="flex items-center gap-1.5 rounded-full border border-warning/60 bg-background/90 px-3 py-2 font-semibold text-warning shadow-lg backdrop-blur"
        >
          <Inbox size={14} aria-hidden="true" /> {t('dev.badge')}
        </button>
      )}
    </div>
  );
}
