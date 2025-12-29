import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar, SidebarPlaceholder } from '../../components/layout/Sidebar';

// Mock NavigationTree
vi.mock('../../components/navigation/NavigationTree', () => ({
  NavigationTree: () => <div data-testid="navigation-tree">Navigation Tree</div>,
}));

describe('Sidebar Components', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  describe('Sidebar', () => {
    it('renders NavigationTree', () => {
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <Sidebar />
          </MemoryRouter>
        </QueryClientProvider>,
      );
      expect(screen.getByTestId('navigation-tree')).toBeInTheDocument();
    });

    it('renders without crashing', () => {
      expect(() => {
        render(
          <QueryClientProvider client={queryClient}>
            <MemoryRouter>
              <Sidebar />
            </MemoryRouter>
          </QueryClientProvider>,
        );
      }).not.toThrow();
    });
  });

  describe('SidebarPlaceholder', () => {
    it('renders placeholder heading', () => {
      render(<SidebarPlaceholder />);
      expect(screen.getByText('Navigation')).toBeInTheDocument();
    });

    it('renders placeholder text', () => {
      render(<SidebarPlaceholder />);
      expect(
        screen.getByText(/Navigation tree will appear here once implemented/i),
      ).toBeInTheDocument();
    });

    it('has correct CSS class', () => {
      const { container } = render(<SidebarPlaceholder />);
      const placeholder = container.querySelector('.arc-sidebar-placeholder');
      expect(placeholder).toBeInTheDocument();
    });

    it('renders without crashing', () => {
      expect(() => render(<SidebarPlaceholder />)).not.toThrow();
    });
  });
});
