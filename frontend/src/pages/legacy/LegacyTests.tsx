import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Calendar, HardDrive, Loader2, Inbox, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import ButtonLink from '../../components/ui/ButtonLink';
import Button from '../../components/ui/Button';
import { legacyEndpoints as endpoints } from '../../config/legacyEndpoints';
import useDocumentTitle from '../../hooks/useDocumentTitle';

interface LegacyTest {
  id: string;
  title: string;
  created_at: string;
  file_size: string;
}

/** Saved-tests list for the old backend (apiMode = 'legacy'). */
export default function LegacyTests() {
  const { t, i18n } = useTranslation();
  useDocumentTitle('meta.tests');
  const { user } = useAuth();
  const [tests, setTests] = useState<LegacyTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTests() {
      if (!user?.email) return;
      try {
        const res = await fetch(endpoints.tests(user.email));
        if (!res.ok) throw new Error();
        setTests(await res.json());
      } catch {
        setError(t('tests.loadError'));
      } finally {
        setLoading(false);
      }
    }
    fetchTests();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const formatDate = (value: string) => {
    const d = new Date(String(value).replace(' ', 'T'));
    return Number.isNaN(d.getTime())
      ? value
      : new Intl.DateTimeFormat(i18n.resolvedLanguage, { dateStyle: 'medium', timeStyle: 'short' }).format(d);
  };

  const handleDownload = async (testId: string, title: string) => {
    setError('');
    try {
      const res = await fetch(endpoints.download(testId));
      if (!res.ok) throw new Error();
      const url = URL.createObjectURL(await res.blob());
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch {
      setError(t('tests.downloadError'));
    }
  };

  // GDPR Art. 17: users can erase their saved tests themselves.
  const handleDelete = async (testId: string) => {
    if (confirmId !== testId) {
      setConfirmId(testId);
      return;
    }
    setError('');
    setNotice('');
    setDeletingId(testId);
    try {
      const res = await fetch(endpoints.deleteTest(testId, user!.email), { method: 'DELETE' });
      if (!res.ok) throw new Error();
      setTests((prev) => prev.filter((x) => x.id !== testId));
      setNotice(t('tests.deleted'));
    } catch {
      setError(t('tests.deleteError'));
    } finally {
      setDeletingId(null);
      setConfirmId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-80px)] items-center justify-center" role="status">
        <Loader2 className="h-8 w-8 animate-spin text-accent" aria-hidden="true" />
        <span className="sr-only">{t('common.loading')}</span>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-10">
        <h1 className="mb-2 text-3xl font-extrabold tracking-tight">{t('tests.title')}</h1>
        <p className="text-sm text-muted">{t('tests.subtitle')}</p>
        <p className="mt-1 text-xs text-muted">{t('tests.retention')}</p>
      </div>

      <p role="status" aria-live="polite" className="mb-6 rounded-2xl border border-success/40 bg-success/10 p-4 text-sm text-success empty:hidden">
        {notice}
      </p>

      {error && (
        <div role="alert" className="mb-6 rounded-2xl border border-danger/40 bg-danger/10 p-4 text-sm text-danger">
          {error}
        </div>
      )}

      {tests.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center justify-center rounded-3xl border border-border/40 bg-surface/10 p-16 text-center"
        >
          <Inbox size={48} className="mb-4 text-muted" aria-hidden="true" />
          <h2 className="mb-1 text-lg font-semibold">{t('tests.emptyTitle')}</h2>
          <p className="mb-6 max-w-xs text-sm text-muted">{t('tests.emptyDesc')}</p>
          <ButtonLink to="/chat" size="sm">{t('tests.goToApp')}</ButtonLink>
        </motion.div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-border/40 bg-surface/10 shadow-xl backdrop-blur-md">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-border/40 bg-surface/30 text-xs font-semibold uppercase tracking-wider text-muted">
                <th scope="col" className="p-5">{t('tests.columns.name')}</th>
                <th scope="col" className="p-5">
                  <span className="flex items-center gap-1"><Calendar size={14} aria-hidden="true" /> {t('tests.columns.created')}</span>
                </th>
                <th scope="col" className="p-5">
                  <span className="flex items-center gap-1"><HardDrive size={14} aria-hidden="true" /> {t('tests.columns.size')}</span>
                </th>
                <th scope="col" className="p-5 text-right">{t('tests.columns.action')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30 text-sm">
              {tests.map((test, index) => (
                <motion.tr
                  key={test.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="group transition-colors hover:bg-surface/20"
                >
                  <td className="p-5 font-medium">
                    <span className="flex items-center gap-3">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-danger/30 bg-danger/10 text-xs font-bold text-danger" aria-hidden="true">
                        PDF
                      </span>
                      <span className="max-w-md truncate">{test.title}</span>
                    </span>
                  </td>
                  <td className="whitespace-nowrap p-5 text-muted">{formatDate(test.created_at)}</td>
                  <td className="p-5 font-mono text-xs text-muted">{test.file_size}</td>
                  <td className="p-5">
                    <span className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleDownload(test.id, test.title)}>
                        <Download size={14} aria-hidden="true" /> {t('common.download')}
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        isLoading={deletingId === test.id}
                        onClick={() => handleDelete(test.id)}
                        onBlur={() => confirmId === test.id && setConfirmId(null)}
                        aria-label={`${t('tests.delete')}: ${test.title}`}
                      >
                        {deletingId !== test.id && <Trash2 size={14} aria-hidden="true" />}
                        {confirmId === test.id ? t('tests.confirmDelete') : t('tests.delete')}
                      </Button>
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
