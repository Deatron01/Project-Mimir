import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext();

const readUser = () => {
  try {
    return JSON.parse(localStorage.getItem('mimir_user') || 'null');
  } catch {
    return null;
  }
};

export const AuthProvider = ({ children }) => {
  // NOTE: still a client-side placeholder until the auth service lands (GW-01 / FE-04).
  const [user, setUser] = useState(readUser);

  const login = (userData) => {
    setUser(userData);
    try {
      localStorage.setItem('mimir_user', JSON.stringify(userData));
    } catch {
      /* ignore */
    }
  };

  const logout = () => {
    setUser(null);
    try {
      localStorage.removeItem('mimir_user');
    } catch {
      /* ignore */
    }
  };

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
