import { createContext, useContext, useCallback, useEffect, useState } from 'react';
import { authApi } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Revalida la sesión contra el backend: actualiza el usuario según el token
  // realmente guardado. Si el token ya no es válido, cierra la sesión.
  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem('vx_token');
    if (!token) { setUser(null); return null; }
    try {
      const { data } = await authApi.me();
      setUser(data);
      return data;
    } catch {
      localStorage.removeItem('vx_token');
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    // Si se llega con ?fresh=1 (botón "Ir a la aplicación" de la landing),
    // forzar autenticación: descartar cualquier sesión previa y exigir login.
    if (new URLSearchParams(window.location.search).get('fresh') === '1') {
      localStorage.removeItem('vx_token');
      setLoading(false);
      return;
    }
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  // Si una acción devuelve 403, el token guardado podría ya no ser de admin
  // (p.ej. se inició sesión con otra cuenta en otra pestaña). Revalidamos:
  // si el usuario real ya no es admin, el panel de admin deja de mostrarse.
  useEffect(() => {
    const onForbidden = () => { refreshUser(); };
    // localStorage se comparte entre pestañas: si el token cambia o se borra
    // en otra pestaña, esta pestaña sincroniza su sesión.
    const onStorage = (e) => { if (e.key === 'vx_token') refreshUser(); };
    window.addEventListener('vx:forbidden', onForbidden);
    window.addEventListener('storage', onStorage);
    return () => {
      window.removeEventListener('vx:forbidden', onForbidden);
      window.removeEventListener('storage', onStorage);
    };
  }, [refreshUser]);

  const login = async (email, password) => {
    const { data } = await authApi.login(email, password);
    localStorage.setItem('vx_token', data.access_token);
    setUser(data.user);
    return data.user;
  };

  const register = async (form) => {
    // No autenticamos automáticamente: tras registrarse, el usuario debe
    // iniciar sesión. (El backend devuelve un token, pero aquí lo ignoramos.)
    const { data } = await authApi.register(form);
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem('vx_token');
    setUser(null);
  };

  const isAdmin = user?.rol === 'admin';

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAdmin, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
