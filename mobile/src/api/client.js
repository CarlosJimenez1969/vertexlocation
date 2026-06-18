import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ⚠️ Cambia esta IP por la de tu backend.
// En emulador Android usa 10.0.2.2; en dispositivo físico, la IP LAN de tu PC.
export const API_BASE = 'http://10.0.2.2:8000';

const api = axios.create({ baseURL: `${API_BASE}/api` });

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('vx_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;

export const authApi = {
  login: (email, password) => api.post('/auth/login-json', { email, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

export const petsApi = {
  list: () => api.get('/pets'),
  create: (data) => api.post('/pets', data),
};

export const positionsApi = {
  latest: (petId) => api.get(`/positions/latest/${petId}`),
};

export const moodApi = {
  current: (petId) => api.get(`/mood/${petId}/current`),
  activity: (petId, dias = 7) => api.get(`/mood/${petId}/activity?dias=${dias}`),
};

export const alertsApi = {
  list: () => api.get('/alerts'),
};
