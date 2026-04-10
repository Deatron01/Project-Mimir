import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Zap, Shield, Sparkles, Upload, FileText, Download, Loader2 } from 'lucide-react';
import Button from '../components/ui/Button';
import { cn } from '../utils/cn';

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.2 } }
};

export default function Home() {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [resultData, setResultData] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!file || !query) {
      setErrorMsg("Kérlek, tölts fel egy fájlt és add meg a témát!");
      return;
    }
    setIsLoading(true);
    setErrorMsg("");
    setResultData(null);
    setPdfUrl(null);
    try {
      setStatusMsg("Szöveg kinyerése (Wellspring)...");
      const formData = new FormData();
      formData.append("file", file);
      const wellRes = await fetch(import.meta.env.VITE_WELLSPRING_URL, { method: "POST", body: formData });
      if (!wellRes.ok) throw new Error("Hiba a szöveg kinyerése közben");
      const wellData = await wellRes.json();
      const extractedText = wellData.content;

      setStatusMsg("Szöveg feldolgozása (RuneCarver)...");
      const runeRes = await fetch(import.meta.env.VITE_RUNECARVER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, extension: file.name.split('.').pop(), content: extractedText })
      });
      if (!runeRes.ok) throw new Error("Hiba a szöveg feldolgozása közben");
      const runeData = await runeRes.json();
      const chunks = runeData.chunks;

      setStatusMsg("Adatok indexelése (Bifrost)...");
      const ingestRes = await fetch(import.meta.env.VITE_BIFROST_INGEST_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chunks })
      });
      if (!ingestRes.ok) throw new Error("Hiba az adatok indexelése közben");

      setStatusMsg("AI kérdésgenerálás... Ez 15-30 másodpercig tarthat.");
      const genRes = await fetch(import.meta.env.VITE_BIFROST_GENERATE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: parseInt(limit, 10) })
      });
      if (!genRes.ok) throw new Error("Hiba a kérdések generálása közben");
      const genData = await genRes.json();
      const llmData = genData.data;
      setResultData(llmData);

      setStatusMsg("PDF vizsgaanyag elkészítése (Skald)...");
      const skaldRes = await fetch(import.meta.env.VITE_SKALD_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(llmData)
      });
      if (!skaldRes.ok) throw new Error("Hiba a PDF generálása közben");
      const pdfBlob = await skaldRes.blob();
      setPdfUrl(URL.createObjectURL(pdfBlob));
      setStatusMsg("Kész! A vizsgaanyag sikeresen elkészült.");
    } catch (err) {
      setErrorMsg(err.message || "Ismeretlen hiba történt a folyamat során.");
      setStatusMsg("");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative overflow-hidden">

      {/* Hero */}
      <section className="relative max-w-7xl mx-auto px-6 pt-24 pb-16 lg:pt-32 text-center">
        <motion.div initial="hidden" animate="visible" variants={staggerContainer} className="max-w-3xl mx-auto flex flex-col items-center">
          <motion.div variants={fadeInUp} className="mb-6 inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border bg-surface/30 backdrop-blur-sm text-sm text-accent">
            <Sparkles size={14} className="text-white"/>
            <span>AI Támogatott Tesztgeneráló Webszolgáltatás</span>
          </motion.div>
          <motion.h1 variants={fadeInUp} className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-tight">
            Okos tesztgenerálás a <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent via-primary to-accent">Mimir AI</span> segítségével
          </motion.h1>
          <motion.p variants={fadeInUp} className="text-lg md:text-xl text-textMain/70 mb-10 max-w-2xl leading-relaxed">
            Töltsd fel saját oktatási anyagaidat (.txt, .pdf), és a Mimir AI generál belőlük professzionális vizsgakérdéseket másodpercek alatt, lokálisan és biztonságosan a webszolgáltatásunkon keresztül.
          </motion.p>
        </motion.div>

        {/* Generator App UI */}
        <motion.div id="generator" initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }} className="mt-12 mx-auto max-w-4xl text-left rounded-2xl border border-border/50 bg-background/60 backdrop-blur-xl shadow-2xl overflow-hidden">
          <div className="border-b border-border/50 bg-surface/30 px-6 py-4 flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-accent/80"></div>
            <div className="w-3 h-3 rounded-full bg-primary/80"></div>
            <div className="w-3 h-3 rounded-full bg-border"></div>
            <span className="ml-4 text-xs font-medium text-textMain/40 tracking-widest">MIMIR TEST GENERATOR</span>
          </div>

          <div className="p-6 md:p-10">
            <form onSubmit={handleGenerate} className="flex flex-col gap-8">
              <div className="grid md:grid-cols-2 gap-8">
                {/* 1. Upload */}
                <div>
                  <label className="block text-sm font-medium text-textMain mb-2">1. Tudásbázis feltöltése</label>
                  <div className="relative border-2 border-dashed border-border/60 rounded-xl p-8 text-center hover:border-primary/60 transition-colors bg-surface/10">
                    <input type="file" accept=".txt,.pdf" onChange={(e) => setFile(e.target.files[0])} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                    <div className="flex flex-col items-center gap-3">
                      <div className="p-3 bg-surface rounded-full text-accent">
                        {file ? <FileText size={24} /> : <Upload size={24} />}
                      </div>
                      <span className="text-sm font-medium text-textMain/70">
                        {file ? file.name : "Kattints ide vagy húzz ide egy fájlt (.txt, .pdf)"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 2. Params */}
                <div className="flex flex-col gap-6">
                  <div>
                    <label className="block text-sm font-medium text-textMain mb-2">2. Vizsga témája (AI Prompt)</label>
                    <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Pl. Kik vettek részt az Apollo-11 küldetésben?" className="w-full bg-surface/30 border border-border/50 rounded-xl px-4 py-3 text-textMain placeholder:text-textMain/30 focus:outline-none focus:ring-2 focus:ring-accent/50" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-textMain mb-2">3. Felhasznált forrásbekezdések száma (Limit: {limit})</label>
                    <input type="range" min="1" max="5" value={limit} onChange={(e) => setLimit(e.target.value)} className="w-full accent-accent" />
                  </div>
                </div>
              </div>

              {/* Status and CTA */}
              <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-border/30">
                <div className="text-sm flex items-center gap-3">
                  {isLoading && <Loader2 className="animate-spin h-5 w-5 text-accent" />}
                  {isLoading && <span className="text-accent animate-pulse leading-relaxed">{statusMsg}</span>}
                  {!isLoading && statusMsg && <span className="text-green-400 leading-relaxed">{statusMsg}</span>}
                  {errorMsg && <span className="text-red-400 leading-relaxed">Hiba: {errorMsg}</span>}
                </div>
                <Button type="submit" isLoading={isLoading} className="w-full sm:w-auto">Teszt Generálása</Button>
              </div>
            </form>

            {/* Result Area */}
            {resultData && pdfUrl && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-10 p-6 rounded-xl border border-primary/30 bg-surface/20">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                  <div>
                    <h3 className="text-xl font-bold text-textMain">Sikeres generálás</h3>
                    <p className="text-sm text-textMain/60 mt-1">A nyers JSON adatok és a letölthető PDF vizsgaanyag elkészült.</p>
                  </div>
                  <a href={pdfUrl} download="mimir_vizsgaanyag.pdf" className="inline-flex items-center justify-center gap-2 h-11 px-6 rounded-full font-medium bg-accent text-background hover:bg-white transition-colors">
                    <Download size={18} /> Letöltés (PDF)
                  </a>
                </div>
                <div className="bg-[#0f0012] p-4 rounded-lg overflow-auto max-h-64 text-xs font-mono text-textMain/80">
                  <pre>{JSON.stringify(resultData, null, 2)}</pre>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-24 mt-12 border-t border-border/20">
        <motion.h2 initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeInUp} className="text-3xl md:text-5xl font-extrabold tracking-tight mb-16 text-center leading-tight">
          A <span className="text-accent">Mimir</span> webszolgáltatás előnyei
        </motion.h2>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { title: "Pontos pipeline", icon: Zap, desc: "A Wellspring és RuneCarver modulok optimalizált sebességgel, hiba nélkül dolgozzák fel a dokumentumokat a Mimir webszolgáltatásában." },
            { title: "Lokálisan biztonságos", icon: Shield, desc: "A Mimir a háttérben lokális AI modelleket használ, így az oktatási anyagaid sosem hagyják el a webszolgáltatás biztonságos környezetét." },
            { title: "Gyönyörű PDF Export", icon: Sparkles, desc: "A Skald engine tipográfiailag helyes, letisztult PDF fájlokat generál azonnal, amelyek azonnal felhasználhatók vizsgáztatásra." }
          ].map((feature, idx) => (
            <div key={idx} className="p-8 rounded-2xl border border-border/30 bg-surface/10 hover:bg-surface/30 transition-colors backdrop-blur-sm">
              <div className="w-12 h-12 rounded-xl bg-primary/20 text-accent flex items-center justify-center mb-6">
                <feature.icon size={24} />
              </div>
              <h3 className="text-xl font-semibold mb-3 leading-tight">{feature.title}</h3>
              <p className="text-textMain/60 leading-relaxed text-sm">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}