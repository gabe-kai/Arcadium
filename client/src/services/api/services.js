import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';

/**
 * Fetch logs for a specific service
 * @param {string} serviceId - Service identifier (e.g., 'wiki', 'auth')
 * @param {number} limit - Maximum number of log entries to fetch (default: 100)
 * @param {string} level - Optional log level filter (ERROR, WARNING, INFO, DEBUG)
 * @param {string} token - Optional auth token
 */
export function fetchServiceLogs(serviceId, limit = 100, level = null, token = null) {
  // Get service URL from environment or use defaults
  const serviceUrls = {
    wiki: import.meta.env.VITE_WIKI_API_BASE_URL?.replace('/api', '') || 'http://localhost:5000',
    auth: import.meta.env.VITE_AUTH_SERVICE_URL || 'http://localhost:8000',
  };

  const logEndpoints = {
    wiki: '/api/admin/logs',
    auth: '/api/logs',
  };

  const baseUrl = serviceUrls[serviceId];
  const endpoint = logEndpoints[serviceId];

  if (!baseUrl || !endpoint) {
    return Promise.reject(new Error(`Logs endpoint not available for service: ${serviceId}`));
  }

  const url = `${baseUrl}${endpoint}?limit=${limit}${level ? `&level=${level}` : ''}`;

  const config = {
    timeout: 10000, // 10 seconds
  };

  if (token) {
    config.headers = {
      Authorization: `Bearer ${token}`,
    };
  }

  return apiClient.get(url, config)
    .then((res) => res.data)
    .catch((error) => {
      // Handle errors gracefully
      if (error.response?.status === 401 || error.response?.status === 403) {
        return { logs: [], count: 0, error: 'Authentication required' };
      }
      if (error.code === 'ECONNABORTED') {
        return { logs: [], count: 0, error: 'Request timeout' };
      }
      return { logs: [], count: 0, error: error.message || 'Failed to fetch logs' };
    });
}

/**
 * Fetch service status for all services
 * Temporarily works without authentication
 * Uses a longer timeout since this endpoint checks multiple services
 * @param {string} token - Optional auth token to use for the request (not required currently)
 */
export function fetchServiceStatus(token = null) {
  const config = {
    timeout: 30000, // 30 seconds - service checks can take time
  };

  // Token is optional - endpoint is temporarily public
  // If token is provided, attach it directly to avoid localStorage timing issues
  if (token) {
    config.headers = {
      Authorization: `Bearer ${token}`,
    };
  }

  return apiClient
    .get('/admin/service-status', config)
    .then((res) => res.data)
    .catch((error) => {

      // Handle 401 (Unauthorized) or 403 (Forbidden) gracefully
      // Don't throw error - return empty result so component can show "unknown" status
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        console.warn('Service status returned 401/403 - authentication issue');
        // Return empty status object to indicate no access
        // Include error info to help distinguish auth issues
        return {
          services: {},
          last_updated: null,
          authError: true,
          error: error?.response?.status === 401 ? 'Authentication required' : 'Access forbidden'
        };
      }
      // Handle timeout gracefully - service checks might be slow
      if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
        console.warn('Service status check timed out - some services may be slow or unreachable');
        // Return empty services to indicate timeout/failure
        return { services: {}, last_updated: null, error: 'Request timeout - services may be slow or unreachable' };
      }
      // Log other errors for debugging
      console.error('Service status fetch error:', {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        message: error?.message,
        url: error?.config?.url,
      });
      // Re-throw other errors (network errors, etc.)
      throw error;
    });
}

/**
 * React Query hook for service status
 * @param {boolean} enabled - Whether to enable the query (default: true)
 * @param {boolean} authReady - Whether auth is ready (default: true)
 * @param {string} token - Optional auth token to use for the request
 */
export function useServiceStatus(enabled = true, authReady = true, token = null) {
  return useQuery({
    queryKey: ['serviceStatus', token], // Include token in query key to refetch if token changes
    queryFn: () => fetchServiceStatus(token),
    enabled: enabled && authReady, // Only run if enabled AND auth is ready
    refetchInterval: enabled && authReady ? 15000 : false, // Refetch every 15 seconds for responsive updates
    refetchIntervalInBackground: false, // Don't refetch when tab is in background to save resources
    retry: (failureCount, error) => {
      // Don't retry on 401/403 (authentication/authorization errors)
      // These are handled gracefully in fetchServiceStatus
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        return false;
      }
      // Don't retry on timeout - service checks are slow, don't compound the issue
      if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
        return false;
      }
      // Retry network/5xx errors up to 1 time (reduced from 2 to avoid long waits)
      return failureCount < 1;
    },
  });
}

/**
 * Refresh service status (triggers a new health check)
 */
export function refreshServiceStatus() {
  return apiClient.post('/admin/service-status/refresh').then((res) => res.data);
}

/**
 * Mutation hook for refreshing service status
 */
/**
 * React Query hook for fetching service logs
 * @param {string} serviceId - Service identifier
 * @param {boolean} enabled - Whether to fetch logs
 * @param {number} limit - Maximum number of log entries
 * @param {string} level - Optional log level filter
 * @param {string} token - Optional auth token
 */
export function useServiceLogs(serviceId, enabled = true, limit = 100, level = null, token = null) {
  return useQuery({
    queryKey: ['serviceLogs', serviceId, limit, level, token],
    queryFn: () => fetchServiceLogs(serviceId, limit, level, token),
    enabled: enabled && !!serviceId,
    refetchInterval: false, // Don't auto-refresh logs
    retry: 1,
  });
}

export function useRefreshServiceStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: refreshServiceStatus,
    onSuccess: () => {
      // Invalidate and refetch service status after refresh
      queryClient.invalidateQueries({ queryKey: ['serviceStatus'] });
    },
  });
}

/**
 * Update service status notes (for manual maintenance notes)
 */
export function updateServiceStatusNotes(serviceId, notes) {
  return apiClient
    .put('/admin/service-status', {
      service: serviceId,
      notes,
    })
    .then((res) => res.data);
}

/**
 * Mutation hook for updating service status notes
 */
export function useUpdateServiceStatusNotes() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ serviceId, notes }) => updateServiceStatusNotes(serviceId, notes),
    onSuccess: () => {
      // Invalidate and refetch service status after update
      queryClient.invalidateQueries({ queryKey: ['serviceStatus'] });
    },
  });
}
