import { motion } from 'framer-motion';
import { BrainCircuit, Server, Users } from 'lucide-react';
import { Trans, useTranslation } from 'react-i18next';
import useDocumentTitle from '../hooks/useDocumentTitle';

export default function About() {
  const { t } = useTranslation();
  useDocumentTitle('meta.about');

  const items = [
    { key: 'local', icon: Server },
    { key: 'engine', icon: BrainCircuit },
    { key: 'teachers', icon: Users },
  ];

  return (
    <div className="relative min-h-[80vh] overflow-hidden">
      <div className="pointer-events-none absolute left-[-10%] top-[20%] h-[40rem] w-[40rem] rounded-full bg-surface/30 blur-[120px]" aria-hidden="true" />

      <section className="relative mx-auto max-w-4xl px-6 pb-16 pt-24 text-center">
        <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8 text-4xl font-extrabold tracking-tight md:text-6xl">
          <Trans i18nKey="about.title" components={{ 1: <span className="bg-gradient-to-r from-accent to-primary bg-clip-text text-transparent" /> }} />
        </motion.h1>

        <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mb-16 text-lg leading-relaxed text-muted">
          {t('about.intro')}
        </motion.p>

        <div className="grid gap-6 text-left md:grid-cols-3">
          {items.map(({ key, icon: Icon }, i) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.1 }}
              className="rounded-2xl border border-border/50 bg-surface/20 p-6 backdrop-blur-sm"
            >
              <Icon size={32} className="mb-4 text-accent" aria-hidden="true" />
              <h2 className="mb-2 text-xl font-bold">{t(`about.items.${key}.title`)}</h2>
              <p className="text-sm leading-relaxed text-muted">{t(`about.items.${key}.desc`)}</p>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
