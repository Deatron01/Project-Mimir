import React from 'react';
import { motion } from 'framer-motion';
import { BrainCircuit, Server, Users } from 'lucide-react';

export default function About() {
  return (
    <div className="relative overflow-hidden min-h-[80vh]">
      {/* Background Glow */}
      <div className="absolute top-[20%] left-[-10%] w-[40rem] h-[40rem] bg-surface/30 rounded-full blur-[120px] pointer-events-none" />

      <section className="relative max-w-4xl mx-auto px-6 pt-24 pb-16 text-center">
        <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-4xl md:text-6xl font-extrabold tracking-tight mb-8">
          A <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-primary">Mimir</span> Története
        </motion.h1>
        <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="text-lg text-textMain/70 leading-relaxed mb-16">
          A skandináv mitológiában Mimir a bölcsesség óriása, a tudás forrásának őrzője. Ebből az inspirációból hoztuk létre ezt a platformot, amely a mesterséges intelligencia segítségével szintetizálja a te tudásbázisodat, és alakítja át strukturált, azonnal használható vizsgaanyagokká.
        </motion.p>

        <div className="grid md:grid-cols-3 gap-6 text-left">
          {[
            { icon: Server, title: "Lokális Architektúra", desc: "Minden Qwen AI modell és vektoradatbázis nálad fut, maximális adatvédelmet biztosítva." },
            { icon: BrainCircuit, title: "Modern AI Motor", desc: "A Wellspring, RuneCarver és Bifrost microservice-ek együttműködve, hallucináció-mentesen dolgoznak." },
            { icon: Users, title: "Oktatókra Szabva", desc: "Azért hoztuk létre, hogy a tanárok és instruktorok órákat spóroljanak a vizsgaírással." }
          ].map((item, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 + (i * 0.1) }} className="p-6 rounded-2xl border border-border/50 bg-surface/20 backdrop-blur-sm">
              <item.icon size={32} className="text-accent mb-4" />
              <h3 className="text-xl font-bold mb-2">{item.title}</h3>
              <p className="text-sm text-textMain/60 leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}