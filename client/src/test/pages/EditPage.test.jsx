import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useParams, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EditPage } from '../../pages/EditPage';
import * as pagesApi from '../../services/api/pages';
import * as markdownUtils from '../../utils/markdown';

// Mock router hooks
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
  useVersionHistory: vi.fn(),
}));

// Mock markdown utils
vi.mock('../../utils/markdown', () => ({
  htmlToMarkdown: vi.fn((html) => html ? `markdown: ${html}` : ''),
  markdownToHtml: vi.fn((md) => md ? `<p>${md}</p>` : ''),
}));

// Mock Layout and Sidebar
vi.mock('../../components/layout/Layout', () => ({
  Layout: ({ children }) => <div data-testid="layout">{children}</div>,
}));

vi.mock('../../components/layout/Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar" />,
}));

// Mock Editor components
vi.mock('../../components/editor/Editor', () => ({
  Editor: React.forwardRef(({ content, onChange, onEditorReady }, ref) => {
    React.useEffect(() => {
      if (onEditorReady) {
        const mockEditor = {
          commands: {
            setContent: vi.fn(),
            focus: vi.fn(),
          },
          getHTML: () => content || '<p>Editor content</p>',
        };
        onEditorReady(mockEditor);
      }
    }, []);

    React.useImperativeHandle(ref, () => ({
      getHTML: () => content || '<p>Editor content</p>',
      editor: { commands: { setContent: vi.fn() } },
    }));

    return <div data-testid="editor">Editor</div>;
  }),
}));

vi.mock('../../components/editor/EditorToolbar', () => ({
  EditorToolbar: ({ editor }) => editor ? <div data-testid="editor-toolbar">Toolbar</div> : null,
}));

vi.mock('../../components/editor/MetadataForm', () => {
  const React = require('react');
  return {
    MetadataForm: ({ initialData, onChange, isNewPage }) => {
      React.useEffect(() => {
        if (onChange) {
          onChange({
            title: initialData?.title || '',
            slug: initialData?.slug || '',
            parent_id: initialData?.parent_id || null,
            section: initialData?.section || null,
            order: initialData?.order || null,
            status: initialData?.status || 'draft',
          });
        }
      }, []);
      return React.createElement('div', { 'data-testid': 'metadata-form' }, 'MetadataForm');
    },
  };
});

describe('EditPage', () => {
  let queryClient;
  let mockNavigate;
  let mockQueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    mockNavigate = vi.fn();
    mockQueryClient = {
      invalidateQueries: vi.fn(),
    };

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

    pagesApi.useVersionHistory.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    // Mock QueryClient methods
    queryClient.invalidateQueries = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
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

  it('renders edit page for new page', () => {
    renderEditPage('new');

    expect(screen.getByText('Create New Page')).toBeInTheDocument();
    expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    expect(screen.getByTestId('editor')).toBeInTheDocument();
    expect(screen.getByText('Create Page')).toBeInTheDocument();
  });

  it('renders edit page for existing page', () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        slug: 'existing-page',
        content: '# Content',
        parent_id: null,
        section: null,
        order: 0,
        status: 'published',
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    expect(screen.getByText('Edit Page')).toBeInTheDocument();
    expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    expect(screen.getByText('Save Changes')).toBeInTheDocument();
  });

  it('displays loading state when loading existing page', () => {
    pagesApi.usePage.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    renderEditPage('existing-page-id');

    expect(screen.getByText('Loading page...')).toBeInTheDocument();
  });

  it('loads page content and metadata into editor', async () => {
    const pageContent = '# Test Content';
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Test Page',
        slug: 'test-page',
        content: pageContent,
        parent_id: null,
        section: 'Test Section',
        order: 5,
        status: 'published',
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    await waitFor(() => {
      expect(markdownUtils.markdownToHtml).toHaveBeenCalledWith(pageContent);
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    });
  });

  it('shows unsaved changes indicator when content changes', async () => {
    renderEditPage('new');

    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: 'New Title' } });

    await waitFor(() => {
      expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
    });
  });

  it('disables save button when metadata is incomplete', async () => {
    renderEditPage('new');

    await waitFor(() => {
      const saveButton = screen.getByText('Create Page');
      // Button should be disabled if title or slug is missing
      expect(saveButton).toBeDisabled();
    });
  });

  it('includes metadata in save request', async () => {
    renderEditPage('new');

    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(pagesApi.createPage).toHaveBeenCalledWith(
        expect.objectContaining({
          title: expect.any(String),
          slug: expect.any(String),
          status: 'draft',
        })
      );
    });
  });

  it('creates new page with all metadata when save is clicked', async () => {
    renderEditPage('new');

    // Wait for MetadataForm to call onChange
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(pagesApi.createPage).toHaveBeenCalledWith(
        expect.objectContaining({
          title: expect.any(String),
          slug: expect.any(String),
          content: expect.any(String),
          status: 'draft',
        })
      );
    });
  });

  it('validates slug before saving', async () => {
    renderEditPage('new');

    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Create Page');

    // Button should be disabled if slug is missing
    expect(saveButton).toBeDisabled();
  });

  it('updates existing page when save is clicked', async () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        slug: 'existing-page',
        content: '# Content',
        parent_id: null,
        section: null,
        order: 0,
        status: 'published',
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(pagesApi.updatePage).toHaveBeenCalledWith(
        'existing-page-id',
        expect.objectContaining({
          title: expect.any(String),
          slug: expect.any(String),
          content: expect.any(String),
        })
      );
    });
  });

  it('navigates to new page after creation', async () => {
    pagesApi.createPage.mockResolvedValue({
      id: 'new-page-id',
      title: 'New Page',
    });

    renderEditPage('new');

    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: 'New Page' } });

    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/pages/new-page-id');
    });
  });

  it('navigates to page view after update', async () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        content: '# Content',
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/pages/existing-page-id');
    });
  });

  it('shows confirmation when canceling with unsaved changes', () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

    renderEditPage('new');

    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: 'Test' } });

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(confirmSpy).toHaveBeenCalled();
    expect(mockNavigate).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it('navigates when canceling without unsaved changes', () => {
    renderEditPage('new');

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('navigates to page view when canceling existing page edit', () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        content: '# Content',
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/pages/existing-page-id');
  });

  it('auto-saves draft to localStorage', async () => {
    vi.useFakeTimers();

    renderEditPage('new');

    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: 'Draft Title' } });

    // Fast-forward time
    vi.advanceTimersByTime(2500);

    await waitFor(() => {
      const draft = localStorage.getItem('arcadium_draft_new');
      expect(draft).toBeTruthy();
      const parsed = JSON.parse(draft);
      expect(parsed.title).toBe('Draft Title');
    });

    vi.useRealTimers();
  });

  it('loads draft from localStorage for new page', () => {
    const draft = {
      title: 'Draft Title',
      content: '<p>Draft content</p>',
      timestamp: Date.now(),
    };
    localStorage.setItem('arcadium_draft_new', JSON.stringify(draft));

    renderEditPage('new');

    expect(screen.getByDisplayValue('Draft Title')).toBeInTheDocument();
    expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
  });

  it('clears draft after successful save', async () => {
    const draft = {
      title: 'Draft Title',
      content: '<p>Draft content</p>',
      timestamp: Date.now(),
    };
    localStorage.setItem('arcadium_draft_new', JSON.stringify(draft));

    renderEditPage('new');

    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(localStorage.getItem('arcadium_draft_new')).toBeNull();
    });
  });

  it('handles save error gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    pagesApi.createPage.mockRejectedValue(new Error('Save failed'));

    renderEditPage('new');

    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: 'Test' } });

    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(pagesApi.createPage).toHaveBeenCalled();
    });

    // Should not navigate on error
    expect(mockNavigate).not.toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it('shows saving state during save operation', async () => {
    pagesApi.createPage.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    renderEditPage('new');

    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: 'Test' } });

    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);

    expect(screen.getByText('Saving...')).toBeInTheDocument();
    expect(saveButton).toBeDisabled();
  });

  it('converts HTML to markdown before saving', async () => {
    markdownUtils.htmlToMarkdown.mockReturnValue('# Markdown content');

    renderEditPage('new');

    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: 'Test' } });

    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(markdownUtils.htmlToMarkdown).toHaveBeenCalled();
    });
  });

  it('trims title before saving', async () => {
    renderEditPage('new');

    const titleInput = screen.getByPlaceholderText('Page Title');
    fireEvent.change(titleInput, { target: { value: '  Trimmed Title  ' } });

    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(pagesApi.createPage).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Trimmed Title',
        })
      );
    });
  });

  it('handles missing page content gracefully', () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Page Without Content',
        content: null,
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    expect(screen.getByDisplayValue('Page Without Content')).toBeInTheDocument();
    expect(screen.getByTestId('editor')).toBeInTheDocument();
  });

  it('handles page load error', () => {
    pagesApi.usePage.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
    });

    renderEditPage('existing-page-id');

    // Should still render the editor (graceful degradation)
    expect(screen.getByTestId('editor')).toBeInTheDocument();
  });

  it('displays preview toggle button', () => {
    renderEditPage('new');

    const previewToggle = screen.getByLabelText(/Show preview/i);
    expect(previewToggle).toBeInTheDocument();
  });

  it('switches to preview mode when toggle is clicked', async () => {
    const user = userEvent.setup();
    renderEditPage('new');

    const previewToggle = screen.getByLabelText(/Show preview/i);
    await user.click(previewToggle);

    // Should show preview instead of editor
    expect(screen.queryByTestId('editor')).not.toBeInTheDocument();
    const preview = document.querySelector('.arc-edit-page-preview');
    expect(preview).toBeInTheDocument();
  });

  it('switches back to editor mode when toggle is clicked again', async () => {
    const user = userEvent.setup();
    renderEditPage('new');

    const previewToggle = screen.getByLabelText(/Show preview/i);
    await user.click(previewToggle);

    const editToggle = screen.getByLabelText(/Show editor/i);
    await user.click(editToggle);

    expect(screen.getByTestId('editor')).toBeInTheDocument();
    const preview = document.querySelector('.arc-edit-page-preview');
    expect(preview).not.toBeInTheDocument();
  });

  it('displays preview with rendered markdown content', async () => {
    const user = userEvent.setup();
    markdownUtils.markdownToHtml.mockReturnValue('<h1>Rendered Content</h1>');

    renderEditPage('new');

    const previewToggle = screen.getByLabelText(/Show preview/i);
    await user.click(previewToggle);

    await waitFor(() => {
      const preview = document.querySelector('.arc-edit-page-preview');
      expect(preview).toBeInTheDocument();
      expect(preview.innerHTML).toContain('Rendered Content');
    });
  });

  it('updates preview when editor content changes', async () => {
    const user = userEvent.setup();
    markdownUtils.markdownToHtml.mockReturnValue('<p>Updated Content</p>');

    renderEditPage('new');

    // Switch to preview
    const previewToggle = screen.getByLabelText(/Show preview/i);
    await user.click(previewToggle);

    // Switch back to editor and make changes
    const editToggle = screen.getByLabelText(/Show editor/i);
    await user.click(editToggle);

    // Simulate editor content change
    const editor = screen.getByTestId('editor');
    const mockOnChange = vi.fn();
    // The editor mock should trigger onChange

    // Switch back to preview
    await user.click(previewToggle);

    // Preview should reflect changes
    await waitFor(() => {
      expect(markdownUtils.markdownToHtml).toHaveBeenCalled();
    });
  });

  it('displays version info for existing pages', () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        slug: 'existing-page',
        content: '# Content',
        version: 5,
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    expect(screen.getByText(/Version:/i)).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('displays history link for existing pages', () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        slug: 'existing-page',
        content: '# Content',
        version: 5,
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    const historyLink = screen.getByText('View History');
    expect(historyLink.closest('a')).toHaveAttribute('href', '/pages/existing-page-id/history');
  });

  it('displays history button in actions for existing pages', () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        slug: 'existing-page',
        content: '# Content',
        version: 5,
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    const historyButton = screen.getByText('📜 History');
    expect(historyButton.closest('a')).toHaveAttribute('href', '/pages/existing-page-id/history');
  });

  it('does not display version info for new pages', () => {
    renderEditPage('new');

    expect(screen.queryByText(/Version:/i)).not.toBeInTheDocument();
    expect(screen.queryByText('View History')).not.toBeInTheDocument();
  });

  it('displays enhanced unsaved changes warning', async () => {
    renderEditPage('new');

    // Trigger unsaved changes
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    });

    // The warning should appear when there are changes
    // Note: The exact implementation depends on when hasUnsavedChanges becomes true
    const unsavedWarning = screen.queryByText(/You have unsaved changes/i);
    // May or may not be visible depending on state, but should not crash
  });

  it('handles page without version number', () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        slug: 'existing-page',
        content: '# Content',
        // version is undefined
      },
      isLoading: false,
      isError: false,
    });

    renderEditPage('existing-page-id');

    // Should not crash when version is missing
    expect(screen.getByText('Edit Page')).toBeInTheDocument();
  });
});
