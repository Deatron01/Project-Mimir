import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ButtonLink from '../ui/ButtonLink';
import Button from '../ui/Button';
import { useAuth } from '../../context/AuthContext';
import SettingsMenu, { SettingsPanelContent } from '../settings/SettingsMenu';
import ModeToggle from '../settings/ModeToggle';
import LanguageSwitcher from '../settings/LanguageSwitcher';
import { cn } from '../../utils/cn';
import QueueIndicator from './QueueIndicator';

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn('text-sm font-medium transition-colors', isActive ? 'text-textMain underline decoration-accent decoration-2 underline-offset-8' : 'text-textMain hover:text-accent');

export default function Navbar() {
  const { t } = useTranslation();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout, mode } = useAuth();
  const appPath = mode === 'v1' ? '/topics' : '/chat';
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Close the mobile menu on navigation.
  useEffect(() => setMobileOpen(false), [location.pathname]);

  const links = [
    { to: '/', label: t('nav.home'), end: true },
    { to: '/about', label: t('nav.about') },
    { to: '/pricing', label: t('nav.pricing') },
    ...(user && mode === 'v1' ? [{ to: '/topics', label: t('nav.topics') }] : []),
    ...(user ? [{ to: '/tests', label: t('nav.tests') }] : []),
  ];

  return (
    <header
      className={cn(
        'fixed top-0 z-50 w-full transition-all duration-300',
        isScrolled || mobileOpen ? 'border-b border-border/40 bg-background/85 shadow-lg backdrop-blur-md' : 'bg-transparent',
      )}
    >
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between gap-4 px-6">
        <Link to="/" className="flex items-center gap-2" aria-label={t('common.appName')}>
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-primary to-accent" aria-hidden="true" />
          <span className="text-xl font-bold tracking-tight text-textMain">Mimir</span>
        </Link>

        <nav aria-label={t('nav.main')} className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <LanguageSwitcher />
          <ModeToggle />
          <SettingsMenu />
          <span className="mx-1 h-6 w-px bg-border/50" aria-hidden="true" />
          {user ? (
            <>
              {mode === 'v1' && <QueueIndicator />}
              <ButtonLink to={appPath} size="sm">{t('nav.openApp')}</ButtonLink>
              <Button variant="ghost" size="sm" onClick={() => void logout()}>
                {t('nav.logout')}
              </Button>
            </>
          ) : (
            <>
              <ButtonLink to="/login" variant="ghost" size="sm">
                  {t('nav.login')}
                </ButtonLink>
              <ButtonLink to="/register" size="sm">{t('nav.register')}</ButtonLink>
            </>
          )}
        </div>

        <div className="flex items-center gap-1 md:hidden">
          <ModeToggle />
          <button
            type="button"
            className="p-2 text-textMain"
            onClick={() => setMobileOpen((v) => !v)}
            aria-expanded={mobileOpen}
            aria-controls="mobile-menu"
            aria-label={mobileOpen ? t('nav.closeMenu') : t('nav.openMenu')}
          >
            {mobileOpen ? <X size={24} aria-hidden="true" /> : <Menu size={24} aria-hidden="true" />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            id="mobile-menu"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="max-h-[calc(100vh-5rem)] overflow-y-auto border-b border-border/40 bg-background px-6 py-4 shadow-xl md:hidden"
          >
            <nav aria-label={t('nav.main')} className="flex flex-col">
              {links.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  end={l.end}
                  className={({ isActive }) =>
                    cn('border-b border-border/30 py-3', isActive ? 'text-accent' : 'text-textMain')
                  }
                >
                  {l.label}
                </NavLink>
              ))}
            </nav>

            <div className="flex flex-col gap-2 pt-4">
              {user ? (
                <>
                  <ButtonLink to={appPath} className="w-full">{t('nav.openApp')}</ButtonLink>
                  <Button variant="outline" className="w-full" onClick={() => void logout()}>
                    {t('nav.logout')}
                  </Button>
                </>
              ) : (
                <>
                  <ButtonLink to="/login" variant="outline" className="w-full">
                      {t('nav.login')}
                    </ButtonLink>
                  <ButtonLink to="/register" className="w-full">{t('nav.register')}</ButtonLink>
                </>
              )}
            </div>

            <div className="mt-6 border-t border-border/30 pt-4">
              <SettingsPanelContent />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
