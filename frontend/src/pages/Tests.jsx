import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, FilePdf, Calendar, HardDrive, Loader2, Inbox } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';

export default function Tests() {
  const { user } = useAuth();
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchTests() {
      if (!user?.email) return;
      try {
        const res = await fetch(`https://api.mimir-ai.hu/api/v1/tests?user_id=${user.email}`);
        if (!res.ok) throw new Error('Nem sikerült betölteni a tesztek előzményeit.');
        const data = await res.json();
        setTests(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchTests();
  }, [user]);

  const handleDownload = async (testId, title) => {
    try {
      const res = await fetch(`https://api.mimir-ai.hu/api/v1/tests/download/${testId}`);
      if (!res.ok) throw new Error('A letöltés sikertelen.');
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-80px)]">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-extrabold tracking-tight mb-2">Generált Vizsgaanyagok</h1>
        <p className="text-textMain/60 text-sm">Itt találod az összes korábban elkészített tesztedet, melyeket bármikor újra letölthetsz.</p>
      </div>

      {error && (
        <div className="p-4 mb-6 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-200 text-sm">
          {error}
        </div>
      )}

      {tests.length === 0 ? (
        <motion.div 
          initial={{ opacity: 0, y: 20 }} 
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center justify-center p-16 rounded-3xl border border-border/40 bg-surface/10 text-center"
        >
          <Inbox size={48} className="text-textMain/30 mb-4" />
          <h3 className="text-lg font-semibold mb-1">Nincs még mentett teszted</h3>
          <p className="text-sm text-textMain/50 max-w-xs">Térj vissza a Chat oldalra, tölts fel egy dokumentumot és generálj egy új vizsgát!</p>
        </motion.div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-border/40 bg-surface/10 backdrop-blur-md shadow-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border/40 bg-surface/30 text-xs font-semibold uppercase tracking-wider text-textMain/60">
                <th className="p-5">Teszt megnevezése</th>
                <th className="p-5 flex items-center gap-1"><Calendar size={14} /> Létrehozva</th>
                <th className="p-5"><div className="flex items-center gap-1"><HardDrive size={14} /> Méret</div></th>
                <th className="p-5 text-right">Művelet</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30 text-sm">
              {tests.map((test, index) => (
                <motion.tr 
                  key={test.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-surface/20 transition-colors group"
                >
                  <td className="p-5 font-medium flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-red-500/10 text-red-400 flex items-center justify-center border border-red-500/20">
                      <span className="font-bold text-xs">PDF</span>
                    </div>
                    <span className="truncate max-w-md">{test.title}</span>
                  </td>
                  <td className="p-5 text-textMain/70">{test.created_at}</td>
                  <td className="p-5 text-textMain/60 font-mono text-xs">{test.file_size}</td>
                  <td className="p-5 text-right">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleDownload(test.id, test.title)}
                      className="group-hover:bg-accent group-hover:text-background transition-all"
                    >
                      <Download size={14} className="mr-1.5" /> Letöltés
                    </Button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}