import { useState } from 'react';
import { Mail, MailCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import AuthCard from '../../components/auth/AuthCard';
import Button from '../../components/ui/Button';
import IconField from '../../components/ui/IconField';
import ErrorNotice from '../../components/common/ErrorNotice';
import { api } from '../../api/client';
import { unwrap } from '../../api/errors';
import useDocumentTitle from '../../hooks/useDocumentTitle';

export default function ForgotPassword() {
  const { t } = useTranslation();
  useDocumentTitle('meta.forgot');
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      unwrap(await api().POST('/auth/password/forgot', { body: { email: email.trim() } }));
      setSent(true);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthCard
      title={t('auth.forgot.title')}
      subtitle={sent ? undefined : t('auth.forgot.subtitle')}
      footer={
        <Link to="/login" className="font-medium text-accent hover:underline">
          {t('auth.forgot.back')}
        </Link>
      }
    >
      {sent ? (
        <div role="status" className="flex flex-col items-center gap-3 text-center">
          <MailCheck size={44} className="text-accent" aria-hidden="true" />
          <p className="text-sm text-muted">{t('auth.forgot.sent', { email })}</p>
        </div>
      ) : (
        <form onSubmit={submit} className="flex flex-col gap-5">
          <IconField
            id="forgot-email"
            label={t('auth.email')}
            icon={Mail}
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder={t('auth.emailPlaceholder')}
          />
          <ErrorNotice error={error} />
          <Button type="submit" isLoading={busy} className="w-full">
            {t('auth.forgot.submit')}
          </Button>
        </form>
      )}
    </AuthCard>
  );
}
