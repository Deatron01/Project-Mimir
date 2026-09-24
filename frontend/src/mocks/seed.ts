import type { DB, MockFile, MockTopic } from './db';
import { generateExam } from './generator';

export const DEMO_EMAIL = 'demo@mimir.hu';
export const DEMO_PASSWORD = 'mimir-demo-2026';

const SAMPLE_TEXT = `# Fotoszintézis
A fotoszintézis az a folyamat, amelynek során a zöld növények a napfény energiáját kémiai energiává alakítják.
A folyamat a kloroplasztiszokban zajlik, amelyek klorofill nevű zöld színanyagot tartalmaznak.
A fényszakaszban a víz bontása során oxigén szabadul fel, és ATP valamint NADPH keletkezik.
A sötétszakasz, más néven Calvin-ciklus, a sztrómában megy végbe, és szén-dioxidból szőlőcukrot állít elő.
A fotoszintézis sebességét a fényintenzitás, a szén-dioxid-koncentráció és a hőmérséklet befolyásolja.
A légzés és a fotoszintézis egymást kiegészítő folyamatok, mert az egyik terméke a másik kiindulási anyaga.
A C4-es növények, például a kukorica, meleg és száraz körülmények között hatékonyabban kötik meg a szén-dioxidot.
A klorofill elsősorban a vörös és a kék fényt nyeli el, a zöld fényt pedig visszaveri, ezért látjuk zöldnek a leveleket.`;

/** Seeds a verified demo account with one ready topic and a saved test, so the mock is useful on first load. */
export function seed(db: DB): void {
  let n = 0;
  const id = (p: string) => `${p}_seed${(n += 1)}`;
  const t0 = new Date(Date.now() - 3 * 86_400_000).toISOString();
  const user = { id: 'usr_demo', email: DEMO_EMAIL, password: DEMO_PASSWORD, language: 'hu' as const, verified: true, created_at: t0 };
  db.users.push(user);

  const topic: MockTopic = {
    id: 'top_demo',
    user_id: user.id,
    name: 'Fotoszintézis (demo)',
    description: 'Biológia 9. évfolyam – minta téma a próbaüzemhez.',
    status: 'active',
    file_count: 1,
    total_bytes: new Blob([SAMPLE_TEXT]).size,
    saved_test_count: 1,
    created_at: t0,
    updated_at: t0,
    last_activity_at: t0,
    expires_at: new Date(Date.parse(t0) + 90 * 86_400_000).toISOString(),
  };
  db.topics.push(topic);

  const file: MockFile = {
    id: 'fil_demo',
    topic_id: topic.id,
    user_id: user.id,
    filename: 'fotoszintezis.md',
    mime: 'text/markdown',
    size_bytes: topic.total_bytes,
    status: 'ready',
    error_code: null,
    chunk_count: 3,
    page_count: 1,
    created_at: t0,
    text: SAMPLE_TEXT,
  };
  db.files.push(file);

  const session = { id: 'ses_demo', topic_id: topic.id, user_id: user.id, title: 'Első dolgozat', message_count: 2, created_at: t0, updated_at: t0 };
  db.sessions.push(session);
  const options = { count: 5, types: ['mcq', 'tf'] as ('mcq' | 'tf')[], difficulty: 'medium' as const, exam_language: 'hu' as const, mode: 'fast' as const };
  const exam = generateExam(topic.name, [file], options, () => id('q'));
  const test = {
    id: 'tst_demo',
    topic_id: topic.id,
    session_id: session.id,
    user_id: user.id,
    title: exam.title,
    question_count: exam.questions.length,
    saved: true,
    created_at: t0,
    updated_at: t0,
    exam,
  };
  db.tests.push(test);
  db.messages.push(
    { id: 'msg_demo1', session_id: session.id, topic_id: topic.id, role: 'user', content: 'Készíts egy 5 kérdéses dolgozatot a fotoszintézisről.', job_id: null, test_id: null, options, created_at: t0 },
    { id: 'msg_demo2', session_id: session.id, topic_id: topic.id, role: 'assistant', content: 'Elkészült a 5 kérdéses teszt. Nézd át és szerkeszd, mielőtt felhasználod.', job_id: null, test_id: test.id, created_at: t0 },
  );
}
