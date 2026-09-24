/**
 * Deterministic fake "LLM" for the mock API. Builds questions from sentences of the uploaded TXT/MD files
 * (PDF/DOCX are not parsed in the browser, so their questions are generic). Good enough to exercise the UI.
 */
import type { Citation, Difficulty, GenerationOptions, Language, Question, QuestionType } from '../api/types';
import type { MockFile } from './db';

interface Sentence {
  text: string;
  file: MockFile;
  index: number;
}

const WORD = /[\p{L}][\p{L}\p{N}-]{5,}/gu;

export function sentencesOf(files: MockFile[]): Sentence[] {
  const out: Sentence[] = [];
  for (const file of files) {
    const parts = file.text
      .replace(/^#+.*$/gm, '')
      .replace(/\s+/g, ' ')
      .split(/(?<=[.!?])\s+(?=[\p{Lu}0-9])/u)
      .map((s) => s.trim())
      .filter((s) => s.length >= 40 && s.length <= 260);
    parts.forEach((text, index) => out.push({ text, file, index }));
  }
  return out;
}

const cite = (s: Sentence): Citation => ({
  file_id: s.file.id,
  chunk_id: `${s.file.id}-c${Math.floor(s.index / 3)}`,
  filename: s.file.filename,
  page: Math.floor(s.index / 8) + 1,
  snippet: s.text.length > 180 ? `${s.text.slice(0, 177)}…` : s.text,
});

/** Small seeded PRNG so the same topic gives stable output within one request. */
function rng(seed: number) {
  let x = seed || 1;
  return () => {
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    return ((x >>> 0) % 10_000) / 10_000;
  };
}
const hash = (s: string) => [...s].reduce((h, c) => (Math.imul(h, 31) + c.charCodeAt(0)) | 0, 7);

const T = {
  hu: {
    fill: (s: string) => `Melyik szó hiányzik a következő állításból? „${s}”`,
    tf: (s: string) => `Igaz vagy hamis? ${s}`,
    open: (s: string) => `Fejtse ki saját szavaival: ${s}`,
    true: 'Igaz',
    false: 'Hamis',
    genericMcq: (f: string, n: number) => `Melyik állítás foglalja össze legjobban a(z) „${f}” dokumentum ${n}. részének fő gondolatát?`,
    genericAns: ['A szakasz fő gondolata', 'Egy mellékes részlet', 'A dokumentum nem tárgyalja', 'Egy ellentétes állítás'],
    genericTf: (f: string) => `Igaz vagy hamis? A(z) „${f}” dokumentum tartalmaz definíciókat.`,
    genericOpen: (f: string) => `Foglalja össze a(z) „${f}” dokumentum legfontosabb fogalmait!`,
    modelAnswer: 'Mintaválasz: a dokumentum kulcsfogalmainak pontos, saját szavas összefoglalása.',
    title: (topic: string) => `${topic} – témazáró`,
  },
  en: {
    fill: (s: string) => `Which word is missing from this statement? "${s}"`,
    tf: (s: string) => `True or false? ${s}`,
    open: (s: string) => `Explain in your own words: ${s}`,
    true: 'True',
    false: 'False',
    genericMcq: (f: string, n: number) => `Which statement best summarises the main idea of part ${n} of "${f}"?`,
    genericAns: ['The main idea of the section', 'A minor detail', 'Not covered by the document', 'A contradicting claim'],
    genericTf: (f: string) => `True or false? "${f}" contains definitions.`,
    genericOpen: (f: string) => `Summarise the key concepts of "${f}".`,
    modelAnswer: 'Model answer: an accurate summary of the key concepts in the student’s own words.',
    title: (topic: string) => `${topic} – end-of-unit test`,
  },
};

function makeQuestion(
  type: QuestionType,
  s: Sentence | null,
  pool: string[],
  lang: Language,
  difficulty: Difficulty,
  rand: () => number,
  n: number,
  fallbackFile: MockFile | undefined,
): Omit<Question, 'id'> {
  const L = T[lang];
  if (!s) {
    const f = fallbackFile?.filename ?? 'dokumentum';
    const citations: Citation[] = fallbackFile ? [{ file_id: fallbackFile.id, chunk_id: `${fallbackFile.id}-c${n}`, filename: f, page: n, snippet: '' }] : [];
    if (type === 'tf') return { type, text: L.genericTf(f), answers: [{ text: L.true, is_correct: true }, { text: L.false, is_correct: false }], citations, difficulty };
    if (type === 'open') return { type, text: L.genericOpen(f), answers: [{ text: L.modelAnswer, is_correct: true }], citations, difficulty };
    return { type, text: L.genericMcq(f, n), answers: L.genericAns.map((text, i) => ({ text, is_correct: i === 0 })), citations, difficulty };
  }
  const words = s.text.match(WORD) ?? [];
  const citations = [cite(s)];
  if (type === 'mcq' && words.length) {
    const key = words.reduce((a, b) => (b.length > a.length ? b : a));
    const distractors = [...new Set(pool.filter((w) => w.toLowerCase() !== key.toLowerCase()))]
      .sort(() => rand() - 0.5)
      .slice(0, 3);
    while (distractors.length < 3) distractors.push(`${key.slice(0, -2)}${'xyz'[distractors.length]}`);
    const answers = [{ text: key, is_correct: true }, ...distractors.map((text) => ({ text, is_correct: false }))].sort(() => rand() - 0.5);
    return { type, text: L.fill(s.text.replace(key, '_____')), answers, citations, difficulty };
  }
  if (type === 'tf' || (type === 'mcq' && !words.length)) {
    const flip = rand() < 0.5 && words.length > 0 && pool.length > 1;
    let statement = s.text;
    if (flip) {
      const w = words[Math.floor(rand() * words.length)];
      const other = pool.find((p) => p.toLowerCase() !== w.toLowerCase()) ?? w;
      statement = s.text.replace(w, other);
    }
    return {
      type: 'tf',
      text: L.tf(statement),
      answers: [
        { text: L.true, is_correct: !flip },
        { text: L.false, is_correct: flip },
      ],
      citations,
      difficulty,
    };
  }
  const cut = s.text.split(/[,;:]/)[0];
  return { type: 'open', text: L.open(cut.length > 30 ? cut : s.text), answers: [{ text: s.text, is_correct: true }], citations, difficulty };
}

export function generateExam(
  topicName: string,
  files: MockFile[],
  opts: GenerationOptions,
  newId: () => string,
  salt = '',
): { title: string; questions: Question[] } {
  const rand = rng(hash(topicName + salt + JSON.stringify(opts)));
  const all = sentencesOf(files).sort(() => rand() - 0.5);
  const pool = [...new Set(all.flatMap((s) => s.text.match(WORD) ?? []))];
  const questions: Question[] = [];
  for (let i = 0; i < opts.count; i += 1) {
    const type = opts.types[i % opts.types.length];
    const s = all.length ? all[i % all.length] : null;
    questions.push({ id: newId(), ...makeQuestion(type, s, pool, opts.exam_language, opts.difficulty, rand, i + 1, files[i % Math.max(files.length, 1)]) });
  }
  return { title: T[opts.exam_language].title(topicName), questions };
}

export function regenerateQuestion(q: Question, files: MockFile[], lang: Language, newId: () => string): Question {
  const salt = `${q.id}-${Date.now()}`;
  const [fresh] = generateExam('x', files, { count: 1, types: [q.type], difficulty: q.difficulty, exam_language: lang, mode: 'fast' }, newId, salt).questions;
  return { ...fresh, id: q.id };
}

/** Very small retrieval for "ask" messages: best keyword overlap. */
export function answerQuestion(question: string, files: MockFile[], lang: Language): { content: string; citations: Citation[] } {
  const terms = new Set((question.toLowerCase().match(/[\p{L}]{4,}/gu) ?? []).map((w) => w.slice(0, 6)));
  const scored = sentencesOf(files)
    .map((s) => ({ s, score: (s.text.toLowerCase().match(/[\p{L}]{4,}/gu) ?? []).filter((w) => terms.has(w.slice(0, 6))).length }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 2);
  if (!scored.length) {
    return {
      content: lang === 'hu' ? 'Erre nem találtam választ a téma dokumentumaiban.' : "I couldn't find an answer to that in this topic's documents.",
      citations: [],
    };
  }
  const intro = lang === 'hu' ? 'A dokumentumaid alapján:' : 'Based on your documents:';
  return { content: `${intro} ${scored.map((x) => x.s.text).join(' ')}`, citations: scored.map((x) => cite(x.s)) };
}
