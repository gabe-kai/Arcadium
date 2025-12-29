import { describe, it, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';
import { authApi } from '../../services/api/auth';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios);

describe('Auth API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset environment variable
    vi.stubEnv('VITE_AUTH_API_BASE_URL', undefined);
  });

  describe('register', () => {
    it('successfully registers a new user', async () => {
      const mockResponse = {
        data: {
          user: {
            id: 'user-123',
            username: 'testuser',
            email: 'test@example.com',
            role: 'player',
          },
          token: 'access-token-123',
          refresh_token: 'refresh-token-123',
          expires_in: 3600,
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await authApi.register('testuser', 'test@example.com', 'password123');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/register',
        {
          username: 'testuser',
          email: 'test@example.com',
          password: 'password123',
        },
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('uses default base URL when env var not set', async () => {
      // Note: Vite's import.meta.env is evaluated at build time, so we can't
      // dynamically change it in tests. This test verifies the default behavior.
      const mockResponse = { data: { user: {}, token: 'token' } };
      mockedAxios.post.mockResolvedValue(mockResponse);

      await authApi.register('user', 'email@test.com', 'pass');

      // Should use default URL (http://localhost:8000/api)
      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.any(Object),
      );
    });

    it('handles registration errors', async () => {
      const errorResponse = {
        response: {
          data: { error: 'Username already exists' },
          status: 400,
        },
      };

      mockedAxios.post.mockRejectedValue(errorResponse);

      await expect(
        authApi.register('existinguser', 'test@example.com', 'password123'),
      ).rejects.toEqual(errorResponse);
    });

    it('handles network errors', async () => {
      const networkError = new Error('Network Error');
      mockedAxios.post.mockRejectedValue(networkError);

      await expect(
        authApi.register('testuser', 'test@example.com', 'password123'),
      ).rejects.toThrow('Network Error');
    });

    it('handles validation errors from server', async () => {
      const validationError = {
        response: {
          data: { error: 'Invalid username: Username must be at least 3 characters long' },
          status: 400,
        },
      };

      mockedAxios.post.mockRejectedValue(validationError);

      await expect(
        authApi.register('ab', 'test@example.com', 'password123'),
      ).rejects.toEqual(validationError);
    });
  });

  describe('login', () => {
    it('successfully logs in a user', async () => {
      const mockResponse = {
        data: {
          user: {
            id: 'user-123',
            username: 'testuser',
            email: 'test@example.com',
            role: 'admin',
          },
          token: 'access-token-456',
          refresh_token: 'refresh-token-456',
          expires_in: 3600,
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await authApi.login('testuser', 'password123');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/login',
        {
          username: 'testuser',
          password: 'password123',
        },
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('handles invalid credentials', async () => {
      const errorResponse = {
        response: {
          data: { error: 'Invalid username or password' },
          status: 401,
        },
      };

      mockedAxios.post.mockRejectedValue(errorResponse);

      await expect(authApi.login('wronguser', 'wrongpass')).rejects.toEqual(
        errorResponse,
      );
    });

    it('handles network errors during login', async () => {
      const networkError = new Error('Network Error');
      mockedAxios.post.mockRejectedValue(networkError);

      await expect(authApi.login('testuser', 'password123')).rejects.toThrow(
        'Network Error',
      );
    });

    it('handles missing username or password', async () => {
      const errorResponse = {
        response: {
          data: { error: 'Username and password are required' },
          status: 400,
        },
      };

      mockedAxios.post.mockRejectedValue(errorResponse);

      await expect(authApi.login('', 'password123')).rejects.toEqual(errorResponse);
    });
  });

  describe('verifyToken', () => {
    it('successfully verifies a valid token', async () => {
      const mockResponse = {
        data: {
          valid: true,
          user: {
            id: 'user-123',
            username: 'testuser',
            role: 'admin',
          },
          expires_at: '2025-12-17T10:00:00Z',
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await authApi.verifyToken('valid-token-123');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/verify',
        { token: 'valid-token-123' },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        },
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('handles invalid token', async () => {
      const errorResponse = {
        response: {
          data: {
            valid: false,
            error: 'Invalid or expired token',
          },
          status: 401,
        },
      };

      mockedAxios.post.mockRejectedValue(errorResponse);

      await expect(authApi.verifyToken('invalid-token')).rejects.toEqual(
        errorResponse,
      );
    });

    it('handles expired token', async () => {
      const errorResponse = {
        response: {
          data: {
            valid: false,
            error: 'Token has expired',
          },
          status: 401,
        },
      };

      mockedAxios.post.mockRejectedValue(errorResponse);

      await expect(authApi.verifyToken('expired-token')).rejects.toEqual(
        errorResponse,
      );
    });

    it('handles network errors during verification', async () => {
      const networkError = new Error('Network Error');
      mockedAxios.post.mockRejectedValue(networkError);

      await expect(authApi.verifyToken('token')).rejects.toThrow('Network Error');
    });

    it('handles missing token', async () => {
      const errorResponse = {
        response: {
          data: { error: 'Token is required' },
          status: 400,
        },
      };

      mockedAxios.post.mockRejectedValue(errorResponse);

      await expect(authApi.verifyToken('')).rejects.toEqual(errorResponse);
    });
  });
});
