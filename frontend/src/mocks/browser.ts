import { setupWorker } from 'msw/browser';
import { makeHandlers } from './handlers';
import { resumeJobs } from './runner';

/** Starts the in-browser mock API. Requests to anything but the v1 API pass through untouched. */
export async function startMockApi(apiBaseUrl: string): Promise<void> {
  const worker = setupWorker(...makeHandlers(apiBaseUrl));
  await worker.start({
    onUnhandledRequest: 'bypass',
    quiet: import.meta.env.PROD,
    serviceWorker: { url: `${import.meta.env.BASE_URL}mockServiceWorker.js` },
  });
  resumeJobs();
}
