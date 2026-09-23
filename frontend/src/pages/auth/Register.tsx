import { useState } from 'react';
import { ArrowRight, Lock, Mail, MailCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Trans, useTranslation } from 'react-i18next';
import Button from '../../components/ui/Button';
import IconField from '../../components/ui/IconField';
import SegmentedControl from '../../components/ui/SegmentedControl';
import AuthCard from '../../components/auth/AuthCard';
import ErrorNotice from '../../components/common/ErrorNotice';
import { useAuth } from '../../context/AuthContext';
import useDocumentTitle from '../../hooks/useDocumentTitle';
import { MIN_PASSWORD_LENGTH, type Language } from '../../api/types';

export default function Register() {
  const { t, i18n } = useTranslation();
  useDocumentTitle('meta.register');
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [language, setLanguage] = useState<Language>(i18n.resolvedLanguage === 'en' ? 'en' : 'hu');
  const [age, setAge] = useState(false);
  const [terms, setTerms] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [localError, setLocalError] = useState('');
  const [done, setDone] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLocalError('');
    if (password.length < MIN_PASSWORD_LENGTH) return setLocalError(t('auth.register.tooShort', { min: MIN_PASSWORD_LENGTH }));
    if (password !== confirm) return setLocalError(t('auth.register.mismatch'));
    if (!age) return setLocalError(t('auth.register.ageRequired'));
    if (!terms) return setLocalError(t('auth.register.termsRequired'));
    setBusy(true);
    try {
      await register({ email: email.trim(), password, language, confirmAge16: age });
      setDone(true);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <AuthCard title={t('auth.register.checkInboxTitle')}>
        <div className="flex flex-col items-center gap-4 text-center" role="status">
          <MailCheck size={44} className="text-accent" aria-hidden="true" />
          <p className="text-sm text-muted">{t('auth.register.checkInbox', { email })}</p>
          <Link to="/login" className="font-medium text-accent hover:underline">
            {t('auth.register.loginLink')}
          </Link>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title={t('auth.register.title')}
      subtitle={t('auth.register.subtitle')}
      footer={
        <>
          {t('auth.register.hasAccount')}{' '}
          <Link to="/login" className="font-medium text-accent hover:underline">
            {t('auth.register.loginLink')}
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="flex flex-col gap-5" noValidate>
        <IconField
          id="register-email"
          label={t('auth.email')}
          icon={Mail}
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder={t('auth.emailPlaceholder')}
        />
        <IconField
          id="register-password"
          label={t('auth.password')}
          icon={Lock}
          type="password"
          autoComplete="new-password"
          minLength={MIN_PASSWORD_LENGTH}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          placeholder={t('auth.register.passwordPlaceholder', { min: MIN_PASSWORD_LENGTH })}
          hint={t('auth.register.passwordHint', { min: MIN_PASSWORD_LENGTH })}
        />
        <IconField
          id="register-confirm"
          label={t('auth.register.confirm')}
          icon={Lock}
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
          placeholder="••••••••"
        />
        <div>
          <span className="mb-2 ml-1 block text-sm font-medium text-textMain">{t('auth.register.language')}</span>
          <SegmentedControl
            label={t('auth.register.language')}
            value={language}
            onChange={setLanguage}
            options={[
              { value: 'hu', label: 'Magyar' },
              { value: 'en', label: 'English' },
            ]}
          />
        </div>
        <label className="flex cursor-pointer items-start gap-2 text-sm">
          <input type="checkbox" checked={age} onChange={(e) => setAge(e.target.checked)} required className="mt-0.5 h-4 w-4 shrink-0 accent-[rgb(var(--c-primary))]" />
          <span>{t('auth.register.age16')}</span>
        </label>
        <label className="flex cursor-pointer items-start gap-2 text-sm">
          <input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} required className="mt-0.5 h-4 w-4 shrink-0 accent-[rgb(var(--c-primary))]" />
          <span>
            <Trans
              i18nKey="auth.register.acceptTerms"
              components={{
                terms: <Link to="/terms" target="_blank" className="font-medium text-accent hover:underline" />,
                privacy: <Link to="/privacy" target="_blank" className="font-medium text-accent hover:underline" />,
              }}
            />
          </span>
        </label>

        {localError && (
          <p role="alert" className="text-center text-sm text-danger">
            {localError}
          </p>
        )}
        <ErrorNotice error={error} />
        <Button type="submit" isLoading={busy} className="group mt-1 w-full">
          {!busy && (
            <>
              {t('auth.register.submit')}
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </>
          )}
        </Button>
      </form>
    </AuthCard>
  );
}
