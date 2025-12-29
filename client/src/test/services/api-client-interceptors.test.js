import { describe, it, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';
import { apiClient } from '../../services/api/client';
import { getToken } from '../../services/auth/tokenStorage';

// Mock tokenStorage
vi.mock('../../services/auth/tokenStorage', () => ({
  getToken: vi.fn(),
}));

describe('API Client Interceptors', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getToken.mockReturnValue(null);
  });

  describe('Request Interceptor', () => {
    it('adds Authorization header when token exists', async () => {
      getToken.mockReturnValue('test-token-123');

      // Mock axios request
      const mockRequest = {
        headers: {},
        url: '/test',
        method: 'get',
      };

      // Get the request interceptor
      const requestInterceptor = apiClient.interceptors.request.handlers[0];
      const result = await requestInterceptor.fulfilled(mockRequest);

      expect(result.headers.Authorization).toBe('Bearer test-token-123');
    });

    it('does not add Authorization header when token is null', async () => {
      getToken.mockReturnValue(null);

      const mockRequest = {
        headers: {},
        url: '/test',
        method: 'get',
      };

      const requestInterceptor = apiClient.interceptors.request.handlers[0];
      const result = await requestInterceptor.fulfilled(mockRequest);

      expect(result.headers.Authorization).toBeUndefined();
    });

    it('does not override existing Authorization header', async () => {
      getToken.mockReturnValue('token-123');

      const mockRequest = {
        headers: {
          Authorization: 'Bearer existing-token',
        },
        url: '/test',
        method: 'get',
      };

      const requestInterceptor = apiClient.interceptors.request.handlers[0];
      const result = await requestInterceptor.fulfilled(mockRequest);

      expect(result.headers.Authorization).toBe('Bearer existing-token');
    });

    it('creates headers object if it does not exist', async () => {
      getToken.mockReturnValue('token-123');

      const mockRequest = {
        url: '/test',
        method: 'get',
      };

      const requestInterceptor = apiClient.interceptors.request.handlers[0];
      const result = await requestInterceptor.fulfilled(mockRequest);

      expect(result.headers).toBeDefined();
      expect(result.headers.Authorization).toBe('Bearer token-123');
    });

    it('handles empty string token', async () => {
      getToken.mockReturnValue('');

      const mockRequest = {
        headers: {},
        url: '/test',
        method: 'get',
      };

      const requestInterceptor = apiClient.interceptors.request.handlers[0];
      const result = await requestInterceptor.fulfilled(mockRequest);

      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  describe('Response Interceptor', () => {
    it('passes through successful responses', async () => {
      const mockResponse = {
        data: { success: true },
        status: 200,
        statusText: 'OK',
      };

      const responseInterceptor = apiClient.interceptors.response.handlers[0];
      const result = await responseInterceptor.fulfilled(mockResponse);

      expect(result).toEqual(mockResponse);
    });

    it('rejects errors and logs them', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const mockError = {
        message: 'Network Error',
        response: {
          status: 500,
          data: { error: 'Internal Server Error' },
        },
      };

      const responseInterceptor = apiClient.interceptors.response.handlers[0];

      await expect(responseInterceptor.rejected(mockError)).rejects.toEqual(mockError);
      expect(consoleSpy).toHaveBeenCalledWith('API error:', mockError);

      consoleSpy.mockRestore();
    });

    it('handles network errors without response', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const mockError = {
        message: 'Network Error',
        request: {},
      };

      const responseInterceptor = apiClient.interceptors.response.handlers[0];

      await expect(responseInterceptor.rejected(mockError)).rejects.toEqual(mockError);
      expect(consoleSpy).toHaveBeenCalledWith('API error:', mockError);

      consoleSpy.mockRestore();
    });

    it('handles timeout errors', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const mockError = {
        code: 'ECONNABORTED',
        message: 'timeout of 10000ms exceeded',
      };

      const responseInterceptor = apiClient.interceptors.response.handlers[0];

      await expect(responseInterceptor.rejected(mockError)).rejects.toEqual(mockError);
      expect(consoleSpy).toHaveBeenCalledWith('API error:', mockError);

      consoleSpy.mockRestore();
    });
  });
});
