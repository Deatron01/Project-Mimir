import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { LogOut, Menu, X } from 'lucide-react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ButtonLink from '../ui/ButtonLink';
import Button from '../ui/Button';
import Mascot from '../mascot/Mascot';
import { useAuth } from '../../context/AuthContext';
import SettingsMenu, { SettingsPanelContent } from '../settings/SettingsMenu';
import ModeToggle from '../settings/ModeToggle';
import LanguageSwitcher from '../settings/LanguageSwitcher';
import { cn } from '../../utils/cn';
import QueueIndicator from './QueueIndicator';

export default function Navbar() {
  const { t } = useTranslation();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout, mode } = useAuth();
  const appPath = mode === 'v1' ? '/topics' : '/chat';
  const location = useLocation();
  const inApp = /^\/(topics|tests|chat)(\/|$)/.test(location.pathname);

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
    ...(user && mode === 'v1' ? [{ to: '/topics', label: t('nav.topics') }] : []),
    ...(user ? [{ to: '/tests', label: t('nav.tests') }] : []),
  ];

  return (
    <header
      className={cn(
        'fixed top-0 z-50 w-full transition-all duration-300',
        isScrolled || mobileOpen || inApp ? 'border-b border-border/40 bg-background/90 shadow-sm backdrop-blur-md' : 'bg-transparent',
      )}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 md:px-6">
        <Link to={user ? appPath : '/'} className="group flex items-center gap-2 rounded-full pr-2" aria-label={t('common.appName')}>
          <motion.span whileHover={{ rotate: -8, scale: 1.08 }} transition={{ type: 'spring', stiffness: 400, damping: 15 }}>
            <Mascot size={38} float={false} />
          </motion.span>
          <span className="text-xl font-extrabold tracking-tight text-textMain">Mimir</span>
        </Link>

        <nav aria-label={t('nav.main')} className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                cn('relative isolate rounded-full px-4 py-2 text-sm font-semibold transition-colors', isActive ? 'text-onPrimary' : 'text-textMain hover:bg-surface/60')
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.span
                      layoutId="nav-active"
                      className="absolute inset-0 -z-10 rounded-full bg-primary"
                      transition={{ type: 'spring', stiffness: 500, damping: 38 }}
                    />
                  )}
                  {l.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-1.5 md:flex">
          {user && mode === 'v1' && <QueueIndicator />}
          <LanguageSwitcher />
          <ModeToggle />
          <SettingsMenu />
          <span className="mx-1 h-6 w-px bg-border/50" aria-hidden="true" />
          {user ? (
            <>
              {!inApp && <ButtonLink to={appPath} size="sm">{t('nav.openApp')}</ButtonLink>}
              <Button variant="ghost" size="sm" onClick={() => void logout()}>
                <LogOut size={15} aria-hidden="true" /> {t('nav.logout')}
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
          {user && mode === 'v1' && <QueueIndicator />}
          <ModeToggle />
          <button
            type="button"
            className="flex h-11 w-11 items-center justify-center rounded-full text-textMain hover:bg-surface/60"
            onClick={() => setMobileOpen((v) => !v)}
            aria-expanded={mobileOpen}
            aria-controls="mobile-menu"
            aria-label={mobileOpen ? t('nav.closeMenu') : t('nav.openMenu')}
          >
            <AnimatePresence mode="wait" initial={false}>
              <motion.span
                key={mobileOpen ? 'x' : 'menu'}
                initial={{ rotate: -90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: 90, opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="flex"
              >
                {mobileOpen ? <X size={24} aria-hidden="true" /> : <Menu size={24} aria-hidden="true" />}
              </motion.span>
            </AnimatePresence>
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            id="mobile-menu"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="max-h-[calc(100dvh-4rem)] overflow-y-auto border-b border-border/40 bg-background shadow-xl md:hidden"
          >
            <div className="px-4 py-4">
              <nav aria-label={t('nav.main')} className="flex flex-col gap-1">
                {links.map((l) => (
                  <NavLink
                    key={l.to}
                    to={l.to}
                    end={l.end}
                    className={({ isActive }) =>
                      cn('rounded-2xl px-4 py-3 font-semibold', isActive ? 'bg-primary text-onPrimary' : 'text-textMain hover:bg-surface/60')
                    }
                  >
                    {l.label}
                  </NavLink>
                ))}
              </nav>

              <div className="flex flex-col gap-2 pt-4">
                {user ? (
                  <>
                    {!inApp && <ButtonLink to={appPath} className="w-full">{t('nav.openApp')}</ButtonLink>}
                    <Button variant="outline" className="w-full" onClick={() => void logout()}>
                      <LogOut size={16} aria-hidden="true" /> {t('nav.logout')}
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
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
