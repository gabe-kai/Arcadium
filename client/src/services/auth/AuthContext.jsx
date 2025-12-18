import React, { createContext, useContext, useMemo, useState, useEffect } from 'react';
import { getToken, setToken, clearToken } from './tokenStorage';
import { authApi } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => getToken());
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore user info from token on mount
  useEffect(() => {
    let isMounted = true;
    
    const restoreAuth = async () => {
      const storedToken = getToken();
      if (storedToken) {
        try {
          // Verify token and get user info
          const result = await authApi.verifyToken(storedToken);
          
          // Only update state if component is still mounted
          if (!isMounted) return;
          
          if (result.valid && result.user) {
            setTokenState(storedToken);
            // Normalize user object format
            setUser({
              id: result.user.id || result.user.user_id,
              username: result.user.username || '',
              role: result.user.role || 'viewer',
              email: result.user.email,
            });
          } else {
            // Token is invalid, clear it
            clearToken();
            setTokenState(null);
            setUser(null);
          }
        } catch (error) {
          // Ignore aborted requests (component unmounted)
          if (error.code === 'ECONNABORTED' || error.message === 'Request aborted') {
            return;
          }
          
          // Token verification failed, clear it
          console.warn('Token verification failed on mount:', error);
          
          // Only update state if component is still mounted
          if (!isMounted) return;
          
          clearToken();
          setTokenState(null);
          setUser(null);
        }
      } else {
        if (!isMounted) return;
        setTokenState(null);
        setUser(null);
      }
      
      if (isMounted) {
        setIsLoading(false);
      }
    };

    restoreAuth();
    
    // Cleanup function to prevent state updates after unmount
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (token) {
      setToken(token);
    } else {
      clearToken();
    }
  }, [token]);

  const signIn = async (nextToken, userInfo = null) => {
    setTokenState(nextToken);
    setUser(userInfo);
    setToken(nextToken);
  };

  const signOut = () => {
    clearToken();
    setTokenState(null);
    setUser(null);
  };

  const value = useMemo(
    () => ({ token, user, signIn, signOut, isAuthenticated: Boolean(token), isLoading }),
    [token, user, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
