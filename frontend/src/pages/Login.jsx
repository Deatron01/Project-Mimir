import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      // IDE KERÜL A BACKEND API HÍVÁS (ahol az auth.py fut majd)
      // Példa: const res = await fetch('http://localhost:8000/api/login', { ... })
      
      // Szimulált hálózati késleltetés a teszteléshez
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Szimulált válasz
      setSuccessMsg('Sikeres belépés! Átirányítás...');
      login({ email });
      navigate('/chat');

    } catch (err) {
      setErrorMsg('Helytelen e-mail vagy jelszó!');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative overflow-hidden min-h-[80vh] flex items-center justify-center">
      <div className="absolute top-[20%] left-[-10%] w-[40rem] h-[40rem] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }} 
        className="w-full max-w-md px-6 z-10"
      >
        <div className="p-8 rounded-3xl border border-border/50 bg-background/60 backdrop-blur-xl shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-accent to-primary" />
          
          <div className="text-center mb-8">
            <h1 className="text-3xl font-extrabold tracking-tight mb-2">Üdv újra a Mimirben</h1>
            <p className="text-sm text-textMain/60">Jelentkezz be a fiókodba a folytatáshoz</p>
          </div>

          <form onSubmit={handleLogin} className="flex flex-col gap-5">
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
                  placeholder="••••••••"
                  className="w-full bg-surface/30 border border-border/50 rounded-xl py-3 pl-11 pr-4 text-textMain placeholder:text-textMain/30 focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all"
                />
              </div>
            </div>

            {errorMsg && <p className="text-sm text-red-400 text-center">{errorMsg}</p>}
            {successMsg && <p className="text-sm text-green-400 text-center">{successMsg}</p>}

            <Button type="submit" isLoading={isLoading} className="w-full mt-2 group">
              {!isLoading && (
                <>
                  Bejelentkezés
                  <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-textMain/60">
            Nincs még fiókod?{' '}
            <Link to="/register" className="text-accent hover:underline font-medium">
              Regisztrálj itt
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}