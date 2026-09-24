/** Export formats produced by the mock (the real ones come from the-forge). */
import type { Exam, ExportRequest, Question } from '../api/types';

const LETTERS = 'ABCDEFGH';

function shuffled<T>(arr: T[], seed: number): T[] {
  const a = [...arr];
  let x = seed || 1;
  for (let i = a.length - 1; i > 0; i -= 1) {
    x = (x * 1103515245 + 12345) & 0x7fffffff;
    const j = x % (i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function variant(exam: Exam, n: number, shuffle: boolean): Exam {
  if (!shuffle && n === 1) return exam;
  const questions = shuffle || n > 1 ? shuffled(exam.questions, n * 7919) : exam.questions;
  return {
    ...exam,
    questions: questions.map((q, i) => (shuffle && q.type === 'mcq' ? { ...q, answers: shuffled(q.answers, n * 31 + i) } : q)),
  };
}

// ---------- minimal text PDF (Helvetica, WinAnsi) ----------
const TRANSLIT: Record<string, string> = { ő: 'ö', Ő: 'Ö', ű: 'ü', Ű: 'Ü', '–': '-', '—': '-', '„': '"', '”': '"', '“': '"', '’': "'", '…': '...' };
function winAnsi(s: string): number[] {
  return [...s].map((ch) => {
    const c = TRANSLIT[ch] ?? ch;
    const code = c.charCodeAt(0);
    return code < 256 ? code : 63;
  });
}
function pdfString(s: string): string {
  return winAnsi(s)
    .map((b) => (b === 40 || b === 41 || b === 92 ? `\\${String.fromCharCode(b)}` : b < 32 || b > 126 ? `\\${b.toString(8).padStart(3, '0')}` : String.fromCharCode(b)))
    .join('');
}
function wrap(text: string, max = 90): string[] {
  const out: string[] = [];
  let line = '';
  for (const w of text.split(/\s+/)) {
    if ((line + ' ' + w).trim().length > max) {
      out.push(line);
      line = w;
    } else line = (line + ' ' + w).trim();
  }
  if (line) out.push(line);
  return out;
}

export function simplePdf(lines: { text: string; size?: number; bold?: boolean }[]): Uint8Array {
  const pages: string[] = [];
  let y = 800;
  let cur = '';
  for (const l of lines) {
    const size = l.size ?? 11;
    for (const part of l.text ? wrap(l.text, size > 12 ? 60 : 90) : ['']) {
      if (y < 50) {
        pages.push(cur);
        cur = '';
        y = 800;
      }
      cur += `BT /${l.bold ? 'F2' : 'F1'} ${size} Tf 50 ${y} Td (${pdfString(part)}) Tj ET\n`;
      y -= size + 5;
    }
  }
  pages.push(cur);
  const objs: string[] = [];
  const add = (s: string) => objs.push(s);
  add('<< /Type /Catalog /Pages 2 0 R >>');
  add(''); // pages placeholder
  add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>');
  add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>');
  const kids: number[] = [];
  for (const content of pages) {
    const bytes = winAnsiLength(content);
    add(`<< /Length ${bytes} >>\nstream\n${content}endstream`);
    const contentId = objs.length;
    add(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${contentId} 0 R >>`);
    kids.push(objs.length);
  }
  objs[1] = `<< /Type /Pages /Kids [${kids.map((k) => `${k} 0 R`).join(' ')}] /Count ${kids.length} >>`;
  let body = '%PDF-1.4\n';
  const offsets: number[] = [];
  objs.forEach((o, i) => {
    offsets.push(body.length);
    body += `${i + 1} 0 obj\n${o}\nendobj\n`;
  });
  const xref = body.length;
  body += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n${offsets.map((o) => `${String(o).padStart(10, '0')} 00000 n \n`).join('')}`;
  body += `trailer\n<< /Size ${objs.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
  return new Uint8Array([...body].map((c) => c.charCodeAt(0) & 0xff));
}
const winAnsiLength = (s: string) => s.length; // content is already escaped to 1 byte per char

function examLines(exam: Exam, withKey: boolean, label: string) {
  const lines: { text: string; size?: number; bold?: boolean }[] = [{ text: `${exam.title}${label}`, size: 16, bold: true }, { text: '' }];
  exam.questions.forEach((q, i) => {
    lines.push({ text: `${i + 1}. ${q.text}`, bold: true });
    if (q.type !== 'open') q.answers.forEach((a, j) => lines.push({ text: `   ${LETTERS[j]}) ${a.text}` }));
    else lines.push({ text: '   ____________________________________________' }, { text: '   ____________________________________________' });
    lines.push({ text: '' });
  });
  if (withKey) {
    lines.push({ text: 'Answer key / Megoldókulcs', size: 13, bold: true });
    exam.questions.forEach((q, i) =>
      lines.push({ text: `${i + 1}. ${q.type === 'open' ? q.answers[0]?.text ?? '' : q.answers.map((a, j) => (a.is_correct ? LETTERS[j] : '')).join('')}` }),
    );
  }
  return lines;
}

// ---------- GIFT / Moodle XML ----------
const giftEsc = (s: string) => s.replace(/([~=#{}:\\])/g, '\\$1');
function gift(q: Question, i: number): string {
  const head = `::Q${i + 1}:: ${giftEsc(q.text)}`;
  if (q.type === 'tf') return `${head} {${q.answers.find((a) => a.is_correct)?.text.match(/^(igaz|true)$/i) ? 'TRUE' : 'FALSE'}}`;
  if (q.type === 'open') return `${head} {}`;
  return `${head} {\n${q.answers.map((a) => `  ${a.is_correct ? '=' : '~'}${giftEsc(a.text)}`).join('\n')}\n}`;
}
const xmlEsc = (s: string) => s.replace(/[<>&"']/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' })[c]!);
function moodle(exam: Exam): string {
  const qs = exam.questions.map((q, i) => {
    const type = q.type === 'mcq' ? 'multichoice' : q.type === 'tf' ? 'truefalse' : 'essay';
    const answers = q.type === 'open' ? '' : q.answers.map((a) => `    <answer fraction="${a.is_correct ? 100 : 0}"><text>${xmlEsc(a.text)}</text></answer>`).join('\n');
    return `  <question type="${type}">\n    <name><text>Q${i + 1}</text></name>\n    <questiontext format="html"><text>${xmlEsc(q.text)}</text></questiontext>\n${answers}${q.type === 'mcq' ? '\n    <single>true</single>' : ''}\n  </question>`;
  });
  return `<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n${qs.join('\n')}\n</quiz>\n`;
}

export function exportExam(exam: Exam, req: ExportRequest): { body: BodyInit; type: string; ext: string } {
  const variants = req.variants ?? 1;
  const list = Array.from({ length: variants }, (_, i) => variant(exam, i + 1, Boolean(req.shuffle_answers) || variants > 1));
  switch (req.format) {
    case 'json':
      return { body: JSON.stringify(variants === 1 ? list[0] : list, null, 2), type: 'application/json', ext: 'json' };
    case 'gift':
      return { body: list.map((e) => e.questions.map(gift).join('\n\n')).join('\n\n'), type: 'text/plain', ext: 'txt' };
    case 'moodle_xml':
      return { body: moodle(list[0]), type: 'application/xml', ext: 'xml' };
    default: {
      const lines = list.flatMap((e, i) => examLines(e, req.format === 'pdf_with_key', variants > 1 ? ` (${'AB'[i]})` : ''));
      return { body: simplePdf(lines) as unknown as BodyInit, type: 'application/pdf', ext: 'pdf' };
    }
  }
}
