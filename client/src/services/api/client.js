import axios from 'axios';
import { getToken } from '../auth/tokenStorage';

const baseURL =
  import.meta.env.VITE_WIKI_API_BASE_URL || 'http://localhost:5000/api';

export const apiClient = axios.create({
  baseURL,
  timeout: 10000,
});

// Attach Authorization header when a token is present
apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    if (!config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Basic error logging; can be expanded later
    console.error('API error:', error);
    return Promise.reject(error);
  },
);
