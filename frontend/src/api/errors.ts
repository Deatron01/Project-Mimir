import type { ErrorCode } from './types';

/** Normalised API error. `code` drives the `errors.<CODE>` translation key. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: ErrorCode | 'NETWORK' | 'UNKNOWN';
  readonly requestId?: string;
  readonly details?: Record<string, unknown>;

  constructor(opts: { status: number; code: ApiError['code']; message?: string; requestId?: string; details?: Record<string, unknown> }) {
    super(opts.message || opts.code);
    this.name = 'ApiError';
    this.status = opts.status;
    this.code = opts.code;
    this.requestId = opts.requestId;
    this.details = opts.details;
  }

  /** Translation key for this error; unknown codes fall back to a generic message. */
  get i18nKey(): string {
    return `errors.${this.code}`;
  }
}

const isEnvelope = (b: unknown): b is { error: { code: string; message?: string; request_id?: string; details?: Record<string, unknown> } } =>
  typeof b === 'object' && b !== null && 'error' in b && typeof (b as { error: unknown }).error === 'object' && (b as { error: { code?: unknown } }).error !== null && typeof (b as { error: { code?: unknown } }).error.code === 'string';

/** Builds an ApiError from a parsed body (openapi-fetch `error`) and the HTTP status. */
export function toApiError(body: unknown, status: number): ApiError {
  if (isEnvelope(body)) {
    const e = body.error;
    return new ApiError({ status, code: e.code as ErrorCode, message: e.message, requestId: e.request_id, details: e.details });
  }
  const code: ApiError['code'] =
    status === 401 ? 'AUTH_REQUIRED' : status === 413 ? 'FILE_TOO_LARGE' : status === 429 ? 'RATE_LIMITED' : status >= 500 ? 'INTERNAL' : 'UNKNOWN';
  return new ApiError({ status, code, message: typeof body === 'string' ? body : undefined });
}

export async function errorFromResponse(res: Response): Promise<ApiError> {
  let body: unknown;
  try {
    body = await res.clone().json();
  } catch {
    body = undefined;
  }
  return toApiError(body, res.status);
}

export const networkError = (cause?: unknown): ApiError =>
  new ApiError({ status: 0, code: 'NETWORK', message: cause instanceof Error ? cause.message : 'Network error' });

/** Unwraps an openapi-fetch result: returns `data` or throws an ApiError. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined || !result.response.ok) throw toApiError(result.error, result.response.status);
  return result.data as T;
}
