/**
 * In-memory database for the mock API (MSW). Persisted to localStorage so a page reload keeps the demo state.
 * Only used when `useMocks` is on – never in production against the real backend.
 */
import type { ChatSession, Job, Language, Message, Test, Topic, TopicFile } from '../api/types';
import { seed } from './seed';

import { MOCK_DB_KEY_NAME } from './constants';

export const MOCK_DB_KEY = MOCK_DB_KEY_NAME;

export interface MockUser {
  id: string;
  email: string;
  password: string;
  language: Language;
  verified: boolean;
  created_at: string;
}
export interface MockFile extends TopicFile {
  user_id: string;
  /** Extracted text (TXT/MD only in the mock), truncated. */
  text: string;
}
export interface MockTopic extends Topic {
  user_id: string;
}
export interface MockSession extends ChatSession {
  user_id: string;
}
export interface MockMessage extends Message {
  topic_id: string;
}
export interface MockTest extends Test {
  user_id: string;
}
export interface MockJob extends Job {
  user_id: string;
  /** Internal payload the runner needs. */
  payload: Record<string, unknown>;
}
export interface MockMail {
  id: string;
  to: string;
  subject: string;
  link: string;
  created_at: string;
}
export interface MockEvent {
  id: number;
  topic_id: string;
  name: string;
  data: unknown;
}

export interface DB {
  version: 1;
  users: MockUser[];
  topics: MockTopic[];
  files: MockFile[];
  sessions: MockSession[];
  messages: MockMessage[];
  tests: MockTest[];
  jobs: MockJob[];
  /** Stands in for the HttpOnly refresh cookie: which user the browser is "logged in" as. */
  refreshUserId: string | null;
  verifyTokens: Record<string, string>;
  resetTokens: Record<string, string>;
  outbox: MockMail[];
  exports: Record<string, unknown>;
  events: MockEvent[];
  seq: number;
}

const empty = (): DB => ({
  version: 1,
  users: [],
  topics: [],
  files: [],
  sessions: [],
  messages: [],
  tests: [],
  jobs: [],
  refreshUserId: null,
  verifyTokens: {},
  resetTokens: {},
  outbox: [],
  exports: {},
  events: [],
  seq: 1,
});

let db: DB = load();

function load(): DB {
  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(MOCK_DB_KEY) : null;
    if (raw) {
      const parsed = JSON.parse(raw) as DB;
      if (parsed.version === 1) return parsed;
    }
  } catch {
    /* corrupted or unavailable – start fresh */
  }
  const fresh = empty();
  seed(fresh);
  return fresh;
}

let scheduled = false;
function save(): void {
  try {
    // Keep the event log short; it only serves Last-Event-ID resumes.
    db.events = db.events.slice(-200);
    localStorage.setItem(MOCK_DB_KEY, JSON.stringify(db));
  } catch {
    /* quota exceeded or no storage – state lives in memory for this tab */
  }
}
/** Saves at the end of the current task (many mutations in one handler cost one write). */
export function persist(): void {
  if (scheduled) return;
  scheduled = true;
  queueMicrotask(() => {
    scheduled = false;
    save();
  });
}
if (typeof window !== 'undefined') window.addEventListener('pagehide', save);

export const getDb = (): DB => db;

/** Resets the mock to its seeded state (used by tests and the dev mailbox "reset" button). */
export function resetDb(withSeed = true): DB {
  db = empty();
  if (withSeed) seed(db);
  try {
    localStorage.removeItem(MOCK_DB_KEY);
  } catch {
    /* ignore */
  }
  return db;
}

export const nextId = (prefix: string): string => {
  db.seq += 1;
  const rand = Math.random().toString(36).slice(2, 8);
  return `${prefix}_${db.seq.toString(36)}${rand}`;
};
export const now = (): string => new Date().toISOString();
export const addDays = (iso: string, days: number): string => new Date(Date.parse(iso) + days * 86_400_000).toISOString();

export const INACTIVITY_DAYS = 90;

export function touchTopic(topic: MockTopic): void {
  const t = now();
  topic.updated_at = t;
  topic.last_activity_at = t;
  topic.expires_at = addDays(t, INACTIVITY_DAYS);
}

/** Recomputes the denormalised counters on a topic. */
export function recount(topic: MockTopic): void {
  const files = db.files.filter((f) => f.topic_id === topic.id);
  topic.file_count = files.length;
  topic.total_bytes = files.reduce((s, f) => s + f.size_bytes, 0);
  topic.saved_test_count = db.tests.filter((t) => t.topic_id === topic.id && t.saved).length;
}

export const publicTopic = ({ user_id: _u, ...t }: MockTopic): Topic => t;
export const publicFile = ({ user_id: _u, text: _t, ...f }: MockFile): TopicFile => f;
export const publicSession = ({ user_id: _u, ...s }: MockSession): ChatSession => s;
export const publicMessage = ({ topic_id: _t, ...m }: MockMessage): Message => m;
export const publicTest = ({ user_id: _u, ...t }: MockTest): Test => t;
export const publicJob = ({ user_id: _u, payload: _p, ...j }: MockJob): Job => j;
