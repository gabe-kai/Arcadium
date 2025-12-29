import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getToken, setToken, clearToken } from '../../services/auth/tokenStorage';

describe('tokenStorage utilities', () => {
  let store = {};
  let localStorageMock;

  beforeEach(() => {
    store = {};
    localStorageMock = {
      getItem: vi.fn((key) => store[key] || null),
      setItem: vi.fn((key, value) => {
        store[key] = value.toString();
      }),
      removeItem: vi.fn((key) => {
        delete store[key];
      }),
    };
    // Mock global localStorage
    global.localStorage = localStorageMock;
    vi.clearAllMocks();
  });

  describe('getToken', () => {
    it('returns null when no token is stored', () => {
      const token = getToken();
      expect(token).toBeNull();
      expect(localStorage.getItem).toHaveBeenCalledWith('arcadium_wiki_token');
    });

    it('returns stored token', () => {
      store['arcadium_wiki_token'] = 'test-token-123';
      const token = getToken();
      expect(token).toBe('test-token-123');
    });

    it('handles localStorage errors gracefully', () => {
      localStorage.getItem.mockImplementation(() => {
        throw new Error('Storage error');
      });
      const token = getToken();
      expect(token).toBeNull();
    });
  });

  describe('setToken', () => {
    it('stores token when provided', () => {
      setToken('new-token-456');
      expect(localStorage.setItem).toHaveBeenCalledWith('arcadium_wiki_token', 'new-token-456');
    });

    it('removes token when null is provided', () => {
      store['arcadium_wiki_token'] = 'existing-token';
      setToken(null);
      expect(localStorage.removeItem).toHaveBeenCalledWith('arcadium_wiki_token');
      expect(store['arcadium_wiki_token']).toBeUndefined();
    });

    it('removes token when empty string is provided', () => {
      store['arcadium_wiki_token'] = 'existing-token';
      setToken('');
      expect(localStorage.removeItem).toHaveBeenCalledWith('arcadium_wiki_token');
      expect(store['arcadium_wiki_token']).toBeUndefined();
    });

    it('handles localStorage errors gracefully', () => {
      localStorage.setItem.mockImplementation(() => {
        throw new Error('Storage error');
      });
      expect(() => setToken('token')).not.toThrow();
    });
  });

  describe('clearToken', () => {
    it('removes token from storage', () => {
      store['arcadium_wiki_token'] = 'existing-token';
      clearToken();
      expect(localStorage.removeItem).toHaveBeenCalledWith('arcadium_wiki_token');
      expect(store['arcadium_wiki_token']).toBeUndefined();
    });

    it('does nothing when no token exists', () => {
      expect(() => clearToken()).not.toThrow();
      expect(localStorage.removeItem).toHaveBeenCalledWith('arcadium_wiki_token');
      expect(store['arcadium_wiki_token']).toBeUndefined();
    });
  });
});
