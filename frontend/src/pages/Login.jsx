import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '../components/ui/Button';
import IconField from '../components/ui/IconField';
import { useAuth } from '../context/AuthContext';
import useDocumentTitle from '../hooks/useDocumentTitle';

export default function Login() {
  const { t } = useTranslation();
  useDocumentTitle('meta.login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');
    try {
      // TODO(GW-01 / FE-04): replace with the real auth service call.
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setSuccessMsg(t('auth.login.success'));
      login({ email });
      navigate('/chat');
    } catch {
      setErrorMsg(t('auth.login.error'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-[80vh] items-center justify-center overflow-hidden">
      <div className="pointer-events-none absolute left-[-10%] top-[20%] h-[40rem] w-[40rem] rounded-full bg-primary/20 blur-[120px]" aria-hidden="true" />

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="z-10 w-full max-w-md px-6">
        <div className="card relative overflow-hidden p-8">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-accent to-primary" />

          <div className="mb-8 text-center">
            <h1 className="mb-2 text-3xl font-extrabold tracking-tight">{t('auth.login.title')}</h1>
            <p className="text-sm text-muted">{t('auth.login.subtitle')}</p>
          </div>

          <form onSubmit={handleLogin} className="flex flex-col gap-5">
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

            <div aria-live="polite">
              {errorMsg && <p className="text-center text-sm text-danger">{errorMsg}</p>}
              {successMsg && <p className="text-center text-sm text-success">{successMsg}</p>}
            </div>

            <Button type="submit" isLoading={isLoading} className="group mt-2 w-full">
              {!isLoading && (
                <>
                  {t('auth.login.submit')}
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-muted">
            {t('auth.login.noAccount')}{' '}
            <Link to="/register" className="font-medium text-accent hover:underline">
              {t('auth.login.registerLink')}
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
