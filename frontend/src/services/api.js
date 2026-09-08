import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Attach JWT token automatically
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Global response error handler
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token on authentication failure
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: async (username, email, password) => {
    const res = await apiClient.post('/auth/register', { username, email, password });
    return res.data;
  },
  login: async (username, password) => {
    const res = await apiClient.post('/auth/login', { username, password });
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

export const sessionAPI = {
  startSession: async (metadata = {}) => {
    const res = await apiClient.post('/sessions/start', {
      user_agent: navigator.userAgent,
      screen_resolution: `${window.screen.width}x${window.screen.height}`,
      ...metadata,
    });
    return res.data;
  },
  stopSession: async (sessionId) => {
    const res = await apiClient.post('/sessions/stop', { session_id: sessionId });
    return res.data;
  },
  getSession: async (sessionId) => {
    const res = await apiClient.get(`/sessions/${sessionId}`);
    return res.data;
  },
};

export const behaviorAPI = {
  sendKeystrokes: async (sessionId, events) => {
    const res = await apiClient.post('/behavior/keystrokes', {
      session_id: sessionId,
      events,
    });
    return res.data;
  },
  sendMouse: async (sessionId, events) => {
    const res = await apiClient.post('/behavior/mouse', {
      session_id: sessionId,
      events,
    });
    return res.data;
  },
};

export const predictAPI = {
  predict: async (sessionId) => {
    const res = await apiClient.post('/predict', { session_id: sessionId });
    return res.data;
  },
  getHistory: async (sessionId) => {
    const res = await apiClient.get('/predictions/history', {
      params: { session_id: sessionId },
    });
    return res.data;
  },
};

export const explainAPI = {
  explain: async (sessionId) => {
    const res = await apiClient.post('/explain', { session_id: sessionId });
    return res.data;
  },
};
