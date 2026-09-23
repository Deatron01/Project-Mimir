import createClient, { type Client } from 'openapi-fetch';
import type { paths } from './schema';
import { getConfig } from '../config/runtime';
import { getAccessToken, setAccessToken } from './tokens';
import { errorFromResponse, networkError } from './errors';
import type { AuthSession, User } from './types';

type SessionListener = (user: User | null, reason?: 'expired') => void;
const sessionListeners = new Set<SessionListener>();
export const onSessionChange = (l: SessionListener): (() => void) => {
  sessionListeners.add(l);
  return () => sessionListeners.delete(l);
};

export function applySession(session: AuthSession | null, reason?: 'expired'): void {
  setAccessToken(session?.access_token ?? null);
  sessionListeners.forEach((l) => l(session?.user ?? null, reason));
}

const apiUrl = (path: string) => `${getConfig().apiBaseUrl}${path}`;
const isAuthPath = (url: string) => /\/auth\/(login|refresh|register|verify|password)/.test(url);

let refreshing: Promise<AuthSession | null> | null = null;

/**
 * Exchanges the HttpOnly refresh cookie for a new access token. Concurrent callers share one request,
 * so a burst of 401s triggers a single refresh.
 */
export function refreshSession(): Promise<AuthSession | null> {
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const res = await fetch(apiUrl('/auth/refresh'), { method: 'POST', credentials: 'include' });
        if (!res.ok) return null;
        return (await res.json()) as AuthSession;
      } catch {
        return null;
      }
    })().finally(() => {
      refreshing = null;
    });
  }
  return refreshing;
}

function withAuth(req: Request): Request {
  const token = getAccessToken();
  if (!token) return req;
  const headers = new Headers(req.headers);
  headers.set('Authorization', `Bearer ${token}`);
  return new Request(req, { headers });
}

/**
 * fetch wrapper used by every API call: adds the bearer token and, on `401 TOKEN_EXPIRED`,
 * refreshes once and replays the request. A failed refresh ends the session.
 */
export async function authFetch(req: Request): Promise<Response> {
  const replay = req.clone();
  let res: Response;
  try {
    res = await fetch(withAuth(req));
  } catch (e) {
    throw networkError(e);
  }
  if (res.status !== 401 || isAuthPath(req.url) || !getAccessToken()) return res;
  const err = await errorFromResponse(res);
  if (err.code !== 'TOKEN_EXPIRED') return res;
  const session = await refreshSession();
  if (!session) {
    applySession(null, 'expired');
    return res;
  }
  applySession(session);
  return fetch(withAuth(replay));
}

let client: Client<paths> | null = null;
let clientBase = '';

/** Typed client for the v1 API. Created lazily so it picks up `/config.json`. */
export function api(): Client<paths> {
  const base = getConfig().apiBaseUrl;
  if (!client || clientBase !== base) {
    client = createClient<paths>({ baseUrl: base, fetch: authFetch, credentials: 'include' });
    clientBase = base;
  }
  return client;
}

export { apiUrl };
