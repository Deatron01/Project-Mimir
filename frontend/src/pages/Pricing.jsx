import React from 'react';
import { motion } from 'framer-motion';
import { Check, Minus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Button from '../components/ui/Button';
import useDocumentTitle from '../hooks/useDocumentTitle';

export default function Pricing() {
  const { t } = useTranslation();
  useDocumentTitle('meta.pricing');
  const list = (key) => t(key, { returnObjects: true });

  return (
    <div className="relative min-h-[80vh] overflow-hidden">
      <div className="pointer-events-none absolute right-[-10%] top-[10%] h-[40rem] w-[40rem] rounded-full bg-primary/20 blur-[120px]" aria-hidden="true" />

      <section className="relative mx-auto max-w-6xl px-6 pb-16 pt-24 text-center">
        <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6 text-4xl font-extrabold tracking-tight md:text-6xl">
          {t('pricing.title')}
        </motion.h1>
        <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mx-auto mb-16 max-w-2xl text-lg text-muted">
          {t('pricing.subtitle')}
        </motion.p>

        <div className="mx-auto grid max-w-4xl gap-8 text-left md:grid-cols-2">
          {/* Free tier */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col rounded-3xl border border-border/50 bg-surface/20 p-8 backdrop-blur-sm"
          >
            <h2 className="mb-2 text-2xl font-bold">{t('pricing.free.name')}</h2>
            <div className="mb-6 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-textMain">{t('pricing.free.price')}</span>
              <span className="text-muted">{t('pricing.free.period')}</span>
            </div>
            <p className="mb-8 min-h-10 text-sm text-muted">{t('pricing.free.desc')}</p>
            <ul className="mb-8 flex flex-grow flex-col gap-4">
              {list('pricing.free.features').map((f) => (
                <li key={f} className="flex items-center gap-3 text-sm">
                  <Check size={18} className="text-success" aria-hidden="true" /> {f}
                </li>
              ))}
              {list('pricing.free.notIncluded').map((f) => (
                <li key={f} className="flex items-center gap-3 text-sm text-muted line-through decoration-muted/60">
                  <Minus size={18} aria-hidden="true" /> {f}
                  <span className="sr-only">({t('pricing.notIncludedLabel')})</span>
                </li>
              ))}
            </ul>
            <Button variant="outline" className="w-full">
              {t('pricing.free.cta')}
            </Button>
          </motion.div>

          {/* Pro tier */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="relative flex flex-col overflow-hidden rounded-3xl border border-accent bg-gradient-to-b from-surface/40 to-background p-8"
          >
            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-accent to-primary" />
            <div className="absolute right-6 top-6 rounded-full bg-accent/15 px-3 py-1 text-xs font-bold uppercase text-accent">
              {t('pricing.pro.badge')}
            </div>
            <h2 className="mb-2 text-2xl font-bold">{t('pricing.pro.name')}</h2>
            <div className="mb-6 flex items-baseline gap-2">
              <span className="bg-gradient-to-r from-accent to-primary bg-clip-text text-4xl font-extrabold text-transparent">{t('pricing.pro.price')}</span>
              <span className="text-muted">{t('pricing.pro.period')}</span>
            </div>
            <p className="mb-8 min-h-10 text-sm text-muted">{t('pricing.pro.desc')}</p>
            <ul className="mb-8 flex flex-grow flex-col gap-4">
              {list('pricing.pro.features').map((f) => (
                <li key={f} className="flex items-center gap-3 text-sm">
                  <Check size={18} className="text-accent" aria-hidden="true" /> {f}
                </li>
              ))}
            </ul>
            <Button className="w-full">{t('pricing.pro.cta')}</Button>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
