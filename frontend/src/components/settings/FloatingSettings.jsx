import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, X } from 'lucide-react';
import SettingsPanel from './SettingsPanel';

export default function FloatingSettings() {
  const [isOpen, setIsOpen] = useState(false);
  const [panelSide, setPanelSide] = useState('left'); // 'left' or 'right'
  const [windowConstraints, setWindowConstraints] = useState({ top: 0, left: 0, right: 0, bottom: 0 });
  
  const containerRef = useRef(null);
  const isDragging = useRef(false);

  // Update drag constraints dynamically based on window size
  useEffect(() => {
    const updateConstraints = () => {
      // 64px is roughly the size of the button + some padding
      setWindowConstraints({
        top: 20,
        left: 20,
        right: window.innerWidth - 84,
        bottom: window.innerHeight - 84,
      });
    };
    
    updateConstraints();
    window.addEventListener('resize', updateConstraints);
    return () => window.removeEventListener('resize', updateConstraints);
  }, []);

  // Handle outside click to close the panel
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen]);

  const handleDragStart = () => {
    isDragging.current = true;
    if (isOpen) setIsOpen(false); // Close panel while dragging
  };

  const handleDragEnd = (event, info) => {
    // Add a small delay to prevent the click event from firing immediately after drag
    setTimeout(() => {
      isDragging.current = false;
    }, 150);

    // Determine which side of the screen the button is on to open the panel inwards
    if (info.point.x > window.innerWidth / 2) {
      setPanelSide('left');
    } else {
      setPanelSide('right');
    }
  };

  const togglePanel = () => {
    // If it was just a drag, don't open the panel
    if (!isDragging.current) {
      setIsOpen((prev) => !prev);
    }
  };

  return (
    <motion.div
      ref={containerRef}
      drag
      dragMomentum={false} // Prevents flying off screen after release
      dragElastic={0.1}
      dragConstraints={windowConstraints}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      // Initial positioning (bottom right corner)
      initial={{ x: window.innerWidth - 100, y: window.innerHeight - 100 }}
      className="fixed top-0 left-0 z-[9999] flex flex-col"
      style={{ touchAction: 'none' }} // Prevents page scroll while dragging on mobile
    >
      {/* The Floating Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={togglePanel}
        aria-label="Toggle Theme Settings"
        className="w-14 h-14 rounded-full bg-primary text-background shadow-lg flex items-center justify-center cursor-grab active:cursor-grabbing border-2 border-transparent hover:border-accent/50 transition-colors"
      >
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.div
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <X size={24} />
            </motion.div>
          ) : (
            <motion.div
              key="settings"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Settings size={24} />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {/* The Theme Panel */}
      <AnimatePresence>
        {isOpen && <SettingsPanel key="theme-panel-key" panelSide={panelSide} />}
      </AnimatePresence>
    </motion.div>
  );
}