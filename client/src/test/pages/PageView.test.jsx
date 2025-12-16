import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PageView } from '../../pages/PageView';
import * as pagesApi from '../../services/api/pages';

// Mock useParams
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(),
  };
});

// Mock the API module
vi.mock('../../services/api/pages', () => ({
  usePage: vi.fn(),
  useBreadcrumb: vi.fn(),
  usePageNavigation: vi.fn(),
}));

// Mock Layout and Sidebar to simplify tests
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children }) => <div data-testid="layout">{children}</div>,
}));

vi.mock('../../components/layout/Sidebar', () => ({
  SidebarPlaceholder: () => <div data-testid="sidebar" />,
}));

// Mock navigation components
vi.mock('../../components/navigation/Breadcrumb', () => ({
  Breadcrumb: ({ breadcrumb }) => breadcrumb ? <nav data-testid="breadcrumb">Breadcrumb</nav> : null,
}));

vi.mock('../../components/navigation/PageNavigation', () => ({
  PageNavigation: ({ navigation }) => navigation ? <nav data-testid="page-navigation">Navigation</nav> : null,
}));

// Mock utility functions
vi.mock('../../utils/syntaxHighlight', () => ({
  highlightCodeBlocks: vi.fn(),
}));

vi.mock('../../utils/linkHandler', () => ({
  processLinks: vi.fn(),
}));

describe('PageView', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();
    // Mock useParams - use vi.mocked to avoid redefinition errors
    vi.mocked(useParams).mockReturnValue({ pageId: 'test-page-id' });
    // Default mock returns for breadcrumb and navigation
    pagesApi.useBreadcrumb.mockReturnValue({ data: null });
    pagesApi.usePageNavigation.mockReturnValue({ data: null });
  });

  const renderPageView = (pageId = 'test-page-id') => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[`/pages/${pageId}`]}>
          <PageView />
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('displays loading state', () => {
    pagesApi.usePage.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.getByText(/Loading page…/i)).toBeInTheDocument();
  });

  it('displays error state when page fails to load', () => {
    pagesApi.usePage.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    renderPageView('test-page-id');
    expect(screen.getByText(/Unable to load page/i)).toBeInTheDocument();
  });

  it('displays error state when page is null', () => {
    pagesApi.usePage.mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.getByText(/Unable to load page/i)).toBeInTheDocument();
  });

  it('displays page content when loaded successfully', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page Title',
      html_content: '<p>Test page content</p>',
      updated_at: '2025-01-15T10:00:00Z',
      word_count: 100,
      content_size_kb: 2.5,
      status: 'published',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    expect(screen.getByText('Test Page Title')).toBeInTheDocument();
    expect(screen.getByText(/Test page content/i)).toBeInTheDocument();
  });

  it('displays page metadata when available', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      updated_at: '2025-01-15T10:00:00Z',
      word_count: 150,
      content_size_kb: 3.2,
      status: 'published',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    // Check for metadata elements
    expect(screen.getByText(/Last updated/i)).toBeInTheDocument();
    expect(screen.getByText(/150 words/i)).toBeInTheDocument();
    expect(screen.getByText(/3.2 KB/i)).toBeInTheDocument();
    expect(screen.getByText(/published/i)).toBeInTheDocument();
  });

  it('handles missing optional metadata gracefully', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      // No updated_at, word_count, content_size_kb, or status
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    // Page should still render
    expect(screen.getByText('Test Page')).toBeInTheDocument();
    expect(screen.getByText(/Content/i)).toBeInTheDocument();
  });

  it('displays "No page selected" when pageId is missing', () => {
    // Mock useParams to return no pageId
    vi.mocked(useParams).mockReturnValue({});

    pagesApi.usePage.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });
    
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <PageView />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText(/No page selected/i)).toBeInTheDocument();
  });

  it('displays breadcrumb when available', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
    };

    const mockBreadcrumb = [
      { id: 'page-1', title: 'Home', slug: 'home' },
      { id: 'test-page-id', title: 'Test Page', slug: 'test' },
    ];

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    pagesApi.useBreadcrumb.mockReturnValue({
      data: mockBreadcrumb,
    });

    renderPageView('test-page-id');
    expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
  });

  it('displays page navigation when available', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
    };

    const mockNavigation = {
      previous: { id: 'page-1', title: 'Previous', slug: 'prev' },
      next: { id: 'page-3', title: 'Next', slug: 'next' },
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    pagesApi.usePageNavigation.mockReturnValue({
      data: mockNavigation,
    });

    renderPageView('test-page-id');
    expect(screen.getByTestId('page-navigation')).toBeInTheDocument();
  });

  it('does not display breadcrumb when null', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    pagesApi.useBreadcrumb.mockReturnValue({
      data: null,
    });

    renderPageView('test-page-id');
    expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
  });

  it('does not display navigation when null', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    pagesApi.usePageNavigation.mockReturnValue({
      data: null,
    });

    renderPageView('test-page-id');
    expect(screen.queryByTestId('page-navigation')).not.toBeInTheDocument();
  });
});
