import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { IndexPage } from '../../pages/IndexPage';

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

describe('IndexPage', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  const renderIndexPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <IndexPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  it('renders index heading', () => {
    renderIndexPage();
    expect(screen.getByText('Index')).toBeInTheDocument();
  });

  it('renders placeholder text', () => {
    renderIndexPage();
    expect(
      screen.getByText(/An alphabetical index of pages will be implemented here/i),
    ).toBeInTheDocument();
  });

  it('renders navigation tree in sidebar', () => {
    renderIndexPage();
    expect(screen.getByTestId('navigation-tree')).toBeInTheDocument();
  });

  it('renders layout with sidebar', () => {
    renderIndexPage();
    expect(screen.getByTestId('layout')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('renders without crashing', () => {
    expect(() => renderIndexPage()).not.toThrow();
  });
});
