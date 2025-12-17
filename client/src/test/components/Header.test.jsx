import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Header } from '../../components/layout/Header';
import { useAuth } from '../../services/auth/AuthContext';

// Mock useAuth
vi.mock('../../services/auth/AuthContext');

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      signOut: vi.fn(),
    });
  });

  const renderHeader = () => {
    return render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>,
    );
  };

  describe('Unauthenticated State', () => {
    it('renders sign in button when not authenticated', () => {
      renderHeader();
      expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
    });

    it('navigates to sign-in page when sign in button is clicked', async () => {
      const user = userEvent.setup();
      renderHeader();

      await user.click(screen.getByRole('button', { name: 'Sign in' }));

      expect(mockNavigate).toHaveBeenCalledWith('/signin');
    });

    it('does not show user menu when not authenticated', () => {
      renderHeader();
      expect(screen.queryByText(/User/)).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Sign out' })).not.toBeInTheDocument();
    });

    it('renders logo link', () => {
      renderHeader();
      const logoLink = screen.getByRole('link', { name: /Arcadium Wiki/i });
      expect(logoLink).toBeInTheDocument();
      expect(logoLink).toHaveAttribute('href', '/');
    });

    it('renders search input', () => {
      renderHeader();
      const searchInput = screen.getByPlaceholderText('Search the wiki...');
      expect(searchInput).toBeInTheDocument();
      expect(searchInput).toHaveAttribute('type', 'search');
    });
  });

  describe('Authenticated State', () => {
    beforeEach(() => {
      useAuth.mockReturnValue({
        isAuthenticated: true,
        user: {
          id: 'user-123',
          username: 'testuser',
          email: 'test@example.com',
          role: 'admin',
        },
        signOut: vi.fn(),
      });
    });

    it('renders user menu when authenticated', () => {
      renderHeader();
      expect(screen.getByText('testuser')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign out' })).toBeInTheDocument();
    });

    it('does not show sign in button when authenticated', () => {
      renderHeader();
      expect(screen.queryByRole('button', { name: 'Sign in' })).not.toBeInTheDocument();
    });

    it('displays username from user object', () => {
      renderHeader();
      expect(screen.getByText('testuser')).toBeInTheDocument();
    });

    it('displays fallback "User" when username is missing', () => {
      useAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: 'user-123', email: 'test@example.com' },
        signOut: vi.fn(),
      });

      renderHeader();
      expect(screen.getByText('User')).toBeInTheDocument();
    });

    it('displays fallback "User" when user object is null', () => {
      useAuth.mockReturnValue({
        isAuthenticated: true,
        user: null,
        signOut: vi.fn(),
      });

      renderHeader();
      expect(screen.getByText('User')).toBeInTheDocument();
    });

    it('calls signOut and navigates to home when sign out is clicked', async () => {
      const user = userEvent.setup();
      const mockSignOut = vi.fn();
      useAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: 'user-123', username: 'testuser' },
        signOut: mockSignOut,
      });

      renderHeader();

      await user.click(screen.getByRole('button', { name: 'Sign out' }));

      expect(mockSignOut).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });

    it('handles sign out with different user roles', async () => {
      const user = userEvent.setup();
      const roles = ['admin', 'player', 'writer', 'viewer'];

      for (const role of roles) {
        const mockSignOut = vi.fn();
        useAuth.mockReturnValue({
          isAuthenticated: true,
          user: { id: 'user-123', username: 'testuser', role },
          signOut: mockSignOut,
        });

        const { unmount } = renderHeader();

        await user.click(screen.getByRole('button', { name: 'Sign out' }));

        expect(mockSignOut).toHaveBeenCalled();
        unmount();
      }
    });
  });

  describe('Edge Cases', () => {
    it('handles rapid authentication state changes', () => {
      const { rerender } = renderHeader();

      // Start unauthenticated
      expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();

      // Switch to authenticated
      useAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: 'user-123', username: 'testuser' },
        signOut: vi.fn(),
      });
      rerender(
        <MemoryRouter>
          <Header />
        </MemoryRouter>,
      );

      expect(screen.getByRole('button', { name: 'Sign out' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Sign in' })).not.toBeInTheDocument();

      // Switch back to unauthenticated
      useAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        signOut: vi.fn(),
      });
      rerender(
        <MemoryRouter>
          <Header />
        </MemoryRouter>,
      );

      expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Sign out' })).not.toBeInTheDocument();
    });

    it('handles user object with only id', () => {
      useAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: 'user-123' },
        signOut: vi.fn(),
      });

      renderHeader();
      expect(screen.getByText('User')).toBeInTheDocument();
    });

    it('handles empty username string', () => {
      useAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: 'user-123', username: '' },
        signOut: vi.fn(),
      });

      renderHeader();
      expect(screen.getByText('User')).toBeInTheDocument();
    });

    it('handles very long usernames', () => {
      const longUsername = 'a'.repeat(100);
      useAuth.mockReturnValue({
        isAuthenticated: true,
        user: { id: 'user-123', username: longUsername },
        signOut: vi.fn(),
      });

      renderHeader();
      expect(screen.getByText(longUsername)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper button types', () => {
      renderHeader();
      const signInButton = screen.getByRole('button', { name: 'Sign in' });
      expect(signInButton).toHaveAttribute('type', 'button');
    });

    it('has accessible search input', () => {
      renderHeader();
      const searchInput = screen.getByPlaceholderText('Search the wiki...');
      expect(searchInput).toHaveAttribute('type', 'search');
    });

    it('has accessible logo link', () => {
      renderHeader();
      const logoLink = screen.getByRole('link', { name: /Arcadium Wiki/i });
      expect(logoLink).toBeInTheDocument();
    });
  });
});
