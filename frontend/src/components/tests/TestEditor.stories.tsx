import type { Meta, StoryObj } from '@storybook/react-vite';
import { fn } from 'storybook/test';
import TestEditor from './TestEditor';

const meta: Meta<typeof TestEditor> = {
  title: 'Tests/TestEditor',
  component: TestEditor,
  args: {
    onSubmit: fn(),
    onRegenerate: fn(),
    canSave: true,
    fileNames: { f1: 'fotoszintezis.pdf' },
    initial: {
      title: 'Fotoszintézis – témazáró',
      questions: [
        {
          id: 'q1',
          type: 'mcq',
          difficulty: 'medium',
          text: 'Hol zajlik a fotoszintézis?',
          answers: [
            { text: 'A kloroplasztiszban', is_correct: true },
            { text: 'A mitokondriumban', is_correct: false },
            { text: 'A sejtmagban', is_correct: false },
            { text: 'A riboszómán', is_correct: false },
          ],
          citations: [{ file_id: 'f1', chunk_id: 'c1', page: 3, snippet: 'A folyamat a kloroplasztiszokban zajlik…' }],
        },
        { id: 'q2', type: 'tf', difficulty: 'easy', text: 'A klorofill a zöld fényt nyeli el.', answers: [{ text: 'Igaz', is_correct: false }, { text: 'Hamis', is_correct: true }], citations: [] },
        { id: 'q3', type: 'open', difficulty: 'hard', text: 'Hasonlítsd össze a fény- és a sötétszakaszt!', answers: [{ text: 'A fényszakaszban…', is_correct: true }], citations: [] },
      ],
    },
  },
};
export default meta;
export const Default: StoryObj<typeof TestEditor> = {};
export const Regenerating: StoryObj<typeof TestEditor> = { args: { regeneratingIds: new Set(['q1']) } };
