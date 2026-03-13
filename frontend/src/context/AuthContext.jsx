import { createContext, useContext, useEffect, useState } from 'react';

import { authApi, clearAuthSession, getStoredToken, storeAuthSession } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => getStoredToken());
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      const storedToken = getStoredToken();
      if (!storedToken) {
        if (isMounted) {
          setIsReady(true);
        }
        return;
      }

      try {
        const currentUser = await authApi.me();
        if (isMounted) {
          setToken(storedToken);
          setUser(currentUser);
        }
      } catch {
        clearAuthSession();
        if (isMounted) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsReady(true);
        }
      }
    }

    restoreSession();
    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (credentials) => {
    const response = await authApi.login(credentials);
    storeAuthSession(response.access_token, response.user);
    setToken(response.access_token);
    setUser(response.user);
    return response.user;
  };

  const register = async (payload) => {
    await authApi.register(payload);
    return login(payload);
  };

  const logout = () => {
    clearAuthSession();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: Boolean(token && user),
        isReady,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
