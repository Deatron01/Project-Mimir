import { describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NewTopicModal from './NewTopicModal';
import { loginDemo, renderRoutes } from '../../test/utils';
import { getDb } from '../../mocks/db';
import { uploadFiles } from '../../api/upload';

// jsdom multipart bodies never reach MSW, so the XHR upload is stubbed here; the real upload is covered by the
// mock-API tests (node environment) and the Playwright E2E test.
vi.mock('../../api/upload', () => ({ uploadFiles: vi.fn(async () => ({ files: [], job_ids: [] })) }));

function setup() {
  return renderRoutes(
    [
      { path: '/topics', element: <NewTopicModal open onClose={() => undefined} /> },
      { path: '/topics/:id/*', element: <p>workspace</p> },
    ],
    { initialPath: '/topics' },
  );
}

describe('NewTopicModal', () => {
  it('is an accessible modal that focuses the name field', async () => {
    await loginDemo();
    setup();
    const dialog = await screen.findByRole('dialog', { name: 'New topic' });
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    await waitFor(() => expect(screen.getByLabelText(/^Name/)).toHaveFocus());
  });

  it('requires a name', async () => {
    await loginDemo();
    setup();
    await userEvent.click(await screen.findByRole('button', { name: 'Create topic' }));
    expect(await screen.findByText('Give the topic a name.')).toBeInTheDocument();
    expect(screen.getByLabelText(/^Name/)).toHaveAttribute('aria-invalid', 'true');
  });

  it('requires consent before uploading files', async () => {
    await loginDemo();
    setup();
    await userEvent.type(await screen.findByLabelText(/^Name/), 'Chemistry');
    const input = document.querySelector('input[type=file]') as HTMLInputElement;
    await userEvent.upload(input, new File(['Some text about atoms. '.repeat(10)], 'atoms.txt', { type: 'text/plain' }));
    await userEvent.click(screen.getByRole('button', { name: 'Create and upload' }));
    expect(await screen.findByText('Please tick the box to upload.')).toBeInTheDocument();
    expect(getDb().topics.some((t) => t.name === 'Chemistry')).toBe(false);
  });

  it('creates the topic, uploads and opens the workspace', async () => {
    await loginDemo();
    const { router } = setup();
    await userEvent.type(await screen.findByLabelText(/^Name/), 'Chemistry');
    const input = document.querySelector('input[type=file]') as HTMLInputElement;
    await userEvent.upload(input, new File(['Some text about atoms. '.repeat(10)], 'atoms.txt', { type: 'text/plain' }));
    await userEvent.click(screen.getByRole('checkbox', { name: /I confirm that I may use these documents/ }));
    await userEvent.click(screen.getByRole('button', { name: 'Create and upload' }));
    await waitFor(() => expect(router.state.location.pathname).toMatch(/^\/topics\/top_.+\/files$/));
    const topic = getDb().topics.find((t) => t.name === 'Chemistry')!;
    expect(uploadFiles).toHaveBeenCalledWith(topic.id, [expect.objectContaining({ name: 'atoms.txt' })], expect.anything());
  });
});
