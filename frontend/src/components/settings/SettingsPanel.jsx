import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

const panelVariants = {
  hidden: { opacity: 0, scale: 0.95, pointerEvents: 'none' },
  visible: { 
    opacity: 1, 
    scale: 1, 
    pointerEvents: 'auto',
    transition: { type: 'spring', damping: 20, stiffness: 300 }
  },
  exit: { 
    opacity: 0, 
    scale: 0.95,
    pointerEvents: 'none', 
    transition: { duration: 0.2 } 
    }
};

export default function SettingsPanel({ panelSide }) {
  const { themes, activeThemeId, setActiveThemeId } = useTheme();

  // Dynamically position the panel based on where the floating button is
  const positionClasses = panelSide === 'left' 
    ? 'right-[calc(100%+16px)] origin-right' 
    : 'left-[calc(100%+16px)] origin-left';

  return (
    <motion.div
      variants={panelVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      // Stop propagation so clicking inside the panel doesn't trigger drag on the parent
      onPointerDown={(e) => e.stopPropagation()}
      className={`absolute top-0 w-64 p-5 rounded-2xl bg-surface/80 backdrop-blur-xl border border-primary/20 shadow-glass z-50 ${positionClasses}`}
    >
      <h3 className="text-sm font-bold tracking-wider uppercase text-textMain/70 mb-4">
        Theme Appearance
      </h3>
      
      <div className="flex flex-col gap-3">
        {themes.map((theme) => {
          const isActive = activeThemeId === theme.id;
          
          return (
            <button
              key={theme.id}
              onClick={() => setActiveThemeId(theme.id)}
              className={`relative flex items-center gap-3 p-2 rounded-xl transition-all duration-300 group hover:bg-background/50 ${
                isActive ? 'bg-background/80 ring-1 ring-primary/50' : ''
              }`}
              aria-label={`Select ${theme.name} theme`}
            >
              {/* Color preview circles */}
              <div className="flex -space-x-2">
                <span className="w-6 h-6 rounded-full shadow-sm border border-black/10" style={{ backgroundColor: theme.colors.primary }} />
                <span className="w-6 h-6 rounded-full shadow-sm border border-black/10" style={{ backgroundColor: theme.colors.accent }} />
              </div>
              
              <span className={`text-sm font-medium transition-colors ${isActive ? 'text-primary' : 'text-textMain group-hover:text-textMain/80'}`}>
                {theme.name}
              </span>

              {isActive && (
                <motion.div layoutId="check-icon" className="ml-auto text-primary">
                  <Check size={16} strokeWidth={3} />
                </motion.div>
              )}
            </button>
          );
        })}
      </div>
    </motion.div>
  );
}