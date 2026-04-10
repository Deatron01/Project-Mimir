import React from 'react';
import { motion } from 'framer-motion';

export default function Privacy() {
  return (
    <div className="relative overflow-hidden min-h-[80vh] py-20">
      <div className="absolute top-[10%] left-[-10%] w-[30rem] h-[30rem] bg-surface/30 rounded-full blur-[100px] pointer-events-none" />
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }} 
        className="max-w-4xl mx-auto px-6 z-10 relative"
      >
        <div className="p-8 md:p-12 rounded-3xl border border-border/50 bg-background/60 backdrop-blur-xl shadow-2xl">
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-8">Adatkezelési Tájékoztató</h1>
          
          <div className="space-y-6 text-textMain/70 leading-relaxed text-sm md:text-base">
            <p>Utolsó frissítés: 2026. április 4.</p>
            
            <h2 className="text-xl font-bold text-textMain mt-8 mb-4">1. Általános rendelkezések</h2>
            <p>A Mimir AI kiemelt figyelmet fordít a személyes adatok védelmére. Mivel szolgáltatásunk alapvetően egy lokálisan futtatható architektúrára épül, a feltöltött oktatási anyagok és vizsgakérdések nem kerülnek felhő alapú külső szerverekre, azokat a saját infrastruktúrája dolgozza fel.</p>
            
            <h2 className="text-xl font-bold text-textMain mt-8 mb-4">2. Kezelt adatok köre</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>Regisztráció során megadott e-mail cím és titkosított jelszó.</li>
              <li>Kapcsolatfelvételi űrlapon megadott név és e-mail cím.</li>
              <li>A weboldal használata során elmentett munkamenet (cookie) azonosítók.</li>
            </ul>

            <h2 className="text-xl font-bold text-textMain mt-8 mb-4">3. Az adatkezelés célja</h2>
            <p>A felhasználói fiókok kezelése, a szolgáltatáshoz való hozzáférés biztosítása, valamint a felhasználókkal való kommunikáció (pl. jelszó-visszaállítás, technikai támogatás).</p>

            <h2 className="text-xl font-bold text-textMain mt-8 mb-4">4. Adatbiztonság</h2>
            <p>Az adatbázisban tárolt jelszavakat bcrypt technológiával titkosítjuk. A szolgáltatás kommunikációja titkosított csatornákon keresztül történik.</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}