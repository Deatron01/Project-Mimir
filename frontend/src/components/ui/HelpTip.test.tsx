import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HelpTip from './HelpTip';
import { renderUi } from '../../test/utils';

describe('HelpTip', () => {
  it('opens on click, announces its text and closes on Escape, returning focus', async () => {
    renderUi(<HelpTip label="Difficulty">Easy questions check facts.</HelpTip>);
    const button = screen.getByRole('button', { name: 'Help: Difficulty' });
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Easy questions check facts.')).not.toBeInTheDocument();

    await userEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');
    // Once in the live region (for screen readers), once in the floating bubble.
    expect(screen.getAllByText('Easy questions check facts.').length).toBeGreaterThan(0);

    await userEvent.keyboard('{Escape}');
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(button).toHaveFocus();
  });

  it('toggles closed on a second click', async () => {
    renderUi(<HelpTip label="Mode">Fast is good for practice.</HelpTip>);
    const button = screen.getByRole('button', { name: 'Help: Mode' });
    await userEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');
    await userEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });
});
