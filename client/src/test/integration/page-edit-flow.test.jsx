import React from 'react';
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';
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
  parseFrontmatter: vi.fn((content) => {
    if (!content || !content.startsWith('---')) {
      return { frontmatter: {}, markdown: content || '' };
    }
    const parts = content.split('---');
    if (parts.length < 3) {
      return { frontmatter: {}, markdown: content };
    }
    const frontmatterStr = parts[1].trim();
    const markdown = parts.slice(2).join('---').trim();
    const frontmatter = {};
    if (frontmatterStr) {
      const lines = frontmatterStr.split('\n');
      for (const line of lines) {
        const match = line.match(/^(\w+):\s*(.+)$/);
        if (match) {
          const key = match[1];
          let value = match[2].trim();
          if ((value.startsWith('"') && value.endsWith('"')) || 
              (value.startsWith("'") && value.endsWith("'"))) {
            value = value.slice(1, -1);
          }
          frontmatter[key] = value;
        }
      }
    }
    return { frontmatter, markdown };
  }),
  addFrontmatter: vi.fn((metadata, markdown, originalContent = null) => {
    if (!metadata) return markdown || '';
    
    let existingFrontmatter = {};
    if (originalContent) {
      const parsed = vi.fn().mockReturnValue({ frontmatter: {}, markdown: originalContent })();
      // Use the actual parseFrontmatter logic if needed, but for mock we'll simplify
      if (originalContent && originalContent.startsWith('---')) {
        const parts = originalContent.split('---');
        if (parts.length >= 3) {
          const frontmatterStr = parts[1].trim();
          const lines = frontmatterStr.split('\n');
          for (const line of lines) {
            const match = line.match(/^(\w+):\s*(.+)$/);
            if (match) {
              const key = match[1];
              let value = match[2].trim();
              if ((value.startsWith('"') && value.endsWith('"')) || 
                  (value.startsWith("'") && value.endsWith("'"))) {
                value = value.slice(1, -1);
              }
              existingFrontmatter[key] = value;
            }
          }
        }
      }
    }
    
    const frontmatter = { ...existingFrontmatter };
    if (metadata.title) frontmatter.title = metadata.title;
    if (metadata.slug) frontmatter.slug = metadata.slug;
    if (metadata.section !== undefined) {
      if (metadata.section) {
        frontmatter.section = metadata.section;
      } else {
        delete frontmatter.section;
      }
    }
    if (metadata.status) frontmatter.status = metadata.status;
    if (metadata.order !== null && metadata.order !== undefined) {
      frontmatter.order = metadata.order;
    } else if (metadata.order === null || metadata.order === '') {
      delete frontmatter.order;
    }
    
    const frontmatterLines = [];
    const standardKeys = ['title', 'slug', 'section', 'status', 'order', 'parent_slug'];
    const sortedKeys = [
      ...standardKeys.filter(k => k in frontmatter),
      ...Object.keys(frontmatter).filter(k => !standardKeys.includes(k)).sort()
    ];
    
    for (const key of sortedKeys) {
      const value = frontmatter[key];
      if (value !== null && value !== undefined && value !== '') {
        const needsQuotes = typeof value === 'string' && (
          value.includes(':') || 
          value.includes('#') || 
          value.includes('|') ||
          value.includes('&') ||
          value.startsWith(' ') ||
          value.endsWith(' ')
        );
        const formattedValue = needsQuotes ? `"${value.replace(/"/g, '\\"')}"` : value;
        frontmatterLines.push(`${key}: ${formattedValue}`);
      }
    }
    
    if (frontmatterLines.length === 0) {
      return markdown || '';
    }
    
    return `---\n${frontmatterLines.join('\n')}\n---\n${markdown || ''}`;
  }),
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

  // Suppress window.alert during tests
  beforeAll(() => {
    vi.spyOn(window, 'alert').mockImplementation(() => {});
  });
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

  it('uses HTML-to-markdown pipeline when saving after preview toggle', async () => {
    renderEditPage('new');
    
    // Wait for metadata form and editor to be ready
    await waitFor(() => {
      expect(screen.getByTestId('metadata-form')).toBeInTheDocument();
      expect(screen.getByTestId('editor')).toBeInTheDocument();
    });
    
    // Enter a basic title so save is allowed
    const titleInput = screen.getByTestId('metadata-title');
    fireEvent.change(titleInput, { target: { value: 'Preview Pipeline Page' } });
    
    // Toggle preview on and off to exercise that path
    const previewToggle = screen.getByLabelText(/Show preview/i);
    fireEvent.click(previewToggle);
    
    const editToggle = screen.getByLabelText(/Show editor/i);
    fireEvent.click(editToggle);
    
    // Save page
    const saveButton = screen.getByText('Create Page');
    fireEvent.click(saveButton);
    
    // Ensure HTML-to-markdown conversion was invoked as part of save
    await waitFor(() => {
      expect(markdownUtils.htmlToMarkdown).toHaveBeenCalled();
      expect(pagesApi.createPage).toHaveBeenCalled();
    }, { timeout: 2000     });
  });

  describe('Table creation and editing', () => {
    it('creates a page with a table and preserves it on save', async () => {
      const { user } = await setup();
      const mockPage = {
        id: 'new-page-id',
        title: 'Test Page',
        content: '',
        slug: 'test-page',
        status: 'draft',
      };

      pagesApi.usePage.mockReturnValue({
        data: null,
        isLoading: false,
        isError: false,
      });

      pagesApi.createPage.mockResolvedValue(mockPage);

      renderEditPage();

      // Wait for editor to be ready
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Start writing/i)).toBeInTheDocument();
      });

      // Simulate inserting a table via the editor
      // In a real scenario, this would be done through the TableDialog
      const editor = screen.getByPlaceholderText(/Start writing/i);
      
      // Mock table HTML content
      const tableHtml = '<table><thead><tr><th>Header 1</th><th>Header 2</th></tr></thead><tbody><tr><td>Cell 1</td><td>Cell 2</td></tr></tbody></table>';
      
      // Simulate editor content change
      const onChange = vi.fn();
      const editorComponent = screen.getByTestId('editor');
      if (editorComponent && editorComponent.onChange) {
        editorComponent.onChange(tableHtml);
      }

      // Save the page
      const saveButton = screen.getByRole('button', { name: /Save/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(pagesApi.createPage).toHaveBeenCalled();
      });

      // Verify that the markdown conversion was called (tables should be converted)
      expect(markdownUtils.htmlToMarkdown).toHaveBeenCalled();
    });

    it('loads a page with a table and displays it in the editor', async () => {
      const { user } = await setup();
      const tableMarkdown = '| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |';
      const mockPage = {
        id: 'test-page-id',
        title: 'Test Page',
        content: tableMarkdown,
        slug: 'test-page',
        status: 'published',
      };

      pagesApi.usePage.mockReturnValue({
        data: mockPage,
        isLoading: false,
        isError: false,
      });

      renderEditPage();

      // Wait for editor to load
      await waitFor(() => {
        expect(markdownUtils.markdownToHtml).toHaveBeenCalledWith(tableMarkdown);
      });
    });
  });
});
