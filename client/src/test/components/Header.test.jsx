import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Header } from '../../components/layout/Header';
import { useAuth } from '../../services/auth/AuthContext';

// Mock useAuth
vi.mock('../../services/auth/AuthContext');

// Mock useNavigate and useLocation
const mockNavigate = vi.fn();
let mockLocation = { pathname: '/', search: '' };

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
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
      const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);
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

    it('calls signOut and stays on current page when sign out is clicked', async () => {
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
      // Should not navigate away - user stays on current page
      expect(mockNavigate).not.toHaveBeenCalled();
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

  describe('Search Functionality', () => {
    beforeEach(() => {
      // Clear localStorage before each test
      localStorage.clear();
      // Reset location mock
      mockLocation.pathname = '/';
      mockLocation.search = '';
      vi.clearAllMocks();
    });

    it('submits search query and navigates to search page', async () => {
      const user = userEvent.setup();
      renderHeader();
      const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

      await user.type(searchInput, 'test query');
      await user.keyboard('{Enter}');

      expect(mockNavigate).toHaveBeenCalledWith('/search?q=test%20query');
    });

    it('shows clear button when search input has value', async () => {
      const user = userEvent.setup();
      renderHeader();
      const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

      await user.type(searchInput, 'test');
      const clearButton = screen.getByRole('button', { name: 'Clear search' });
      expect(clearButton).toBeInTheDocument();
    });

    it('clears search input when clear button is clicked', async () => {
      const user = userEvent.setup();
      renderHeader();
      const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

      await user.type(searchInput, 'test');
      const clearButton = screen.getByRole('button', { name: 'Clear search' });
      await user.click(clearButton);

      expect(searchInput).toHaveValue('');
      expect(screen.queryByRole('button', { name: 'Clear search' })).not.toBeInTheDocument();
    });

    it('focuses search input when Ctrl+K is pressed', async () => {
      const user = userEvent.setup();
      renderHeader();
      const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

      await user.keyboard('{Control>}k{/Control}');

      expect(searchInput).toHaveFocus();
    });

    it('focuses search input when Cmd+K is pressed (Mac)', async () => {
      const user = userEvent.setup();
      renderHeader();
      const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

      await user.keyboard('{Meta>}k{/Meta}');

      expect(searchInput).toHaveFocus();
    });

    it('does not submit empty search query', async () => {
      const user = userEvent.setup();
      renderHeader();
      const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

      await user.type(searchInput, '   ');
      await user.keyboard('{Enter}');

      expect(mockNavigate).not.toHaveBeenCalled();
    });

    describe('Recent Searches', () => {
      it('shows recent searches dropdown when input is focused and there are recent searches', async () => {
        localStorage.setItem('arcadium_recent_searches', JSON.stringify(['test1', 'test2']));
        const user = userEvent.setup();
        renderHeader();

        const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);
        await user.click(searchInput);

        await waitFor(() => {
          expect(screen.getByText('Recent searches')).toBeInTheDocument();
        });
        expect(screen.getByText('test1')).toBeInTheDocument();
        expect(screen.getByText('test2')).toBeInTheDocument();
      });

      it('does not show recent searches dropdown when there are no recent searches', async () => {
        const user = userEvent.setup();
        renderHeader();
        const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

        await user.click(searchInput);

        expect(screen.queryByText('Recent searches')).not.toBeInTheDocument();
      });

      it('saves search query to recent searches on submit', async () => {
        const user = userEvent.setup();
        renderHeader();
        const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

        await user.type(searchInput, 'new search');
        await user.keyboard('{Enter}');

        const recentSearches = JSON.parse(localStorage.getItem('arcadium_recent_searches') || '[]');
        expect(recentSearches).toContain('new search');
      });

      it('moves existing search to front when searched again', async () => {
        localStorage.setItem('arcadium_recent_searches', JSON.stringify(['old1', 'old2', 'old3']));
        const user = userEvent.setup();
        renderHeader();

        const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);
        await user.type(searchInput, 'old2');
        await user.keyboard('{Enter}');

        await waitFor(() => {
          const recentSearches = JSON.parse(localStorage.getItem('arcadium_recent_searches') || '[]');
          expect(recentSearches[0]).toBe('old2');
          expect(recentSearches.length).toBe(3);
        });
      });

      it('limits recent searches to 10 items', async () => {
        const manySearches = Array.from({ length: 12 }, (_, i) => `search${i}`);
        localStorage.setItem('arcadium_recent_searches', JSON.stringify(manySearches));
        const user = userEvent.setup();
        renderHeader();

        const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);
        await user.type(searchInput, 'new search');
        await user.keyboard('{Enter}');

        await waitFor(() => {
          const recentSearches = JSON.parse(localStorage.getItem('arcadium_recent_searches') || '[]');
          expect(recentSearches.length).toBe(10);
          expect(recentSearches[0]).toBe('new search');
        });
      });

      it('navigates to search page when recent search is clicked', async () => {
        localStorage.setItem('arcadium_recent_searches', JSON.stringify(['test query']));
        const user = userEvent.setup();
        renderHeader();

        const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);
        await user.click(searchInput);

        const recentSearchButton = await waitFor(() => screen.getByText('test query'));
        await user.click(recentSearchButton);

        expect(mockNavigate).toHaveBeenCalledWith('/search?q=test%20query');
      });

      it('handles localStorage errors gracefully', async () => {
        // Mock localStorage to throw error
        const originalGetItem = Storage.prototype.getItem;
        Storage.prototype.getItem = vi.fn(() => {
          throw new Error('localStorage error');
        });

        const user = userEvent.setup();
        renderHeader();
        const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

        // Should not crash
        await user.type(searchInput, 'test');
        await user.keyboard('{Enter}');

        // Restore
        Storage.prototype.getItem = originalGetItem;
        expect(mockNavigate).toHaveBeenCalled();
      });

      it('handles malformed localStorage data gracefully', async () => {
        localStorage.setItem('arcadium_recent_searches', 'invalid json');
        const user = userEvent.setup();
        renderHeader();

        const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);
        await user.click(searchInput);

        // Should not show dropdown with invalid data
        await waitFor(() => {
          expect(screen.queryByText('Recent searches')).not.toBeInTheDocument();
        });
      });

      it('closes recent searches dropdown when clicking outside', async () => {
        localStorage.setItem('arcadium_recent_searches', JSON.stringify(['test1']));
        const user = userEvent.setup();
        renderHeader();

        const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);
        await user.click(searchInput);

        await waitFor(() => {
          expect(screen.getByText('Recent searches')).toBeInTheDocument();
        });

        // Click outside
        await user.click(document.body);

        await waitFor(() => {
          expect(screen.queryByText('Recent searches')).not.toBeInTheDocument();
        });
      });
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
      const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);
      expect(searchInput).toHaveAttribute('type', 'search');
      expect(searchInput).toHaveAttribute('aria-label', 'Search the wiki');
    });

    it('has accessible logo link', () => {
      renderHeader();
      const logoLink = screen.getByRole('link', { name: /Arcadium Wiki/i });
      expect(logoLink).toBeInTheDocument();
    });

    it('has accessible clear button', async () => {
      const user = userEvent.setup();
      renderHeader();
      const searchInput = screen.getByPlaceholderText(/Search the wiki.*Ctrl\+K/i);

      await user.type(searchInput, 'test');
      const clearButton = screen.getByRole('button', { name: 'Clear search' });
      expect(clearButton).toHaveAttribute('type', 'button');
      expect(clearButton).toHaveAttribute('aria-label', 'Clear search');
    });
  });

  describe('Mobile Menu Toggle', () => {
    it('renders mobile menu toggle when onMenuToggle prop is provided', () => {
      const mockToggle = vi.fn();
      render(
        <MemoryRouter>
          <Header onMenuToggle={mockToggle} isLeftSidebarOpen={false} />
        </MemoryRouter>,
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');
      expect(menuToggle).toBeInTheDocument();
      expect(menuToggle).toHaveAttribute('aria-expanded', 'false');
    });

    it('calls onMenuToggle when mobile menu button is clicked', async () => {
      const user = userEvent.setup();
      const mockToggle = vi.fn();
      render(
        <MemoryRouter>
          <Header onMenuToggle={mockToggle} isLeftSidebarOpen={false} />
        </MemoryRouter>,
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');
      await user.click(menuToggle);

      expect(mockToggle).toHaveBeenCalledTimes(1);
    });

    it('shows close icon when sidebar is open', () => {
      render(
        <MemoryRouter>
          <Header onMenuToggle={vi.fn()} isLeftSidebarOpen={true} />
        </MemoryRouter>,
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');
      expect(menuToggle).toHaveAttribute('aria-expanded', 'true');
      expect(menuToggle).toHaveTextContent('✕');
    });

    it('shows hamburger icon when sidebar is closed', () => {
      render(
        <MemoryRouter>
          <Header onMenuToggle={vi.fn()} isLeftSidebarOpen={false} />
        </MemoryRouter>,
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');
      expect(menuToggle).toHaveAttribute('aria-expanded', 'false');
      expect(menuToggle).toHaveTextContent('☰');
    });

    it('does not render mobile menu toggle when onMenuToggle is not provided', () => {
      render(
        <MemoryRouter>
          <Header />
        </MemoryRouter>,
      );

      expect(screen.queryByLabelText('Toggle navigation menu')).not.toBeInTheDocument();
    });

    it('has proper accessibility attributes for mobile menu toggle', () => {
      render(
        <MemoryRouter>
          <Header onMenuToggle={vi.fn()} isLeftSidebarOpen={false} />
        </MemoryRouter>,
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');
      expect(menuToggle).toHaveAttribute('aria-label', 'Toggle navigation menu');
      expect(menuToggle).toHaveAttribute('aria-expanded', 'false');
      expect(menuToggle).toHaveAttribute('title', 'Menu');
    });
  });
});
