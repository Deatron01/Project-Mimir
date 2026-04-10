import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Paperclip, Loader2, FileText, Download, Bot, User } from 'lucide-react';
import { cn } from '../utils/cn';

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'ai',
      content: 'Szia! Én a Mimir AI vagyok. Kérlek csatolj egy dokumentumot (PDF/TXT), és írd le, hogy milyen témában, hány kérdéses vizsgát generáljak belőle!'
    }
  ]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  
  // A teljes chat görgethető dobozának referenciája
  const chatContainerRef = useRef(null);

  // Biztonságos görgetés, ami csak a doboz belsejét mozgatja, nem rántja le az egész weblapot
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  // Minden új üzenetnél vagy státuszváltásnál legörgetünk
  useEffect(() => { 
    scrollToBottom(); 
  }, [messages, isLoading, statusMsg]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() && !file) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: input,
      attachedFile: file ? file.name : null
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      if (!file) {
        throw new Error("Kérlek, csatolj egy dokumentumot is a tesztgeneráláshoz!");
      }

      // 1. Wellspring (Kinyerés)
      setStatusMsg("Szöveg kinyerése a dokumentumból...");
      const formData = new FormData();
      formData.append("file", file);
      const wellRes = await fetch(import.meta.env.VITE_WELLSPRING_URL, { method: "POST", body: formData });
      if (!wellRes.ok) throw new Error("Hiba a szöveg kinyerése közben");
      const wellData = await wellRes.json();

      // 2. RuneCarver (Darabolás)
      setStatusMsg("Szövegrészek elemzése és darabolása...");
      const runeRes = await fetch(import.meta.env.VITE_RUNECARVER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, extension: file.name.split('.').pop(), content: wellData.content })
      });
      if (!runeRes.ok) throw new Error("Hiba a szöveg feldolgozása közben");
      const runeData = await runeRes.json();

      // 3. Bifrost (Indexelés)
      setStatusMsg("Tudásbázis építése (Vektorizálás)...");
      await fetch(import.meta.env.VITE_BIFROST_INGEST_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chunks: runeData.chunks })
      });

      // 4. Bifrost (Generálás)
      setStatusMsg("A mesterséges intelligencia írja a kérdéseket...");
      const genRes = await fetch(import.meta.env.VITE_BIFROST_GENERATE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg.content, limit: 3 })
      });
      if (!genRes.ok) throw new Error("Hiba a kérdések generálása közben");
      const genData = await genRes.json();

      // 5. Skald (PDF)
      setStatusMsg("PDF dokumentum szerkesztése...");
      const skaldRes = await fetch(import.meta.env.VITE_SKALD_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(genData.data)
      });
      if (!skaldRes.ok) throw new Error("Hiba a PDF generálása közben");
      
      const pdfBlob = await skaldRes.blob();
      const pdfUrl = URL.createObjectURL(pdfBlob);

      // Siker! AI válasz hozzáadása
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'ai',
        content: 'Elkészült a vizsgaanyagod a megadott dokumentum alapján! Alább letöltheted a kész PDF-et.',
        resultData: genData.data,
        pdfUrl: pdfUrl
      }]);
      setFile(null);

    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'ai',
        content: `Hiba történt: ${err.message}`,
        isError: true
      }]);
    } finally {
      setIsLoading(false);
      setStatusMsg('');
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] max-w-5xl mx-auto px-4 md:px-6 py-6">
      
      {/* Chat üzenetek területe (A ref ide került a belső görgetéshez) */}
      <div 
        ref={chatContainerRef} 
        className="flex-1 overflow-y-auto mb-6 pr-2 space-y-6 scrollbar-thin scrollbar-thumb-surface scrollbar-track-transparent"
      >
        {messages.map((msg) => (
          <motion.div 
            key={msg.id} 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              "flex gap-4 max-w-[85%]",
              msg.role === 'user' ? "ml-auto flex-row-reverse" : ""
            )}
          >
            {/* Avatar */}
            <div className={cn(
              "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center",
              msg.role === 'ai' ? "bg-primary/20 text-accent" : "bg-surface/50 text-textMain"
            )}>
              {msg.role === 'ai' ? <Bot size={20} /> : <User size={20} />}
            </div>

            {/* Bubble */}
            <div className={cn(
              "p-4 rounded-2xl shadow-sm",
              msg.role === 'user' 
                ? "bg-surface text-textMain rounded-tr-none border border-border/30" 
                : msg.isError 
                  ? "bg-red-500/10 text-red-200 border border-red-500/30 rounded-tl-none" 
                  : "bg-background/80 border border-primary/20 rounded-tl-none"
            )}>
              {/* User csatolt fájl jelzése */}
              {msg.attachedFile && (
                <div className="flex items-center gap-2 mb-2 p-2 bg-background/50 rounded-lg text-xs text-textMain/70 border border-border/50">
                  <FileText size={14} className="text-accent"/> <span>{msg.attachedFile}</span>
                </div>
              )}
              
              <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              
              {/* AI Generált Eredmény megtekintése */}
              {msg.pdfUrl && (
                <div className="mt-4 pt-4 border-t border-border/30">
                  <a href={msg.pdfUrl} download="mimir_vizsga.pdf" className="inline-flex items-center gap-2 px-4 py-2 bg-accent text-background rounded-lg font-medium hover:bg-white transition-colors text-sm">
                    <Download size={16} /> Eredmény Letöltése (PDF)
                  </a>
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {/* Loading Indikátor */}
        {isLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4 max-w-[85%]">
            <div className="w-10 h-10 rounded-full bg-primary/20 text-accent flex items-center justify-center">
              <Loader2 size={20} className="animate-spin" />
            </div>
            <div className="p-4 rounded-2xl bg-background/80 border border-primary/20 rounded-tl-none flex items-center gap-3">
              <span className="text-sm text-textMain/70 animate-pulse">{statusMsg || 'Gondolkodom...'}</span>
            </div>
          </motion.div>
        )}
      </div>

      {/* Input Szekció (Bottom Bar) */}
      <div className="relative bg-surface/40 backdrop-blur-xl border border-border/50 rounded-3xl p-2 shadow-2xl shrink-0">
        {/* Fájl preview */}
        {file && (
          <div className="absolute -top-12 left-4 flex items-center gap-2 bg-surface border border-border/50 px-3 py-1.5 rounded-lg text-sm shadow-lg">
            <FileText size={14} className="text-accent" />
            <span className="truncate max-w-[200px] text-textMain/80">{file.name}</span>
            <button onClick={() => setFile(null)} className="ml-2 text-textMain/40 hover:text-red-400">✕</button>
          </div>
        )}

        <form onSubmit={handleSend} className="flex items-end gap-2">
          {/* Fájl csatolás gomb */}
          <label className="p-3 text-textMain/50 hover:text-accent hover:bg-background/50 rounded-full cursor-pointer transition-colors shrink-0 mb-1 ml-1">
            <input type="file" className="hidden" accept=".pdf,.txt" onChange={(e) => setFile(e.target.files[0])} disabled={isLoading} />
            <Paperclip size={20} />
          </label>

          {/* Szövegdoboz */}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(e); } }}
            placeholder="Írd le, milyen vizsgát szeretnél..."
            className="flex-1 bg-transparent border-none focus:ring-0 resize-none py-3.5 px-2 max-h-32 text-textMain placeholder:text-textMain/30 text-sm md:text-base outline-none scrollbar-thin"
            rows="1"
            disabled={isLoading}
          />

          {/* JAVÍTOTT: Küldés gomb flexbox-szal és fix mérettel */}
          <button 
            type="submit" 
            disabled={isLoading || (!input.trim() && !file)}
            className="relative flex items-center justify-center w-12 h-12 bg-accent text-background hover:bg-white disabled:opacity-50 disabled:hover:bg-accent rounded-full transition-all shrink-0 mb-1 mr-1"
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              // A Send ikon vizuálisan kicsit balra tolódik alapból, ezért kapott egy 2px-es korrekciót jobbra
              <Send size={20} className="translate-x-[2px]" /> 
            )}
          </button>
        </form>
      </div>
      <div className="text-center mt-3 text-xs text-textMain/40 shrink-0">
        A Mimir AI hibázhat. Kérjük, vizsgáztatás előtt ellenőrizze a generált tartalmat.
      </div>
    </div>
  );
}