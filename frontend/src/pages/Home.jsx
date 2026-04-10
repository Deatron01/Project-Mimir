import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Zap, Shield, Sparkles, FileText, Bot, User, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.2 } }
};

export default function Home() {
  const { user } = useAuth(); // AuthContext használata a gombok dinamikus irányításához

  return (
    <div className="relative overflow-hidden">

      {/* Hero Szekció */}
      <section className="relative max-w-7xl mx-auto px-6 pt-24 pb-12 lg:pt-32 text-center z-10">
        <motion.div initial="hidden" animate="visible" variants={staggerContainer} className="max-w-4xl mx-auto flex flex-col items-center">
          <motion.div variants={fadeInUp} className="mb-6 inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-accent/30 bg-accent/10 backdrop-blur-sm text-sm text-accent font-medium shadow-[0_0_15px_rgba(100,255,218,0.2)]">
            <Sparkles size={16} />
            <span>Az okos vizsgagenerátor új generációja</span>
          </motion.div>
          
          <motion.h1 variants={fadeInUp} className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-tight">
            Mímir kútjából fakad a <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent via-primary to-accent">tudás</span>
          </motion.h1>
          
          <motion.p variants={fadeInUp} className="text-lg md:text-xl text-textMain/70 mb-10 max-w-2xl leading-relaxed">
            Töltsd fel saját oktatási anyagaidat, és a Mimir AI másodpercek alatt professzionális vizsgakérdéseket generál belőlük egy modern, interaktív chat felületen.
          </motion.p>
          
          <motion.div variants={fadeInUp} className="flex flex-col sm:flex-row gap-4">
            <Link to={user ? "/chat" : "/login"}>
              <Button size="lg" className="w-full sm:w-auto group shadow-lg shadow-accent/20">
                {user ? "Irány a Chat" : "Próbáld ki ingyen"} 
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <a href="#features">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                Hogyan működik?
              </Button>
            </a>
          </motion.div>
        </motion.div>
      </section>

      {/* Chat UI Mockup (A régi generátor helyett) */}
      <section className="relative max-w-5xl mx-auto px-6 mt-8 mb-24 z-10">
        <motion.div 
          initial={{ opacity: 0, y: 50 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.8, delay: 0.4 }} 
          className="rounded-3xl border border-border/50 bg-background/50 backdrop-blur-xl shadow-2xl shadow-primary/10 overflow-hidden"
        >
          {/* Mockup Fejléc */}
          <div className="border-b border-border/50 bg-surface/40 px-6 py-4 flex items-center gap-2">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
            </div>
            <span className="ml-4 text-xs font-semibold text-textMain/50 tracking-widest uppercase flex items-center gap-2">
              <Bot size={14} className="text-accent" /> Mimir AI Chat
            </span>
          </div>

          {/* Fake Üzenetek */}
          <div className="p-6 md:p-10 space-y-8 bg-gradient-to-b from-surface/10 to-transparent">
            
            {/* User Message */}
            <motion.div 
              initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.8 }}
              className="flex gap-4 max-w-[85%] ml-auto flex-row-reverse"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-surface text-textMain flex items-center justify-center border border-border">
                <User size={20} />
              </div>
              <div className="p-4 rounded-2xl bg-surface text-textMain rounded-tr-none border border-border/30 shadow-md">
                <div className="flex items-center gap-2 mb-3 p-2 bg-background/60 rounded-lg text-xs border border-border/50 w-max">
                  <FileText size={14} className="text-accent"/> <span className="font-mono">biologia_tetelek.pdf</span>
                </div>
                <p className="text-sm md:text-base leading-relaxed">Kérlek készíts egy 10 kérdéses feleletválasztós (MCQ) vizsgát a csatolt anyagból, kifejezetten a sejtosztódás témakörére fókuszálva!</p>
              </div>
            </motion.div>

            {/* AI Message */}
            <motion.div 
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.5 }}
              className="flex gap-4 max-w-[85%]"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/20 text-accent flex items-center justify-center border border-primary/30 shadow-[0_0_10px_rgba(100,255,218,0.2)]">
                <Bot size={20} />
              </div>
              <div className="p-5 rounded-2xl bg-background/80 border border-primary/30 rounded-tl-none shadow-lg relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-accent"></div>
                <p className="text-sm md:text-base leading-relaxed mb-4">
                  Elkészült a vizsgaanyag! A feltöltött dokumentumból kinyertem a sejtosztódással kapcsolatos legfontosabb fogalmakat (mitózis, meiózis), és legeneráltam a 10 szakmailag lektorált kérdést.
                </p>
                <div className="flex items-center gap-2 text-sm text-green-400 font-medium mb-4">
                  <CheckCircle size={16} /> Hallucináció-szűrés sikeres
                </div>
                <Button size="sm" className="shadow-lg hover:shadow-accent/20">
                  <FileText size={16} className="mr-2" /> Letöltés (PDF)
                </Button>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-24 border-t border-border/20 relative">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px] bg-gradient-to-r from-transparent via-accent/30 to-transparent"></div>
        
        <motion.h2 initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp} className="text-3xl md:text-5xl font-extrabold tracking-tight mb-16 text-center leading-tight">
          A <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-primary">Mimir</span> architektúra előnyei
        </motion.h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { title: "RAG alapú pontosság", icon: Zap, desc: "A rendszer szemantikus darabolást (RuneCarver) használ. Csak a feltöltött dokumentumod tényeire támaszkodik, minimalizálva az AI hallucinációt." },
            { title: "Zárt & Biztonságos", icon: Shield, desc: "Az oktatási anyagaid sosem hagyják el a rendszert. Nincs külső OpenAI hívás, a Qwen LLM lokális konténerben, szigorú adatvédelemmel fut." },
            { title: "Szupergyors PDF Export", icon: Sparkles, desc: "A Skald engine tipográfiailag helyes, letisztult PDF fájlokat generál azonnal, amelyek azonnal nyomtathatók és felhasználhatók vizsgáztatásra." }
          ].map((feature, idx) => (
            <motion.div 
              key={idx} 
              initial="hidden" 
              whileInView="visible" 
              viewport={{ once: true }} 
              variants={{ hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { delay: idx * 0.2 } } }}
              className="p-8 rounded-3xl border border-border/30 bg-surface/10 hover:bg-surface/40 hover:border-accent/30 transition-all duration-300 backdrop-blur-sm group"
            >
              <div className="w-14 h-14 rounded-2xl bg-primary/10 text-accent flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-primary/20 transition-transform duration-300">
                <feature.icon size={28} />
              </div>
              <h3 className="text-xl font-bold mb-3 leading-tight">{feature.title}</h3>
              <p className="text-textMain/60 leading-relaxed text-sm">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="relative py-24 text-center px-6 border-t border-border/20 bg-surface/5">
        <h2 className="text-3xl md:text-4xl font-bold mb-6">Készen állsz az első vizsgád legenerálására?</h2>
        <p className="text-textMain/60 mb-10 max-w-xl mx-auto">Csatlakozz a platformhoz, és spórolj órákat a vizsgaírásra szánt időből a Mimir AI segítségével.</p>
        <Link to={user ? "/chat" : "/register"}>
          <Button size="lg" className="shadow-[0_0_20px_rgba(100,255,218,0.3)]">
            {user ? "Kezdjük el!" : "Fiók létrehozása"}
          </Button>
        </Link>
      </section>

    </div>
  );
}