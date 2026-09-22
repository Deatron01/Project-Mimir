import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Zap, Shield, Sparkles, FileText, Bot, User, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Trans, useTranslation } from 'react-i18next';
import Button from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import useDocumentTitle from '../hooks/useDocumentTitle';

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.2 } },
};

const gradientText = 'text-transparent bg-clip-text bg-gradient-to-r from-accent via-primary to-accent';

export default function Home() {
  const { t } = useTranslation();
  const { user } = useAuth();
  useDocumentTitle('meta.home');

  const features = [
    { key: 'rag', icon: Zap },
    { key: 'secure', icon: Shield },
    { key: 'export', icon: Sparkles },
  ];

  return (
    <div className="relative overflow-hidden">
      {/* Hero */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-12 pt-24 text-center lg:pt-32">
        <motion.div initial="hidden" animate="visible" variants={staggerContainer} className="mx-auto flex max-w-4xl flex-col items-center">
          <motion.div
            variants={fadeInUp}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-sm font-medium text-accent shadow-lg shadow-accent/10 backdrop-blur-sm"
          >
            <Sparkles size={16} aria-hidden="true" />
            <span>{t('home.badge')}</span>
          </motion.div>

          <motion.h1 variants={fadeInUp} className="mb-8 text-5xl font-extrabold leading-tight tracking-tight md:text-7xl">
            <Trans i18nKey="home.title" components={{ 1: <span className={gradientText} /> }} />
          </motion.h1>

          <motion.p variants={fadeInUp} className="mb-10 max-w-2xl text-lg leading-relaxed text-muted md:text-xl">
            {t('home.subtitle')}
          </motion.p>

          <motion.div variants={fadeInUp} className="flex flex-col gap-4 sm:flex-row">
            <Link to={user ? '/chat' : '/login'}>
              <Button size="lg" className="group w-full shadow-lg shadow-accent/20 sm:w-auto">
                {user ? t('home.ctaApp') : t('home.ctaTry')}
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" aria-hidden="true" />
              </Button>
            </Link>
            <a href="#features">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                {t('home.howItWorks')}
              </Button>
            </a>
          </motion.div>
        </motion.div>
      </section>

      {/* Product mock-up */}
      <section className="relative z-10 mx-auto mb-24 mt-8 max-w-5xl px-6" aria-hidden="true">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="overflow-hidden rounded-3xl border border-border/50 bg-background/50 shadow-2xl shadow-primary/10 backdrop-blur-xl"
        >
          <div className="flex items-center gap-2 border-b border-border/50 bg-surface/40 px-6 py-4">
            <div className="flex gap-2">
              <div className="h-3 w-3 rounded-full bg-red-500/80" />
              <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <div className="h-3 w-3 rounded-full bg-green-500/80" />
            </div>
            <span className="ml-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-muted">
              <Bot size={14} className="text-accent" /> {t('home.mock.title')}
            </span>
          </div>

          <div className="space-y-8 bg-gradient-to-b from-surface/10 to-transparent p-6 md:p-10">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8 }}
              className="ml-auto flex max-w-[85%] flex-row-reverse gap-4"
            >
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-border bg-surface text-textMain">
                <User size={20} />
              </div>
              <div className="rounded-2xl rounded-tr-none border border-border/30 bg-surface p-4 text-textMain shadow-md">
                <div className="mb-3 flex w-max items-center gap-2 rounded-lg border border-border/50 bg-background/60 p-2 text-xs">
                  <FileText size={14} className="text-accent" /> <span className="font-mono">{t('home.mock.fileName')}</span>
                </div>
                <p className="text-sm leading-relaxed md:text-base">{t('home.mock.userMessage')}</p>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.5 }} className="flex max-w-[85%] gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-primary/30 bg-primary/20 text-accent shadow-md shadow-accent/20">
                <Bot size={20} />
              </div>
              <div className="relative overflow-hidden rounded-2xl rounded-tl-none border border-primary/30 bg-background/80 p-5 shadow-lg">
                <div className="absolute left-0 top-0 h-full w-1 bg-accent" />
                <p className="mb-4 text-sm leading-relaxed md:text-base">{t('home.mock.aiMessage')}</p>
                <div className="mb-4 flex items-center gap-2 text-sm font-medium text-success">
                  <CheckCircle size={16} /> {t('home.mock.check')}
                </div>
                <Button size="sm" tabIndex={-1} className="shadow-lg hover:shadow-accent/20">
                  <FileText size={16} /> {t('home.mock.download')}
                </Button>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section id="features" className="relative mx-auto max-w-7xl scroll-mt-24 border-t border-border/20 px-6 py-24">
        <div className="absolute left-1/2 top-0 h-px w-3/4 -translate-x-1/2 bg-gradient-to-r from-transparent via-accent/30 to-transparent" />

        <motion.h2
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={fadeInUp}
          className="mb-16 text-center text-3xl font-extrabold leading-tight tracking-tight md:text-5xl"
        >
          <Trans i18nKey="home.featuresTitle" components={{ 1: <span className="bg-gradient-to-r from-accent to-primary bg-clip-text text-transparent" /> }} />
        </motion.h2>

        <div className="grid gap-8 md:grid-cols-3">
          {features.map(({ key, icon: Icon }, idx) => (
            <motion.div
              key={key}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={{ hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { delay: idx * 0.2 } } }}
              className="group rounded-3xl border border-border/30 bg-surface/10 p-8 backdrop-blur-sm transition-all duration-300 hover:border-accent/30 hover:bg-surface/40"
            >
              <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-accent transition-transform duration-300 group-hover:scale-110 group-hover:bg-primary/20">
                <Icon size={28} aria-hidden="true" />
              </div>
              <h3 className="mb-3 text-xl font-bold leading-tight">{t(`home.features.${key}.title`)}</h3>
              <p className="text-sm leading-relaxed text-muted">{t(`home.features.${key}.desc`)}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="relative border-t border-border/20 bg-surface/5 px-6 py-24 text-center">
        <h2 className="mb-6 text-3xl font-bold md:text-4xl">{t('home.ctaTitle')}</h2>
        <p className="mx-auto mb-10 max-w-xl text-muted">{t('home.ctaSubtitle')}</p>
        <Link to={user ? '/chat' : '/register'}>
          <Button size="lg" className="shadow-lg shadow-accent/30">
            {user ? t('home.ctaStart') : t('home.ctaRegister')}
          </Button>
        </Link>
      </section>
    </div>
  );
}
