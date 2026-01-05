import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header } from '../../components/layout/Header';
import { Footer } from '../../components/layout/Footer';
import { Layout } from '../../components/layout/Layout';
import React from 'react';

// Mock AuthContext to avoid provider requirements in layout tests
vi.mock('../../services/auth/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    isAuthenticated: false,
    user: null,
    signOut: vi.fn(),
    signIn: vi.fn(),
  })),
  AuthProvider: ({ children }) => <>{children}</>,
}));

// Mock navigation tree hook to avoid API calls
vi.mock('../../services/api/pages', () => ({
  useNavigationTree: vi.fn(() => ({ data: [], isLoading: false, isError: false })),
}));

// Mock ServiceStatusIndicator to avoid QueryClient requirement
vi.mock('../../components/common/ServiceStatusIndicator', () => ({
  ServiceStatusIndicator: () => <div data-testid="service-status">Service Status</div>,
}));

// Mock ThemeToggle to avoid matchMedia requirement
vi.mock('../../components/common/ThemeToggle', () => ({
  ThemeToggle: () => <button data-testid="theme-toggle">Theme</button>,
}));

// Mock window.matchMedia for theme detection
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('Layout Components', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  describe('Header', () => {
    it('renders logo and search', () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <Header />
          </MemoryRouter>
        </QueryClientProvider>
      );
      expect(screen.getByText(/Arcadium Wiki/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Search the wiki/i)).toBeInTheDocument();
    });
  });

  describe('Footer', () => {
    it('renders footer text', () => {
      render(<Footer />);
      expect(screen.getByText(/Arcadium Wiki/i)).toBeInTheDocument();
    });
  });

  describe('Layout', () => {
    const renderWithProviders = (component) => {
      return render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            {component}
          </MemoryRouter>
        </QueryClientProvider>
      );
    };

    it('renders children', () => {
      renderWithProviders(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );
      expect(screen.getByText(/Test Content/i)).toBeInTheDocument();
    });

    it('renders sidebar when provided', () => {
      renderWithProviders(
        <Layout sidebar={<div>Sidebar Content</div>}>
          <div>Main Content</div>
        </Layout>
      );
      expect(screen.getByText(/Sidebar Content/i)).toBeInTheDocument();
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('renders right sidebar when provided', () => {
      renderWithProviders(
        <Layout rightSidebar={<div>Right Sidebar</div>}>
          <div>Main Content</div>
        </Layout>
      );
      expect(screen.getByText(/Right Sidebar/i)).toBeInTheDocument();
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('renders both sidebars when provided', () => {
      renderWithProviders(
        <Layout
          sidebar={<div>Left Sidebar</div>}
          rightSidebar={<div>Right Sidebar</div>}
        >
          <div>Main Content</div>
        </Layout>
      );
      expect(screen.getByText(/Left Sidebar/i)).toBeInTheDocument();
      expect(screen.getByText(/Right Sidebar/i)).toBeInTheDocument();
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('applies correct CSS class when right sidebar is present', () => {
      const { container } = renderWithProviders(
        <Layout rightSidebar={<div>Right Sidebar</div>}>
          <div>Content</div>
        </Layout>
      );

      const main = container.querySelector('.arc-main');
      expect(main).toHaveClass('arc-main-with-right-sidebar');
    });

    it('does not apply right sidebar class when right sidebar is absent', () => {
      const { container } = renderWithProviders(
        <Layout>
          <div>Content</div>
        </Layout>
      );

      const main = container.querySelector('.arc-main');
      expect(main).not.toHaveClass('arc-main-with-right-sidebar');
    });

    it('handles null sidebar gracefully', () => {
      renderWithProviders(
        <Layout sidebar={null}>
          <div>Main Content</div>
        </Layout>
      );
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('handles null right sidebar gracefully', () => {
      renderWithProviders(
        <Layout rightSidebar={null}>
          <div>Main Content</div>
        </Layout>
      );
      expect(screen.getByText(/Main Content/i)).toBeInTheDocument();
    });

    it('renders Header and Footer', () => {
      renderWithProviders(
        <Layout>
          <div>Content</div>
        </Layout>
      );

      const logos = screen.getAllByText(/Arcadium Wiki/i);
      expect(logos.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Design', () => {
    const renderWithProviders = (component) => {
      return render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            {component}
          </MemoryRouter>
        </QueryClientProvider>
      );
    };

    beforeEach(() => {
      // Reset window size before each test
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 768,
      });
    });

    it('shows mobile menu toggle button on mobile viewport', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      renderWithProviders(
        <Layout sidebar={<div>Sidebar</div>}>
          <div>Content</div>
        </Layout>
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');
      expect(menuToggle).toBeInTheDocument();
    });

    it('toggles left sidebar when menu button is clicked on mobile', async () => {
      const user = userEvent.setup();
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      const { container } = renderWithProviders(
        <Layout sidebar={<div>Sidebar Content</div>}>
          <div>Content</div>
        </Layout>
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');
      const sidebar = container.querySelector('.arc-sidebar.arc-sidebar-mobile');

      // Sidebar should be hidden initially
      expect(sidebar).not.toHaveClass('active');

      // Click to open
      await user.click(menuToggle);
      expect(sidebar).toHaveClass('active');

      // Click to close
      await user.click(menuToggle);
      expect(sidebar).not.toHaveClass('active');
    });

    it('shows right sidebar toggle button on mobile when right sidebar exists', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      renderWithProviders(
        <Layout rightSidebar={<div>Right Sidebar</div>}>
          <div>Content</div>
        </Layout>
      );

      const rightToggle = screen.getByLabelText('Toggle table of contents');
      expect(rightToggle).toBeInTheDocument();
    });

    it('toggles right sidebar when toggle button is clicked on mobile', async () => {
      const user = userEvent.setup();
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      const { container } = renderWithProviders(
        <Layout rightSidebar={<div>Right Sidebar</div>}>
          <div>Content</div>
        </Layout>
      );

      const rightToggle = screen.getByLabelText('Toggle table of contents');
      const rightSidebar = container.querySelector('.arc-sidebar-right.arc-sidebar-mobile');

      // Sidebar should be hidden initially
      expect(rightSidebar).not.toHaveClass('active');

      // Click to open
      await user.click(rightToggle);
      expect(rightSidebar).toHaveClass('active');

      // Click to close
      await user.click(rightToggle);
      expect(rightSidebar).not.toHaveClass('active');
    });

    it('closes sidebars when overlay is clicked on mobile', async () => {
      const user = userEvent.setup();
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      const { container } = renderWithProviders(
        <Layout sidebar={<div>Sidebar</div>}>
          <div>Content</div>
        </Layout>
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');
      const sidebar = container.querySelector('.arc-sidebar.arc-sidebar-mobile');
      const overlay = container.querySelector('.arc-sidebar-overlay');

      // Open sidebar
      await user.click(menuToggle);
      expect(sidebar).toHaveClass('active');
      expect(overlay).toHaveClass('active');

      // Click overlay to close
      await user.click(overlay);
      expect(sidebar).not.toHaveClass('active');
    });

    it('closes sidebars when Escape key is pressed on mobile', async () => {
      const user = userEvent.setup();
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      const { container } = renderWithProviders(
        <Layout sidebar={<div>Sidebar</div>}>
          <div>Content</div>
        </Layout>
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');
      const sidebar = container.querySelector('.arc-sidebar.arc-sidebar-mobile');

      // Open sidebar
      await user.click(menuToggle);
      expect(sidebar).toHaveClass('active');

      // Press Escape
      await user.keyboard('{Escape}');
      expect(sidebar).not.toHaveClass('active');
    });

    it('prevents body scroll when mobile sidebar is open', async () => {
      const user = userEvent.setup();
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      renderWithProviders(
        <Layout sidebar={<div>Sidebar</div>}>
          <div>Content</div>
        </Layout>
      );

      const menuToggle = screen.getByLabelText('Toggle navigation menu');

      // Open sidebar
      await user.click(menuToggle);
      expect(document.body.style.overflow).toBe('hidden');

      // Close sidebar
      await user.click(menuToggle);
      expect(document.body.style.overflow).toBe('');
    });

    it('hides sidebars from main layout on mobile (uses drawer instead)', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      const { container } = renderWithProviders(
        <Layout sidebar={<div>Sidebar</div>} rightSidebar={<div>Right</div>}>
          <div>Content</div>
        </Layout>
      );

      // Regular sidebars should not be visible in main layout
      const regularSidebars = container.querySelectorAll('.arc-sidebar:not(.arc-sidebar-mobile)');
      regularSidebars.forEach((sidebar) => {
        expect(sidebar).not.toBeVisible();
      });
    });

    it('updates mobile state when window is resized', async () => {
      const { rerender } = renderWithProviders(
        <Layout sidebar={<div>Sidebar</div>}>
          <div>Content</div>
        </Layout>
      );

      // Start desktop
      expect(screen.queryByLabelText('Toggle navigation menu')).not.toBeInTheDocument();

      // Resize to mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });
      window.dispatchEvent(new Event('resize'));

      // Re-render to trigger useEffect
      rerender(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <Layout sidebar={<div>Sidebar</div>}>
              <div>Content</div>
            </Layout>
          </MemoryRouter>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument();
      });
    });
  });
});
