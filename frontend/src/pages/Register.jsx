import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (password !== confirmPassword) {
      setErrorMsg('A két jelszó nem egyezik!');
      return;
    }

    if (password.length < 6) {
      setErrorMsg('A jelszónak legalább 6 karakternek kell lennie!');
      return;
    }

    setIsLoading(true);

    try {
      // IDE KERÜL A BACKEND API HÍVÁS
      // Példa: const res = await fetch('http://localhost:8000/api/register', { ... })
      
      // Szimuláció
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setSuccessMsg('Sikeres regisztráció! Kérlek, erősítsd meg az e-mail címedet a kiküldött linkkel.');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
    } catch (err) {
      setErrorMsg('Hiba történt a regisztráció során.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative overflow-hidden min-h-[80vh] flex items-center justify-center mt-10">
      <div className="absolute top-[20%] right-[-10%] w-[40rem] h-[40rem] bg-surface/40 rounded-full blur-[120px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }} 
        className="w-full max-w-md px-6 z-10"
      >
        <div className="p-8 rounded-3xl border border-border/50 bg-background/60 backdrop-blur-xl shadow-2xl relative overflow-hidden">
          
          <div className="text-center mb-8">
            <h1 className="text-3xl font-extrabold tracking-tight mb-2">Új fiók létrehozása</h1>
            <p className="text-sm text-textMain/60">Csatlakozz a Mimir közösségéhez</p>
          </div>

          <form onSubmit={handleRegister} className="flex flex-col gap-5">
            <div>
              <label className="block text-sm font-medium text-textMain mb-2 ml-1">E-mail cím</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail size={18} className="text-textMain/40" />
                </div>
                <input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="pelda@email.com"
                  className="w-full bg-surface/30 border border-border/50 rounded-xl py-3 pl-11 pr-4 text-textMain placeholder:text-textMain/30 focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-textMain mb-2 ml-1">Jelszó</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock size={18} className="text-textMain/40" />
                </div>
                <input 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="Legalább 6 karakter"
                  className="w-full bg-surface/30 border border-border/50 rounded-xl py-3 pl-11 pr-4 text-textMain placeholder:text-textMain/30 focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-textMain mb-2 ml-1">Jelszó újra</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock size={18} className="text-textMain/40" />
                </div>
                <input 
                  type="password" 
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full bg-surface/30 border border-border/50 rounded-xl py-3 pl-11 pr-4 text-textMain placeholder:text-textMain/30 focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all"
                />
              </div>
            </div>

            {errorMsg && <p className="text-sm text-red-400 text-center">{errorMsg}</p>}
            {successMsg && <p className="text-sm text-green-400 text-center leading-relaxed">{successMsg}</p>}

            <Button type="submit" isLoading={isLoading} className="w-full mt-2 group">
              {!isLoading && (
                <>
                  Regisztráció
                  <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-textMain/60">
            Már van fiókod?{' '}
            <Link to="/login" className="text-accent hover:underline font-medium">
              Lépj be itt
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}