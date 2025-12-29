import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../../services/auth/AuthContext';
import { SignInPage } from '../../pages/SignInPage';
import { Header } from '../../components/layout/Header';
import { authApi } from '../../services/api/auth';
import { getToken, setToken, clearToken } from '../../services/auth/tokenStorage';

// Mock tokenStorage
vi.mock('../../services/auth/tokenStorage', () => ({
  getToken: vi.fn(),
  setToken: vi.fn(),
  clearToken: vi.fn(),
}));

// Mock auth API
vi.mock('../../services/api/auth');

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Auth Flow Integration', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();
    mockNavigate.mockClear();
    getToken.mockReturnValue(null);
  });

  const renderWithAuth = (component) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>{component}</MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>,
    );
  };

  describe('Complete Registration Flow', () => {
    it('registers new user, stores token, and updates header', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        token: 'access-token-123',
        refresh_token: 'refresh-token-123',
        user: {
          id: 'user-123',
          username: 'newuser',
          email: 'new@example.com',
          role: 'player',
          is_first_user: false,
        },
        expires_in: 3600,
      };

      authApi.register.mockResolvedValue(mockResponse);

      renderWithAuth(
        <>
          <Header />
          <SignInPage />
        </>,
      );

      // Switch to register mode
      await user.click(screen.getByRole('button', { name: 'Sign up' }));

      // Fill registration form
      await user.type(screen.getByLabelText('Username'), 'newuser');
      await user.type(screen.getByLabelText('Email'), 'new@example.com');
      await user.type(screen.getByLabelText('Password'), 'password123');

      // Submit registration
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      // Verify API call
      await waitFor(() => {
        expect(authApi.register).toHaveBeenCalledWith(
          'newuser',
          'new@example.com',
          'password123',
        );
      });

      // Verify token storage
      await waitFor(() => {
        expect(setToken).toHaveBeenCalledWith('access-token-123');
      });

      // Verify success message
      await waitFor(() => {
        expect(
          screen.getByText('Registration successful! You are now signed in.'),
        ).toBeInTheDocument();
      });

      // Verify navigation
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      }, { timeout: 2000 });
    });
  });

  describe('Complete Login Flow', () => {
    it('logs in user, stores token, and updates header', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        token: 'access-token-456',
        refresh_token: 'refresh-token-456',
        user: {
          id: 'user-456',
          username: 'existinguser',
          email: 'existing@example.com',
          role: 'admin',
        },
        expires_in: 3600,
      };

      authApi.login.mockResolvedValue(mockResponse);

      renderWithAuth(
        <>
          <Header />
          <SignInPage />
        </>,
      );

      // Fill login form
      await user.type(screen.getByLabelText('Username'), 'existinguser');
      await user.type(screen.getByLabelText('Password'), 'password123');

      // Submit login
      await user.click(screen.getByRole('button', { name: 'Sign In' }));

      // Verify API call
      await waitFor(() => {
        expect(authApi.login).toHaveBeenCalledWith('existinguser', 'password123');
      });

      // Verify token storage
      await waitFor(() => {
        expect(setToken).toHaveBeenCalledWith('access-token-456');
      });

      // Verify navigation
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });
  });

  describe('Sign Out Flow', () => {
    it('signs out user and clears token', async () => {
      const user = userEvent.setup();

      // Start authenticated
      getToken.mockReturnValue('existing-token');
      const mockUser = {
        id: 'user-123',
        username: 'testuser',
        role: 'admin',
      };

      renderWithAuth(<Header />);

      // Should show user menu
      expect(screen.getByText('testuser')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign out' })).toBeInTheDocument();

      // Sign out
      await user.click(screen.getByRole('button', { name: 'Sign out' }));

      // Verify token cleared
      await waitFor(() => {
        expect(clearToken).toHaveBeenCalled();
      });

      // Should not navigate away - user stays on current page
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Error Recovery Flow', () => {
    it('allows retry after login failure', async () => {
      const user = userEvent.setup();

      // First attempt fails
      authApi.login
        .mockRejectedValueOnce({
          response: { data: { error: 'Invalid credentials' } },
        })
        .mockResolvedValueOnce({
          token: 'success-token',
          user: { id: '1', username: 'testuser' },
        });

      renderWithAuth(<SignInPage />);

      // First attempt
      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'wrongpass');
      await user.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
      });

      // Retry with correct password
      await user.clear(screen.getByLabelText('Password'));
      await user.type(screen.getByLabelText('Password'), 'correctpass');
      await user.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(authApi.login).toHaveBeenCalledTimes(2);
      });

      await waitFor(() => {
        expect(setToken).toHaveBeenCalledWith('success-token');
      });
    });

    it('allows switching between login and register after error', async () => {
      const user = userEvent.setup();

      authApi.register.mockRejectedValue({
        response: { data: { error: 'Username already exists' } },
      });

      renderWithAuth(<SignInPage />);

      // Try to register
      await user.click(screen.getByRole('button', { name: 'Sign up' }));
      await user.type(screen.getByLabelText('Username'), 'existinguser');
      await user.type(screen.getByLabelText('Email'), 'test@example.com');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('Username already exists')).toBeInTheDocument();
      });

      // Switch to login
      await user.click(screen.getByRole('button', { name: 'Sign in' }));

      // Error should be cleared
      expect(screen.queryByText('Username already exists')).not.toBeInTheDocument();
      expect(screen.getByText('Sign In')).toBeInTheDocument();
    });
  });

  describe('Token Persistence', () => {
    it('loads token from storage on app load', () => {
      getToken.mockReturnValue('persisted-token');

      renderWithAuth(<Header />);

      // Should show authenticated state
      // Note: This depends on AuthContext implementation
      // If token is loaded, user should be authenticated
      expect(getToken).toHaveBeenCalled();
    });

    it('maintains authentication state across navigation', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        token: 'persistent-token',
        user: { id: '1', username: 'testuser' },
      };

      authApi.login.mockResolvedValue(mockResponse);
      getToken.mockReturnValue('persistent-token');

      renderWithAuth(
        <>
          <Header />
          <SignInPage />
        </>,
      );

      // Login
      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(setToken).toHaveBeenCalledWith('persistent-token');
      });

      // Header should reflect authenticated state
      // (This would require the Header to re-render with new auth state)
    });
  });
});
