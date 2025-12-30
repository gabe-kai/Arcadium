import axios from 'axios';
import { getToken, clearToken } from '../auth/tokenStorage';

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
  } else {
    // Log warning if no token for authenticated endpoints (excluding service-status which is temporarily public)
    const isAuthEndpoint = (config.url?.includes('/admin/') && !config.url?.includes('/admin/service-status')) ||
                          (config.method && ['post', 'put', 'delete'].includes(config.method.toLowerCase()));
    if (isAuthEndpoint) {
      console.warn('No authentication token found for', config.method?.toUpperCase() || 'GET', config.url);
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Ignore aborted/cancelled requests (common during component unmount or navigation)
    if (error.code === 'ECONNABORTED' || error.message === 'Request aborted' || error.name === 'CanceledError') {
      // Log timeout/aborted errors for visibility in tests and debugging
      console.error('API error:', error);
      return Promise.reject(error);
    }

    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      const errorMessage = error.response?.data?.error || 'Authentication failed';
      const requestUrl = error.config?.url || '';

      // Skip redirect for service-status endpoint (allows anonymous browsing)
      // This endpoint gracefully handles 401/403 for non-admin users
      if (requestUrl.includes('/admin/service-status')) {
        // Just log and reject - let the calling code handle it gracefully
        console.warn('Service status requires authentication:', errorMessage);
        return Promise.reject(error);
      }

      console.warn('Authentication error (401):', errorMessage);

      // Clear invalid token
      clearToken();

      // Only redirect if we're not already on the sign-in page
      if (window.location.pathname !== '/signin' && !window.location.pathname.startsWith('/signin')) {
        // Store the current location to redirect back after login
        const currentPath = window.location.pathname + window.location.search;
        sessionStorage.setItem('redirectAfterLogin', currentPath);

        // Show user-friendly message
        alert('Your session has expired. Please sign in again.');

        // Redirect to sign-in page
        window.location.href = '/signin';
      }
    }

    // Basic error logging; can be expanded later
    // Only log non-401, non-aborted errors
    if (error.response?.status !== 401 && error.code !== 'ECONNABORTED') {
      console.error('API error:', error);
    }
    return Promise.reject(error);
  },
);
