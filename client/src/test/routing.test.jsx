import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App } from '../App';

// Mock BrowserRouter to use MemoryRouter for testing with configurable initial entries
let mockInitialEntries = ['/'];
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    BrowserRouter: ({ children, future }) => {
      const { MemoryRouter } = actual;
      return <MemoryRouter initialEntries={mockInitialEntries} future={future}>{children}</MemoryRouter>;
    },
  };
});

// Mock API hooks to avoid actual API calls
vi.mock('../services/api/pages', () => ({
  usePage: vi.fn(() => ({ data: null, isLoading: false, isError: false })),
  useBreadcrumb: vi.fn(() => ({ data: null })),
  usePageNavigation: vi.fn(() => ({ data: null })),
}));

// Mock utility functions
vi.mock('../utils/syntaxHighlight', () => ({
  highlightCodeBlocks: vi.fn(),
}));

vi.mock('../utils/linkHandler', () => ({
  processLinks: vi.fn(),
}));

describe('Routing', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    // Reset mock initial entries
    mockInitialEntries = ['/'];
  });

  it('renders HomePage at root path', () => {
    mockInitialEntries = ['/'];
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    expect(screen.getByText(/Welcome to the Arcadium Wiki/i)).toBeInTheDocument();
  });

  it('renders PageView for page routes', () => {
    mockInitialEntries = ['/pages/test-page-id'];
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    // PageView shows loading or error state when no page data
    expect(screen.getByText(/Loading page…|Unable to load page|No page selected/i)).toBeInTheDocument();
  });

  it('renders SearchPage for search route', () => {
    mockInitialEntries = ['/search'];
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    expect(screen.getByText(/Search/i)).toBeInTheDocument();
  });

  it('renders EditPage for edit route', () => {
    mockInitialEntries = ['/pages/test-page-id/edit'];
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    // EditPage should render (may show loading or editor)
    expect(screen.getByPlaceholderText(/Page Title/i) || screen.getByText(/Loading/i)).toBeTruthy();
  });

  it('renders EditPage for new page route', () => {
    mockInitialEntries = ['/pages/new/edit'];
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    expect(screen.getByPlaceholderText(/Page Title/i)).toBeInTheDocument();
  });

  it('handles invalid routes gracefully', () => {
    mockInitialEntries = ['/invalid-route'];
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    // Should not crash, may show 404 or default to home
    expect(screen.getByText(/Welcome/i) || screen.getByText(/404/i)).toBeTruthy();
  });
});
