import React from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from './Navbar';
import Footer from './Footer';

export default function Layout({ children }) {
  const { t } = useTranslation();
  return (
    <div className="relative flex min-h-screen flex-col selection:bg-accent/30 selection:text-textMain">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-full focus:bg-primary focus:px-4 focus:py-2 focus:text-onPrimary"
      >
        {t('nav.skipToContent')}
      </a>

      {/* Global background glow – uses the palette's original brand colours in both modes. */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-background" aria-hidden="true">
        <div className="absolute left-[-10%] top-[-15%] h-[50rem] w-[50rem] rounded-full bg-brandPrimary opacity-30 blur-[100px] transition-colors duration-1000 ease-in-out" />
        <div className="absolute right-[-15%] top-[20%] h-[45rem] w-[45rem] rounded-full bg-brandAccent opacity-25 blur-[100px] transition-colors duration-1000 ease-in-out" />
        <div className="absolute bottom-[-10%] left-[5%] h-[50rem] w-[50rem] rounded-full bg-surface opacity-70 blur-[90px] transition-colors duration-1000 ease-in-out" />
      </div>

      <Navbar />

      <main id="main" tabIndex={-1} className="relative z-10 flex-grow pt-20 focus:outline-none">
        {children}
      </main>

      <div className="relative z-10">
        <Footer />
      </div>
    </div>
  );
}
