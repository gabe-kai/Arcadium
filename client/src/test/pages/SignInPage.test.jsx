import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SignInPage } from '../../pages/SignInPage';
import { useAuth } from '../../services/auth/AuthContext';
import { authApi } from '../../services/api/auth';

// Mock dependencies
vi.mock('../../services/auth/AuthContext');
vi.mock('../../services/api/auth');
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children }) => <div>{children}</div>,
}));

const mockNavigate = vi.fn();
const mockSignIn = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('SignInPage', () => {
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
    useAuth.mockReturnValue({
      signIn: mockSignIn,
      signOut: vi.fn(),
      isAuthenticated: false,
      user: null,
      token: null,
    });
  });

  const renderSignInPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <SignInPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  const getLoginSubmitButton = () => {
    const buttons = screen.getAllByRole('button', { name: /Sign In/i });
    return buttons.find((btn) => btn.type === 'submit') || buttons[0];
  };

  describe('Login Mode', () => {
    it('renders login form by default', () => {
      renderSignInPage();
      // Use getByRole for heading to avoid multiple matches with button text
      expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
      expect(screen.getByLabelText('Username')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
      expect(screen.queryByLabelText('Email')).not.toBeInTheDocument();
    });

    it('displays correct subtitle for login', () => {
      renderSignInPage();
      expect(
        screen.getByText('Sign in to your Arcadium account'),
      ).toBeInTheDocument();
    });

    it('shows switch to register link', () => {
      renderSignInPage();
      expect(screen.getByText(/Don't have an account?/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign up' })).toBeInTheDocument();
    });

    it('successfully logs in with valid credentials', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        token: 'access-token-123',
        user: {
          id: 'user-123',
          username: 'testuser',
          email: 'test@example.com',
          role: 'admin',
        },
      };

      authApi.login.mockResolvedValue(mockResponse);

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(authApi.login).toHaveBeenCalledWith('testuser', 'password123');
      });

      await waitFor(() => {
        expect(mockSignIn).toHaveBeenCalledWith(mockResponse.token, mockResponse.user);
      });
    });

    it('displays error message on login failure', async () => {
      const user = userEvent.setup();
      const error = {
        response: {
          data: { error: 'Invalid username or password' },
        },
      };

      authApi.login.mockRejectedValue(error);

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'wronguser');
      await user.type(screen.getByLabelText('Password'), 'wrongpass');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(screen.getByText('Invalid username or password')).toBeInTheDocument();
      });
    });

    it('displays error when username is missing', async () => {
      const user = userEvent.setup();

      renderSignInPage();

      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(screen.getByText('Username and password are required')).toBeInTheDocument();
      });

      expect(authApi.login).not.toHaveBeenCalled();
    });

    it('displays error when password is missing', async () => {
      const user = userEvent.setup();

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(screen.getByText('Username and password are required')).toBeInTheDocument();
      });

      expect(authApi.login).not.toHaveBeenCalled();
    });

    it('shows loading state during login', async () => {
      const user = userEvent.setup();
      let resolveLogin;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });

      authApi.login.mockReturnValue(loginPromise);

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(screen.getByText('Please wait...')).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: 'Please wait...' })).toBeDisabled();

      resolveLogin({
        token: 'token',
        user: { id: '1', username: 'testuser' },
      });
    });

    it('disables form fields during loading', async () => {
      const user = userEvent.setup();
      let resolveLogin;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });

      authApi.login.mockReturnValue(loginPromise);

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(screen.getByLabelText('Username')).toBeDisabled();
        expect(screen.getByLabelText('Password')).toBeDisabled();
      });

      resolveLogin({
        token: 'token',
        user: { id: '1', username: 'testuser' },
      });
    });
  });

  describe('Register Mode', () => {
    it('switches to register mode when clicking sign up link', async () => {
      const user = userEvent.setup();

      renderSignInPage();

      await user.click(screen.getByRole('button', { name: 'Sign up' }));

      // Use getAllByText since "Create Account" may appear in multiple places
      const createAccountElements = screen.getAllByText('Create Account');
      expect(createAccountElements.length).toBeGreaterThan(0);
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(
        screen.getByText('Create a new account to get started'),
      ).toBeInTheDocument();
    });

    it('successfully registers a new user', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        token: 'access-token-456',
        user: {
          id: 'user-456',
          username: 'newuser',
          email: 'new@example.com',
          role: 'player',
          is_first_user: false,
        },
      };

      authApi.register.mockResolvedValue(mockResponse);

      renderSignInPage();

      // Switch to register mode
      await user.click(screen.getByRole('button', { name: 'Sign up' }));

      await user.type(screen.getByLabelText('Username'), 'newuser');
      await user.type(screen.getByLabelText('Email'), 'new@example.com');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(authApi.register).toHaveBeenCalledWith(
          'newuser',
          'new@example.com',
          'password123',
        );
      });

      await waitFor(() => {
        expect(mockSignIn).toHaveBeenCalledWith(mockResponse.token, mockResponse.user);
      });
    });

    it('displays success message after registration', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        token: 'token',
        user: { id: '1', username: 'newuser' },
      };

      authApi.register.mockResolvedValue(mockResponse);

      renderSignInPage();

      await user.click(screen.getByRole('button', { name: 'Sign up' }));
      await user.type(screen.getByLabelText('Username'), 'newuser');
      await user.type(screen.getByLabelText('Email'), 'new@example.com');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(
          screen.getByText('Registration successful! You are now signed in.'),
        ).toBeInTheDocument();
      });
    });

    it('displays error message on registration failure', async () => {
      const user = userEvent.setup();
      const error = {
        response: {
          data: { error: 'Username already exists' },
        },
      };

      authApi.register.mockRejectedValue(error);

      renderSignInPage();

      await user.click(screen.getByRole('button', { name: 'Sign up' }));
      await user.type(screen.getByLabelText('Username'), 'existinguser');
      await user.type(screen.getByLabelText('Email'), 'test@example.com');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('Username already exists')).toBeInTheDocument();
      });
    });

    it('validates all fields are required for registration', async () => {
      const user = userEvent.setup();

      renderSignInPage();

      await user.click(screen.getByRole('button', { name: 'Sign up' }));
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('All fields are required')).toBeInTheDocument();
      });

      expect(authApi.register).not.toHaveBeenCalled();
    });

    it('clears form when switching between modes', async () => {
      const user = userEvent.setup();

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(screen.getByRole('button', { name: 'Sign up' }));

      expect(screen.getByLabelText('Username')).toHaveValue('');
      expect(screen.getByLabelText('Password')).toHaveValue('');
    });

    it('switches back to login mode from register', async () => {
      const user = userEvent.setup();

      renderSignInPage();

      await user.click(screen.getByRole('button', { name: 'Sign up' }));
      // Use getAllByText since "Create Account" may appear in multiple places
      const createAccountElements = screen.getAllByText('Create Account');
      expect(createAccountElements.length).toBeGreaterThan(0);

      // "Sign in" appears in multiple places - get the switch button specifically
      const signInButtons = screen.getAllByRole('button', { name: /Sign in/i });
      // The switch button should be the one that's not the main submit button
      const switchButton = signInButtons.find(btn => btn.type === 'button');
      await user.click(switchButton || signInButtons[0]);
      expect(screen.getByRole('heading', { name: /Sign in/i })).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles network errors gracefully', async () => {
      const user = userEvent.setup();
      const networkError = new Error('Network Error');

      authApi.login.mockRejectedValue(networkError);

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(screen.getByText('Network Error')).toBeInTheDocument();
      });
    });

    it('handles errors without response data', async () => {
      const user = userEvent.setup();
      const error = new Error('An error occurred');

      authApi.login.mockRejectedValue(error);

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(screen.getByText('An error occurred')).toBeInTheDocument();
      });
    });

    it('clears previous errors when submitting again', async () => {
      const user = userEvent.setup();

      authApi.login
        .mockRejectedValueOnce({
          response: { data: { error: 'First error' } },
        })
        .mockResolvedValueOnce({
          token: 'token',
          user: { id: '1', username: 'testuser' },
        });

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'wrongpass');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument();
      });

      await user.clear(screen.getByLabelText('Password'));
      await user.type(screen.getByLabelText('Password'), 'correctpass');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderSignInPage();
      expect(screen.getByLabelText('Username')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
    });

    it('has proper autocomplete attributes', () => {
      renderSignInPage();
      const usernameInput = screen.getByLabelText('Username');
      const passwordInput = screen.getByLabelText('Password');

      expect(usernameInput).toHaveAttribute('autocomplete', 'username');
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password');
    });

    it('has proper autocomplete for register mode', async () => {
      const user = userEvent.setup();
      renderSignInPage();

      await user.click(screen.getByRole('button', { name: 'Sign up' }));

      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');

      expect(emailInput).toHaveAttribute('autocomplete', 'email');
      expect(passwordInput).toHaveAttribute('autocomplete', 'new-password');
    });

    it('has error role for error messages', async () => {
      const user = userEvent.setup();
      authApi.login.mockRejectedValue({
        response: { data: { error: 'Test error' } },
      });

      renderSignInPage();

      await user.type(screen.getByLabelText('Username'), 'testuser');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.click(getLoginSubmitButton());

      await waitFor(() => {
        const errorElement = screen.getByText('Test error');
        expect(errorElement).toHaveAttribute('role', 'alert');
      });
    });
  });
});
