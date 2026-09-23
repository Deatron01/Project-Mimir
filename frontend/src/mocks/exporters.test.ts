import { describe, expect, it } from 'vitest';
import { exportExam } from './exporters';
import type { Exam } from '../api/types';

const exam: Exam = {
  title: 'Árvíztűrő tükörfúrógép',
  questions: [
    { id: 'a', type: 'mcq', text: 'Mi a {válasz}?', answers: [{ text: 'Igen', is_correct: true }, { text: 'Nem', is_correct: false }], citations: [], difficulty: 'easy' },
    { id: 'b', type: 'tf', text: 'Igaz?', answers: [{ text: 'Igaz', is_correct: false }, { text: 'Hamis', is_correct: true }], citations: [], difficulty: 'easy' },
  ],
};

describe('mock exporters', () => {
  it('writes a PDF', async () => {
    const out = exportExam(exam, { format: 'pdf_with_key' });
    const bytes = out.body as unknown as Uint8Array;
    expect(String.fromCharCode(...bytes.slice(0, 8))).toBe('%PDF-1.4');
    expect(out.type).toBe('application/pdf');
  });
  it('escapes GIFT control characters and encodes true/false', () => {
    const out = String(exportExam(exam, { format: 'gift' }).body);
    expect(out).toContain('Mi a \\{válasz\\}?');
    expect(out).toContain('{FALSE}');
  });
  it('writes Moodle XML', () => {
    const out = String(exportExam(exam, { format: 'moodle_xml' }).body);
    expect(out).toContain('<question type="multichoice">');
    expect(out).toContain('<answer fraction="100"><text>Igen</text></answer>');
  });
});
