import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import About from './pages/About';
import Pricing from './pages/Pricing';
import Login from './pages/Login';
import Register from './pages/Register';
import Contact from './pages/Contact';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';

// Új importok a témaváltóhoz és a lebegő gombhoz
import { ThemeProvider } from './context/ThemeContext';
import FloatingSettings from './components/settings/FloatingSettings';

function App() {
  return (
    // A ThemeProvider körbeöleli az egész appot, így a színek mindenhol elérhetők lesznek
    <ThemeProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
          </Routes>
        </Layout>
      </Router>
      
      {/* A lebegő beállítások gomb a Routeren kívül (de a Provideren belül) kap helyet, 
          hogy navigáció közben is folyamatosan a képernyőn maradjon */}
      <FloatingSettings />
    </ThemeProvider>
  );
}

export default App;