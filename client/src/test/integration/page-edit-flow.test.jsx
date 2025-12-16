import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, useParams, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EditPage } from '../../pages/EditPage';
import * as pagesApi from '../../services/api/pages';
import * as markdownUtils from '../../utils/markdown';

// Mock router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(),
    useNavigate: vi.fn(),
  };
});

// Mock API
vi.mock('../../services/api/pages', () => ({
  usePage: vi.fn(),
  createPage: vi.fn(),
  updatePage: vi.fn(),
  useBreadcrumb: vi.fn(() => ({ data: null })),
  usePageNavigation: vi.fn(() => ({ data: null })),
}));

// Mock markdown utils
vi.mock('../../utils/markdown', () => ({
  htmlToMarkdown: vi.fn((html) => html ? `markdown: ${html}` : ''),
  markdownToHtml: vi.fn((md) => md ? `<p>${md}</p>` : ''),
}));

// Mock components
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children }) => <div data-testid="layout">{children}</div>,
}));

vi.mock('../../components/layout/Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar" />,
}));

vi.mock('../../components/editor/Editor', () => ({
  Editor: React.forwardRef(({ content, onChange, onEditorReady }, ref) => {
    const [htmlContent, setHtmlContent] = React.useState(content || '');
    
    React.useEffect(() => {
      if (onEditorReady) {
        const mockEditor = {
          commands: {
            setContent: vi.fn((html) => setHtmlContent(html)),
            focus: vi.fn(),
          },
          getHTML: () => htmlContent,
        };
        onEditorReady(mockEditor);
      }
    }, []);
    
    React.useImperativeHandle(ref, () => ({
      getHTML: () => htmlContent,
      editor: { commands: { setContent: vi.fn() } },
    }));
    
    React.useEffect(() => {
      if (onChange) {
        onChange(htmlContent);
      }
    }, [htmlContent]);
    
    return React.createElement('div', { 'data-testid': 'editor' }, `Editor: ${htmlContent}`);
  }),
}));

vi.mock('../../components/editor/EditorToolbar', () => ({
  EditorToolbar: () => <div data-testid="editor-toolbar">Toolbar</div>,
}));

vi.mock('../../components/navigation/Breadcrumb', () => ({
  Breadcrumb: () => null,
}));

vi.mock('../../components/navigation/PageNavigation', () => ({
  PageNavigation: () => null,
}));

vi.mock('../../utils/syntaxHighlight', () => ({
  highlightCodeBlocks: vi.fn(),
}));

vi.mock('../../utils/linkHandler', () => ({
  processLinks: vi.fn(),
}));

describe('Page Edit Flow Integration', () => {
  let queryClient;
  let mockNavigate;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    
    mockNavigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);
    vi.mocked(useParams).mockReturnValue({ pageId: 'new' });
    
    pagesApi.usePage.mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
    });
    
    pagesApi.createPage.mockResolvedValue({
      id: 'new-page-id',
      title: 'New Page',
    });
    
    pagesApi.updatePage.mockResolvedValue({
      id: 'existing-page-id',
      title: 'Updated Page',
    });
    
    localStorage.clear();
  });

  const renderEditPage = (pageId = 'new') => {
    vi.mocked(useParams).mockReturnValue({ pageId });
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[`/pages/${pageId}/edit`]}>
          <EditPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('completes full create page flow', async () => {
    renderEditPage('new');
    
    // Enter title
    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: 'New Test Page' } });
    
    // Wait for editor to be ready
    await waitFor(() => {
      expect(screen.getByTestId('editor')).toBeInTheDocument();
    });
    
    // Save page
    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);
    
    // Verify API call
    await waitFor(() => {
      expect(pagesApi.createPage).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'New Test Page',
          status: 'draft',
        })
      );
    });
    
    // Verify navigation
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/pages/new-page-id');
    });
  });

  it('completes full edit page flow', async () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        content: '# Original Content',
      },
      isLoading: false,
      isError: false,
    });
    
    renderEditPage('existing-page-id');
    
    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByDisplayValue('Existing Page')).toBeInTheDocument();
    });
    
    // Update title
    const titleInput = screen.getByDisplayValue('Existing Page');
    fireEvent.change(titleInput, { target: { value: 'Updated Page Title' } });
    
    // Save changes
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    // Verify API call
    await waitFor(() => {
      expect(pagesApi.updatePage).toHaveBeenCalledWith(
        'existing-page-id',
        expect.objectContaining({
          title: 'Updated Page Title',
        })
      );
    });
  });

  it('handles error during page creation', async () => {
    pagesApi.createPage.mockRejectedValue(new Error('Creation failed'));
    
    renderEditPage('new');
    
    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: 'Test Page' } });
    
    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(pagesApi.createPage).toHaveBeenCalled();
    });
    
    // Should not navigate on error
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('handles error during page update', async () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        content: '# Content',
      },
      isLoading: false,
      isError: false,
    });
    
    pagesApi.updatePage.mockRejectedValue(new Error('Update failed'));
    
    renderEditPage('existing-page-id');
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('Existing Page')).toBeInTheDocument();
    });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(pagesApi.updatePage).toHaveBeenCalled();
    });
    
    // Should not navigate on error
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('preserves draft across page reloads', async () => {
    // Set up draft in localStorage
    const draft = {
      title: 'Draft Title',
      content: '<p>Draft content</p>',
      timestamp: Date.now(),
    };
    localStorage.setItem('arcadium_draft_new', JSON.stringify(draft));
    
    renderEditPage('new');
    
    // Draft should be loaded
    await waitFor(() => {
      expect(screen.getByDisplayValue('Draft Title')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
  });

  it('clears draft after successful save', async () => {
    const draft = {
      title: 'Draft Title',
      content: '<p>Draft</p>',
      timestamp: Date.now(),
    };
    localStorage.setItem('arcadium_draft_new', JSON.stringify(draft));
    
    renderEditPage('new');
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('Draft Title')).toBeInTheDocument();
    });
    
    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(localStorage.getItem('arcadium_draft_new')).toBeNull();
    });
  });
});
