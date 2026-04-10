import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-background py-12 mt-24">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between gap-6">
        <div className="flex flex-col gap-2">
          <span className="font-bold text-xl tracking-tight text-textMain">Mimir</span>
          <p className="text-textMain/60 text-sm max-w-sm leading-relaxed">
            Mesterséges Intelligenciával támogatott tesztgeneráló webszolgáltatás.
          </p>
        </div>
        
        <div className="flex gap-10 text-sm text-textMain/60">
          <div className="flex flex-col gap-3">
            <Link to="/privacy" className="hover:text-accent transition-colors">Adatkezelési Tájékoztató</Link>
            <Link to="/terms" className="hover:text-accent transition-colors">Felhasználási Feltételek</Link>
          </div>
          <div className="flex flex-col gap-3">
            <Link to="/contact" className="hover:text-accent transition-colors">Kapcsolat</Link>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-6 mt-10 text-xs text-textMain/40 text-center md:text-left">
        &copy; {currentYear} Mimir Project. Minden jog fenntartva.
      </div>
    </footer>
  );
}