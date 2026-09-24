import { apiUrl, applySession, refreshSession } from './client';
import { getAccessToken } from './tokens';
import { toApiError, networkError, ApiError } from './errors';
import type { TopicFile } from './types';

export interface UploadResult {
  files: TopicFile[];
  job_ids: string[];
}

function buildForm(files: File[]): FormData {
  const form = new FormData();
  files.forEach((f) => form.append('files[]', f, f.name));
  form.append('consent', 'true');
  return form;
}

/** fetch fallback where XHR does not exist (Node tests, workers): no byte progress, just 0 → 1. */
async function sendWithFetch(topicId: string, files: File[], onProgress?: (fraction: number) => void, signal?: AbortSignal) {
  const token = getAccessToken();
  onProgress?.(0);
  let res: Response;
  try {
    res = await fetch(apiUrl(`/topics/${encodeURIComponent(topicId)}/files`), {
      method: 'POST',
      body: buildForm(files),
      credentials: 'include',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      signal,
    });
  } catch (e) {
    throw networkError(e);
  }
  onProgress?.(1);
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    /* empty body */
  }
  return { status: res.status, body };
}

function sendOnce(topicId: string, files: File[], onProgress?: (fraction: number) => void, signal?: AbortSignal) {
  if (typeof XMLHttpRequest === 'undefined') return sendWithFetch(topicId, files, onProgress, signal);
  return new Promise<{ status: number; body: unknown }>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', apiUrl(`/topics/${encodeURIComponent(topicId)}/files`));
    xhr.withCredentials = true;
    const token = getAccessToken();
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.responseType = 'json';
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(e.loaded / e.total);
    };
    xhr.onload = () => resolve({ status: xhr.status, body: xhr.response });
    xhr.onerror = () => reject(networkError());
    xhr.onabort = () => reject(new ApiError({ status: 0, code: 'NETWORK', message: 'aborted' }));
    signal?.addEventListener('abort', () => xhr.abort(), { once: true });
    xhr.send(buildForm(files));
  });
}

/**
 * Multipart upload with byte progress (fetch cannot report upload progress, so this uses XHR).
 * Only call after the user ticked the consent box – the server rejects `consent=false` with CONSENT_REQUIRED.
 */
export async function uploadFiles(
  topicId: string,
  files: File[],
  opts: { onProgress?: (fraction: number) => void; signal?: AbortSignal } = {},
): Promise<UploadResult> {
  let r = await sendOnce(topicId, files, opts.onProgress, opts.signal);
  if (r.status === 401 && getAccessToken()) {
    const session = await refreshSession();
    if (!session) {
      applySession(null, 'expired');
      throw toApiError(r.body, r.status);
    }
    applySession(session);
    r = await sendOnce(topicId, files, opts.onProgress, opts.signal);
  }
  if (r.status < 200 || r.status >= 300) throw toApiError(r.body, r.status);
  return r.body as UploadResult;
}
