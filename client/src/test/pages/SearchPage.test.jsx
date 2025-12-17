import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SearchPage } from '../../pages/SearchPage';

// Mock NavigationTree
vi.mock('../../components/navigation/NavigationTree', () => ({
  NavigationTree: () => <div data-testid="navigation-tree">Navigation Tree</div>,
}));

// Mock Layout
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children, sidebar }) => (
    <div data-testid="layout">
      {sidebar && <div data-testid="sidebar">{sidebar}</div>}
      <main>{children}</main>
    </div>
  ),
}));

describe('SearchPage', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  const renderSearchPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <SearchPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  it('renders search heading', () => {
    renderSearchPage();
    expect(screen.getByText('Search')).toBeInTheDocument();
  });

  it('renders placeholder text', () => {
    renderSearchPage();
    expect(
      screen.getByText(/Global search results will appear here/i),
    ).toBeInTheDocument();
  });

  it('renders navigation tree in sidebar', () => {
    renderSearchPage();
    expect(screen.getByTestId('navigation-tree')).toBeInTheDocument();
  });

  it('renders layout with sidebar', () => {
    renderSearchPage();
    expect(screen.getByTestId('layout')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('renders without crashing', () => {
    expect(() => renderSearchPage()).not.toThrow();
  });
});
