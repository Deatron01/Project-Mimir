import React from 'react';
import { motion } from 'framer-motion';

export default function Terms() {
  return (
    <div className="relative overflow-hidden min-h-[80vh] py-20">
      <div className="absolute bottom-[10%] right-[-10%] w-[30rem] h-[30rem] bg-primary/10 rounded-full blur-[100px] pointer-events-none" />
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }} 
        className="max-w-4xl mx-auto px-6 z-10 relative"
      >
        <div className="p-8 md:p-12 rounded-3xl border border-border/50 bg-background/60 backdrop-blur-xl shadow-2xl">
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-8">Felhasználási Feltételek</h1>
          
          <div className="space-y-6 text-textMain/70 leading-relaxed text-sm md:text-base">
            <p>Kérjük, figyelmesen olvassa el az alábbi Felhasználási Feltételeket a Mimir AI szolgáltatás használata előtt.</p>
            
            <h2 className="text-xl font-bold text-textMain mt-8 mb-4">1. A Szolgáltatás leírása</h2>
            <p>A Mimir egy mesterséges intelligenciával támogatott tesztgeneráló platform. A rendszer képes a feltöltött dokumentumokból automatikusan kérdéseket és vizsgaanyagokat generálni a Qwen AI modell segítségével.</p>
            
            <h2 className="text-xl font-bold text-textMain mt-8 mb-4">2. Felhasználói felelősség</h2>
            <p>A felhasználó kizárólag olyan anyagokat tölthet fel a rendszerbe, amelyekhez megfelelő szerzői joggal vagy felhasználási engedéllyel rendelkezik. A generált vizsgaanyagok szakmai ellenőrzése minden esetben a felhasználó felelőssége.</p>

            <h2 className="text-xl font-bold text-textMain mt-8 mb-4">3. Generált tartalom</h2>
            <p>Bár a rendszer hallucináció-csökkentő mechanizmusokkal (RAG) dolgozik, a nagy nyelvi modellek természetéből adódóan a Mimir nem vállal garanciát a generált vizsgakérdések 100%-os tényszerű pontosságáért. Az éles vizsgáztatás előtt az anyag emberi lektorálása kötelező.</p>

            <h2 className="text-xl font-bold text-textMain mt-8 mb-4">4. Szolgáltatás elérhetősége</h2>
            <p>Ingyenes csomagunk esetében a szolgáltatást "ahogy van" alapon nyújtjuk, garantált rendelkezésre állás (SLA) nélkül. A Pro előfizetők számára a szerződésben foglalt technikai támogatást biztosítjuk.</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}