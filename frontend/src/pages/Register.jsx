import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '../components/ui/Button';
import IconField from '../components/ui/IconField';
import useDocumentTitle from '../hooks/useDocumentTitle';

export default function Register() {
  const { t } = useTranslation();
  useDocumentTitle('meta.register');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    if (password !== confirmPassword) {
      setErrorMsg(t('auth.register.mismatch'));
      return;
    }
    if (password.length < 6) {
      setErrorMsg(t('auth.register.tooShort'));
      return;
    }
    setIsLoading(true);
    try {
      // TODO(GW-01 / FE-04): replace with the real auth service call.
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setSuccessMsg(t('auth.register.success'));
      setEmail('');
      setPassword('');
      setConfirmPassword('');
    } catch {
      setErrorMsg(t('auth.register.error'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative mt-10 flex min-h-[80vh] items-center justify-center overflow-hidden">
      <div className="pointer-events-none absolute right-[-10%] top-[20%] h-[40rem] w-[40rem] rounded-full bg-surface/40 blur-[120px]" aria-hidden="true" />

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="z-10 w-full max-w-md px-6">
        <div className="card relative overflow-hidden p-8">
          <div className="mb-8 text-center">
            <h1 className="mb-2 text-3xl font-extrabold tracking-tight">{t('auth.register.title')}</h1>
            <p className="text-sm text-muted">{t('auth.register.subtitle')}</p>
          </div>

          <form onSubmit={handleRegister} className="flex flex-col gap-5">
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
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder={t('auth.register.passwordPlaceholder')}
            />
            <IconField
              id="register-confirm"
              label={t('auth.register.confirm')}
              icon={Lock}
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="••••••••"
            />

            <div aria-live="polite">
              {errorMsg && <p className="text-center text-sm text-danger">{errorMsg}</p>}
              {successMsg && <p className="text-center text-sm leading-relaxed text-success">{successMsg}</p>}
            </div>

            <Button type="submit" isLoading={isLoading} className="group mt-2 w-full">
              {!isLoading && (
                <>
                  {t('auth.register.submit')}
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-muted">
            {t('auth.register.hasAccount')}{' '}
            <Link to="/login" className="font-medium text-accent hover:underline">
              {t('auth.register.loginLink')}
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
