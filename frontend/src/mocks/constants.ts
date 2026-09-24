/** Storage key of the mock database (kept separate so the page bundle does not pull in the mock). */
export const MOCK_DB_KEY_NAME = 'mimir-mock-db';

/** Mock of GET /models: two university-server models and the local Ollama model. */
export const MOCK_MODELS = {
  local_only: false,
  external_available: true,
  default: 'auto',
  models: [
    { id: 'gpt-oss:120b', label: 'gpt-oss:120b', location: 'external' as const },
    { id: 'Qwen3.8-Flash-Next', label: 'Qwen3.8-Flash-Next', location: 'external' as const },
    { id: 'local', label: 'qwen2.5:7b', location: 'local' as const },
  ],
  estimates_s: { external: 45, local: 120 },
};
