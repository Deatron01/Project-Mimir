import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { estimate, PREP_SECONDS } from './GenerationProgress';
import ModelSelect, { AUTO_MODEL, locationOf, validModel, type ModelList } from './ModelSelect';
import { splitDuration } from '../../utils/format';
import { renderUi } from '../../test/utils';

const T0 = 1_000_000;

describe('estimate', () => {
  it('before the job starts: typical prep time plus the expected generation time', () => {
    const e = estimate('chunking', null, T0 + 5000, T0, 60);
    expect(e.progress).toBeCloseTo(0.05);
    expect(e.remainingS).toBe(PREP_SECONDS - 5 + 60);
    expect(e.overdue).toBe(false);
  });

  it('during generation: maps server progress onto the rest of the bar and counts down between polls', () => {
    const job = { progress: 0.5, eta_s: 30, elapsed_s: 30, expected_total_s: 60, receivedAt: T0 + 40_000 };
    const right = estimate('generating', job, T0 + 40_000, T0, 60);
    const later = estimate('generating', job, T0 + 50_000, T0, 60);
    expect(right.progress).toBeCloseTo(0.6);
    expect(right.remainingS).toBe(30);
    expect(later.remainingS).toBe(20);
  });

  it('never promises zero while running and flags a long overrun', () => {
    const job = { progress: 0.3, eta_s: 2, elapsed_s: 200, expected_total_s: 60, receivedAt: T0 };
    const e = estimate('generating', job, T0 + 10_000, T0, 60);
    expect(e.remainingS).toBe(3);
    expect(e.overdue).toBe(true);
  });
});

describe('splitDuration', () => {
  it('keeps seconds under a minute and rounds to 5 s above', () => {
    expect(splitDuration(42)).toEqual({ m: 0, s: 42 });
    expect(splitDuration(83)).toEqual({ m: 1, s: 25 });
    expect(splitDuration(-3)).toEqual({ m: 0, s: 0 });
  });
});

const LIST: ModelList = {
  local_only: false,
  external_available: true,
  default: AUTO_MODEL,
  models: [
    { id: 'gpt-oss:120b', label: 'gpt-oss:120b', location: 'external' },
    { id: 'local', label: 'qwen2.5:7b', location: 'local' },
  ],
};

describe('model selection', () => {
  it('knows where each choice runs and drops choices the server no longer offers', () => {
    expect(locationOf(LIST, AUTO_MODEL)).toBe('external');
    expect(locationOf({ ...LIST, external_available: false }, AUTO_MODEL)).toBe('local');
    expect(locationOf(LIST, 'local')).toBe('local');
    expect(validModel(LIST, 'removed-model')).toBe(AUTO_MODEL);
    expect(validModel(LIST, 'local')).toBe('local');
  });

  it('shows the data-location badge for the chosen model', async () => {
    renderUi(<ModelSelect list={LIST} value="local" onChange={() => undefined} />);
    expect(await screen.findByText('Data stays on this server')).toBeInTheDocument();
    expect(screen.getByRole('group', { name: 'University server' })).toBeInTheDocument();
  });
});
