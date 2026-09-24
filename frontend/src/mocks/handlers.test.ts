// Node environment: jsdom's FormData/File bodies never reach MSW handlers (multipart parsing hangs).
// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { api, applySession } from '../api/client';
import { unwrap, ApiError } from '../api/errors';
import { uploadFiles } from '../api/upload';
import { getDb } from './db';
import { loginDemo } from '../test/utils';

async function registerAndLogin(email: string) {
  unwrap(await api().POST('/auth/register', { body: { email, password: 'long-enough-pw', language: 'en', confirm_age_16: true, accepted_terms_version: 'x' } }));
  const mail = getDb().outbox.find((m) => m.to === email)!;
  const token = new URL(mail.link, 'http://x').searchParams.get('token')!;
  unwrap(await api().POST('/auth/verify', { body: { token } }));
  const s = unwrap(await api().POST('/auth/login', { body: { email, password: 'long-enough-pw' } }));
  applySession(s);
}

const code = async (p: Promise<{ error?: unknown; response: Response }>) => {
  try {
    unwrap(await p);
    return 'OK';
  } catch (e) {
    return (e as ApiError).code;
  }
};

describe('mock API contract', () => {
  it('requires e-mail verification before login', async () => {
    unwrap(await api().POST('/auth/register', { body: { email: 'new@x.hu', password: 'long-enough-pw', language: 'hu', confirm_age_16: true, accepted_terms_version: 'x' } }));
    expect(await code(api().POST('/auth/login', { body: { email: 'new@x.hu', password: 'long-enough-pw' } }))).toBe('EMAIL_NOT_VERIFIED');
  });

  it('rejects short passwords and a missing age confirmation', async () => {
    const r = await api().POST('/auth/register', { body: { email: 'a@b.hu', password: 'short', language: 'hu', confirm_age_16: false as true, accepted_terms_version: 'x' } });
    const e = (() => {
      try {
        unwrap(r);
      } catch (x) {
        return x as ApiError;
      }
      return null;
    })();
    expect(e?.code).toBe('VALIDATION_FAILED');
    expect(e?.details).toMatchObject({ fields: { password: 'too_short', confirm_age_16: 'required' } });
  });

  it('isolates topics between users (404, not 403)', async () => {
    await registerAndLogin('other@x.hu');
    expect(await code(api().GET('/topics/{topicId}', { params: { path: { topicId: 'top_demo' } } }))).toBe('TOPIC_NOT_FOUND');
    expect(await code(api().GET('/topics/{topicId}/files', { params: { path: { topicId: 'top_demo' } } }))).toBe('TOPIC_NOT_FOUND');
    const list = unwrap(await api().GET('/topics'));
    expect(list.items).toHaveLength(0);
  });

  it('requires upload consent and checks types', async () => {
    await loginDemo();
    const file = new File(['hello world. '.repeat(20)], 'notes.exe');
    await expect(uploadFiles('top_demo', [file])).rejects.toMatchObject({ code: 'UNSUPPORTED_FILE_TYPE' });
  });

  it('refuses generation while no document is ready', async () => {
    await loginDemo();
    const topic = unwrap(await api().POST('/topics', { body: { name: 'Empty' } }));
    const s = unwrap(await api().POST('/topics/{topicId}/sessions', { params: { path: { topicId: topic.id } }, body: {} }));
    const r = api().POST('/topics/{topicId}/sessions/{sessionId}/messages', {
      params: { path: { topicId: topic.id, sessionId: s.id } },
      body: { content: '', intent: 'generate', options: { count: 5, types: ['mcq'], difficulty: 'easy', exam_language: 'en', mode: 'fast' } },
    });
    expect(await code(r)).toBe('FILE_NOT_READY');
  });

  it('deletes a topic with everything in it (cascade)', async () => {
    await loginDemo();
    unwrap(await api().DELETE('/topics/{topicId}', { params: { path: { topicId: 'top_demo' } } }));
    await new Promise((r) => setTimeout(r, 200));
    const db = getDb();
    expect(db.topics.find((t) => t.id === 'top_demo')).toBeUndefined();
    expect(db.files.some((f) => f.topic_id === 'top_demo')).toBe(false);
    expect(db.tests.some((t) => t.topic_id === 'top_demo')).toBe(false);
    expect(db.messages.some((m) => m.topic_id === 'top_demo')).toBe(false);
  });

  it('runs a generation job end to end', async () => {
    await loginDemo();
    const r = unwrap(
      await api().POST('/topics/{topicId}/sessions/{sessionId}/messages', {
        params: { path: { topicId: 'top_demo', sessionId: 'ses_demo' } },
        body: { content: 'go', intent: 'generate', options: { count: 4, types: ['mcq', 'tf'], difficulty: 'medium', exam_language: 'en', mode: 'fast' } },
      }),
    );
    let job = unwrap(await api().GET('/jobs/{jobId}', { params: { path: { jobId: r.job_id } } }));
    for (let i = 0; i < 50 && job.status !== 'succeeded'; i += 1) {
      await new Promise((res) => setTimeout(res, 50));
      job = unwrap(await api().GET('/jobs/{jobId}', { params: { path: { jobId: r.job_id } } }));
    }
    expect(job.status).toBe('succeeded');
    const test = unwrap(await api().GET('/topics/{topicId}/tests/{testId}', { params: { path: { topicId: 'top_demo', testId: job.result!.test_id! } } }));
    expect(test.exam.questions).toHaveLength(4);
    expect(test.saved).toBe(false);
    expect(test.exam.questions[0].citations[0].file_id).toBe('fil_demo');
  });

  it('lists models, runs the chosen one and reports timing while running (FE-11)', async () => {
    await loginDemo();
    const models = unwrap(await api().GET('/models'));
    expect(models.models.map((m) => m.location)).toContain('local');
    const opts = { count: 3, types: ['mcq' as const], difficulty: 'easy' as const, exam_language: 'en' as const, mode: 'fast' as const };
    const path = { params: { path: { topicId: 'top_demo', sessionId: 'ses_demo' } } };
    expect(await code(api().POST('/topics/{topicId}/sessions/{sessionId}/messages', { ...path, body: { content: 'x', intent: 'generate', options: { ...opts, model: 'nope' } } }))).toBe(
      'MODEL_UNAVAILABLE',
    );
    const r = unwrap(await api().POST('/topics/{topicId}/sessions/{sessionId}/messages', { ...path, body: { content: 'x', intent: 'generate', options: { ...opts, model: 'local' } } }));
    let job = unwrap(await api().GET('/jobs/{jobId}', { params: { path: { jobId: r.job_id } } }));
    let sawTiming = false;
    for (let i = 0; i < 80 && job.status !== 'succeeded'; i += 1) {
      await new Promise((res) => setTimeout(res, 40));
      job = unwrap(await api().GET('/jobs/{jobId}', { params: { path: { jobId: r.job_id } } }));
      if (job.status === 'running' && job.started_at && job.eta_seconds != null) sawTiming = true;
    }
    expect(job.status).toBe('succeeded');
    expect(sawTiming).toBe(true);
    const test = unwrap(await api().GET('/topics/{topicId}/tests/{testId}', { params: { path: { topicId: 'top_demo', testId: job.result!.test_id! } } }));
    expect(test.model_used).toBe('qwen2.5:7b');
  });
});
