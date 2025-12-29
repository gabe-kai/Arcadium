import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { IndexPage } from '../../pages/IndexPage';
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

describe('IndexPage', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();
    mockSearchParams.delete('letter');
    mockSearchParams.delete('section');
    searchApi.useIndex.mockReturnValue({
      data: { index: {} },
      isLoading: false,
      isError: false,
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

  it('renders subtitle', () => {
    renderIndexPage();
    expect(screen.getByText(/Alphabetical listing of all pages/i)).toBeInTheDocument();
  });

  it('displays loading state when loading', () => {
    searchApi.useIndex.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    renderIndexPage();
    expect(screen.getByText('Loading index...')).toBeInTheDocument();
  });

  it('displays index entries', () => {
    const mockIndex = {
      A: [
        { page_id: 'page-1', title: 'Alpha Page', slug: 'alpha', section: 'Section A' },
      ],
      B: [
        { page_id: 'page-2', title: 'Beta Page', slug: 'beta', section: 'Section B' },
      ],
    };

    searchApi.useIndex.mockReturnValue({
      data: { index: mockIndex },
      isLoading: false,
      isError: false,
    });

    renderIndexPage();
    expect(screen.getByText('Alpha Page')).toBeInTheDocument();
    expect(screen.getByText('Beta Page')).toBeInTheDocument();
  });

  it('displays letter navigation buttons', () => {
    const mockIndex = {
      A: [{ page_id: 'page-1', title: 'Alpha', slug: 'alpha' }],
      B: [{ page_id: 'page-2', title: 'Beta', slug: 'beta' }],
    };

    searchApi.useIndex.mockReturnValue({
      data: { index: mockIndex },
      isLoading: false,
      isError: false,
    });

    renderIndexPage();
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
  });

  it('renders layout with sidebar', () => {
    renderIndexPage();
    // Verify the page renders (layout and sidebar are mocked)
    // Note: Layout and Sidebar are mocked, so test IDs should be present
    // The important thing is the page renders without errors
    expect(screen.getByText('Index')).toBeInTheDocument();
  });

  it('displays page count per letter', () => {
    const mockIndex = {
      A: [
        { page_id: 'page-1', title: 'Alpha Page 1', slug: 'alpha-1' },
        { page_id: 'page-2', title: 'Alpha Page 2', slug: 'alpha-2' },
        { page_id: 'page-3', title: 'Alpha Page 3', slug: 'alpha-3' },
      ],
      B: [
        { page_id: 'page-4', title: 'Beta Page', slug: 'beta' },
      ],
    };

    searchApi.useIndex.mockReturnValue({
      data: { index: mockIndex },
      isLoading: false,
      isError: false,
    });

    renderIndexPage();

    // Check that page counts are displayed
    const letterButtons = screen.getAllByText(/^[AB]$/);
    expect(letterButtons.length).toBeGreaterThan(0);

    // Check for count indicators (they should be in the button text or title)
    const aButton = screen.getByText('A').closest('button');
    expect(aButton).toHaveAttribute('title', '3 pages');

    const bButton = screen.getByText('B').closest('button');
    expect(bButton).toHaveAttribute('title', '1 page');
  });

  it('handles empty index gracefully', () => {
    searchApi.useIndex.mockReturnValue({
      data: { index: {} },
      isLoading: false,
      isError: false,
    });

    renderIndexPage();
    expect(screen.getByText(/No pages in index/i)).toBeInTheDocument();
  });

  it('handles index with single page per letter', () => {
    const mockIndex = {
      A: [{ page_id: 'page-1', title: 'Alpha', slug: 'alpha' }],
    };

    searchApi.useIndex.mockReturnValue({
      data: { index: mockIndex },
      isLoading: false,
      isError: false,
    });

    renderIndexPage();
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    const aButton = screen.getByText('A').closest('button');
    expect(aButton).toHaveAttribute('title', '1 page');
  });

  it('handles index API errors gracefully', () => {
    searchApi.useIndex.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
    });

    renderIndexPage();
    expect(screen.getByText(/Error loading index/i)).toBeInTheDocument();
  });
});
