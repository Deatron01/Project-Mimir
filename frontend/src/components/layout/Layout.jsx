import React from 'react';
import Navbar from './Navbar';
import Footer from './Footer';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col relative selection:bg-accent/30 selection:text-textMain">
      
      {/* GLOBÁLIS HÁTTÉR EFFEKT (Megerősített Glow) */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none bg-background">
        
        {/* Bal felső nagy ragyogás (Primary szín) */}
        <div className="absolute top-[-15%] left-[-10%] w-[50rem] h-[50rem] rounded-full bg-primary opacity-30 blur-[100px] transition-colors duration-1000 ease-in-out" />
        
        {/* Jobb középső ragyogás (Accent szín) */}
        <div className="absolute top-[20%] right-[-15%] w-[45rem] h-[45rem] rounded-full bg-accent opacity-25 blur-[100px] transition-colors duration-1000 ease-in-out" />
        
        {/* Bal alsó mélyebb ragyogás (Surface szín) */}
        <div className="absolute bottom-[-10%] left-[5%] w-[50rem] h-[50rem] rounded-full bg-surface opacity-70 blur-[90px] transition-colors duration-1000 ease-in-out" />
        
      </div>

      {/* Navigáció */}
      <Navbar />
      
      {/* A fő tartalom */}
      <main className="flex-grow pt-20 relative z-10">
        {children}
      </main>
      
      {/* Lábléc */}
      <div className="relative z-10">
        <Footer />
      </div>
    </div>
  );
}