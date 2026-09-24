import { describe, expect, it } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server, TEST_API_BASE } from '../../mocks/node';
import { renderUi } from '../../test/utils';
import LegacyChat from './LegacyChat';

const B = TEST_API_BASE;

/** The old backend: extract -> chunk -> ingest -> generate (job) -> status; /models may be missing. */
function legacyBackend({ models = true, status = 'completed' }: { models?: boolean; status?: string } = {}) {
  const seen: { generate?: Record<string, unknown>; export?: Record<string, unknown> } = {};
  server.use(
    http.get(`${B}/models`, () =>
      models
        ? HttpResponse.json({
            local_only: false,
            external_available: true,
            default: 'auto',
            models: [
              { id: 'gpt-oss:120b', label: 'gpt-oss:120b', location: 'external' },
              { id: 'local', label: 'qwen2.5:7b', location: 'local' },
            ],
            estimates_s: { external: 42, local: 120 },
          })
        : new HttpResponse(null, { status: 404 }),
    ),
    http.post(`${B}/extract`, () => HttpResponse.json({ content: 'Photosynthesis turns light into chemical energy.' })),
    http.post(`${B}/chunk`, () => HttpResponse.json({ chunks: [{ content: 'Photosynthesis…' }] })),
    http.post(`${B}/ingest`, () => HttpResponse.json({ status: 'success', indexed_chunks: 1 })),
    http.post(`${B}/generate`, async ({ request }) => {
      seen.generate = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json({ status: 'success', job_id: 'j1', expected_total_s: 42, location: 'local' });
    }),
    http.get(`${B}/status/j1`, () =>
      status === 'completed'
        ? HttpResponse.json({
            status: 'completed',
            stage: 'done',
            progress: 1,
            eta_s: 0,
            data: {
              title: 'Photosynthesis',
              questions: [{ type: 'mcq', text: 'What does it make?', answers: [{ text: 'Sugar', is_correct: true }, { text: 'Salt', is_correct: false }] }],
              metadata: { model_used: 'qwen2.5:7b (local fallback)', processing_location: 'local' },
            },
          })
        : HttpResponse.json({ status: 'processing', stage: 'generating', progress: 0.4, eta_s: 25, elapsed_s: 10, model: 'qwen2.5:7b', location: 'local' }),
    ),
    http.post(`${B}/export`, async ({ request }) => {
      seen.export = (await request.json()) as Record<string, unknown>;
      return new HttpResponse('%PDF', { headers: { 'Content-Type': 'application/pdf' } });
    }),
  );
  return seen;
}

async function startGeneration(user: ReturnType<typeof userEvent.setup>) {
  await user.upload(screen.getByLabelText('Attach a document'), new File(['text'], 'bio.txt', { type: 'text/plain' }));
  await user.click(screen.getByRole('checkbox'));
  await user.type(screen.getByRole('textbox'), '1 question about photosynthesis');
  await user.click(screen.getByRole('button', { name: 'Send' }));
}

describe('LegacyChat', () => {
  it('sends the chosen model, shows progress with a time estimate, and keeps the AI metadata for the PDF', async () => {
    const seen = legacyBackend();
    const user = userEvent.setup();
    renderUi(<LegacyChat />);

    const select = await screen.findByLabelText('Model');
    await user.selectOptions(select, 'local');
    expect(screen.getByText('Data stays on this server')).toBeInTheDocument();
    await user.upload(screen.getByLabelText('Attach a document'), new File(['text'], 'bio.txt', { type: 'text/plain' }));
    expect(screen.getByText(/Processing happens entirely on this server/)).toBeInTheDocument();
    await user.click(screen.getByRole('checkbox'));
    await user.type(screen.getByRole('textbox'), '1 question');
    await user.click(screen.getByRole('button', { name: 'Send' }));

    expect(await screen.findByTestId('generation-progress')).toBeInTheDocument();
    expect(screen.getByTestId('time-estimate')).toHaveTextContent(/Elapsed: 0:0\d/);

    expect(await screen.findByText('Made with: qwen2.5:7b (local fallback)', {}, { timeout: 5000 })).toBeInTheDocument();
    expect(seen.generate).toMatchObject({ model: 'local' });
    expect(localStorage.getItem('mimir-model')).toBe('local');

    await user.click(screen.getByRole('button', { name: /approve these questions/ }));
    await waitFor(() => expect(seen.export).toBeDefined());
    expect(seen.export?.metadata).toMatchObject({ model_used: 'qwen2.5:7b (local fallback)' });
  });

  it('works with an older backend that has no /models: no selector, no model sent', async () => {
    const seen = legacyBackend({ models: false });
    const user = userEvent.setup();
    renderUi(<LegacyChat />);
    await startGeneration(user);
    expect(await screen.findByText('Made with: qwen2.5:7b (local fallback)', {}, { timeout: 5000 })).toBeInTheDocument();
    expect(screen.queryByLabelText('Model')).not.toBeInTheDocument();
    expect(seen.generate).not.toHaveProperty('model');
  });

  it('can stop waiting', async () => {
    legacyBackend({ status: 'processing' });
    const user = userEvent.setup();
    renderUi(<LegacyChat />);
    await startGeneration(user);
    await user.click(await screen.findByRole('button', { name: 'Stop waiting' }));
    expect(await screen.findByText(/You stopped waiting/, {}, { timeout: 5000 })).toBeInTheDocument();
    expect(screen.queryByTestId('generation-progress')).not.toBeInTheDocument();
  });
});
