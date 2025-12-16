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

vi.mock('../../components/editor/MetadataForm', () => {
  const React = require('react');
  return {
    MetadataForm: ({ initialData, onChange, isNewPage }) => {
      const [formData, setFormData] = React.useState({
        title: initialData?.title || '',
        slug: initialData?.slug || (isNewPage ? 'auto-slug' : ''),
        parent_id: initialData?.parent_id || null,
        section: initialData?.section || null,
        order: initialData?.order || null,
        status: initialData?.status || 'draft',
      });

      React.useEffect(() => {
        if (onChange) {
          onChange(formData);
        }
      }, [formData, onChange]);

      const handleTitleChange = (e) => {
        const newTitle = e.target.value;
        const newSlug = isNewPage && !formData.slug ? `slug-${newTitle.toLowerCase()}` : formData.slug;
        const updated = { ...formData, title: newTitle, slug: newSlug };
        setFormData(updated);
      };

      const handleSlugChange = (e) => {
        setFormData({ ...formData, slug: e.target.value });
      };

      return (
        <div data-testid="metadata-form">
          <input
            data-testid="metadata-title"
            value={formData.title}
            onChange={handleTitleChange}
            placeholder="Page Title"
          />
          <input
            data-testid="metadata-slug"
            value={formData.slug}
            onChange={handleSlugChange}
            placeholder="slug"
          />
        </div>
      );
    },
  };
});

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

  it('completes full create page flow with metadata', async () => {
    renderEditPage('new');
    
    // Wait for metadata form and editor to be ready
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
      expect(screen.getByTestId('editor')).toBeInTheDocument();
    });
    
    // Enter metadata - title will auto-generate slug
    const titleInput = screen.getByTestId('metadata-title');
    fireEvent.change(titleInput, { target: { value: 'New Test Page' } });
    
    // Wait a bit for state updates
    await waitFor(() => {
      expect(titleInput.value).toBe('New Test Page');
    }, { timeout: 1000 });
    
    // Save page
    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);
    
    // Verify API call includes metadata
    await waitFor(() => {
      expect(pagesApi.createPage).toHaveBeenCalled();
    }, { timeout: 2000 });
    
    const createCall = pagesApi.createPage.mock.calls[0]?.[0];
    expect(createCall).toMatchObject({
      title: expect.any(String),
      slug: expect.any(String),
      status: 'draft',
    });
  });

  it('completes full edit page flow with metadata', async () => {
    pagesApi.usePage.mockReturnValue({
      data: {
        id: 'existing-page-id',
        title: 'Existing Page',
        slug: 'existing-page',
        content: '# Original Content',
        parent_id: null,
        section: 'Test Section',
        order: 5,
        status: 'published',
      },
      isLoading: false,
      isError: false,
    });
    
    renderEditPage('existing-page-id');
    
    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    });
    
    // Update metadata
    const titleInput = screen.getByTestId('metadata-title');
    fireEvent.change(titleInput, { target: { value: 'Updated Page Title' } });
    
    // Save changes
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    // Verify API call includes metadata
    await waitFor(() => {
      expect(pagesApi.updatePage).toHaveBeenCalled();
    }, { timeout: 2000 });
    
    const updateCall = pagesApi.updatePage.mock.calls[0];
    expect(updateCall[0]).toBe('existing-page-id');
    expect(updateCall[1]).toMatchObject({
      title: expect.any(String),
      slug: expect.any(String),
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

  it('preserves draft with metadata across page reloads', async () => {
    // Set up draft in localStorage with metadata
    const draft = {
      title: 'Draft Title',
      content: '<p>Draft content</p>',
      metadata: {
        title: 'Draft Title',
        slug: 'draft-title',
        parent_id: null,
        section: 'Draft Section',
        order: 10,
        status: 'draft',
      },
      timestamp: Date.now(),
    };
    localStorage.setItem('arcadium_draft_new', JSON.stringify(draft));
    
    renderEditPage('new');
    
    // Draft should be loaded
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    }, { timeout: 2000 });
    
    // Check that unsaved changes indicator appears
    await waitFor(() => {
      expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('clears draft after successful save', async () => {
    const draft = {
      title: 'Draft Title',
      content: '<p>Draft</p>',
      metadata: {
        title: 'Draft Title',
        slug: 'draft-title',
        status: 'draft',
      },
      timestamp: Date.now(),
    };
    localStorage.setItem('arcadium_draft_new', JSON.stringify(draft));
    
    renderEditPage('new');
    
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    });
    
    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(localStorage.getItem('arcadium_draft_new')).toBeNull();
    });
  });

  it('validates metadata before saving', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    
    renderEditPage('new');
    
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    }, { timeout: 2000 });
    
    // Clear title and slug manually
    const titleInput = screen.getByTestId('metadata-title');
    fireEvent.change(titleInput, { target: { value: '' } });
    
    const slugInput = screen.getByTestId('metadata-slug');
    fireEvent.change(slugInput, { target: { value: '' } });
    
    // Wait for state to update
    await waitFor(() => {
      expect(titleInput.value).toBe('');
    }, { timeout: 1000 });
    
    // Try to save without title
    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);
    
    // Should show alert
    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalled();
    }, { timeout: 2000 });
    
    // Should not call API
    expect(pagesApi.createPage).not.toHaveBeenCalled();
    
    alertSpy.mockRestore();
  });

  it('validates slug before saving', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    
    renderEditPage('new');
    
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    }, { timeout: 2000 });
    
    // Set title (will auto-generate slug)
    const titleInput = screen.getByTestId('metadata-title');
    fireEvent.change(titleInput, { target: { value: 'Test Page' } });
    
    // Wait for slug to be generated, then clear it
    await waitFor(() => {
      const slugInput = screen.getByTestId('metadata-slug');
      if (slugInput.value) {
        fireEvent.change(slugInput, { target: { value: '' } });
      }
    }, { timeout: 2000 });
    
    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);
    
    // Should show alert for missing slug
    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalled();
    }, { timeout: 2000 });
    
    alertSpy.mockRestore();
  });

  it('saves page with all metadata fields', async () => {
    renderEditPage('new');
    
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
    }, { timeout: 2000 });
    
    const titleInput = screen.getByTestId('metadata-title');
    fireEvent.change(titleInput, { target: { value: 'Complete Page' } });
    
    // Wait for slug to be auto-generated or set manually
    await waitFor(() => {
      const slugInput = screen.getByTestId('metadata-slug');
      if (!slugInput.value) {
        fireEvent.change(slugInput, { target: { value: 'complete-page' } });
      }
    }, { timeout: 2000 });
    
    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(pagesApi.createPage).toHaveBeenCalled();
    }, { timeout: 2000 });
    
    const createCall = pagesApi.createPage.mock.calls[0]?.[0];
    expect(createCall).toMatchObject({
      title: expect.any(String),
      slug: expect.any(String),
      status: 'draft',
    });
  });
});
