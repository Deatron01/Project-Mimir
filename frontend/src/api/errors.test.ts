import { describe, expect, it } from 'vitest';
import { ApiError, toApiError, unwrap } from './errors';

describe('toApiError', () => {
  it('reads the standard error envelope', () => {
    const e = toApiError({ error: { code: 'FILE_TOO_LARGE', message: 'big', request_id: 'r1', details: { limit: 1 } } }, 413);
    expect(e).toBeInstanceOf(ApiError);
    expect(e.code).toBe('FILE_TOO_LARGE');
    expect(e.requestId).toBe('r1');
    expect(e.i18nKey).toBe('errors.FILE_TOO_LARGE');
  });

  it.each([
    [401, 'AUTH_REQUIRED'],
    [413, 'FILE_TOO_LARGE'],
    [429, 'RATE_LIMITED'],
    [502, 'INTERNAL'],
    [418, 'UNKNOWN'],
  ])('maps a bare %i to %s', (status, code) => {
    expect(toApiError('<html>gateway</html>', status).code).toBe(code);
  });

  it('unwrap throws on error and returns data otherwise', () => {
    const ok = new Response(null, { status: 200 });
    expect(unwrap({ data: 1, response: ok })).toBe(1);
    const bad = new Response(null, { status: 404 });
    expect(() => unwrap({ error: { error: { code: 'TOPIC_NOT_FOUND', message: 'x', request_id: 'r' } }, response: bad })).toThrow(ApiError);
  });
});
