import axios from 'axios';

// Cliente HTTP central. El proxy de Vite redirige /api -> backend:8000
const api = axios.create({ baseURL: '/api' });

// Adjunta el token JWT en cada petición
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('vx_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Si el token expira, redirige al login
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err.response?.status;
    if (status === 401) {
      localStorage.removeItem('vx_token');
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    // 403 = el token no tiene permisos para esta acción. Puede ser que la
    // sesión guardada ya no sea de admin (p.ej. se inició sesión con otra
    // cuenta en otra pestaña). Avisamos para que la app revalide la sesión.
    if (status === 403) {
      window.dispatchEvent(new CustomEvent('vx:forbidden'));
    }
    return Promise.reject(err);
  }
);

export default api;

// --- Endpoints ---
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (email, password) => api.post('/auth/login-json', { email, password }),
  me: () => api.get('/auth/me'),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) =>
    api.post('/auth/reset-password', { token, new_password: newPassword }),
};

export const petsApi = {
  list: () => api.get('/pets'),
  create: (data) => api.post('/pets', data),
  update: (id, data) => api.patch(`/pets/${id}`, data),
  remove: (id) => api.delete(`/pets/${id}`),
  devices: () => api.get('/pets/devices'),
  registerDevice: (data) => api.post('/pets/devices', data),
  uploadPhoto: (id, file) => {
    const fd = new FormData();
    fd.append('file', file);
    return api.post(`/pets/${id}/photo`, fd);
  },
};

export const positionsApi = {
  latest: (petId) => api.get(`/positions/latest/${petId}`),
  history: (petId, dias = 7) => api.get(`/positions/history/${petId}?dias=${dias}`),
};

export const vehiclesApi = {
  list: () => api.get('/vehicles'),
  create: (data) => api.post('/vehicles', data),
  update: (id, data) => api.patch(`/vehicles/${id}`, data),
  remove: (id) => api.delete(`/vehicles/${id}`),
  latest: (id) => api.get(`/vehicles/${id}/latest`),
  history: (id, dias = 7) => api.get(`/vehicles/${id}/history?dias=${dias}`),
  arm: (id) => api.post(`/vehicles/${id}/arm`),
  disarm: (id) => api.post(`/vehicles/${id}/disarm`),
  engineCut: (id, password) => api.post(`/vehicles/${id}/engine-cut`, { password }),
  engineRestore: (id, password) => api.post(`/vehicles/${id}/engine-restore`, { password }),
  uploadPhoto: (id, file) => {
    const fd = new FormData();
    fd.append('file', file);
    return api.post(`/vehicles/${id}/photo`, fd);
  },
};

export const devicesApi = {
  list: () => api.get('/devices'),
  register: (data) => api.post('/devices', data),
  update: (id, data) => api.patch(`/devices/${id}`, data),
  assign: (id, tipo, targetId) => api.post(`/devices/${id}/assign`, { tipo, target_id: targetId }),
  unassign: (id) => api.post(`/devices/${id}/unassign`),
  remove: (id) => api.delete(`/devices/${id}`),
};

export const geofencesApi = {
  list: () => api.get('/geofences'),
  create: (data) => api.post('/geofences', data),
  remove: (id) => api.delete(`/geofences/${id}`),
};

export const moodApi = {
  current: (petId) => api.get(`/mood/${petId}/current`),
  recalculate: (petId) => api.post(`/mood/${petId}/recalculate`),
  history: (petId, dias = 7) => api.get(`/mood/${petId}/history?dias=${dias}`),
  activity: (petId, dias = 7) => api.get(`/mood/${petId}/activity?dias=${dias}`),
};

// --- Administración (solo rol admin) ---
const photoForm = (file) => { const fd = new FormData(); fd.append('file', file); return fd; };
export const adminApi = {
  users: {
    list: () => api.get('/admin/users'),
    create: (data) => api.post('/admin/users', data),
    update: (id, data) => api.patch(`/admin/users/${id}`, data),
  },
  pets: {
    list: () => api.get('/admin/pets'),
    create: (usuarioId, data) => api.post(`/admin/pets?usuario_id=${usuarioId}`, data),
    update: (id, data) => api.patch(`/admin/pets/${id}`, data),
    remove: (id) => api.delete(`/admin/pets/${id}`),
    uploadPhoto: (id, file) => api.post(`/pets/${id}/photo`, photoForm(file)),
  },
  vehicles: {
    list: () => api.get('/admin/vehicles'),
    create: (usuarioId, data) => api.post(`/admin/vehicles?usuario_id=${usuarioId}`, data),
    update: (id, data) => api.patch(`/admin/vehicles/${id}`, data),
    remove: (id) => api.delete(`/admin/vehicles/${id}`),
    uploadPhoto: (id, file) => api.post(`/vehicles/${id}/photo`, photoForm(file)),
  },
  devices: {
    list: () => api.get('/admin/devices'),
    create: (data) => api.post('/admin/devices', data),
    update: (id, data) => api.patch(`/admin/devices/${id}`, data),
    remove: (id) => api.delete(`/admin/devices/${id}`),
    assign: (id, tipo, targetId) => api.post(`/admin/devices/${id}/assign?tipo=${tipo}&target_id=${targetId}`),
    unassign: (id) => api.post(`/admin/devices/${id}/unassign`),
  },
};

export const alertsApi = {
  list: (soloNoLeidas = false) => api.get(`/alerts?solo_no_leidas=${soloNoLeidas}`),
  markRead: (id) => api.post(`/alerts/${id}/read`),
};

export const shareApi = {
  create: (tipo, targetId, horas = 24) => api.post('/share', { tipo, target_id: targetId, horas }),
  list: () => api.get('/share/me'),
  revoke: (id) => api.delete(`/share/${id}`),
  getPublic: (token) => api.get(`/share/${token}`),
};

export const maintenanceApi = {
  list: (vehiculoId) => api.get(`/maintenance?vehiculo_id=${vehiculoId}`),
  create: (data) => api.post('/maintenance', data),
  update: (id, data) => api.patch(`/maintenance/${id}`, data),
  done: (id) => api.post(`/maintenance/${id}/done`),
  remove: (id) => api.delete(`/maintenance/${id}`),
};
