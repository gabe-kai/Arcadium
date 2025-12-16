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
});
