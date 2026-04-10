import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Paperclip, Loader2, FileText, Download, Bot, User, X } from 'lucide-react';
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
  
  const chatContainerRef = useRef(null);

  // Sima és biztonságos görgetés a doboz aljára
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

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

      setStatusMsg("Szöveg kinyerése a dokumentumból...");
      const formData = new FormData();
      formData.append("file", file);
      const wellRes = await fetch(import.meta.env.VITE_WELLSPRING_URL, { method: "POST", body: formData });
      if (!wellRes.ok) throw new Error("Hiba a szöveg kinyerése közben");
      const wellData = await wellRes.json();

      setStatusMsg("Szövegrészek elemzése és darabolása...");
      const runeRes = await fetch(import.meta.env.VITE_RUNECARVER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, extension: file.name.split('.').pop(), content: wellData.content })
      });
      if (!runeRes.ok) throw new Error("Hiba a szöveg feldolgozása közben");
      const runeData = await runeRes.json();

      setStatusMsg("Tudásbázis építése (Vektorizálás)...");
      await fetch(import.meta.env.VITE_BIFROST_INGEST_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chunks: runeData.chunks })
      });

      setStatusMsg("A mesterséges intelligencia írja a kérdéseket...");
      const genRes = await fetch(import.meta.env.VITE_BIFROST_GENERATE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg.content, limit: 3 })
      });
      if (!genRes.ok) throw new Error("Hiba a kérdések generálása közben");
      const genData = await genRes.json();

      setStatusMsg("PDF dokumentum szerkesztése...");
      const skaldRes = await fetch(import.meta.env.VITE_SKALD_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(genData.data)
      });
      if (!skaldRes.ok) throw new Error("Hiba a PDF generálása közben");
      
      const pdfBlob = await skaldRes.blob();
      const pdfUrl = URL.createObjectURL(pdfBlob);

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
    <div className="flex flex-col h-[calc(100vh-80px)] max-w-4xl mx-auto px-4 md:px-6 py-6">
      
      {/* --- CHAT ÜZENETEK TARTOMÁNYA --- */}
      <div 
        ref={chatContainerRef} 
        className="flex-1 overflow-y-auto mb-4 pr-2 space-y-6 scrollbar-thin scrollbar-thumb-surface scrollbar-track-transparent"
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
            <div className={cn(
              "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm",
              msg.role === 'ai' ? "bg-primary/20 text-accent border border-primary/30" : "bg-surface text-textMain border border-border"
            )}>
              {msg.role === 'ai' ? <Bot size={20} /> : <User size={20} />}
            </div>

            <div className={cn(
              "p-4 rounded-2xl shadow-md",
              msg.role === 'user' 
                ? "bg-surface text-textMain rounded-tr-none border border-border/50" 
                : msg.isError 
                  ? "bg-red-500/10 text-red-200 border border-red-500/30 rounded-tl-none" 
                  : "bg-surface/50 backdrop-blur-md border border-border/50 rounded-tl-none"
            )}>
              {msg.attachedFile && (
                <div className="flex items-center gap-2 mb-3 p-2 bg-background/60 rounded-lg text-xs text-textMain/80 border border-border/50 w-max">
                  <FileText size={14} className="text-accent"/> <span>{msg.attachedFile}</span>
                </div>
              )}
              
              <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              
              {msg.pdfUrl && (
                <div className="mt-4 pt-4 border-t border-border/30">
                  <a href={msg.pdfUrl} download="mimir_vizsga.pdf" className="inline-flex items-center gap-2 px-5 py-2.5 bg-accent text-background rounded-xl font-medium hover:bg-white transition-colors text-sm shadow-lg shadow-accent/20">
                    <Download size={16} /> Eredmény Letöltése (PDF)
                  </a>
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {isLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4 max-w-[85%]">
            <div className="w-10 h-10 rounded-full bg-primary/20 text-accent border border-primary/30 flex items-center justify-center">
              <Loader2 size={20} className="animate-spin" />
            </div>
            <div className="p-4 rounded-2xl bg-surface/50 backdrop-blur-md border border-border/50 rounded-tl-none flex items-center gap-3 shadow-md">
              <span className="text-sm text-textMain/70 animate-pulse">{statusMsg || 'Gondolkodom...'}</span>
            </div>
          </motion.div>
        )}
      </div>

      {/* --- ALSÓ BEVITELI MEZŐ (INPUT AREA) --- */}
      <div className="shrink-0 w-full flex flex-col items-center gap-3 mt-2">
        
        {/* Lebegő fájl címke */}
        {file && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="self-start ml-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border border-border/60 bg-surface/80 backdrop-blur-md text-sm shadow-sm"
          >
            <FileText size={14} className="text-accent" />
            <span className="truncate max-w-[200px] text-textMain/90 font-medium">{file.name}</span>
            <button 
              type="button" 
              onClick={() => setFile(null)} 
              className="ml-1 text-textMain/50 hover:text-red-400 transition-colors"
            >
              <X size={14} />
            </button>
          </motion.div>
        )}

        {/* Kapszula alakú beviteli mező - A KÉPED ALAPJÁN */}
        <form 
          onSubmit={handleSend} 
          className="w-full flex items-center gap-2 bg-transparent border border-border/80 rounded-full pl-2 pr-2 py-1.5 shadow-sm focus-within:border-accent/60 transition-colors backdrop-blur-md"
        >
          {/* Fájl csatolás gomb - Tökéletesen középre igazítva */}
          <label className="flex items-center justify-center w-10 h-10 text-textMain/60 hover:text-accent cursor-pointer transition-colors shrink-0 rounded-full hover:bg-surface/50">
            <input type="file" className="hidden" accept=".pdf,.txt" onChange={(e) => setFile(e.target.files[0])} disabled={isLoading} />
            <Paperclip size={20} />
          </label>

          {/* Szövegdoboz */}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(e); } }}
            placeholder="Írd le, milyen vizsgát szeretnél..."
            className="flex-1 bg-transparent border-none focus:ring-0 resize-none py-2.5 px-2 text-textMain placeholder:text-textMain/40 text-[15px] outline-none scrollbar-none"
            rows="1"
            style={{ minHeight: '44px', maxHeight: '120px' }}
            disabled={isLoading}
          />

          {/* Küldés gomb - Halványabb háttérrel a képed szerint, ikon teljesen középen */}
          <button 
            type="submit" 
            disabled={isLoading || (!input.trim() && !file)}
            className="flex items-center justify-center w-10 h-10 bg-textMain/10 hover:bg-accent text-textMain/80 hover:text-background disabled:opacity-50 disabled:hover:bg-textMain/10 rounded-full transition-all shrink-0"
          >
            {isLoading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Send size={18} /> 
            )}
          </button>
        </form>

        <div className="text-[11px] text-textMain/40 tracking-wide text-center">
          A Mimir AI hibázhat. Kérjük, vizsgáztatás előtt ellenőrizze a generált tartalmat.
        </div>
      </div>
      
    </div>
  );
}