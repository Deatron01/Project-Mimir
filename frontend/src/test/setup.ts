import '@testing-library/jest-dom/vitest';
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server, TEST_API_BASE } from '../mocks/node';
import { resetDb } from '../mocks/db';
import { setMockSpeed } from '../mocks/runner';
import { setConfig } from '../config/runtime';
import { setAccessToken } from '../api/tokens';
import i18n from '../i18n';

setConfig({ apiBaseUrl: TEST_API_BASE, apiMode: 'v1', useMocks: false, privacyEmail: '' });
setMockSpeed(40);

const hasDom = typeof window !== 'undefined';

// jsdom lacks these browser APIs.
if (hasDom && !window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}
if (hasDom) {
  window.scrollTo = (() => undefined) as typeof window.scrollTo;
  Element.prototype.scrollTo = function scrollTo() {} as typeof Element.prototype.scrollTo;
}
if (!URL.createObjectURL) URL.createObjectURL = () => 'blob:test';
if (!URL.revokeObjectURL) URL.revokeObjectURL = () => undefined;

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
beforeEach(async () => {
  if (hasDom) localStorage.clear();
  resetDb();
  setAccessToken(null);
  await i18n.changeLanguage('en');
});
afterEach(() => {
  if (hasDom) cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());
