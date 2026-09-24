/**
 * Simulated job workers + topic event bus for the mock API. Mirrors the real pipeline closely enough for the
 * UI: ingestion stages, one "GPU" generation queue with queue positions, cancellation, and SSE events.
 *
 * Demo switches: a file whose name contains "fail" fails ingestion (NO_TEXT_EXTRACTED); a chat message that
 * contains "#fail" makes generation fail (LLM_UNAVAILABLE).
 */
import type { ErrorCode, GenerationOptions, Language } from '../api/types';
import {
  getDb,
  nextId,
  now,
  persist,
  publicFile,
  publicJob,
  publicMessage,
  recount,
  touchTopic,
  type MockJob,
  type MockMessage,
  type MockTest,
} from './db';
import { answerQuestion, generateExam, regenerateQuestion } from './generator';
import { MOCK_MODELS } from './constants';

/** Speeds the simulation up in unit/E2E tests. */
let SPEED = 1;
export const setMockSpeed = (s: number) => {
  SPEED = s;
};
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms / SPEED));

// ------------------------------------------------------------------ events
type Sub = (e: { id: number; name: string; data: unknown }) => void;
const subs = new Map<string, Set<Sub>>();

export function subscribe(topicId: string, fn: Sub): () => void {
  if (!subs.has(topicId)) subs.set(topicId, new Set());
  subs.get(topicId)!.add(fn);
  return () => subs.get(topicId)?.delete(fn);
}

export function emit(topicId: string, name: string, data: unknown): void {
  const db = getDb();
  db.seq += 1;
  const ev = { id: db.seq, topic_id: topicId, name, data };
  db.events.push(ev);
  persist();
  subs.get(topicId)?.forEach((fn) => fn(ev));
}

export const eventsSince = (topicId: string, lastId: number) =>
  getDb().events.filter((e) => e.topic_id === topicId && e.id > lastId);

// ------------------------------------------------------------------ jobs
const pushJob = (job: MockJob) => {
  persist();
  if (job.topic_id) emit(job.topic_id, job.status === 'succeeded' ? 'job.succeeded' : job.status === 'failed' ? 'job.failed' : 'job.progress', { job: publicJob(job) });
};

const cancelled = (job: MockJob) => getDb().jobs.find((j) => j.id === job.id)?.status === 'cancelled';

function fail(job: MockJob, code: ErrorCode) {
  job.status = 'failed';
  job.error_code = code;
  job.stage = null;
  pushJob(job);
}

export function createJob(partial: Pick<MockJob, 'type' | 'topic_id' | 'user_id' | 'payload'>): MockJob {
  const job: MockJob = {
    id: nextId('job'),
    status: 'queued',
    stage: null,
    progress: 0,
    queue_position: null,
    error_code: null,
    result: null,
    created_at: now(),
    ...partial,
  };
  getDb().jobs.push(job);
  persist();
  schedule(job);
  return job;
}

// One simulated GPU: generation-type jobs run one at a time.
const gpuQueue: MockJob[] = [];
let gpuBusy = false;
const GPU_TYPES = new Set(['generate_test', 'answer_question', 'regenerate_question']);

function refreshQueuePositions() {
  gpuQueue.forEach((j, i) => {
    if (j.queue_position !== i + 1) {
      j.queue_position = i + 1;
      pushJob(j);
    }
  });
}

async function drainGpu() {
  if (gpuBusy) return;
  gpuBusy = true;
  while (gpuQueue.length) {
    const job = gpuQueue.shift()!;
    refreshQueuePositions();
    if (cancelled(job)) continue;
    job.queue_position = null;
    await run(job);
  }
  gpuBusy = false;
}

function schedule(job: MockJob) {
  if (GPU_TYPES.has(job.type)) {
    gpuQueue.push(job);
    refreshQueuePositions();
    void drainGpu();
  } else {
    void run(job);
  }
}

/** Re-schedules jobs that were in flight when the page was reloaded. */
export function resumeJobs(): void {
  getDb()
    .jobs.filter((j) => j.status === 'queued' || j.status === 'running')
    .forEach((j) => {
      j.status = 'queued';
      j.progress = 0;
      schedule(j);
    });
}

/** Remaining time from the pace so far (the real backend blends this with its history of job durations). */
function etaSeconds(job: MockJob): number | null {
  if (!job.started_at || job.progress < 0.05) return null;
  const elapsed = (Date.now() - Date.parse(job.started_at)) / 1000;
  return Math.max(1, Math.round((elapsed * (1 - job.progress)) / job.progress));
}

async function step(job: MockJob, stage: string, progress: number, ms: number): Promise<boolean> {
  if (cancelled(job)) return false;
  job.status = 'running';
  job.started_at ??= now();
  job.stage = stage;
  job.progress = progress;
  job.eta_seconds = etaSeconds(job);
  pushJob(job);
  await sleep(ms);
  return !cancelled(job);
}

async function run(job: MockJob) {
  try {
    switch (job.type) {
      case 'ingest_file':
        return await runIngest(job);
      case 'generate_test':
        return await runGenerate(job);
      case 'answer_question':
        return await runAnswer(job);
      case 'regenerate_question':
        return await runRegenerate(job);
      case 'delete_topic':
        return await runDeleteTopic(job);
      case 'export_account':
        return await runExport(job);
      case 'delete_account':
        return await runDeleteAccount(job);
      default:
        return undefined;
    }
  } catch {
    fail(job, 'INTERNAL');
    return undefined;
  }
}

async function runIngest(job: MockJob) {
  const db = getDb();
  const file = db.files.find((f) => f.id === job.payload.file_id);
  if (!file) return fail(job, 'FILE_NOT_FOUND');
  const setFile = (status: typeof file.status) => {
    file.status = status;
    emit(file.topic_id, 'file.status', { file: publicFile(file) });
  };
  for (const [stage, p] of [
    ['extracting', 0.2],
    ['chunking', 0.55],
    ['indexing', 0.8],
  ] as const) {
    setFile(stage);
    if (!(await step(job, stage, p, 900))) return undefined;
    if (stage === 'extracting' && (/fail/i.test(file.filename) || (file.mime.startsWith('text') && !file.text.trim()))) {
      file.status = 'failed';
      file.error_code = 'NO_TEXT_EXTRACTED';
      emit(file.topic_id, 'file.status', { file: publicFile(file) });
      return fail(job, 'NO_TEXT_EXTRACTED');
    }
  }
  file.chunk_count = Math.max(1, Math.ceil((file.text.length || file.size_bytes / 6) / 1200));
  file.page_count = Math.max(1, Math.ceil(file.size_bytes / 3000));
  setFile('ready');
  job.status = 'succeeded';
  job.progress = 1;
  job.stage = null;
  job.result = { file_id: file.id };
  pushJob(job);
}

function assistantMessage(job: MockJob, content: string, extra: Partial<MockMessage> = {}): MockMessage {
  const db = getDb();
  const msg: MockMessage = {
    id: nextId('msg'),
    session_id: job.payload.session_id as string,
    topic_id: job.topic_id!,
    role: 'assistant',
    content,
    job_id: job.id,
    test_id: null,
    created_at: now(),
    ...extra,
  };
  db.messages.push(msg);
  const session = db.sessions.find((s) => s.id === msg.session_id);
  if (session) {
    session.message_count += 1;
    session.updated_at = msg.created_at;
  }
  emit(job.topic_id!, 'message.created', { message: publicMessage(msg) });
  return msg;
}

const readyFiles = (topicId: string, ids?: string[]) =>
  getDb().files.filter((f) => f.topic_id === topicId && f.status === 'ready' && (!ids?.length || ids.includes(f.id)));

async function runGenerate(job: MockJob) {
  const db = getDb();
  const opts = job.payload.options as GenerationOptions;
  const lang = opts.exam_language;
  const model = MOCK_MODELS.models.find((m) => m.id === opts.model);
  const local = model ? model.location === 'local' : !MOCK_MODELS.external_available;
  const slow = (opts.mode === 'thorough' ? 2 : 1) * (local ? 1.5 : 1);
  if (!(await step(job, 'retrieving', 0.1, 700))) return undefined;
  const steps = Math.min(6, Math.max(2, Math.ceil(opts.count / 3)));
  for (let i = 0; i < steps; i += 1) {
    if (!(await step(job, 'generating', 0.2 + (0.6 * i) / steps, (500 * slow) + opts.count * 40))) return undefined;
  }
  if (String(job.payload.content).includes('#fail')) {
    assistantMessage(job, '', { error_code: 'LLM_UNAVAILABLE' });
    return fail(job, 'LLM_UNAVAILABLE');
  }
  if (!(await step(job, 'validating', 0.9, 500))) return undefined;
  const topic = db.topics.find((t) => t.id === job.topic_id);
  if (!topic) return fail(job, 'TOPIC_NOT_FOUND');
  const exam = generateExam(topic.name, readyFiles(topic.id, opts.file_ids), opts, () => nextId('q'), job.id);
  const test: MockTest = {
    id: nextId('tst'),
    topic_id: topic.id,
    session_id: job.payload.session_id as string,
    user_id: job.user_id,
    title: exam.title,
    question_count: exam.questions.length,
    saved: false,
    created_at: now(),
    updated_at: now(),
    model_used: model?.label ?? MOCK_MODELS.models[0].label,
    exam,
  };
  db.tests.push(test);
  touchTopic(topic);
  const content =
    lang === 'hu'
      ? `Elkészült a ${exam.questions.length} kérdéses teszt. Nézd át és szerkeszd, mielőtt felhasználod.`
      : `Your ${exam.questions.length}-question test is ready. Review and edit it before you use it.`;
  const msg = assistantMessage(job, content, { test_id: test.id });
  job.status = 'succeeded';
  job.progress = 1;
  job.stage = null;
  job.result = { test_id: test.id, message_id: msg.id };
  pushJob(job);
}

async function runAnswer(job: MockJob) {
  if (!(await step(job, 'retrieving', 0.3, 500))) return undefined;
  if (!(await step(job, 'generating', 0.7, 900))) return undefined;
  const lang = (job.payload.language as Language) ?? 'hu';
  const { content, citations } = answerQuestion(String(job.payload.content), readyFiles(job.topic_id!), lang);
  const msg = assistantMessage(job, content, { citations });
  job.status = 'succeeded';
  job.progress = 1;
  job.stage = null;
  job.result = { message_id: msg.id };
  pushJob(job);
}

async function runRegenerate(job: MockJob) {
  const db = getDb();
  if (!(await step(job, 'generating', 0.4, 1200))) return undefined;
  const test = db.tests.find((t) => t.id === job.payload.test_id);
  const idx = test?.exam.questions.findIndex((q) => q.id === job.payload.question_id) ?? -1;
  if (!test || idx < 0) return fail(job, 'TEST_NOT_FOUND');
  const lang = (job.payload.language as Language) ?? 'hu';
  test.exam.questions[idx] = regenerateQuestion(test.exam.questions[idx], readyFiles(test.topic_id), lang, () => nextId('q'));
  test.updated_at = now();
  job.status = 'succeeded';
  job.progress = 1;
  job.stage = null;
  job.result = { test_id: test.id };
  pushJob(job);
}

export function purgeTopic(topicId: string): void {
  const db = getDb();
  db.files = db.files.filter((f) => f.topic_id !== topicId);
  db.sessions = db.sessions.filter((s) => s.topic_id !== topicId);
  db.messages = db.messages.filter((m) => m.topic_id !== topicId);
  db.tests = db.tests.filter((t) => t.topic_id !== topicId);
  db.topics = db.topics.filter((t) => t.id !== topicId);
}

async function runDeleteTopic(job: MockJob) {
  const topicId = job.topic_id!;
  await step(job, 'destroying_key', 0.3, 600);
  await step(job, 'purging', 0.7, 900);
  purgeTopic(topicId);
  job.status = 'succeeded';
  job.progress = 1;
  job.stage = null;
  pushJob(job);
  emit(topicId, 'topic.deleted', { topic_id: topicId });
  getDb().events = getDb().events.filter((e) => e.topic_id !== topicId || e.name === 'topic.deleted');
}

async function runExport(job: MockJob) {
  const db = getDb();
  await sleep(1200);
  const user = db.users.find((u) => u.id === job.user_id);
  if (!user) return fail(job, 'AUTH_REQUIRED');
  const topics = db.topics.filter((t) => t.user_id === user.id);
  db.exports[job.id] = {
    exported_at: now(),
    account: { id: user.id, email: user.email, language: user.language, created_at: user.created_at },
    topics: topics.map((t) => ({
      ...t,
      files: db.files.filter((f) => f.topic_id === t.id).map(publicFile),
      sessions: db.sessions
        .filter((s) => s.topic_id === t.id)
        .map((s) => ({ ...s, messages: db.messages.filter((m) => m.session_id === s.id).map(publicMessage) })),
      tests: db.tests.filter((x) => x.topic_id === t.id),
    })),
  };
  job.status = 'succeeded';
  job.progress = 1;
  job.result = { download_url: `/__mock/exports/${job.id}` };
  persist();
}

async function runDeleteAccount(job: MockJob) {
  const db = getDb();
  await sleep(1000);
  db.topics.filter((t) => t.user_id === job.user_id).forEach((t) => purgeTopic(t.id));
  db.users = db.users.filter((u) => u.id !== job.user_id);
  if (db.refreshUserId === job.user_id) db.refreshUserId = null;
  job.status = 'succeeded';
  job.progress = 1;
  persist();
}

export function recountAll(topicId: string) {
  const t = getDb().topics.find((x) => x.id === topicId);
  if (t) recount(t);
}
