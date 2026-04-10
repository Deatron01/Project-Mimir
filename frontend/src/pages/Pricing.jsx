import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import Button from '../components/ui/Button';

export default function Pricing() {
  return (
    <div className="relative overflow-hidden min-h-[80vh]">
      <div className="absolute top-[10%] right-[-10%] w-[40rem] h-[40rem] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />

      <section className="relative max-w-6xl mx-auto px-6 pt-24 pb-16 text-center">
        <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-4xl md:text-6xl font-extrabold tracking-tight mb-6">
          Egyszerű, átlátható árazás
        </motion.h1>
        <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="text-lg text-textMain/70 mb-16 max-w-2xl mx-auto">
          Mivel a Mimir a te saját hardvereden (lokálisan) fut, nincsenek rejtett felhő-költségek vagy API díjak. Válassz az igényeidhez illő támogatási csomagok közül.
        </motion.p>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto text-left">
          {/* Free Tier */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }} className="p-8 rounded-3xl border border-border/50 bg-surface/20 backdrop-blur-sm flex flex-col">
            <h3 className="text-2xl font-bold mb-2">Nyílt Forráskód</h3>
            <div className="flex items-baseline gap-2 mb-6">
              <span className="text-4xl font-extrabold text-white">0 Ft</span>
              <span className="text-textMain/60">/ örökké</span>
            </div>
            <p className="text-sm text-textMain/70 mb-8 h-10">Tökéletes diákoknak és hobbistáknak, akik maguk üzemeltetik a rendszert.</p>
            <ul className="flex flex-col gap-4 mb-8 flex-grow">
              <li className="flex items-center gap-3 text-sm"><Check size={18} className="text-green-400" /> Teljes lokális hozzáférés</li>
              <li className="flex items-center gap-3 text-sm"><Check size={18} className="text-green-400" /> Végtelen vizsgagenerálás</li>
              <li className="flex items-center gap-3 text-sm"><Check size={18} className="text-green-400" /> Skald PDF Engine</li>
              <li className="flex items-center gap-3 text-sm text-textMain/40"><Check size={18} className="opacity-0" /> Közösségi Discord támogatás</li>
            </ul>
            <Button variant="outline" className="w-full">Letöltés GitHub-ról</Button>
          </motion.div>

          {/* Pro Tier */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }} className="p-8 rounded-3xl border border-accent bg-gradient-to-b from-surface/40 to-background flex flex-col relative overflow-hidden">
            <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-accent to-primary" />
            <div className="absolute top-6 right-6 px-3 py-1 bg-accent/20 text-accent text-xs font-bold rounded-full">AJÁNLOTT</div>
            
            <h3 className="text-2xl font-bold mb-2">Pro Támogatás</h3>
            <div className="flex items-baseline gap-2 mb-6">
              <span className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-accent to-primary">15.000 Ft</span>
              <span className="text-textMain/60">/ hó</span>
            </div>
            <p className="text-sm text-textMain/70 mb-8 h-10">Intézményeknek és tanároknak, akik garantált működést és frissítéseket igényelnek.</p>
            <ul className="flex flex-col gap-4 mb-8 flex-grow">
              <li className="flex items-center gap-3 text-sm"><Check size={18} className="text-accent" /> Minden a Nyílt csomagból</li>
              <li className="flex items-center gap-3 text-sm"><Check size={18} className="text-accent" /> Dedikált technikai beüzemelés</li>
              <li className="flex items-center gap-3 text-sm"><Check size={18} className="text-accent" /> Prioritásos hibajavítás</li>
              <li className="flex items-center gap-3 text-sm"><Check size={18} className="text-accent" /> Korai hozzáférés új funkciókhoz</li>
            </ul>
            <Button className="w-full">Előfizetés</Button>
          </motion.div>
        </div>
      </section>
    </div>
  );
}