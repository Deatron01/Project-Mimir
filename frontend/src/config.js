// Single place for backend endpoints. Every service is reachable through the API gateway under /api/v1.
const fallback = import.meta.env.PROD ? 'https://api.mimir-ai.hu/api/v1' : '/api/v1';
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || fallback).replace(/\/$/, '');

export const endpoints = {
  extract: `${API_BASE}/extract`,
  chunk: `${API_BASE}/chunk`,
  ingest: `${API_BASE}/ingest`,
  generate: `${API_BASE}/generate`,
  status: (jobId) => `${API_BASE}/status/${encodeURIComponent(jobId)}`,
  exportPdf: `${API_BASE}/export`,
  tests: (userId) => `${API_BASE}/tests?user_id=${encodeURIComponent(userId)}`,
  download: (testId) => `${API_BASE}/tests/download/${encodeURIComponent(testId)}`,
};
