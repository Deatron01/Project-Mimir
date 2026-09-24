import { useEffect, useRef, useState } from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import AuthCard from '../../components/auth/AuthCard';
import ErrorNotice from '../../components/common/ErrorNotice';
import Spinner from '../../components/common/Spinner';
import { api } from '../../api/client';
import { unwrap } from '../../api/errors';
import useDocumentTitle from '../../hooks/useDocumentTitle';

export default function VerifyEmail() {
  const { t } = useTranslation();
  useDocumentTitle('meta.verify');
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const [state, setState] = useState<'pending' | 'ok' | 'error'>('pending');
  const [error, setError] = useState<unknown>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return; // StrictMode runs effects twice; the token is single-use.
    started.current = true;
    void (async () => {
      try {
        unwrap(await api().POST('/auth/verify', { body: { token } }));
        setState('ok');
      } catch (e) {
        setError(e);
        setState('error');
      }
    })();
  }, [token]);

  return (
    <AuthCard title={t('auth.verify.title')}>
      {state === 'pending' && <Spinner className="py-6" label={t('auth.verify.pending')} />}
      {state === 'ok' && (
        <div role="status" className="flex flex-col items-center gap-4 text-center">
          <CheckCircle2 size={44} className="text-success" aria-hidden="true" />
          <p className="text-sm text-muted">{t('auth.verify.success')}</p>
          <Link to="/login" className="font-medium text-accent hover:underline">
            {t('auth.register.loginLink')}
          </Link>
        </div>
      )}
      {state === 'error' && (
        <div className="space-y-4 text-center">
          <ErrorNotice error={error} />
          <p className="text-sm text-muted">{t('auth.verify.failedHint')}</p>
        </div>
      )}
    </AuthCard>
  );
}
