import { motion } from 'framer-motion';
import { ArrowRight, FileText, ListChecks, Printer, ShieldCheck, Sparkles, Target } from 'lucide-react';
import { Trans, useTranslation } from 'react-i18next';
import ButtonLink from '../components/ui/ButtonLink';
import Mascot from '../components/mascot/Mascot';
import HowItWorks from '../components/common/HowItWorks';
import { useAuth } from '../context/AuthContext';
import useDocumentTitle from '../hooks/useDocumentTitle';

const fadeInUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' } },
};

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.12 } } };

const gradientText = 'text-transparent bg-clip-text bg-gradient-to-r from-accent via-primary to-accent';

export default function Home() {
  const { t } = useTranslation();
  const { user, mode } = useAuth();
  useDocumentTitle('meta.home');
  const appPath = mode === 'v1' ? '/topics' : '/chat';

  const features = [
    { key: 'rag', icon: Target },
    { key: 'secure', icon: ShieldCheck },
    { key: 'export', icon: Printer },
  ];

  return (
    <div className="relative overflow-hidden">
      {/* Hero */}
      <section className="relative z-10 mx-auto grid max-w-7xl items-center gap-12 px-4 pb-16 pt-12 md:px-6 lg:grid-cols-[1.1fr_1fr] lg:pt-20">
        <motion.div initial="hidden" animate="visible" variants={stagger} className="flex flex-col items-center text-center lg:items-start lg:text-left">
          <motion.p
            variants={fadeInUp}
            className="mb-5 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-sm font-semibold text-accent"
          >
            <Sparkles size={16} aria-hidden="true" />
            {t('home.badge')}
          </motion.p>

          <motion.h1 variants={fadeInUp} className="mb-6 text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl md:text-6xl">
            <Trans i18nKey="home.title" components={{ 1: <span className={gradientText} /> }} />
          </motion.h1>

          <motion.p variants={fadeInUp} className="mb-8 max-w-xl text-lg leading-relaxed text-muted">
            {t('home.subtitle')}
          </motion.p>

          <motion.div variants={fadeInUp} className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
            <ButtonLink to={user ? appPath : '/register'} size="lg" className="group w-full shadow-lg shadow-primary/20 sm:w-auto">
              {user ? t('home.ctaApp') : t('home.ctaTry')}
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </ButtonLink>
            <ButtonLink href="#how-it-works" variant="outline" size="lg" className="w-full sm:w-auto">
              {t('home.howItWorks')}
            </ButtonLink>
          </motion.div>
        </motion.div>

        <ClassPreview />
      </section>

      {/* How it works */}
      <div id="how-it-works" className="relative z-10 mx-auto max-w-6xl scroll-mt-24 px-4 py-16 md:px-6">
        <HowItWorks />
      </div>

      {/* Features */}
      <section aria-labelledby="features-title" className="relative mx-auto max-w-7xl px-4 py-16 md:px-6">
        <motion.h2
          id="features-title"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-80px' }}
          variants={fadeInUp}
          className="mb-10 text-center text-2xl font-extrabold leading-tight tracking-tight md:text-4xl"
        >
          <Trans i18nKey="home.featuresTitle" components={{ 1: <span className="bg-gradient-to-r from-accent to-primary bg-clip-text text-transparent" /> }} />
        </motion.h2>

        <div className="grid gap-5 md:grid-cols-3">
          {features.map(({ key, icon: Icon }, idx) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1, duration: 0.3 }}
              whileHover={{ y: -4 }}
              className="group rounded-3xl border border-border/30 bg-surface/20 p-7 transition-colors hover:border-accent/40 hover:bg-surface/40"
            >
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/15 text-accent transition-transform duration-300 group-hover:scale-110">
                <Icon size={24} aria-hidden="true" />
              </div>
              <h3 className="mb-2 text-lg font-bold leading-tight">{t(`home.features.${key}.title`)}</h3>
              <p className="text-sm leading-relaxed text-muted">{t(`home.features.${key}.desc`)}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="relative mx-auto max-w-4xl px-4 py-16 md:px-6">
        <div className="flex flex-col items-center gap-6 rounded-[2rem] border border-border/40 bg-surface/30 px-6 py-12 text-center md:flex-row md:text-left">
          <Mascot mood="happy" size={120} />
          <div className="flex-1">
            <h2 className="mb-2 text-2xl font-bold md:text-3xl">{t('home.ctaTitle')}</h2>
            <p className="mb-6 text-muted">{t('home.ctaSubtitle')}</p>
            <ButtonLink to={user ? appPath : '/register'} size="lg" className="shadow-lg shadow-primary/20">
              {user ? t('home.ctaStart') : t('home.ctaRegister')}
            </ButtonLink>
          </div>
        </div>
      </section>
    </div>
  );
}

/** Illustration: a few example classes and the mascot offering a test. Decorative, but its text is real. */
function ClassPreview() {
  const { t } = useTranslation();
  const classes = t('home.preview.classes', { returnObjects: true }) as string[];
  const stats = [
    { docs: 4, tests: 6 },
    { docs: 2, tests: 3 },
    { docs: 7, tests: 9 },
  ];
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.25 }}
      className="relative mx-auto w-full max-w-md"
    >
      <ul className="flex flex-col gap-3" aria-label={t('home.preview.label')}>
        {classes.map((name, i) => (
          <motion.li
            key={name}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.45 + i * 0.12 }}
            className={
              'flex items-center gap-4 rounded-2xl border bg-background/70 p-4 shadow-lg backdrop-blur ' +
              (i === 0 ? 'border-accent/60 ring-2 ring-accent/30' : 'border-border/40')
            }
            style={{ marginLeft: `${i * 6}%`, marginRight: `${(2 - i) * 6}%` }}
          >
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-lg font-extrabold text-onPrimary" aria-hidden="true">
              {name.charAt(0)}
            </span>
            <div className="min-w-0">
              <p className="truncate font-bold text-textMain">{name}</p>
              <p className="flex flex-wrap gap-x-3 text-xs text-muted">
                <span className="inline-flex items-center gap-1">
                  <FileText size={12} aria-hidden="true" /> {t('home.preview.docs', { count: stats[i].docs })}
                </span>
                <span className="inline-flex items-center gap-1">
                  <ListChecks size={12} aria-hidden="true" /> {t('home.preview.tests', { count: stats[i].tests })}
                </span>
              </p>
            </div>
          </motion.li>
        ))}
      </ul>
      <div className="mt-6 flex justify-center lg:justify-end">
        <Mascot mood="wave" size={110} say={t('home.preview.bubble')} />
      </div>
    </motion.div>
  );
}
