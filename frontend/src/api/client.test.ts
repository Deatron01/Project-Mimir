import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server, TEST_API_BASE } from '../mocks/node';
import { api, onSessionChange } from './client';
import { getAccessToken, setAccessToken } from './tokens';
import { unwrap, ApiError } from './errors';
import { loginDemo } from '../test/utils';

describe('authFetch', () => {
  it('sends the bearer token', async () => {
    await loginDemo();
    const me = unwrap(await api().GET('/me'));
    expect(me.email).toBe('demo@mimir.hu');
  });

  it('refreshes once on TOKEN_EXPIRED and replays the request', async () => {
    await loginDemo();
    setAccessToken('mock.usr_demo.1'); // expired
    const me = unwrap(await api().GET('/me'));
    expect(me.id).toBe('usr_demo');
    expect(getAccessToken()).not.toBe('mock.usr_demo.1');
  });

  it('shares one refresh between concurrent 401s', async () => {
    await loginDemo();
    setAccessToken('mock.usr_demo.1');
    let refreshes = 0;
    server.events.on('request:start', ({ request }) => {
      if (request.url.endsWith('/auth/refresh')) refreshes += 1;
    });
    await Promise.all([api().GET('/me'), api().GET('/topics'), api().GET('/jobs')]);
    server.events.removeAllListeners();
    expect(refreshes).toBe(1);
  });

  it('ends the session when the refresh fails', async () => {
    await loginDemo();
    setAccessToken('mock.usr_demo.1');
    server.use(http.post(`${TEST_API_BASE}/auth/refresh`, () => HttpResponse.json({ error: { code: 'AUTH_REQUIRED', message: '', request_id: 'x' } }, { status: 401 })));
    const reasons: (string | undefined)[] = [];
    const off = onSessionChange((_u, reason) => reasons.push(reason));
    const r = await api().GET('/me');
    off();
    expect(() => unwrap(r)).toThrow(ApiError);
    expect(reasons).toContain('expired');
    expect(getAccessToken()).toBeNull();
  });
});
