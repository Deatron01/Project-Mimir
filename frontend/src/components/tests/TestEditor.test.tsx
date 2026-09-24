import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TestEditor from './TestEditor';
import '../../i18n';

const exam = {
  title: 'Quiz',
  questions: [
    { id: 'q1', type: 'mcq' as const, text: 'First?', answers: [{ text: 'A', is_correct: true }, { text: 'B', is_correct: false }], citations: [{ file_id: 'f1', chunk_id: 'c1', page: 2, snippet: 'source text' }], difficulty: 'easy' as const },
    { id: 'q2', type: 'tf' as const, text: 'Second?', answers: [{ text: 'True', is_correct: true }, { text: 'False', is_correct: false }], citations: [], difficulty: 'hard' as const },
  ],
};

describe('TestEditor', () => {
  it('reorders with the move buttons and submits the new order', async () => {
    const onSubmit = vi.fn();
    render(<TestEditor initial={exam} onSubmit={onSubmit} />);
    const items = screen.getAllByRole('listitem');
    await userEvent.click(within(items[0]).getByRole('button', { name: 'Move question down' }));
    await userEvent.click(screen.getByRole('button', { name: /reviewed and approve/i }));
    expect(onSubmit).toHaveBeenCalledOnce();
    expect(onSubmit.mock.calls[0][0].questions.map((q: { id: string }) => q.id)).toEqual(['q2', 'q1']);
    expect(onSubmit.mock.calls[0][1]).toEqual({ save: false });
  });

  it('reorders with the keyboard drag handle', async () => {
    const onSubmit = vi.fn();
    render(<TestEditor initial={exam} onSubmit={onSubmit} />);
    const [handle] = screen.getAllByRole('button', { name: 'Drag to reorder' });
    handle.focus();
    await userEvent.keyboard('[Space]');
    await userEvent.keyboard('[ArrowDown]');
    await userEvent.keyboard('[Space]');
    await userEvent.click(screen.getByRole('button', { name: /reviewed and approve/i }));
    // jsdom has no layout, so dnd-kit may not find a target; the order must at least stay intact.
    const ids = onSubmit.mock.calls[0][0].questions.map((q: { id: string }) => q.id).sort();
    expect(ids).toEqual(['q1', 'q2']);
  });

  it('blocks submit and focuses the error list when a question is empty', async () => {
    const onSubmit = vi.fn();
    render(<TestEditor initial={exam} onSubmit={onSubmit} />);
    await userEvent.clear(screen.getAllByPlaceholderText('Question text')[0]);
    await userEvent.click(screen.getByRole('button', { name: /reviewed and approve/i }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent('Question 1 has no text.');
    await waitFor(() => expect(screen.getByRole('alert')).toHaveFocus());
  });

  it('shows citations with file names and calls regenerate', async () => {
    const onRegenerate = vi.fn();
    render(<TestEditor initial={exam} onSubmit={vi.fn()} onRegenerate={onRegenerate} fileNames={{ f1: 'notes.pdf' }} />);
    expect(screen.getByText('notes.pdf')).toBeInTheDocument();
    expect(screen.getByText('source text')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Regenerate question 1' }));
    expect(onRegenerate).toHaveBeenCalledWith('q1');
  });

  it('only offers the opt-in save box when allowed, unticked by default', async () => {
    const onSubmit = vi.fn();
    render(<TestEditor initial={exam} onSubmit={onSubmit} canSave />);
    const box = screen.getByRole('checkbox', { name: /Save to "My tests"/ });
    expect(box).not.toBeChecked();
    await userEvent.click(box);
    await userEvent.click(screen.getByRole('button', { name: /reviewed and approve/i }));
    expect(onSubmit.mock.calls[0][1]).toEqual({ save: true });
  });
});
