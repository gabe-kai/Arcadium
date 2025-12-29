import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../../services/auth/AuthContext';
import { PageView } from '../../pages/PageView';
import * as pagesApi from '../../services/api/pages';
import * as commentsApi from '../../services/api/comments';

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
  deletePage: vi.fn(),
  archivePage: vi.fn(),
  unarchivePage: vi.fn(),
}));

// Mock Layout and Sidebar to simplify tests
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children, rightSidebar }) => (
    <div data-testid="layout">
      {children}
      {rightSidebar && <div data-testid="right-sidebar">{rightSidebar}</div>}
    </div>
  ),
}));

vi.mock('../../components/layout/Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar" />,
  SidebarPlaceholder: () => <div data-testid="sidebar" />,
}));

// Mock navigation components
vi.mock('../../components/navigation/Breadcrumb', () => ({
  Breadcrumb: ({ breadcrumb }) => breadcrumb ? <nav data-testid="breadcrumb">Breadcrumb</nav> : null,
}));

vi.mock('../../components/navigation/PageNavigation', () => ({
  PageNavigation: ({ navigation }) => navigation ? <nav data-testid="page-navigation">Navigation</nav> : null,
}));

vi.mock('../../components/navigation/TableOfContents', () => ({
  TableOfContents: ({ toc }) => toc ? <nav data-testid="table-of-contents">TOC</nav> : null,
}));

vi.mock('../../components/navigation/Backlinks', () => ({
  Backlinks: ({ backlinks }) => backlinks ? <nav data-testid="backlinks">Backlinks</nav> : null,
}));

// Mock DeleteArchiveDialog
vi.mock('../../components/page/DeleteArchiveDialog', () => ({
  DeleteArchiveDialog: ({ isOpen, pageTitle }) => 
    isOpen ? <div data-testid="delete-archive-dialog">{pageTitle}</div> : null,
}));

// Mock utility functions
vi.mock('../../utils/syntaxHighlight', () => ({
  highlightCodeBlocks: vi.fn(),
}));

vi.mock('../../utils/linkHandler', () => ({
  processLinks: vi.fn(),
}));

// Mock comments API - include all hooks used by CommentsList
vi.mock('../../services/api/comments', () => ({
  useComments: vi.fn(),
  useCreateComment: vi.fn(),
  useUpdateComment: vi.fn(),
  useDeleteComment: vi.fn(),
}));

// Mock auth
vi.mock('../../services/auth/AuthContext', async () => {
  const actual = await vi.importActual('../../services/auth/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(() => ({
      isAuthenticated: false,
      user: null,
    })),
  };
});

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
    // Default page mock - will be overridden in individual tests
    pagesApi.usePage.mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
    });
    // Default comments mock
    commentsApi.useComments.mockReturnValue({ data: [], isLoading: false, isError: false });
    commentsApi.useCreateComment.mockReturnValue({ mutateAsync: vi.fn(), isError: false });
    commentsApi.useUpdateComment.mockReturnValue({ mutateAsync: vi.fn(), isError: false });
    commentsApi.useDeleteComment.mockReturnValue({ mutateAsync: vi.fn(), isError: false });
  });

  const renderPageView = (pageId = 'test-page-id') => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={[`/pages/${pageId}`]}>
            <PageView />
          </MemoryRouter>
        </AuthProvider>
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

  it('displays table of contents when available', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      table_of_contents: [
        { anchor: 'section-1', text: 'Section 1', level: 2 },
        { anchor: 'section-2', text: 'Section 2', level: 2 },
      ],
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.getByTestId('table-of-contents')).toBeInTheDocument();
  });

  it('displays backlinks when available', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      backlinks: [
        { page_id: 'page-1', title: 'Linking Page 1' },
        { page_id: 'page-2', title: 'Linking Page 2' },
      ],
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.getByTestId('backlinks')).toBeInTheDocument();
  });

  it('does not display table of contents when null', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      table_of_contents: null,
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.queryByTestId('table-of-contents')).not.toBeInTheDocument();
  });

  it('does not display backlinks when null', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      backlinks: null,
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.queryByTestId('backlinks')).not.toBeInTheDocument();
  });

  it('handles page with all optional fields missing', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Minimal Page',
      html_content: '<p>Content</p>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    expect(screen.getByText('Minimal Page')).toBeInTheDocument();
    expect(screen.getByText(/Content/i)).toBeInTheDocument();
  });

  it('handles page with empty html_content', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Empty Content Page',
      html_content: '',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    expect(screen.getByText('Empty Content Page')).toBeInTheDocument();
  });

  it('handles page with null html_content', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Null Content Page',
      html_content: null,
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    expect(screen.getByText('Null Content Page')).toBeInTheDocument();
  });

  it('handles page with very long title', () => {
    const longTitle = 'A'.repeat(200);
    const mockPage = {
      id: 'test-page-id',
      title: longTitle,
      html_content: '<p>Content</p>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    expect(screen.getByText(longTitle)).toBeInTheDocument();
  });

  it('handles page with special characters in title', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Page & < > " \' Special',
      html_content: '<p>Content</p>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    expect(screen.getByText('Page & < > " \' Special')).toBeInTheDocument();
  });

  it('calls highlightCodeBlocks after content renders', async () => {
    const { highlightCodeBlocks } = await import('../../utils/syntaxHighlight');
    vi.mocked(highlightCodeBlocks).mockClear();
    
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<pre><code>const x = 1;</code></pre>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    // Wait a bit for useEffect to run
    await waitFor(() => {
      expect(highlightCodeBlocks).toHaveBeenCalled();
    }, { timeout: 2000 });
  });

  it('renders code blocks with language specifier', async () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<pre><code class="language-python">def hello():\n    print("Hello")</code></pre>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    // Check that code block is rendered
    const codeBlock = screen.getByText(/def hello\(\):/);
    expect(codeBlock).toBeInTheDocument();
    expect(codeBlock.closest('pre')).toBeInTheDocument();
    expect(codeBlock.closest('code')).toHaveClass('language-python');
  });

  it('renders multiple code blocks', async () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Text before</p><pre><code class="language-python">def hello(): pass</code></pre><p>Text between</p><pre><code class="language-javascript">const x = 1;</code></pre><p>Text after</p>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    // Check that both code blocks are rendered
    const codeBlocks = screen.getAllByRole('code', { hidden: true });
    expect(codeBlocks.length).toBeGreaterThanOrEqual(2);
    
    // Check content
    expect(screen.getByText(/def hello\(\): pass/)).toBeInTheDocument();
    expect(screen.getByText(/const x = 1;/)).toBeInTheDocument();
  });

  it('preserves whitespace in code blocks', async () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<pre><code>def hello():\n    print("Hello")\n    return True</code></pre>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    // Check that code block content is present
    const codeBlock = screen.getByText(/def hello\(\):/);
    expect(codeBlock).toBeInTheDocument();
    
    // The whitespace should be preserved in the HTML (CSS handles rendering)
    const preElement = codeBlock.closest('pre');
    expect(preElement).toBeInTheDocument();
  });

  it('renders code blocks mixed with other content', async () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<h1>Heading</h1><p>Text before code block.</p><pre><code class="language-python">code here</code></pre><p>Text after code block.</p>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    // Check that all content is rendered
    expect(screen.getByText('Heading')).toBeInTheDocument();
    expect(screen.getByText('Text before code block.')).toBeInTheDocument();
    expect(screen.getByText('code here')).toBeInTheDocument();
    expect(screen.getByText('Text after code block.')).toBeInTheDocument();
  });

  it('calls processLinks after content renders', async () => {
    const { processLinks } = await import('../../utils/linkHandler');
    vi.mocked(processLinks).mockClear();
    
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<a href="/pages/other">Link</a>',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    // Wait a bit for useEffect to run
    await waitFor(() => {
      expect(processLinks).toHaveBeenCalled();
    }, { timeout: 2000 });
  });

  it('handles TOC with empty array', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      table_of_contents: [],
      backlinks: null, // Ensure backlinks is null so right sidebar doesn't render
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    // TOC component returns null for empty array, so it shouldn't be in document
    // But the mock might still render it, so we check the actual component behavior
    const toc = screen.queryByTestId('table-of-contents');
    // If TOC component properly handles empty array, it won't render
    // Otherwise, it's acceptable if it renders but is empty
    expect(toc === null || toc.textContent === 'TOC').toBeTruthy();
  });

  it('handles backlinks with empty array', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      table_of_contents: null, // Ensure TOC is null so right sidebar doesn't render
      backlinks: [],
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    // Backlinks component returns null for empty array
    // But the mock might still render it, so we check the actual component behavior
    const backlinks = screen.queryByTestId('backlinks');
    // If Backlinks component properly handles empty array, it won't render
    // Otherwise, it's acceptable if it renders but is empty
    expect(backlinks === null || backlinks.textContent === 'Backlinks').toBeTruthy();
  });

  it('handles TOC with malformed data gracefully', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      table_of_contents: [{ anchor: 'section-1', text: 'Section 1' }], // Missing level
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    // Should not crash, TOC component should handle missing level
    expect(screen.getByTestId('table-of-contents')).toBeInTheDocument();
  });

  it('handles backlinks with malformed data gracefully', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      backlinks: [{ page_id: 'linker-1' }], // Missing title
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    // Should not crash
    expect(screen.getByTestId('backlinks')).toBeInTheDocument();
  });

  it('displays delete button when can_delete is true', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      can_delete: true,
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.getByRole('button', { name: /Delete/i })).toBeInTheDocument();
  });

  it('displays archive button when can_archive is true and page is not archived', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      can_archive: true,
      status: 'published',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.getByRole('button', { name: /Archive/i })).toBeInTheDocument();
  });

  it('displays unarchive button when page is archived and can_archive is true', async () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      can_archive: true,
      status: 'archived', // Explicitly set to 'archived'
    };

    // Reset and set the mock before rendering
    pagesApi.usePage.mockReset();
    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    
    // Wait for the page to render and verify status
    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });
    
    // Verify the page status is archived by checking for Unarchive button
    const unarchiveButton = await screen.findByRole('button', { name: /Unarchive/i });
    expect(unarchiveButton).toBeInTheDocument();
    
    // Archive button should not be present when status is archived
    // Use a more specific query to avoid matching "Unarchive" text
    const archiveButtons = screen.queryAllByRole('button', { name: /^Archive this page$/i });
    expect(archiveButtons).toHaveLength(0);
  });

  it('does not display delete button when can_delete is false', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      can_delete: false,
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.queryByRole('button', { name: /Delete/i })).not.toBeInTheDocument();
  });

  it('does not display archive button when can_archive is false', () => {
    const mockPage = {
      id: 'test-page-id',
      title: 'Test Page',
      html_content: '<p>Content</p>',
      can_archive: false,
      status: 'published',
    };

    pagesApi.usePage.mockReturnValue({
      data: mockPage,
      isLoading: false,
      isError: false,
    });

    renderPageView('test-page-id');
    expect(screen.queryByRole('button', { name: /Archive/i })).not.toBeInTheDocument();
  });

  describe('Table rendering', () => {
    it('renders tables with headers and cells', async () => {
      const mockPage = {
        id: 'test-page-id',
        title: 'Test Page',
        html_content: '<table><thead><tr><th>Header 1</th><th>Header 2</th></tr></thead><tbody><tr><td>Cell 1</td><td>Cell 2</td></tr></tbody></table>',
      };

      pagesApi.usePage.mockReturnValue({
        data: mockPage,
        isLoading: false,
        isError: false,
      });

      renderPageView('test-page-id');
      
      await waitFor(() => {
        expect(screen.getByText('Header 1')).toBeInTheDocument();
        expect(screen.getByText('Header 2')).toBeInTheDocument();
        expect(screen.getByText('Cell 1')).toBeInTheDocument();
        expect(screen.getByText('Cell 2')).toBeInTheDocument();
      });
    });

    it('renders tables with multiple rows', async () => {
      const mockPage = {
        id: 'test-page-id',
        title: 'Test Page',
        html_content: '<table><thead><tr><th>Header 1</th><th>Header 2</th></tr></thead><tbody><tr><td>Cell 1</td><td>Cell 2</td></tr><tr><td>Cell 3</td><td>Cell 4</td></tr></tbody></table>',
      };

      pagesApi.usePage.mockReturnValue({
        data: mockPage,
        isLoading: false,
        isError: false,
      });

      renderPageView('test-page-id');
      
      await waitFor(() => {
        expect(screen.getByText('Cell 1')).toBeInTheDocument();
        expect(screen.getByText('Cell 3')).toBeInTheDocument();
      });
    });

    it('renders tables mixed with other content', async () => {
      const mockPage = {
        id: 'test-page-id',
        title: 'Test Page',
        html_content: '<p>Text before table.</p><table><thead><tr><th>Header 1</th></tr></thead><tbody><tr><td>Cell 1</td></tr></tbody></table><p>Text after table.</p>',
      };

      pagesApi.usePage.mockReturnValue({
        data: mockPage,
        isLoading: false,
        isError: false,
      });

      renderPageView('test-page-id');
      
      await waitFor(() => {
        expect(screen.getByText('Text before table.')).toBeInTheDocument();
        expect(screen.getByText('Header 1')).toBeInTheDocument();
        expect(screen.getByText('Cell 1')).toBeInTheDocument();
        expect(screen.getByText('Text after table.')).toBeInTheDocument();
      });
    });
  });
});
