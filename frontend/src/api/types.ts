import type { components } from './schema';

type S = components['schemas'];
export type ErrorCode = S['ErrorCode'];
export type ErrorEnvelope = S['Error'];
export type User = S['User'];
export type AuthSession = S['Session'];
export type Me = S['Me'];
export type Limits = S['Limits'];
export type Language = S['Language'];
export type Topic = S['Topic'];
export type TopicInput = S['TopicInput'];
export type TopicPatch = S['TopicPatch'];
export type TopicList = S['TopicList'];
export type TopicFile = S['TopicFile'];
export type FileStatus = S['FileStatus'];
export type ChatSession = S['ChatSession'];
export type Message = S['Message'];
export type MessageInput = S['MessageInput'];
export type MessageList = S['MessageList'];
export type GenerationOptions = S['GenerationOptions'];
export type QuestionType = S['QuestionType'];
export type Difficulty = S['Difficulty'];
export type Citation = S['Citation'];
export type Answer = S['Answer'];
export type Question = S['Question'];
export type Exam = S['Exam'];
export type TestSummary = S['TestSummary'];
export type Test = S['Test'];
export type ExportRequest = S['ExportRequest'];
export type ExportFormat = ExportRequest['format'];
export type Job = S['Job'];
export type JobStatus = S['JobStatus'];
export type JobType = S['JobType'];
export type TopicEvent = S['TopicEvent'];
export type SavedTestGroup = { topic: { id: string; name: string }; tests: TestSummary[] };

export const TOPIC_EVENT_NAMES = [
  'job.progress',
  'job.succeeded',
  'job.failed',
  'file.status',
  'message.created',
  'topic.deleted',
  'heartbeat',
] as const;
export type TopicEventName = (typeof TOPIC_EVENT_NAMES)[number];

export const DEFAULT_LIMITS: Limits = {
  max_topics: 50,
  max_files_per_topic: 20,
  max_topic_bytes: 100 * 1024 * 1024,
  max_file_bytes: 20 * 1024 * 1024,
  max_files_per_upload: 10,
  allowed_types: ['pdf', 'txt', 'docx', 'md'],
};

export const TERMS_VERSION = '2026-09-22';
export const MIN_PASSWORD_LENGTH = 10;
