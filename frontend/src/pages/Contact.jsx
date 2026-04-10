import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, MessageSquare, Send } from 'lucide-react';
import Button from '../components/ui/Button';

export default function Contact() {
  const [isLoading, setIsLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setSuccessMsg('');
    
    // Szimulált küldés
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setIsLoading(false);
    setSuccessMsg('Köszönjük megkeresésed! Hamarosan felvesszük veled a kapcsolatot.');
    e.target.reset();
  };

  return (
    <div className="relative overflow-hidden min-h-[80vh] flex items-center justify-center py-12">
      <div className="absolute top-[20%] right-[-10%] w-[40rem] h-[40rem] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }} 
        className="w-full max-w-2xl px-6 z-10"
      >
        <div className="text-center mb-10">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">Lépj velünk kapcsolatba</h1>
          <p className="text-textMain/60 text-lg">Kérdésed van a Mimir működésével vagy a Pro csomaggal kapcsolatban? Írj nekünk!</p>
        </div>

        <div className="p-8 rounded-3xl border border-border/50 bg-background/60 backdrop-blur-xl shadow-2xl">
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-textMain mb-2 ml-1">Neved</label>
                <input 
                  type="text" 
                  required
                  placeholder="Kovács János"
                  className="w-full bg-surface/30 border border-border/50 rounded-xl px-4 py-3 text-textMain placeholder:text-textMain/30 focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-textMain mb-2 ml-1">E-mail címed</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Mail size={18} className="text-textMain/40" />
                  </div>
                  <input 
                    type="email" 
                    required
                    placeholder="pelda@email.com"
                    className="w-full bg-surface/30 border border-border/50 rounded-xl py-3 pl-11 pr-4 text-textMain placeholder:text-textMain/30 focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-textMain mb-2 ml-1">Üzenet</label>
              <div className="relative">
                <div className="absolute top-3 left-0 pl-4 pointer-events-none">
                  <MessageSquare size={18} className="text-textMain/40" />
                </div>
                <textarea 
                  required
                  rows="5"
                  placeholder="Miben segíthetünk?"
                  className="w-full bg-surface/30 border border-border/50 rounded-xl py-3 pl-11 pr-4 text-textMain placeholder:text-textMain/30 focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all resize-none"
                ></textarea>
              </div>
            </div>

            {successMsg && <p className="text-sm text-green-400 text-center font-medium">{successMsg}</p>}

            <Button type="submit" isLoading={isLoading} className="w-full group">
              {!isLoading && (
                <>
                  Üzenet küldése
                  <Send className="ml-2 h-4 w-4 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                </>
              )}
            </Button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}