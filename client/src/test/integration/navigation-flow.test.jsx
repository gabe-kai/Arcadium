import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HomePage } from '../../pages/HomePage';
import * as pagesApi from '../../services/api/pages';

// Mock dependencies
vi.mock('../../components/navigation/NavigationTree', () => ({
  NavigationTree: () => <div data-testid="navigation-tree">Navigation Tree</div>,
}));

vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children, sidebar }) => (
    <div data-testid="layout">
      {sidebar && <div data-testid="sidebar">{sidebar}</div>}
      <main>{children}</main>
    </div>
  ),
}));

vi.mock('../../services/api/pages', () => ({
  useNavigationTree: vi.fn(() => ({
    data: [
      {
        id: 'page-1',
        title: 'Page 1',
        slug: 'page-1',
        children: [
          { id: 'page-1-1', title: 'Page 1.1', slug: 'page-1-1', children: [] },
        ],
      },
    ],
    isLoading: false,
    isError: false,
  })),
}));

describe('Navigation Flow Integration', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();
  });

  const renderHomePage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  it('renders navigation tree on home page', () => {
    renderHomePage();
    expect(screen.getByTestId('navigation-tree')).toBeInTheDocument();
  });

  it('displays welcome content', () => {
    renderHomePage();
    expect(screen.getByText('Welcome to the Arcadium Wiki')).toBeInTheDocument();
  });

  // Note: Full navigation interaction tests are covered in NavigationTree.test.jsx
  // This test verifies the integration of navigation tree in the home page
});
