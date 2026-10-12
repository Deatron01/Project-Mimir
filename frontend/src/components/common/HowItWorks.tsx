import { motion } from 'framer-motion';
import { FolderPlus, ListChecks, UploadCloud } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';

const STEPS = [
  { key: 'create', icon: FolderPlus },
  { key: 'upload', icon: UploadCloud },
  { key: 'generate', icon: ListChecks },
] as const;

/** The three-step "class → documents → tests" explainer, used on the home page and the class dashboard. */
export default function HowItWorks({ compact = false, className, headingLevel = 2 }: { compact?: boolean; className?: string; headingLevel?: 2 | 3 }) {
  const { t } = useTranslation();
  const H = `h${headingLevel}` as const;
  const Item = `h${headingLevel + 1}` as 'h3' | 'h4';
  return (
    <section aria-labelledby="how-title" className={className}>
      <H id="how-title" className={cn(compact ? 'sr-only' : 'mb-8 text-center text-2xl font-extrabold tracking-tight md:text-4xl')}>
        {t('topics.steps.title')}
      </H>
      <ol className={cn('grid gap-3', compact ? 'sm:grid-cols-3' : 'gap-5 md:grid-cols-3')}>
        {STEPS.map(({ key, icon: Icon }, i) => (
          <motion.li
            key={key}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.08, duration: 0.25 }}
            className={cn(
              'relative flex items-start gap-3 rounded-2xl border border-border/40 bg-surface/30',
              compact ? 'p-3' : 'flex-col p-6',
            )}
          >
            <span
              className={cn(
                'flex shrink-0 items-center justify-center rounded-2xl bg-primary text-onPrimary shadow-sm',
                compact ? 'h-10 w-10' : 'h-14 w-14',
              )}
              aria-hidden="true"
            >
              <Icon size={compact ? 18 : 26} />
            </span>
            <div className="min-w-0">
              <Item className={cn('font-bold leading-tight text-textMain', compact ? 'text-sm' : 'mb-1 text-lg')}>
                <span className="mr-1 text-accent">{i + 1}.</span>
                {t(`topics.steps.${key}.title`)}
              </Item>
              <p className={cn('text-muted', compact ? 'text-xs' : 'text-sm leading-relaxed')}>{t(`topics.steps.${key}.desc`)}</p>
            </div>
          </motion.li>
        ))}
      </ol>
    </section>
  );
}
