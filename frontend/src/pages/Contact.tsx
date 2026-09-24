import { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, MessageSquare, Send } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Button from '../components/ui/Button';
import useDocumentTitle from '../hooks/useDocumentTitle';

export default function Contact() {
  const { t } = useTranslation();
  useDocumentTitle('meta.contact');
  const [isLoading, setIsLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    setIsLoading(true);
    setSuccessMsg('');
    // Simulated send – there is no contact endpoint yet.
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);
    setSuccessMsg(t('contact.success'));
    form.reset();
  };

  return (
    <div className="relative flex min-h-[80vh] items-center justify-center overflow-hidden py-12">
      <div className="pointer-events-none absolute right-[-10%] top-[20%] h-[40rem] w-[40rem] rounded-full bg-primary/20 blur-[120px]" aria-hidden="true" />

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="z-10 w-full max-w-2xl px-6">
        <div className="mb-10 text-center">
          <h1 className="mb-4 text-4xl font-extrabold tracking-tight md:text-5xl">{t('contact.title')}</h1>
          <p className="text-lg text-muted">{t('contact.subtitle')}</p>
        </div>

        <div className="card p-8">
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <label htmlFor="contact-name" className="mb-2 ml-1 block text-sm font-medium">
                  {t('contact.name')}
                </label>
                <input id="contact-name" name="name" type="text" required autoComplete="name" placeholder={t('contact.namePlaceholder')} className="field" />
              </div>
              <div>
                <label htmlFor="contact-email" className="mb-2 ml-1 block text-sm font-medium">
                  {t('contact.email')}
                </label>
                <div className="relative">
                  <Mail size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
                  <input id="contact-email" name="email" type="email" required autoComplete="email" placeholder={t('auth.emailPlaceholder')} className="field pl-11" />
                </div>
              </div>
            </div>

            <div>
              <label htmlFor="contact-message" className="mb-2 ml-1 block text-sm font-medium">
                {t('contact.message')}
              </label>
              <div className="relative">
                <MessageSquare size={18} className="pointer-events-none absolute left-4 top-3.5 text-muted" aria-hidden="true" />
                <textarea id="contact-message" name="message" required rows={5} placeholder={t('contact.messagePlaceholder')} className="field resize-none pl-11" />
              </div>
            </div>

            <p role="status" aria-live="polite" className="text-center text-sm font-medium text-success empty:hidden">
              {successMsg}
            </p>

            <Button type="submit" isLoading={isLoading} className="group w-full">
              {!isLoading && (
                <>
                  {t('contact.submit')}
                  <Send className="h-4 w-4 transition-transform group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
                </>
              )}
            </Button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
