import { describe, expect, it } from 'vitest';
import { loadRuntimeConfig, mergeConfig, type RuntimeConfig } from './runtime';

const base: RuntimeConfig = { apiBaseUrl: '/api/v1', apiMode: 'legacy', useMocks: false, privacyEmail: '' };

describe('runtime config', () => {
  it('merges known keys and ignores junk', () => {
    const out = mergeConfig(base, { apiBaseUrl: 'https://x/api/v1/', apiMode: 'v1', useMocks: 'true', privacyEmail: 'dpo@x.hu' });
    expect(out).toEqual({ apiBaseUrl: 'https://x/api/v1', apiMode: 'v1', useMocks: true, privacyEmail: 'dpo@x.hu' });
    expect(mergeConfig(base, { apiMode: 'nope' as never, useMocks: '' })).toEqual(base);
  });

  it('keeps build-time values when /config.json is the SPA fallback page', async () => {
    const html = async () => new Response('<!doctype html>', { headers: { 'content-type': 'text/html' } });
    const before = await loadRuntimeConfig(html as typeof fetch);
    const json = async () => new Response(JSON.stringify({ apiMode: 'v1' }), { headers: { 'content-type': 'application/json' } });
    const after = await loadRuntimeConfig(json as typeof fetch);
    expect(after.apiMode).toBe('v1');
    expect(after.apiBaseUrl).toBe(before.apiBaseUrl);
  });

  it('survives a network failure', async () => {
    const boom = async () => {
      throw new Error('offline');
    };
    await expect(loadRuntimeConfig(boom as typeof fetch)).resolves.toBeTruthy();
  });
});
