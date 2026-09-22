import React from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import useDocumentTitle from '../hooks/useDocumentTitle';

/** Renders a legal document (privacy / terms) from the `legal.<doc>` translation block. */
export default function LegalPage({ doc }) {
  const { t } = useTranslation();
  useDocumentTitle(`meta.${doc}`);
  const sections = t(`legal.${doc}.sections`, { returnObjects: true });
  const lead = t(`legal.${doc}.updated`, { defaultValue: '' }) || t(`legal.${doc}.intro`, { defaultValue: '' });

  return (
    <div className="relative min-h-[80vh] overflow-hidden py-20">
      <div className="pointer-events-none absolute left-[-10%] top-[10%] h-[30rem] w-[30rem] rounded-full bg-surface/30 blur-[100px]" aria-hidden="true" />
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative z-10 mx-auto max-w-4xl px-6">
        <article className="card p-8 md:p-12">
          <h1 className="mb-8 text-3xl font-extrabold tracking-tight md:text-4xl">{t(`legal.${doc}.title`)}</h1>
          <div className="space-y-6 text-sm leading-relaxed text-muted md:text-base">
            {lead && <p>{lead}</p>}
            {Array.isArray(sections) &&
              sections.map((s) => (
                <section key={s.heading}>
                  <h2 className="mb-4 mt-8 text-xl font-bold text-textMain">{s.heading}</h2>
                  {s.body && <p>{s.body}</p>}
                  {s.list && (
                    <ul className="list-disc space-y-2 pl-6">
                      {s.list.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  )}
                </section>
              ))}
          </div>
        </article>
      </motion.div>
    </div>
  );
}
