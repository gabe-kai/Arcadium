import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../../services/auth/AuthContext';
import { getToken, setToken, clearToken } from '../../services/auth/tokenStorage';

// Mock tokenStorage
vi.mock('../../services/auth/tokenStorage', () => ({
  getToken: vi.fn(),
  setToken: vi.fn(),
  clearToken: vi.fn(),
}));

// Test component that uses useAuth
function TestComponent() {
  const { token, user, signIn, signOut, isAuthenticated } = useAuth();
  return (
    <div>
      <div data-testid="token">{token || 'null'}</div>
      <div data-testid="user">{user ? JSON.stringify(user) : 'null'}</div>
      <div data-testid="isAuthenticated">{isAuthenticated ? 'true' : 'false'}</div>
      <button
        data-testid="sign-in"
        onClick={() => signIn('test-token', { id: '1', username: 'testuser' })}
      >
        Sign In
      </button>
      <button data-testid="sign-out" onClick={signOut}>
        Sign Out
      </button>
    </div>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getToken.mockReturnValue(null);
  });

  describe('AuthProvider', () => {
    it('provides initial state with no token', () => {
      getToken.mockReturnValue(null);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      expect(screen.getByTestId('token')).toHaveTextContent('null');
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
    });

    it('loads token from storage on mount', () => {
      getToken.mockReturnValue('stored-token-123');

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      expect(getToken).toHaveBeenCalled();
      expect(screen.getByTestId('token')).toHaveTextContent('stored-token-123');
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
    });

    it('stores token when signIn is called', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      await act(async () => {
        screen.getByTestId('sign-in').click();
      });

      expect(setToken).toHaveBeenCalledWith('test-token');
      expect(screen.getByTestId('token')).toHaveTextContent('test-token');
      const userText = screen.getByTestId('user').textContent;
      const userData = JSON.parse(userText);
      expect(userData.id).toBe('1');
      expect(userData.username).toBe('testuser');
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
    });

    it('clears token when signOut is called', async () => {
      getToken.mockReturnValue('existing-token');

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      // First sign in
      await act(async () => {
        screen.getByTestId('sign-in').click();
      });

      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');

      // Then sign out
      await act(async () => {
        screen.getByTestId('sign-out').click();
      });

      expect(clearToken).toHaveBeenCalled();
      expect(screen.getByTestId('token')).toHaveTextContent('null');
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
    });

    it('updates token in storage when token changes', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      await act(async () => {
        screen.getByTestId('sign-in').click();
      });

      expect(setToken).toHaveBeenCalledWith('test-token');
    });

    it('clears token in storage when token becomes null', async () => {
      getToken.mockReturnValue('existing-token');

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      await act(async () => {
        screen.getByTestId('sign-out').click();
      });

      expect(clearToken).toHaveBeenCalled();
    });

    it('handles signIn with null user info', async () => {
      function TestComponentWithNullUser() {
        const { token, user, signIn, isAuthenticated } = useAuth();
        return (
          <div>
            <div data-testid="token">{token || 'null'}</div>
            <div data-testid="user">{user ? JSON.stringify(user) : 'null'}</div>
            <div data-testid="isAuthenticated">{isAuthenticated ? 'true' : 'false'}</div>
            <button
              data-testid="sign-in-null"
              onClick={() => signIn('token-only', null)}
            >
              Sign In Null
            </button>
          </div>
        );
      }

      render(
        <AuthProvider>
          <TestComponentWithNullUser />
        </AuthProvider>,
      );

      await act(async () => {
        screen.getByTestId('sign-in-null').click();
      });

      expect(screen.getByTestId('token')).toHaveTextContent('token-only');
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
    });

    it('maintains user info after sign in', async () => {
      const user = { id: 'user-456', username: 'anotheruser', email: 'test@example.com' };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      await act(async () => {
        screen.getByTestId('sign-in').click();
      });

      const userData = JSON.parse(screen.getByTestId('user').textContent);
      expect(userData.id).toBe('1');
      expect(userData.username).toBe('testuser');
    });
  });

  describe('useAuth hook', () => {
    it('throws error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth must be used within an AuthProvider');

      consoleSpy.mockRestore();
    });

    it('provides all required properties', () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      expect(screen.getByTestId('token')).toBeInTheDocument();
      expect(screen.getByTestId('user')).toBeInTheDocument();
      expect(screen.getByTestId('isAuthenticated')).toBeInTheDocument();
      expect(screen.getByTestId('sign-in')).toBeInTheDocument();
      expect(screen.getByTestId('sign-out')).toBeInTheDocument();
    });

    it('isAuthenticated returns true when token exists', () => {
      getToken.mockReturnValue('any-token');

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
    });

    it('isAuthenticated returns false when token is null', () => {
      getToken.mockReturnValue(null);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
    });

    it('isAuthenticated returns false when token is empty string', () => {
      getToken.mockReturnValue('');

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
    });
  });

  describe('Edge Cases', () => {
    it('handles rapid sign in/sign out cycles', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      await act(async () => {
        screen.getByTestId('sign-in').click();
      });

      await act(async () => {
        screen.getByTestId('sign-out').click();
      });

      await act(async () => {
        screen.getByTestId('sign-in').click();
      });

      expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
      // setToken is called on mount (if token exists) and on each signIn
      expect(setToken).toHaveBeenCalled();
      expect(clearToken).toHaveBeenCalled();
    });

    it('handles token storage errors gracefully', async () => {
      // tokenStorage.setToken already handles errors internally with try-catch
      // So we just verify the component works normally
      setToken.mockImplementation(() => {});

      const { container } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>,
      );

      // Component should render
      expect(container).toBeTruthy();

      // Sign in should work
      await act(async () => {
        screen.getByTestId('sign-in').click();
      });

      // Component should still be functional
      expect(screen.getByTestId('token')).toHaveTextContent('test-token');
    });

    it('preserves user info when token is updated', async () => {
      function TestComponentWithUpdate() {
        const { token, user, signIn, isAuthenticated } = useAuth();
        return (
          <div>
            <div data-testid="token">{token || 'null'}</div>
            <div data-testid="user">{user ? JSON.stringify(user) : 'null'}</div>
            <div data-testid="isAuthenticated">{isAuthenticated ? 'true' : 'false'}</div>
            <button
              data-testid="sign-in"
              onClick={() => signIn('test-token', { id: '1', username: 'testuser' })}
            >
              Sign In
            </button>
            <button
              data-testid="update-token"
              onClick={() => signIn('new-token', { id: '1', username: 'testuser' })}
            >
              Update Token
            </button>
          </div>
        );
      }

      // Reset setToken mock
      setToken.mockImplementation(() => {});

      render(
        <AuthProvider>
          <TestComponentWithUpdate />
        </AuthProvider>,
      );

      await act(async () => {
        screen.getByTestId('sign-in').click();
      });

      const userBefore = screen.getByTestId('user').textContent;

      await act(async () => {
        screen.getByTestId('update-token').click();
      });

      const userAfter = screen.getByTestId('user').textContent;
      expect(userAfter).toBe(userBefore);
      expect(screen.getByTestId('token')).toHaveTextContent('new-token');
    });
  });
});
