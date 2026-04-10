import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import Button from '../ui/Button';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation(); // Hogy tudjuk, melyik oldalon vagyunk épp
  const { user, logout } = useAuth();
  
  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Segédfüggvény az aktív linkek stílusához
  const isActive = (path) => location.pathname === path;

  return (
    <header className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        isScrolled ? 'bg-background/80 backdrop-blur-md border-b border-border/50 shadow-lg' : 'bg-transparent'
      }`}>
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-accent" />
          <span className="font-bold text-xl tracking-tight text-textMain">Mimir</span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          <Link to="/" className={`text-sm font-medium transition-colors ${isActive('/') ? 'text-accent' : 'text-textMain/80 hover:text-accent'}`}>Főoldal</Link>
          <Link to="/about" className={`text-sm font-medium transition-colors ${isActive('/about') ? 'text-accent' : 'text-textMain/80 hover:text-accent'}`}>Rólunk</Link>
          <Link to="/pricing" className={`text-sm font-medium transition-colors ${isActive('/pricing') ? 'text-accent' : 'text-textMain/80 hover:text-accent'}`}>Árazás</Link>
        </nav>
        
        {/* Asztali gombok */}
        <div className="hidden md:flex items-center gap-4">
          {user ? (
            <>
              <Link to="/chat">
                <Button variant="primary" size="sm">Ugrás a Chatbe</Button>
              </Link>
              <Button variant="ghost" size="sm" onClick={logout}>Kijelentkezés</Button>
            </>
          ) : (
            <>
              <Link to="/login">
                <Button variant="ghost" size="sm">Bejelentkezés</Button>
              </Link>
              <Link to="/register">
                <Button size="sm">Regisztráció</Button>
              </Link>
            </>
          )}
        </div>

        <button className="md:hidden text-textMain p-2" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobil menü */}
      {isMobileMenuOpen && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="md:hidden bg-surface border-b border-border px-6 py-4 flex flex-col gap-4 shadow-xl">
          <Link to="/" onClick={() => setIsMobileMenuOpen(false)} className="text-textMain py-2 border-b border-border/50">Főoldal</Link>
          <Link to="/about" onClick={() => setIsMobileMenuOpen(false)} className="text-textMain py-2 border-b border-border/50">Rólunk</Link>
          <Link to="/pricing" onClick={() => setIsMobileMenuOpen(false)} className="text-textMain py-2 border-b border-border/50">Árazás</Link>
          
          {/* Mobil gombok (Ezek hiányoztak) */}
          <div className="flex flex-col gap-2 pt-2">
            <Link to="/login" onClick={() => setIsMobileMenuOpen(false)}>
              <Button variant="outline" className="w-full">Bejelentkezés</Button>
            </Link>
            <Link to="/register" onClick={() => setIsMobileMenuOpen(false)}>
              <Button className="w-full">Regisztráció</Button>
            </Link>
          </div>
        </motion.div>
      )}
    </header>
  );
}