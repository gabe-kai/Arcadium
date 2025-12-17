import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PageHistoryPage } from '../../pages/PageHistoryPage';
import * as pagesApi from '../../services/api/pages';

// Mock router hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(),
    useNavigate: vi.fn(() => vi.fn()),
  };
});

// Mock API
vi.mock('../../services/api/pages', () => ({
  usePage: vi.fn(),
  useVersionHistory: vi.fn(),
}));

// Mock Layout and Sidebar
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children }) => <div data-testid="layout">{children}</div>,
}));

vi.mock('../../components/layout/Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar" />,
}));

describe('PageHistoryPage', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();
    vi.mocked(useParams).mockReturnValue({ pageId: 'test-page-id' });

    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'test-page-id',
        title: 'Test Page',
        version: 5,
      },
      isLoading: false,
      isError: false,
    });

    pagesApi.useVersionHistory.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });
  });

  const renderPageHistory = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <PageHistoryPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('renders version history page', () => {
    renderPageHistory();

    expect(screen.getByText('Version History')).toBeInTheDocument();
    expect(screen.getByText('Test Page')).toBeInTheDocument();
  });

  it('displays loading state when loading page', () => {
    pagesApi.usePage.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText('Loading version history...')).toBeInTheDocument();
  });

  it('displays loading state when loading versions', () => {
    pagesApi.useVersionHistory.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText('Loading version history...')).toBeInTheDocument();
  });

  it('displays page not found when page does not exist', () => {
    pagesApi.usePage.mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText('Page Not Found')).toBeInTheDocument();
    expect(screen.getByText(/The requested page does not exist/i)).toBeInTheDocument();
  });

  it('displays current version number', () => {
    renderPageHistory();

    expect(screen.getByText(/Current Version: 5/i)).toBeInTheDocument();
  });

  it('displays empty state when no versions exist', () => {
    pagesApi.useVersionHistory.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText(/No version history available/i)).toBeInTheDocument();
  });

  it('displays version list when versions exist', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
        change_summary: 'Updated content',
        diff_stats: { additions: 10, deletions: 5 },
      },
      {
        version: 4,
        created_at: '2024-01-14T09:20:00Z',
        changed_by: { id: 'user-2', username: 'writer2' },
        change_summary: 'Initial version',
        diff_stats: { additions: 50, deletions: 0 },
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText('Version 5')).toBeInTheDocument();
    expect(screen.getByText('Version 4')).toBeInTheDocument();
    expect(screen.getByText('Updated content')).toBeInTheDocument();
    expect(screen.getByText('Initial version')).toBeInTheDocument();
  });

  it('displays current version badge for current version', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText('Current')).toBeInTheDocument();
  });

  it('displays version metadata correctly', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
        change_summary: 'Updated content',
        diff_stats: { additions: 10, deletions: 5 },
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText(/Changed by: writer1/i)).toBeInTheDocument();
    expect(screen.getByText('Updated content')).toBeInTheDocument();
    expect(screen.getByText(/\+10 additions/i)).toBeInTheDocument();
    expect(screen.getByText(/-5 deletions/i)).toBeInTheDocument();
  });

  it('displays version date correctly', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    // Check that date is displayed (format may vary by locale)
    const dateElement = screen.getByText(/1\/15\/2024|Jan 15, 2024|2024-01-15/i);
    expect(dateElement).toBeInTheDocument();
  });

  it('displays view version link for each version', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    const viewLinks = screen.getAllByText('View Version');
    expect(viewLinks.length).toBeGreaterThan(0);
    expect(viewLinks[0].closest('a')).toHaveAttribute('href', '/pages/test-page-id/versions/5');
  });

  it('displays compare link for non-current versions when multiple versions exist', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
      },
      {
        version: 4,
        created_at: '2024-01-14T09:20:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    // Should show compare link for version 4 (not current, and versions.length > 1)
    const compareLinks = screen.getAllByText('Compare with Current');
    expect(compareLinks.length).toBeGreaterThan(0);
    // Find the link for version 4
    const version4Item = screen.getByText('Version 4').closest('.arc-page-history-item');
    const compareLink = version4Item?.querySelector('a[href*="compare"]');
    expect(compareLink).toBeInTheDocument();
    expect(compareLink).toHaveAttribute(
      'href',
      '/pages/test-page-id/versions/compare?from=4&to=5'
    );
  });

  it('does not display compare link for current version', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.queryByText('Compare with Current')).not.toBeInTheDocument();
  });

  it('handles versions without change summary', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText('Version 5')).toBeInTheDocument();
    // Should not crash when change_summary is missing
  });

  it('handles versions without diff stats', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
        changed_by: { id: 'user-1', username: 'writer1' },
        change_summary: 'Updated',
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText('Version 5')).toBeInTheDocument();
    // Should not crash when diff_stats is missing
  });

  it('handles versions without changed_by info', () => {
    const mockVersions = [
      {
        version: 5,
        created_at: '2024-01-15T10:30:00Z',
      },
    ];

    pagesApi.useVersionHistory.mockReturnValue({
      data: mockVersions,
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText('Version 5')).toBeInTheDocument();
    // Should not crash when changed_by is missing
  });

  it('displays back to page link', () => {
    renderPageHistory();

    const backLink = screen.getByText('← Back to Page');
    expect(backLink.closest('a')).toHaveAttribute('href', '/pages/test-page-id');
  });

  it('handles page with null version', () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'test-page-id',
        title: 'Test Page',
        version: null,
      },
      isLoading: false,
      isError: false,
    });

    renderPageHistory();

    expect(screen.getByText(/Current Version: N\/A/i)).toBeInTheDocument();
  });
});
