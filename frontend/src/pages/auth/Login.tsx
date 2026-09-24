import { useState } from 'react';
import { ArrowRight, Lock, Mail } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '../../components/ui/Button';
import IconField from '../../components/ui/IconField';
import AuthCard from '../../components/auth/AuthCard';
import ErrorNotice from '../../components/common/ErrorNotice';
import { useAuth } from '../../context/AuthContext';
import useDocumentTitle from '../../hooks/useDocumentTitle';

export default function Login() {
  const { t } = useTranslation();
  useDocumentTitle('meta.login');
  const { login, mode, sessionExpired } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from;
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email.trim(), password);
      navigate(from ?? (mode === 'v1' ? '/topics' : '/chat'), { replace: true });
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  };

  return (
    <AuthCard
      title={t('auth.login.title')}
      subtitle={t('auth.login.subtitle')}
      footer={
        <>
          {t('auth.login.noAccount')}{' '}
          <Link to="/register" className="font-medium text-accent hover:underline">
            {t('auth.login.registerLink')}
          </Link>
        </>
      }
    >
      {sessionExpired && (
        <p role="status" className="mb-5 rounded-xl border border-warning/50 bg-warning/10 p-3 text-sm text-textMain">
          {t('auth.login.expired')}
        </p>
      )}
      <form onSubmit={submit} className="flex flex-col gap-5">
        <IconField
          id="login-email"
          label={t('auth.email')}
          icon={Mail}
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder={t('auth.emailPlaceholder')}
        />
        <div>
          <IconField
            id="login-password"
            label={t('auth.password')}
            icon={Lock}
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="••••••••"
          />
          {mode === 'v1' && (
            <Link to="/forgot-password" className="ml-1 mt-2 inline-block text-xs font-medium text-accent hover:underline">
              {t('auth.login.forgot')}
            </Link>
          )}
        </div>
        <ErrorNotice error={error} />
        <Button type="submit" isLoading={busy} className="group mt-1 w-full">
          {!busy && (
            <>
              {t('auth.login.submit')}
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </>
          )}
        </Button>
      </form>
    </AuthCard>
  );
}
