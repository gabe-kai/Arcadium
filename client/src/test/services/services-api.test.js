import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useServiceStatus, useServiceLogs, fetchServiceStatus, fetchServiceLogs } from '../../services/api/services';
import { apiClient } from '../../services/api/client';

// Mock the API client
vi.mock('../../services/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Services API', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  describe('fetchServiceStatus', () => {
    it('fetches service status successfully', async () => {
      const mockResponse = {
        services: {
          wiki: {
            name: 'Wiki Service',
            status: 'healthy',
            response_time_ms: 5.2,
          },
        },
        last_updated: '2024-01-01T12:00:00Z',
      };

      apiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await fetchServiceStatus('test-token');

      expect(apiClient.get).toHaveBeenCalledWith('/admin/service-status', {
        timeout: 30000,
        headers: {
          Authorization: 'Bearer test-token',
        },
      });
      expect(result).toEqual(mockResponse);
    });

    it('handles 401/403 errors gracefully', async () => {
      const error = {
        response: { status: 401 },
        message: 'Unauthorized',
      };
      apiClient.get.mockRejectedValue(error);

      const result = await fetchServiceStatus('test-token');

      expect(result).toEqual({
        services: {},
        last_updated: null,
        authError: true,
        error: 'Authentication required',
      });
    });

    it('handles timeout errors gracefully', async () => {
      const error = {
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded',
      };
      apiClient.get.mockRejectedValue(error);

      const result = await fetchServiceStatus('test-token');

      expect(result).toEqual({
        services: {},
        last_updated: null,
        error: 'Request timeout - services may be slow or unreachable',
      });
    });

    it('handles other errors', async () => {
      const error = new Error('Network error');
      apiClient.get.mockRejectedValue(error);

      await expect(fetchServiceStatus('test-token')).rejects.toThrow('Network error');
    });
  });

  describe('useServiceStatus', () => {
    it('returns service status data', async () => {
      const mockResponse = {
        services: {
          wiki: { name: 'Wiki Service', status: 'healthy' },
        },
        last_updated: '2024-01-01T12:00:00Z',
      };

      apiClient.get.mockResolvedValue({ data: mockResponse });

      const wrapper = ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const { result } = renderHook(() => useServiceStatus(true, true, 'test-token'), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockResponse);
    });

    it('handles loading state', () => {
      apiClient.get.mockImplementation(() => new Promise(() => {})); // Never resolves

      const wrapper = ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const { result } = renderHook(() => useServiceStatus(true, true, 'test-token'), { wrapper });

      expect(result.current.isLoading).toBe(true);
    });

    it('handles error state', async () => {
      const error = new Error('Failed to fetch');
      apiClient.get.mockRejectedValue(error);

      const wrapper = ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const { result } = renderHook(() => useServiceStatus(true, true, 'test-token'), { wrapper });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeDefined();
    });
  });

  describe('fetchServiceLogs', () => {
    it('fetches logs for wiki service', async () => {
      const mockLogs = {
        logs: [
          {
            timestamp: '2024-01-01T12:00:00',
            level: 'ERROR',
            message: 'Test error',
            raw_message: 'Test error',
          },
        ],
      };

      apiClient.get.mockResolvedValue({ data: mockLogs });

      const result = await fetchServiceLogs('wiki', 100, null, 'test-token');

      expect(apiClient.get).toHaveBeenCalledWith('/admin/logs', {
        timeout: 15000,
        params: { limit: 100, level: null },
        headers: {
          Authorization: 'Bearer test-token',
        },
      });
      expect(result).toEqual(mockLogs);
    });

    it('fetches logs for auth service', async () => {
      const mockLogs = { logs: [] };
      apiClient.get.mockResolvedValue({ data: mockLogs });

      await fetchServiceLogs('auth', 50, 'ERROR', 'test-token');

      expect(apiClient.get).toHaveBeenCalledWith('/api/logs', {
        timeout: 15000,
        params: { limit: 50, level: 'ERROR' },
        headers: {
          Authorization: 'Bearer test-token',
        },
      });
    });

    it('rejects for unknown service', async () => {
      await expect(fetchServiceLogs('unknown', 100, null, 'test-token')).rejects.toThrow(
        'Logs not available for this service'
      );
    });

    it('handles errors gracefully', async () => {
      const error = { response: { status: 500 }, message: 'Server error' };
      apiClient.get.mockRejectedValue(error);

      await expect(fetchServiceLogs('wiki', 100, null, 'test-token')).rejects.toEqual(error);
    });
  });

  describe('useServiceLogs', () => {
    it('returns logs data', async () => {
      const mockLogs = {
        logs: [
          {
            timestamp: '2024-01-01T12:00:00',
            level: 'ERROR',
            message: 'Test error',
          },
        ],
      };

      apiClient.get.mockResolvedValue({ data: mockLogs });

      const wrapper = ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const { result } = renderHook(
        () => useServiceLogs('wiki', true, 100, null, 'test-token'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockLogs);
    });

    it('does not fetch when disabled', () => {
      const wrapper = ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const { result } = renderHook(
        () => useServiceLogs('wiki', false, 100, null, 'test-token'),
        { wrapper }
      );

      expect(result.current.isLoading).toBe(false);
      expect(apiClient.get).not.toHaveBeenCalled();
    });
  });
});
