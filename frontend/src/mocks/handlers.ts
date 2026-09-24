/**
 * MSW handlers implementing the public v1 API contract (openapi/mimir-public.yaml) against the mock DB.
 * Validation rules and error codes follow the "Mimir API Specification by Module" doc so the UI's error
 * handling can be exercised before the backend exists.
 */
import { http, HttpResponse, delay, type HttpHandler } from 'msw';
import type { ErrorCode, ExportRequest, GenerationOptions, Language, MessageInput, TopicInput, TopicPatch } from '../api/types';
import { DEFAULT_LIMITS, MIN_PASSWORD_LENGTH } from '../api/types';
import {
  addDays,
  getDb,
  INACTIVITY_DAYS,
  nextId,
  now,
  persist,
  publicFile,
  publicJob,
  publicMessage,
  publicSession,
  publicTest,
  publicTopic,
  recount,
  touchTopic,
  type MockFile,
  type MockTopic,
  type MockUser,
} from './db';
import { createJob, eventsSince, subscribe } from './runner';
import { exportExam } from './exporters';

const ACCESS_TTL_MS = 15 * 60_000;
const LATENCY = () => delay(import.meta.env.MODE === 'test' ? 0 : 120 + Math.random() * 180);

let reqSeq = 0;
function err(status: number, code: ErrorCode, message: string = code, details?: Record<string, unknown>) {
  reqSeq += 1;
  return HttpResponse.json({ error: { code, message, request_id: `mock-${reqSeq}`, details } }, { status });
}

const tokenFor = (u: MockUser) => `mock.${u.id}.${Date.now() + ACCESS_TTL_MS}`;
const sessionFor = (u: MockUser) => ({
  access_token: tokenFor(u),
  expires_in: ACCESS_TTL_MS / 1000,
  user: { id: u.id, email: u.email, language: u.language },
});

type Authed = { user: MockUser } | { res: Response };
function auth(request: Request): Authed {
  const h = request.headers.get('authorization') ?? '';
  const m = /^Bearer mock\.(.+)\.(\d+)$/.exec(h);
  if (!m) return { res: err(401, 'AUTH_REQUIRED', 'Missing or invalid token') };
  if (Number(m[2]) < Date.now()) return { res: err(401, 'TOKEN_EXPIRED', 'Access token expired') };
  const user = getDb().users.find((u) => u.id === m[1]);
  if (!user) return { res: err(401, 'AUTH_REQUIRED', 'Unknown user') };
  return { user };
}

function ownTopic(user: MockUser, topicId: string): { topic: MockTopic } | { res: Response } {
  const topic = getDb().topics.find((t) => t.id === topicId && t.user_id === user.id);
  // Other users' topics answer 404 exactly like missing ones (no existence leak).
  if (!topic) return { res: err(404, 'TOPIC_NOT_FOUND') };
  return { topic };
}

const mail = (to: string, subject: string, link: string) => {
  getDb().outbox.unshift({ id: nextId('mail'), to, subject, link, created_at: now() });
  getDb().outbox = getDb().outbox.slice(0, 20);
};

const extOf = (name: string) => name.split('.').pop()?.toLowerCase() ?? '';
const MIME: Record<string, string> = {
  pdf: 'application/pdf',
  txt: 'text/plain',
  md: 'text/markdown',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
};
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

async function json<T>(request: Request): Promise<T | null> {
  try {
    return (await request.json()) as T;
  } catch {
    return null;
  }
}

function validGenOptions(o: GenerationOptions | undefined): string | null {
  if (!o) return 'options required for intent=generate';
  if (!Number.isInteger(o.count) || o.count < 1 || o.count > 50) return 'count must be 1–50';
  if (!Array.isArray(o.types) || !o.types.length || o.types.some((t) => !['mcq', 'tf', 'open'].includes(t))) return 'types invalid';
  if (!['easy', 'medium', 'hard'].includes(o.difficulty)) return 'difficulty invalid';
  if (!['hu', 'en'].includes(o.exam_language)) return 'exam_language invalid';
  if (!['fast', 'thorough'].includes(o.mode)) return 'mode invalid';
  return null;
}

export function makeHandlers(base: string): HttpHandler[] {
  const u = (p: string) => `${base}${p}`;

  return [
    // ------------------------------------------------------------ auth
    http.post(u('/auth/register'), async ({ request }) => {
      await LATENCY();
      const b = await json<{ email?: string; password?: string; language?: Language; confirm_age_16?: boolean; accepted_terms_version?: string }>(request);
      const fields: Record<string, string> = {};
      if (!b?.email || !EMAIL_RE.test(b.email)) fields.email = 'invalid';
      if (!b?.password || b.password.length < MIN_PASSWORD_LENGTH) fields.password = 'too_short';
      if (b?.confirm_age_16 !== true) fields.confirm_age_16 = 'required';
      if (!b?.accepted_terms_version) fields.accepted_terms_version = 'required';
      if (Object.keys(fields).length) return err(400, 'VALIDATION_FAILED', 'Invalid registration', { fields });
      const db = getDb();
      const email = b!.email!.toLowerCase();
      // Same 202 whether or not the address exists (no account enumeration).
      if (!db.users.some((x) => x.email === email)) {
        const user: MockUser = { id: nextId('usr'), email, password: b!.password!, language: b!.language ?? 'hu', verified: false, created_at: now() };
        db.users.push(user);
        const token = nextId('verify');
        db.verifyTokens[token] = user.id;
        mail(email, 'verify', `/verify-email?token=${token}`);
        persist();
      }
      return HttpResponse.json({ status: 'accepted' }, { status: 202 });
    }),

    http.post(u('/auth/verify'), async ({ request }) => {
      await LATENCY();
      const b = await json<{ token?: string }>(request);
      const db = getDb();
      const userId = b?.token ? db.verifyTokens[b.token] : undefined;
      const user = db.users.find((x) => x.id === userId);
      if (!user) return err(400, 'VALIDATION_FAILED', 'Invalid or expired token', { fields: { token: 'invalid' } });
      user.verified = true;
      delete db.verifyTokens[b!.token!];
      persist();
      return new HttpResponse(null, { status: 204 });
    }),

    http.post(u('/auth/login'), async ({ request }) => {
      await LATENCY();
      const b = await json<{ email?: string; password?: string }>(request);
      const db = getDb();
      const user = db.users.find((x) => x.email === b?.email?.toLowerCase());
      if (!user || user.password !== b?.password) return err(401, 'INVALID_CREDENTIALS');
      if (!user.verified) return err(403, 'EMAIL_NOT_VERIFIED');
      db.refreshUserId = user.id;
      persist();
      return HttpResponse.json(sessionFor(user));
    }),

    http.post(u('/auth/refresh'), async () => {
      await LATENCY();
      const db = getDb();
      const user = db.users.find((x) => x.id === db.refreshUserId);
      if (!user) return err(401, 'AUTH_REQUIRED', 'No refresh session');
      return HttpResponse.json(sessionFor(user));
    }),

    http.post(u('/auth/logout'), async () => {
      getDb().refreshUserId = null;
      persist();
      return new HttpResponse(null, { status: 204 });
    }),

    http.post(u('/auth/password/forgot'), async ({ request }) => {
      await LATENCY();
      const b = await json<{ email?: string }>(request);
      const db = getDb();
      const user = db.users.find((x) => x.email === b?.email?.toLowerCase());
      if (user) {
        const token = nextId('reset');
        db.resetTokens[token] = user.id;
        mail(user.email, 'reset', `/reset-password?token=${token}`);
        persist();
      }
      return HttpResponse.json({ status: 'accepted' }, { status: 202 });
    }),

    http.post(u('/auth/password/reset'), async ({ request }) => {
      await LATENCY();
      const b = await json<{ token?: string; new_password?: string }>(request);
      const db = getDb();
      const user = db.users.find((x) => x.id === (b?.token ? db.resetTokens[b.token] : undefined));
      if (!user) return err(400, 'VALIDATION_FAILED', 'Invalid or expired token', { fields: { token: 'invalid' } });
      if (!b?.new_password || b.new_password.length < MIN_PASSWORD_LENGTH)
        return err(400, 'VALIDATION_FAILED', 'Password too short', { fields: { new_password: 'too_short' } });
      user.password = b.new_password;
      user.verified = true;
      delete db.resetTokens[b.token!];
      if (db.refreshUserId === user.id) db.refreshUserId = null; // all sessions revoked
      persist();
      return new HttpResponse(null, { status: 204 });
    }),

    // ------------------------------------------------------------ me
    http.get(u('/me'), async ({ request }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const db = getDb();
      return HttpResponse.json({
        id: a.user.id,
        email: a.user.email,
        language: a.user.language,
        created_at: a.user.created_at,
        usage: {
          topics: db.topics.filter((t) => t.user_id === a.user.id).length,
          saved_tests: db.tests.filter((t) => t.user_id === a.user.id && t.saved).length,
        },
        limits: DEFAULT_LIMITS,
      });
    }),
    http.patch(u('/me'), async ({ request }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const b = await json<{ language?: Language }>(request);
      if (b?.language && !['hu', 'en'].includes(b.language)) return err(400, 'VALIDATION_FAILED');
      if (b?.language) a.user.language = b.language;
      persist();
      const db = getDb();
      return HttpResponse.json({
        id: a.user.id,
        email: a.user.email,
        language: a.user.language,
        created_at: a.user.created_at,
        usage: {
          topics: db.topics.filter((t) => t.user_id === a.user.id).length,
          saved_tests: db.tests.filter((t) => t.user_id === a.user.id && t.saved).length,
        },
        limits: DEFAULT_LIMITS,
      });
    }),
    http.delete(u('/me'), async ({ request }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const b = await json<{ password?: string }>(request);
      if (b?.password !== a.user.password) return err(401, 'INVALID_CREDENTIALS');
      const job = createJob({ type: 'delete_account', topic_id: null, user_id: a.user.id, payload: {} });
      return HttpResponse.json({ job_id: job.id }, { status: 202 });
    }),
    http.post(u('/me/export'), async ({ request }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      if (getDb().jobs.some((j) => j.user_id === a.user.id && j.type === 'export_account' && (j.status === 'queued' || j.status === 'running')))
        return err(409, 'JOB_IN_PROGRESS');
      const job = createJob({ type: 'export_account', topic_id: null, user_id: a.user.id, payload: {} });
      return HttpResponse.json({ job_id: job.id }, { status: 202 });
    }),
    http.get(u('/__mock/exports/:jobId'), ({ request, params }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const job = getDb().jobs.find((j) => j.id === params.jobId && j.user_id === a.user.id);
      const data = job && getDb().exports[job.id];
      if (!data) return err(404, 'JOB_NOT_FOUND');
      return new HttpResponse(JSON.stringify(data, null, 2), {
        headers: { 'Content-Type': 'application/json', 'Content-Disposition': 'attachment; filename="mimir-export.json"' },
      });
    }),

    // ------------------------------------------------------------ topics
    http.get(u('/topics'), async ({ request }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const url = new URL(request.url);
      const q = (url.searchParams.get('q') ?? '').trim().toLowerCase();
      const limit = Math.min(100, Number(url.searchParams.get('limit') ?? 50) || 50);
      const offset = Number(url.searchParams.get('cursor') ?? 0) || 0;
      const all = getDb()
        .topics.filter((t) => t.user_id === a.user.id)
        .filter((t) => !q || t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q))
        .sort((x, y) => y.last_activity_at.localeCompare(x.last_activity_at));
      const page = all.slice(offset, offset + limit);
      return HttpResponse.json({
        items: page.map(publicTopic),
        next_cursor: offset + limit < all.length ? String(offset + limit) : null,
        total: all.length,
      });
    }),
    http.post(u('/topics'), async ({ request }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const b = await json<TopicInput>(request);
      const name = b?.name?.trim() ?? '';
      const description = b?.description?.trim() ?? '';
      if (!name || name.length > 80) return err(400, 'VALIDATION_FAILED', 'Invalid name', { fields: { name: name ? 'too_long' : 'required' } });
      if (description.length > 500) return err(400, 'VALIDATION_FAILED', 'Description too long', { fields: { description: 'too_long' } });
      const db = getDb();
      if (db.topics.filter((t) => t.user_id === a.user.id).length >= DEFAULT_LIMITS.max_topics) return err(409, 'TOPIC_QUOTA_EXCEEDED');
      const t = now();
      const topic: MockTopic = {
        id: nextId('top'),
        user_id: a.user.id,
        name,
        description,
        status: 'active',
        file_count: 0,
        total_bytes: 0,
        saved_test_count: 0,
        created_at: t,
        updated_at: t,
        last_activity_at: t,
        expires_at: addDays(t, INACTIVITY_DAYS),
      };
      db.topics.push(topic);
      persist();
      return HttpResponse.json(publicTopic(topic), { status: 201 });
    }),
    http.get(u('/topics/:topicId'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      recount(o.topic);
      return HttpResponse.json(publicTopic(o.topic));
    }),
    http.patch(u('/topics/:topicId'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      if (o.topic.status === 'deleting') return err(409, 'TOPIC_DELETING');
      const b = (await json<TopicPatch>(request)) ?? {};
      if (b.name !== undefined) {
        const name = b.name.trim();
        if (!name || name.length > 80) return err(400, 'VALIDATION_FAILED', 'Invalid name', { fields: { name: name ? 'too_long' : 'required' } });
        o.topic.name = name;
      }
      if (b.description !== undefined) {
        if (b.description.length > 500) return err(400, 'VALIDATION_FAILED', 'Description too long', { fields: { description: 'too_long' } });
        o.topic.description = b.description.trim();
      }
      touchTopic(o.topic);
      persist();
      return HttpResponse.json(publicTopic(o.topic));
    }),
    http.delete(u('/topics/:topicId'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      o.topic.status = 'deleting';
      const job = createJob({ type: 'delete_topic', topic_id: o.topic.id, user_id: a.user.id, payload: {} });
      return HttpResponse.json({ job_id: job.id }, { status: 202 });
    }),

    // ------------------------------------------------------------ files
    http.get(u('/topics/:topicId/files'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const items = getDb()
        .files.filter((f) => f.topic_id === o.topic.id)
        .sort((x, y) => y.created_at.localeCompare(x.created_at))
        .map(publicFile);
      return HttpResponse.json({ items });
    }),
    http.post(u('/topics/:topicId/files'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      if (o.topic.status === 'deleting') return err(409, 'TOPIC_DELETING');
      let form: FormData;
      try {
        form = await request.formData();
      } catch {
        return err(400, 'VALIDATION_FAILED', 'Expected multipart/form-data');
      }
      if (form.get('consent') !== 'true') return err(400, 'CONSENT_REQUIRED');
      const files = form.getAll('files[]').filter((f): f is File => typeof f !== 'string');
      if (!files.length) return err(400, 'VALIDATION_FAILED', 'No files', { fields: { 'files[]': 'required' } });
      if (files.length > DEFAULT_LIMITS.max_files_per_upload) return err(400, 'VALIDATION_FAILED', 'Too many files', { fields: { 'files[]': 'too_many' } });
      const db = getDb();
      const existing = db.files.filter((f) => f.topic_id === o.topic.id);
      if (existing.length + files.length > DEFAULT_LIMITS.max_files_per_topic) return err(409, 'TOPIC_QUOTA_EXCEEDED', 'Too many files in topic', { limit: DEFAULT_LIMITS.max_files_per_topic });
      for (const f of files) {
        if (!DEFAULT_LIMITS.allowed_types.includes(extOf(f.name))) return err(415, 'UNSUPPORTED_FILE_TYPE', f.name, { filename: f.name });
        if (f.size > DEFAULT_LIMITS.max_file_bytes) return err(413, 'FILE_TOO_LARGE', f.name, { filename: f.name, limit: DEFAULT_LIMITS.max_file_bytes });
      }
      const total = existing.reduce((s, f) => s + f.size_bytes, 0) + files.reduce((s, f) => s + f.size, 0);
      if (total > DEFAULT_LIMITS.max_topic_bytes) return err(413, 'TOPIC_STORAGE_EXCEEDED', 'Topic storage full', { limit: DEFAULT_LIMITS.max_topic_bytes });

      const created: MockFile[] = [];
      for (const f of files) {
        const ext = extOf(f.name);
        const text = ext === 'txt' || ext === 'md' ? (await f.text()).slice(0, 60_000) : '';
        const mf: MockFile = {
          id: nextId('fil'),
          topic_id: o.topic.id,
          user_id: a.user.id,
          filename: f.name,
          mime: MIME[ext] ?? (f.type || 'application/octet-stream'),
          size_bytes: f.size,
          status: 'queued',
          error_code: null,
          chunk_count: 0,
          page_count: null,
          created_at: now(),
          text,
        };
        db.files.push(mf);
        created.push(mf);
      }
      recount(o.topic);
      touchTopic(o.topic);
      const jobs = created.map((f) => createJob({ type: 'ingest_file', topic_id: o.topic.id, user_id: a.user.id, payload: { file_id: f.id } }));
      return HttpResponse.json({ files: created.map(publicFile), job_ids: jobs.map((j) => j.id) }, { status: 202 });
    }),
    http.post(u('/topics/:topicId/files/:fileId/retry'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const f = getDb().files.find((x) => x.id === params.fileId && x.topic_id === o.topic.id);
      if (!f) return err(404, 'FILE_NOT_FOUND');
      if (f.status !== 'failed') return err(409, 'JOB_IN_PROGRESS');
      f.status = 'queued';
      f.error_code = null;
      // Demo: a retried "fail" file succeeds the second time.
      f.filename = f.filename.replace(/fail/gi, 'retry');
      const job = createJob({ type: 'ingest_file', topic_id: o.topic.id, user_id: a.user.id, payload: { file_id: f.id } });
      return HttpResponse.json({ job_id: job.id }, { status: 202 });
    }),
    http.delete(u('/topics/:topicId/files/:fileId'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const db = getDb();
      if (!db.files.some((x) => x.id === params.fileId && x.topic_id === o.topic.id)) return err(404, 'FILE_NOT_FOUND');
      db.files = db.files.filter((x) => x.id !== params.fileId);
      recount(o.topic);
      touchTopic(o.topic);
      persist();
      return new HttpResponse(null, { status: 204 });
    }),

    // ------------------------------------------------------------ sessions & messages
    http.get(u('/topics/:topicId/sessions'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const items = getDb()
        .sessions.filter((s) => s.topic_id === o.topic.id)
        .sort((x, y) => y.updated_at.localeCompare(x.updated_at))
        .map(publicSession);
      return HttpResponse.json({ items });
    }),
    http.post(u('/topics/:topicId/sessions'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const b = (await json<{ title?: string }>(request)) ?? {};
      const t = now();
      const s = {
        id: nextId('ses'),
        topic_id: o.topic.id,
        user_id: a.user.id,
        title: b.title?.trim().slice(0, 120) || (a.user.language === 'en' ? 'New chat' : 'Új beszélgetés'),
        message_count: 0,
        created_at: t,
        updated_at: t,
      };
      getDb().sessions.push(s);
      touchTopic(o.topic);
      persist();
      return HttpResponse.json(publicSession(s), { status: 201 });
    }),
    http.patch(u('/topics/:topicId/sessions/:sessionId'), async ({ request, params }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const s = getDb().sessions.find((x) => x.id === params.sessionId && x.topic_id === o.topic.id);
      if (!s) return err(404, 'SESSION_NOT_FOUND');
      const b = await json<{ title?: string }>(request);
      const title = b?.title?.trim() ?? '';
      if (!title || title.length > 120) return err(400, 'VALIDATION_FAILED', 'Invalid title', { fields: { title: 'invalid' } });
      s.title = title;
      s.updated_at = now();
      persist();
      return HttpResponse.json(publicSession(s));
    }),
    http.delete(u('/topics/:topicId/sessions/:sessionId'), async ({ request, params }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const db = getDb();
      if (!db.sessions.some((x) => x.id === params.sessionId && x.topic_id === o.topic.id)) return err(404, 'SESSION_NOT_FOUND');
      db.sessions = db.sessions.filter((x) => x.id !== params.sessionId);
      db.messages = db.messages.filter((m) => m.session_id !== params.sessionId);
      // Unsaved tests of the session go with it; saved ones stay (opt-in retention).
      db.tests = db.tests.filter((t) => t.session_id !== params.sessionId || t.saved);
      persist();
      return new HttpResponse(null, { status: 204 });
    }),
    http.get(u('/topics/:topicId/sessions/:sessionId/messages'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      if (!getDb().sessions.some((x) => x.id === params.sessionId && x.topic_id === o.topic.id)) return err(404, 'SESSION_NOT_FOUND');
      const url = new URL(request.url);
      const limit = Math.min(100, Number(url.searchParams.get('limit') ?? 50) || 50);
      const offset = Number(url.searchParams.get('cursor') ?? 0) || 0;
      const all = getDb()
        .messages.filter((m) => m.session_id === params.sessionId)
        .sort((x, y) => y.created_at.localeCompare(x.created_at) || y.id.localeCompare(x.id));
      return HttpResponse.json({
        items: all.slice(offset, offset + limit).map(publicMessage),
        next_cursor: offset + limit < all.length ? String(offset + limit) : null,
      });
    }),
    http.post(u('/topics/:topicId/sessions/:sessionId/messages'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      if (o.topic.status === 'deleting') return err(409, 'TOPIC_DELETING');
      const db = getDb();
      const session = db.sessions.find((x) => x.id === params.sessionId && x.topic_id === o.topic.id);
      if (!session) return err(404, 'SESSION_NOT_FOUND');
      const b = await json<MessageInput>(request);
      if (!b || (b.intent !== 'generate' && b.intent !== 'ask')) return err(400, 'VALIDATION_FAILED', 'intent required');
      if ((b.content ?? '').length > 4000) return err(400, 'VALIDATION_FAILED', 'Message too long', { fields: { content: 'too_long' } });
      if (b.intent === 'ask' && !b.content?.trim()) return err(400, 'VALIDATION_FAILED', 'Empty question', { fields: { content: 'required' } });
      if (b.intent === 'generate') {
        const problem = validGenOptions(b.options);
        if (problem) return err(400, 'VALIDATION_FAILED', problem, { fields: { options: problem } });
      }
      const ready = db.files.filter((f) => f.topic_id === o.topic.id && f.status === 'ready' && (!b.options?.file_ids?.length || b.options.file_ids.includes(f.id)));
      if (!ready.length) return err(409, 'FILE_NOT_READY', 'No processed documents in this topic yet');
      const active = db.jobs.filter((j) => j.user_id === a.user.id && ['generate_test', 'answer_question'].includes(j.type) && (j.status === 'queued' || j.status === 'running'));
      if (active.length >= 3) return err(429, 'TOO_MANY_JOBS');

      const msg = {
        id: nextId('msg'),
        session_id: session.id,
        topic_id: o.topic.id,
        role: 'user' as const,
        content: b.content ?? '',
        job_id: null as string | null,
        test_id: null,
        options: b.intent === 'generate' ? b.options : undefined,
        created_at: now(),
      };
      const job = createJob({
        type: b.intent === 'generate' ? 'generate_test' : 'answer_question',
        topic_id: o.topic.id,
        user_id: a.user.id,
        payload: { session_id: session.id, content: msg.content, options: b.options, language: b.options?.exam_language ?? a.user.language },
      });
      msg.job_id = job.id;
      db.messages.push(msg);
      session.message_count += 1;
      session.updated_at = msg.created_at;
      if (session.message_count === 1 && msg.content.trim()) session.title = msg.content.trim().slice(0, 60);
      touchTopic(o.topic);
      persist();
      return HttpResponse.json({ message: publicMessage(msg), job_id: job.id }, { status: 202 });
    }),

    // ------------------------------------------------------------ tests
    http.get(u('/topics/:topicId/tests'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const saved = new URL(request.url).searchParams.get('saved');
      const items = getDb()
        .tests.filter((t) => t.topic_id === o.topic.id && (saved === null || String(t.saved) === saved))
        .sort((x, y) => y.created_at.localeCompare(x.created_at))
        .map(({ exam: _e, user_id: _u, ...s }) => s);
      return HttpResponse.json({ items });
    }),
    http.get(u('/topics/:topicId/tests/:testId'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const t = getDb().tests.find((x) => x.id === params.testId && x.topic_id === o.topic.id);
      if (!t) return err(404, 'TEST_NOT_FOUND');
      return HttpResponse.json(publicTest(t));
    }),
    http.put(u('/topics/:topicId/tests/:testId'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const t = getDb().tests.find((x) => x.id === params.testId && x.topic_id === o.topic.id);
      if (!t) return err(404, 'TEST_NOT_FOUND');
      const b = await json<{ exam?: typeof t.exam }>(request);
      const exam = b?.exam;
      if (!exam || typeof exam.title !== 'string' || !Array.isArray(exam.questions) || !exam.questions.length)
        return err(400, 'VALIDATION_FAILED', 'Invalid exam');
      const bad = exam.questions.findIndex((q) => !q.text?.trim() || (q.type !== 'open' && !q.answers.some((x) => x.is_correct)));
      if (bad >= 0) return err(400, 'VALIDATION_FAILED', 'Invalid question', { fields: { [`questions.${bad}`]: 'invalid' } });
      t.exam = exam;
      t.title = exam.title;
      t.question_count = exam.questions.length;
      t.updated_at = now();
      touchTopic(o.topic);
      persist();
      return HttpResponse.json(publicTest(t));
    }),
    http.post(u('/topics/:topicId/tests/:testId/save'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const t = getDb().tests.find((x) => x.id === params.testId && x.topic_id === o.topic.id);
      if (!t) return err(404, 'TEST_NOT_FOUND');
      t.saved = true;
      t.updated_at = now();
      recount(o.topic);
      persist();
      return HttpResponse.json(publicTest(t));
    }),
    http.delete(u('/topics/:topicId/tests/:testId'), async ({ request, params }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const db = getDb();
      if (!db.tests.some((x) => x.id === params.testId && x.topic_id === o.topic.id)) return err(404, 'TEST_NOT_FOUND');
      db.tests = db.tests.filter((x) => x.id !== params.testId);
      recount(o.topic);
      persist();
      return new HttpResponse(null, { status: 204 });
    }),
    http.post(u('/topics/:topicId/tests/:testId/questions/:questionId/regenerate'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const db = getDb();
      const t = db.tests.find((x) => x.id === params.testId && x.topic_id === o.topic.id);
      if (!t || !t.exam.questions.some((q) => q.id === params.questionId)) return err(404, 'TEST_NOT_FOUND');
      if (db.jobs.some((j) => j.type === 'regenerate_question' && j.payload.question_id === params.questionId && (j.status === 'queued' || j.status === 'running')))
        return err(409, 'JOB_IN_PROGRESS');
      const lang: Language = /[őűáé]/i.test(t.exam.questions[0]?.text ?? '') ? 'hu' : a.user.language;
      const job = createJob({
        type: 'regenerate_question',
        topic_id: o.topic.id,
        user_id: a.user.id,
        payload: { test_id: t.id, question_id: params.questionId, language: lang },
      });
      return HttpResponse.json({ job_id: job.id }, { status: 202 });
    }),
    http.post(u('/topics/:topicId/tests/:testId/export'), async ({ request, params }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const t = getDb().tests.find((x) => x.id === params.testId && x.topic_id === o.topic.id);
      if (!t) return err(404, 'TEST_NOT_FOUND');
      const b = await json<ExportRequest>(request);
      if (!b || !['pdf', 'pdf_with_key', 'moodle_xml', 'gift', 'json'].includes(b.format)) return err(400, 'VALIDATION_FAILED', 'format');
      const out = exportExam(t.exam, b);
      const name = `${t.title.replace(/[^\p{L}\p{N}_-]+/gu, '_').slice(0, 60)}.${out.ext}`;
      return new HttpResponse(out.body, {
        headers: { 'Content-Type': out.type, 'Content-Disposition': `attachment; filename*=UTF-8''${encodeURIComponent(name)}` },
      });
    }),
    http.get(u('/tests'), async ({ request }) => {
      await LATENCY();
      const a = auth(request);
      if ('res' in a) return a.res;
      const db = getDb();
      const groups = db.topics
        .filter((t) => t.user_id === a.user.id)
        .map((topic) => ({
          topic: { id: topic.id, name: topic.name },
          tests: db.tests
            .filter((t) => t.topic_id === topic.id && t.saved)
            .sort((x, y) => y.updated_at.localeCompare(x.updated_at))
            .map(({ exam: _e, user_id: _u, ...s }) => s),
        }))
        .filter((g) => g.tests.length);
      return HttpResponse.json({ groups });
    }),

    // ------------------------------------------------------------ jobs
    http.get(u('/jobs'), async ({ request }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const active = new URL(request.url).searchParams.get('active') === 'true';
      const items = getDb()
        .jobs.filter((j) => j.user_id === a.user.id && (!active || j.status === 'queued' || j.status === 'running'))
        .slice(-50)
        .map(publicJob);
      return HttpResponse.json({ items });
    }),
    http.get(u('/jobs/:jobId'), async ({ request, params }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const j = getDb().jobs.find((x) => x.id === params.jobId && x.user_id === a.user.id);
      if (!j) return err(404, 'JOB_NOT_FOUND');
      return HttpResponse.json(publicJob(j));
    }),
    http.post(u('/jobs/:jobId/cancel'), async ({ request, params }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const j = getDb().jobs.find((x) => x.id === params.jobId && x.user_id === a.user.id);
      if (!j) return err(404, 'JOB_NOT_FOUND');
      if (j.status !== 'queued' && j.status !== 'running') return err(409, 'JOB_IN_PROGRESS', 'Job already finished');
      j.status = 'cancelled';
      j.stage = null;
      j.queue_position = null;
      if (j.type === 'ingest_file') {
        const f = getDb().files.find((x) => x.id === j.payload.file_id);
        if (f) {
          f.status = 'failed';
          f.error_code = 'INTERNAL';
        }
      }
      persist();
      return HttpResponse.json(publicJob(j), { status: 202 });
    }),

    // ------------------------------------------------------------ SSE
    http.get(u('/topics/:topicId/events'), ({ request, params }) => {
      const a = auth(request);
      if ('res' in a) return a.res;
      const o = ownTopic(a.user, String(params.topicId));
      if ('res' in o) return o.res;
      const topicId = o.topic.id;
      const last = Number(request.headers.get('last-event-id') ?? 0) || 0;
      const enc = new TextEncoder();
      let off: (() => void) | undefined;
      let beat: ReturnType<typeof setInterval> | undefined;
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          const send = (e: { id: number; name: string; data: unknown }) => {
            try {
              controller.enqueue(enc.encode(`id: ${e.id}\nevent: ${e.name}\ndata: ${JSON.stringify(e.data)}\n\n`));
            } catch {
              off?.();
            }
          };
          controller.enqueue(enc.encode(`retry: 3000\n\n`));
          if (last) eventsSince(topicId, last).forEach(send);
          off = subscribe(topicId, send);
          beat = setInterval(() => {
            try {
              controller.enqueue(enc.encode(`event: heartbeat\ndata: {}\n\n`));
            } catch {
              if (beat) clearInterval(beat);
            }
          }, 15_000);
          request.signal?.addEventListener('abort', () => {
            off?.();
            if (beat) clearInterval(beat);
            try {
              controller.close();
            } catch {
              /* already closed */
            }
          });
        },
        cancel() {
          off?.();
          if (beat) clearInterval(beat);
        },
      });
      return new HttpResponse(stream, {
        headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' },
      });
    }),
  ];
}
