/** TanStack Query keys. Everything topic-scoped starts with ['topic', topicId] so a topic can be dropped in one call. */
export const qk = {
  me: ['me'] as const,
  topics: (q = '') => ['topics', { q }] as const,
  topicsAll: ['topics'] as const,
  topic: (topicId: string) => ['topic', topicId] as const,
  files: (topicId: string) => ['topic', topicId, 'files'] as const,
  sessions: (topicId: string) => ['topic', topicId, 'sessions'] as const,
  messages: (topicId: string, sessionId: string) => ['topic', topicId, 'sessions', sessionId, 'messages'] as const,
  topicTests: (topicId: string, saved?: boolean) => ['topic', topicId, 'tests', { saved: saved ?? null }] as const,
  topicTestsAll: (topicId: string) => ['topic', topicId, 'tests'] as const,
  test: (topicId: string, testId: string) => ['topic', topicId, 'test', testId] as const,
  savedTests: ['tests', 'saved'] as const,
  activeJobs: ['jobs', 'active'] as const,
  models: ['models'] as const,
  job: (jobId: string) => ['job', jobId] as const,
};
