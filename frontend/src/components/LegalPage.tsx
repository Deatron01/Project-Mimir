import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import useDocumentTitle from '../hooks/useDocumentTitle';

/**
 * Renders a legal document (privacy / terms) from the `legal.<doc>` translation block.
 * A section may have `body` (string), `paragraphs` (string[]), `list` (string[]) and `table` ({ head, rows }).
 */
interface LegalTableData {
  head: string[];
  rows: string[][];
}
interface LegalSection {
  heading: string;
  body?: string;
  list?: string[];
  paragraphs?: string[];
  table?: LegalTableData;
}

export default function LegalPage({ doc }: { doc: 'privacy' | 'terms' }) {
  const { t } = useTranslation();
  useDocumentTitle(`meta.${doc}`);
  const sections = t(`legal.${doc}.sections`, { returnObjects: true }) as unknown as LegalSection[] | string;
  const updated = t(`legal.${doc}.updated`, { defaultValue: '' });
  const intro = t(`legal.${doc}.intro`, { defaultValue: '' });

  return (
    <div className="relative min-h-[80vh] overflow-hidden py-20">
      <div className="pointer-events-none absolute left-[-10%] top-[10%] h-[30rem] w-[30rem] rounded-full bg-surface/30 blur-[100px]" aria-hidden="true" />
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative z-10 mx-auto max-w-5xl px-6">
        <article className="card p-8 md:p-12">
          <h1 className="mb-3 text-3xl font-extrabold tracking-tight md:text-4xl">{t(`legal.${doc}.title`)}</h1>
          {updated && <p className="mb-8 text-sm text-muted">{updated}</p>}
          <div className="space-y-6 text-sm leading-relaxed text-muted md:text-base">
            {intro && <p className="text-textMain">{intro}</p>}
            {Array.isArray(sections) &&
              sections.map((s) => (
                <section key={s.heading} aria-labelledby={slug(s.heading)}>
                  <h2 id={slug(s.heading)} className="mb-4 mt-10 text-xl font-bold text-textMain">
                    {s.heading}
                  </h2>
                  {s.body && <p>{s.body}</p>}
                  {s.list && (
                    <ul className="mb-4 list-disc space-y-2 pl-6">
                      {s.list.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  )}
                  {s.paragraphs?.map((p) => (
                    <p key={p} className="mb-3">
                      {p}
                    </p>
                  ))}
                  {s.table && <LegalTable table={s.table} />}
                </section>
              ))}
          </div>
        </article>
      </motion.div>
    </div>
  );
}

const slug = (text: string) =>
  `sec-${text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[^\w]+/g, '-')
    .replace(/^-|-$/g, '')}`;

function LegalTable({ table }: { table: LegalTableData }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border/40">
      <table className="w-full min-w-[720px] border-collapse text-left text-sm">
        <thead className="bg-surface/50 text-xs uppercase tracking-wider text-textMain">
          <tr>
            {table.head.map((h) => (
              <th key={h} scope="col" className="p-3 font-semibold">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border/30 align-top">
          {table.rows.map((row) => (
            <tr key={row[0]}>
              {row.map((cell, i) =>
                i === 0 ? (
                  <th key={i} scope="row" className="p-3 font-semibold text-textMain">
                    {cell}
                  </th>
                ) : (
                  <td key={i} className="p-3">
                    {cell}
                  </td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
