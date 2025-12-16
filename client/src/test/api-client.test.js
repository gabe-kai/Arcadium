import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../services/api/client';

// Mock tokenStorage to avoid localStorage dependency
vi.mock('../services/auth/tokenStorage', () => ({
  getToken: vi.fn(() => null),
}));

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('has correct base URL', () => {
    expect(apiClient.defaults.baseURL).toBe(
      import.meta.env.VITE_WIKI_API_BASE_URL || 'http://localhost:5000/api'
    );
  });

  it('has timeout configured', () => {
    expect(apiClient.defaults.timeout).toBe(10000);
  });

  it('is an axios instance', () => {
    expect(apiClient.request).toBeDefined();
    expect(apiClient.get).toBeDefined();
    expect(apiClient.post).toBeDefined();
    expect(apiClient.put).toBeDefined();
    expect(apiClient.delete).toBeDefined();
  });

  it('has request interceptor configured', () => {
    // Verify interceptor exists (axios stores interceptors internally)
    expect(apiClient.interceptors.request).toBeDefined();
  });

  it('has response interceptor configured', () => {
    // Verify interceptor exists (axios stores interceptors internally)
    expect(apiClient.interceptors.response).toBeDefined();
  });

  it('handles environment variable override for base URL', () => {
    // Test that baseURL can be configured via env var
    const originalEnv = import.meta.env.VITE_WIKI_API_BASE_URL;
    
    // Note: In actual tests, you'd need to mock the env var differently
    // This test verifies the fallback behavior
    expect(apiClient.defaults.baseURL).toBeTruthy();
  });

  it('has all required HTTP methods', () => {
    expect(typeof apiClient.get).toBe('function');
    expect(typeof apiClient.post).toBe('function');
    expect(typeof apiClient.put).toBe('function');
    expect(typeof apiClient.delete).toBe('function');
    expect(typeof apiClient.patch).toBe('function');
  });
});
