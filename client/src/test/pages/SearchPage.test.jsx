import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SearchPage } from '../../pages/SearchPage';
import * as searchApi from '../../services/api/search';

// Mock useSearchParams
const mockSearchParams = new URLSearchParams();
const mockSetSearchParams = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useSearchParams: () => [mockSearchParams, mockSetSearchParams],
  };
});

// Mock search API
vi.mock('../../services/api/search', () => ({
  useSearch: vi.fn(),
  useIndex: vi.fn(),
}));

// Mock Layout and Sidebar
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children }) => <div data-testid="layout">{children}</div>,
}));

vi.mock('../../components/layout/Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar" />,
}));

describe('SearchPage', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();
    mockSearchParams.delete('q');
    searchApi.useSearch.mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
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
    expect(screen.getByRole('heading', { name: 'Search' })).toBeInTheDocument();
  });

  it('renders search input', () => {
    renderSearchPage();
    expect(screen.getByPlaceholderText(/Search the wiki/i)).toBeInTheDocument();
  });

  it('displays empty state when no query', () => {
    renderSearchPage();
    expect(screen.getByText(/Enter a search query/i)).toBeInTheDocument();
  });

  it('displays loading state when searching', () => {
    mockSearchParams.set('q', 'test');
    searchApi.useSearch.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    renderSearchPage();
    expect(screen.getByText(/Searching/i)).toBeInTheDocument();
  });

  it('displays search results', async () => {
    mockSearchParams.set('q', 'test');
    const mockResults = {
      results: [
        {
          page_id: 'page-1',
          title: 'Test Page',
          section: 'Test Section',
          snippet: 'This is a test snippet',
          relevance_score: 0.85,
        },
      ],
      total: 1,
      query: 'test',
    };

    searchApi.useSearch.mockReturnValue({
      data: mockResults,
      isLoading: false,
      isError: false,
    });

    renderSearchPage();
    
    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });
    expect(screen.getByText('Test Section')).toBeInTheDocument();
  });

  it('displays no results message', () => {
    mockSearchParams.set('q', 'nonexistent');
    const mockResults = {
      results: [],
      total: 0,
      query: 'nonexistent',
    };

    searchApi.useSearch.mockReturnValue({
      data: mockResults,
      isLoading: false,
      isError: false,
    });

    renderSearchPage();
    expect(screen.getByText(/No results found/i)).toBeInTheDocument();
  });

  it('renders layout with sidebar', () => {
    renderSearchPage();
    // Verify the page renders (layout and sidebar are mocked)
    expect(screen.getByTestId('layout')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });
});
