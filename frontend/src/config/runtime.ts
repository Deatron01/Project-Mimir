/**
 * Runtime configuration (FE-03).
 *
 * Priority: `/config.json` (written by the Docker entrypoint from env vars) → build-time `VITE_*` vars → defaults.
 * One image can therefore be promoted from staging to production without a rebuild.
 */
export type ApiMode = 'legacy' | 'v1';

export interface RuntimeConfig {
  /** Base URL of the public API, without a trailing slash (e.g. https://api.mimir-ai.hu/api/v1). */
  apiBaseUrl: string;
  /** `v1` = topic workspace against the /api/v1 contract; `legacy` = the pre-topic flow for the old backend. */
  apiMode: ApiMode;
  /** Serve the v1 API from the in-browser mock (MSW) instead of the network. */
  useMocks: boolean;
  /** Address for data-protection requests; empty hides the mailto link. */
  privacyEmail: string;
}

const bool = (v: unknown): boolean | undefined =>
  v === undefined || v === null || v === '' ? undefined : v === true || String(v).toLowerCase() === 'true';

function fromEnv(): RuntimeConfig {
  const env = import.meta.env;
  const prodFallback = 'https://api.mimir-ai.hu/api/v1';
  const apiMode: ApiMode = env.VITE_API_MODE === 'legacy' || env.VITE_API_MODE === 'v1' ? env.VITE_API_MODE : env.PROD ? 'legacy' : 'v1';
  const useMocks = bool(env.VITE_USE_MOCKS) ?? (!env.PROD && apiMode === 'v1');
  return {
    apiBaseUrl: (env.VITE_API_BASE_URL || (env.PROD ? prodFallback : '/api/v1')).replace(/\/$/, ''),
    apiMode,
    useMocks,
    privacyEmail: env.VITE_PRIVACY_EMAIL || '',
  };
}

let current: RuntimeConfig = fromEnv();

/** Loads `/config.json` if the server provides one. Never throws: a missing or broken file keeps the build-time values. */
export async function loadRuntimeConfig(fetchImpl: typeof fetch = fetch): Promise<RuntimeConfig> {
  try {
    const res = await fetchImpl('/config.json', { cache: 'no-store', headers: { Accept: 'application/json' } });
    const type = res.headers.get('content-type') ?? '';
    if (res.ok && type.includes('json')) {
      current = mergeConfig(current, (await res.json()) as Partial<Record<keyof RuntimeConfig, unknown>>);
    }
  } catch {
    /* no runtime file (e.g. Netlify, dev server) – keep build-time values */
  }
  return current;
}

export function mergeConfig(base: RuntimeConfig, raw: Partial<Record<keyof RuntimeConfig, unknown>>): RuntimeConfig {
  const out = { ...base };
  if (typeof raw.apiBaseUrl === 'string' && raw.apiBaseUrl) out.apiBaseUrl = raw.apiBaseUrl.replace(/\/$/, '');
  if (raw.apiMode === 'legacy' || raw.apiMode === 'v1') out.apiMode = raw.apiMode;
  const mocks = bool(raw.useMocks);
  if (mocks !== undefined) out.useMocks = mocks;
  if (typeof raw.privacyEmail === 'string') out.privacyEmail = raw.privacyEmail;
  return out;
}

export const getConfig = (): RuntimeConfig => current;
/** For tests. */
export const setConfig = (patch: Partial<RuntimeConfig>): void => {
  current = { ...current, ...patch };
};
export const isV1 = (): boolean => current.apiMode === 'v1';
