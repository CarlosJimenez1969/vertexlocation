import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authApi } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const token = await AsyncStorage.getItem('vx_token');
      if (token) {
        try {
          const { data } = await authApi.me();
          setUser(data);
        } catch {
          await AsyncStorage.removeItem('vx_token');
        }
      }
      setLoading(false);
    })();
  }, []);

  const login = async (email, password) => {
    const { data } = await authApi.login(email, password);
    await AsyncStorage.setItem('vx_token', data.access_token);
    setUser(data.user);
  };

  const register = async (form) => {
    const { data } = await authApi.register(form);
    await AsyncStorage.setItem('vx_token', data.access_token);
    setUser(data.user);
  };

  const logout = async () => {
    await AsyncStorage.removeItem('vx_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
