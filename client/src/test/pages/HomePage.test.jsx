import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HomePage } from '../../pages/HomePage';

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

describe('HomePage', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
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

  it('renders welcome heading', () => {
    renderHomePage();
    expect(screen.getByText('Welcome to the Arcadium Wiki')).toBeInTheDocument();
  });

  it('renders description text', () => {
    renderHomePage();
    expect(
      screen.getByText(/This is the frontend UI for the Arcadium Wiki service/i),
    ).toBeInTheDocument();
  });

  it('renders navigation tree in sidebar', () => {
    renderHomePage();
    expect(screen.getByTestId('navigation-tree')).toBeInTheDocument();
  });

  it('renders layout with sidebar', () => {
    renderHomePage();
    expect(screen.getByTestId('layout')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('renders without crashing', () => {
    expect(() => renderHomePage()).not.toThrow();
  });
});
