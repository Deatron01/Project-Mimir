import { getConfig } from './runtime';

/** Endpoints of the pre-topic backend (apiMode = 'legacy'). Removed once the v1 gateway is live. */
const base = () => getConfig().apiBaseUrl;
const e = encodeURIComponent;

export const legacyEndpoints = {
  extract: () => `${base()}/extract`,
  chunk: () => `${base()}/chunk`,
  ingest: () => `${base()}/ingest`,
  generate: () => `${base()}/generate`,
  status: (jobId: string) => `${base()}/status/${e(jobId)}`,
  models: () => `${base()}/models`,
  exportPdf: () => `${base()}/export`,
  tests: (userId: string) => `${base()}/tests?user_id=${e(userId)}`,
  download: (testId: string) => `${base()}/tests/download/${e(testId)}`,
  deleteTest: (testId: string, userId: string) => `${base()}/tests/${e(testId)}?user_id=${e(userId)}`,
};
