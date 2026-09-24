import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import i18n from '../i18n';
import { getConfig, type ApiMode } from '../config/runtime';
import { api, applySession, onSessionChange, refreshSession } from '../api/client';
import { unwrap } from '../api/errors';
import { TERMS_VERSION, type Language, type User } from '../api/types';

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous';

export interface RegisterInput {
  email: string;
  password: string;
  language: Language;
  confirmAge16: boolean;
}

interface AuthValue {
  user: User | null;
  status: AuthStatus;
  mode: ApiMode;
  /** True after a refresh failed; the login page shows a "session expired" notice. */
  sessionExpired: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

// ---- legacy (pre-gateway) placeholder: user object in localStorage, no server session ----
export const LEGACY_USER_KEY = 'mimir_user';
const readLegacyUser = (): User | null => {
  try {
    const raw = JSON.parse(localStorage.getItem(LEGACY_USER_KEY) || 'null') as { email?: string } | null;
    return raw?.email ? { id: raw.email, email: raw.email, language: (i18n.resolvedLanguage as Language) ?? 'hu' } : null;
  } catch {
    return null;
  }
};
const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const mode = getConfig().apiMode;
  const qc = useQueryClient();
  const [user, setUser] = useState<User | null>(() => (mode === 'legacy' ? readLegacyUser() : null));
  const [status, setStatus] = useState<AuthStatus>(() => (mode === 'legacy' ? (readLegacyUser() ? 'authenticated' : 'anonymous') : 'loading'));
  const [sessionExpired, setSessionExpired] = useState(false);
  const userRef = useRef(user);
  userRef.current = user;

  // v1: restore the session from the refresh cookie on page load, then follow token changes.
  useEffect(() => {
    if (mode !== 'v1') return undefined;
    const off = onSessionChange((u, reason) => {
      setUser(u);
      setStatus(u ? 'authenticated' : 'anonymous');
      if (reason === 'expired') {
        setSessionExpired(true);
        qc.clear();
      }
    });
    let cancelled = false;
    void refreshSession().then((s) => {
      if (cancelled) return;
      if (s) applySession(s);
      else {
        setUser(null);
        setStatus('anonymous');
      }
    });
    return () => {
      cancelled = true;
      off();
    };
  }, [mode, qc]);

  // Keep the account language in sync with the UI language switch.
  useEffect(() => {
    if (mode !== 'v1') return undefined;
    const onLang = (lng: string) => {
      const language: Language = lng.startsWith('en') ? 'en' : 'hu';
      const u = userRef.current;
      if (u && u.language !== language) {
        void api()
          .PATCH('/me', { body: { language } })
          .then((r) => r.data && setUser((prev) => (prev ? { ...prev, language } : prev)));
      }
    };
    i18n.on('languageChanged', onLang);
    return () => i18n.off('languageChanged', onLang);
  }, [mode]);

  const login = useCallback(
    async (email: string, password: string): Promise<User> => {
      if (mode === 'legacy') {
        await delay(600);
        const u: User = { id: email, email, language: (i18n.resolvedLanguage as Language) ?? 'hu' };
        try {
          localStorage.setItem(LEGACY_USER_KEY, JSON.stringify({ email }));
        } catch {
          /* ignore */
        }
        setUser(u);
        setStatus('authenticated');
        return u;
      }
      const session = unwrap(await api().POST('/auth/login', { body: { email, password } }));
      setSessionExpired(false);
      applySession(session);
      if (session.user.language && !i18n.resolvedLanguage?.startsWith(session.user.language)) {
        void i18n.changeLanguage(session.user.language);
      }
      return session.user;
    },
    [mode],
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      if (mode === 'legacy') {
        await delay(600);
        return;
      }
      unwrap(
        await api().POST('/auth/register', {
          body: {
            email: input.email,
            password: input.password,
            language: input.language,
            confirm_age_16: true,
            accepted_terms_version: TERMS_VERSION,
          },
        }),
      );
    },
    [mode],
  );

  const logout = useCallback(async () => {
    if (mode === 'legacy') {
      try {
        localStorage.removeItem(LEGACY_USER_KEY);
      } catch {
        /* ignore */
      }
      setUser(null);
      setStatus('anonymous');
      return;
    }
    try {
      await api().POST('/auth/logout');
    } catch {
      /* the local session ends anyway */
    }
    applySession(null);
    qc.clear();
  }, [mode, qc]);

  const value = useMemo<AuthValue>(
    () => ({ user, status, mode, sessionExpired, login, register, logout }),
    [user, status, mode, sessionExpired, login, register, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
};
