import { useState } from 'react';
import { CheckCircle2, Lock } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import AuthCard from '../../components/auth/AuthCard';
import Button from '../../components/ui/Button';
import IconField from '../../components/ui/IconField';
import ErrorNotice from '../../components/common/ErrorNotice';
import { api } from '../../api/client';
import { unwrap } from '../../api/errors';
import { MIN_PASSWORD_LENGTH } from '../../api/types';
import useDocumentTitle from '../../hooks/useDocumentTitle';

export default function ResetPassword() {
  const { t } = useTranslation();
  useDocumentTitle('meta.reset');
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [localError, setLocalError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLocalError('');
    if (password.length < MIN_PASSWORD_LENGTH) return setLocalError(t('auth.register.tooShort', { min: MIN_PASSWORD_LENGTH }));
    if (password !== confirm) return setLocalError(t('auth.register.mismatch'));
    setBusy(true);
    try {
      unwrap(await api().POST('/auth/password/reset', { body: { token, new_password: password } }));
      setDone(true);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthCard title={t('auth.reset.title')} subtitle={done ? undefined : t('auth.reset.subtitle')}>
      {done ? (
        <div role="status" className="flex flex-col items-center gap-4 text-center">
          <CheckCircle2 size={44} className="text-success" aria-hidden="true" />
          <p className="text-sm text-muted">{t('auth.reset.success')}</p>
          <Link to="/login" className="font-medium text-accent hover:underline">
            {t('auth.register.loginLink')}
          </Link>
        </div>
      ) : (
        <form onSubmit={submit} className="flex flex-col gap-5" noValidate>
          <IconField
            id="reset-password"
            label={t('auth.reset.newPassword')}
            icon={Lock}
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            hint={t('auth.register.passwordHint', { min: MIN_PASSWORD_LENGTH })}
          />
          <IconField
            id="reset-confirm"
            label={t('auth.register.confirm')}
            icon={Lock}
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
          />
          {localError && (
            <p role="alert" className="text-center text-sm text-danger">
              {localError}
            </p>
          )}
          <ErrorNotice error={error} />
          <Button type="submit" isLoading={busy} className="w-full">
            {t('auth.reset.submit')}
          </Button>
        </form>
      )}
    </AuthCard>
  );
}
