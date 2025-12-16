import React, { createContext, useContext, useMemo, useState, useEffect } from 'react';
import { getToken, setToken, clearToken } from './tokenStorage';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => getToken());
  const [user, setUser] = useState(null); // Placeholder until real auth integration

  useEffect(() => {
    setToken(token);
  }, [token]);

  const signIn = async (nextToken, userInfo = null) => {
    setTokenState(nextToken);
    setUser(userInfo);
  };

  const signOut = () => {
    clearToken();
    setTokenState(null);
    setUser(null);
  };

  const value = useMemo(
    () => ({ token, user, signIn, signOut, isAuthenticated: Boolean(token) }),
    [token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
