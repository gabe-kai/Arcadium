import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MetadataForm } from '../../components/editor/MetadataForm';
import * as pagesApi from '../../services/api/pages';
import * as slugUtils from '../../utils/slug';

// Mock API functions
vi.mock('../../services/api/pages', () => ({
  searchPages: vi.fn(),
  validateSlug: vi.fn(),
}));

// Mock slug utility
vi.mock('../../utils/slug', () => ({
  generateSlug: vi.fn((title) => title.toLowerCase().replace(/\s+/g, '-')),
}));

describe('MetadataForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    pagesApi.searchPages.mockResolvedValue([]);
    pagesApi.validateSlug.mockResolvedValue({ valid: true });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders all form fields', () => {
    render(<MetadataForm />);
    
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Slug/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Parent Page/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Section/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Order/i)).toBeInTheDocument();
    // Status uses radio buttons, so check for the label text and radio inputs
    expect(screen.getByText(/Status/i)).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /Draft/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /Published/i })).toBeInTheDocument();
  });

  it('displays required indicators', () => {
    render(<MetadataForm />);
    
    // Check that required asterisks are present in the labels
    const titleLabel = screen.getByText(/Title/i);
    expect(titleLabel).toHaveTextContent(/Title \*/);
    
    const slugLabel = screen.getByText(/Slug/i);
    // Slug might appear in multiple places, get the label specifically
    const slugLabels = screen.getAllByText(/Slug/i);
    const slugLabelElement = slugLabels.find(el => el.tagName === 'LABEL' || el.closest('label'));
    expect(slugLabelElement).toBeTruthy();
    if (slugLabelElement) {
      expect(slugLabelElement.textContent).toMatch(/Slug \*/);
    }
  });

  it('loads initial data', () => {
    const initialData = {
      title: 'Test Page',
      slug: 'test-page',
      parent_id: 'parent-id',
      section: 'Test Section',
      order: 5,
      status: 'published',
    };

    render(<MetadataForm initialData={initialData} />);
    
    expect(screen.getByDisplayValue('Test Page')).toBeInTheDocument();
    expect(screen.getByDisplayValue('test-page')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Section')).toBeInTheDocument();
    expect(screen.getByDisplayValue('5')).toBeInTheDocument();
    expect(screen.getByLabelText(/Published/i)).toBeChecked();
  });

  it('auto-generates slug from title for new pages', () => {
    slugUtils.generateSlug.mockReturnValue('test-page');
    
    render(<MetadataForm isNewPage={true} />);
    
    const titleInput = screen.getByLabelText(/Title/i);
    fireEvent.change(titleInput, { target: { value: 'Test Page' } });
    
    expect(slugUtils.generateSlug).toHaveBeenCalledWith('Test Page');
  });

  it('calls onChange when form values change', async () => {
    const onChange = vi.fn();
    
    render(<MetadataForm onChange={onChange} />);
    
    const titleInput = screen.getByLabelText(/Title/i);
    fireEvent.change(titleInput, { target: { value: 'New Title' } });
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalled();
    });
  });

  it('validates slug when it changes', async () => {
    pagesApi.validateSlug.mockResolvedValue({ valid: true });
    
    render(<MetadataForm />);
    
    const slugInput = screen.getByLabelText(/Slug/i);
    fireEvent.change(slugInput, { target: { value: 'test-slug' } });
    
    await waitFor(() => {
      expect(pagesApi.validateSlug).toHaveBeenCalledWith('test-slug', null);
    }, { timeout: 1000 });
  });

  it('shows validation error for invalid slug', async () => {
    pagesApi.validateSlug.mockResolvedValue({ 
      valid: false, 
      message: 'Slug already in use' 
    });
    
    render(<MetadataForm />);
    
    const slugInput = screen.getByLabelText(/Slug/i);
    fireEvent.change(slugInput, { target: { value: 'existing-slug' } });
    
    await waitFor(() => {
      // Error message may appear multiple times, use getAllByText and check at least one exists
      const errorMessages = screen.getAllByText(/Slug already in use/i);
      expect(errorMessages.length).toBeGreaterThan(0);
    }, { timeout: 2000 });
  });

  it('shows validation success for valid slug', async () => {
    pagesApi.validateSlug.mockResolvedValue({ valid: true });
    
    render(<MetadataForm />);
    
    const slugInput = screen.getByLabelText(/Slug/i);
    fireEvent.change(slugInput, { target: { value: 'valid-slug' } });
    
    await waitFor(() => {
      expect(screen.getByText(/Available/i)).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('searches parent pages when typing', async () => {
    const mockPages = [
      { id: 'page-1', title: 'Parent Page 1', section: 'Section 1' },
      { id: 'page-2', title: 'Parent Page 2', section: 'Section 2' },
    ];
    pagesApi.searchPages.mockResolvedValue(mockPages);
    
    render(<MetadataForm />);
    
    const parentInput = screen.getByPlaceholderText(/Search for parent page/i);
    fireEvent.change(parentInput, { target: { value: 'Parent' } });
    
    await waitFor(() => {
      expect(pagesApi.searchPages).toHaveBeenCalledWith('Parent');
    }, { timeout: 1000 });
  });

  it('displays parent page dropdown when results found', async () => {
    const mockPages = [
      { id: 'page-1', title: 'Parent Page 1', section: 'Section 1' },
    ];
    pagesApi.searchPages.mockResolvedValue(mockPages);
    
    render(<MetadataForm />);
    
    const parentInput = screen.getByPlaceholderText(/Search for parent page/i);
    fireEvent.change(parentInput, { target: { value: 'Parent' } });
    
    await waitFor(() => {
      expect(screen.getByText('Parent Page 1')).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('selects parent page from dropdown', async () => {
    const mockPages = [
      { id: 'page-1', title: 'Parent Page 1', section: 'Section 1' },
    ];
    pagesApi.searchPages.mockResolvedValue(mockPages);
    
    render(<MetadataForm />);
    
    const parentInput = screen.getByPlaceholderText(/Search for parent page/i);
    fireEvent.change(parentInput, { target: { value: 'Parent' } });
    
    await waitFor(() => {
      expect(screen.getByText('Parent Page 1')).toBeInTheDocument();
    });
    
    const parentOption = screen.getByText('Parent Page 1');
    fireEvent.click(parentOption);
    
    expect(parentInput).toHaveValue('Parent Page 1');
  });

  it('clears parent selection', async () => {
    const mockPages = [
      { id: 'page-1', title: 'Parent Page 1', section: 'Section 1' },
    ];
    pagesApi.searchPages.mockResolvedValue(mockPages);
    
    render(<MetadataForm initialData={{ parent_id: 'page-1' }} />);
    
    const parentInput = screen.getByPlaceholderText(/Search for parent page/i);
    fireEvent.change(parentInput, { target: { value: 'Parent' } });
    
    await waitFor(() => {
      expect(screen.getByText('Parent Page 1')).toBeInTheDocument();
    });
    
    const clearButton = screen.getByTitle(/Clear parent/i);
    fireEvent.click(clearButton);
    
    expect(parentInput).toHaveValue('');
  });

  it('handles section input', () => {
    render(<MetadataForm />);
    
    const sectionInput = screen.getByLabelText(/Section/i);
    fireEvent.change(sectionInput, { target: { value: 'Game Rules' } });
    
    expect(sectionInput).toHaveValue('Game Rules');
  });

  it('handles order input with valid numbers', () => {
    render(<MetadataForm />);
    
    const orderInput = screen.getByLabelText(/Order/i);
    fireEvent.change(orderInput, { target: { value: '10' } });
    
    expect(orderInput).toHaveValue(10);
  });

  it('rejects negative order values', () => {
    render(<MetadataForm />);
    
    const orderInput = screen.getByLabelText(/Order/i);
    fireEvent.change(orderInput, { target: { value: '-5' } });
    
    // Should not accept negative values
    expect(orderInput).not.toHaveValue(-5);
  });

  it('handles status toggle', () => {
    render(<MetadataForm initialData={{ status: 'draft' }} />);
    
    expect(screen.getByLabelText(/Draft/i)).toBeChecked();
    expect(screen.getByLabelText(/Published/i)).not.toBeChecked();
    
    fireEvent.click(screen.getByLabelText(/Published/i));
    
    expect(screen.getByLabelText(/Published/i)).toBeChecked();
    expect(screen.getByLabelText(/Draft/i)).not.toBeChecked();
  });

  it('displays error messages', () => {
    const errors = {
      title: 'Title is required',
      slug: 'Slug is invalid',
      parent_id: 'Parent not found',
      section: 'Invalid section',
      order: 'Order must be positive',
      status: 'Invalid status',
    };

    render(<MetadataForm errors={errors} />);
    
    expect(screen.getByText('Title is required')).toBeInTheDocument();
    expect(screen.getByText('Slug is invalid')).toBeInTheDocument();
    expect(screen.getByText('Parent not found')).toBeInTheDocument();
    expect(screen.getByText('Invalid section')).toBeInTheDocument();
    expect(screen.getByText('Order must be positive')).toBeInTheDocument();
    expect(screen.getByText('Invalid status')).toBeInTheDocument();
  });

  it('applies error styling to inputs with errors', () => {
    const errors = {
      title: 'Title is required',
    };

    render(<MetadataForm errors={errors} />);
    
    const titleInput = screen.getByLabelText(/Title/i);
    expect(titleInput).toHaveClass('arc-metadata-form-input-error');
  });

  it('handles empty search results', async () => {
    pagesApi.searchPages.mockResolvedValue([]);
    
    render(<MetadataForm />);
    
    const parentInput = screen.getByPlaceholderText(/Search for parent page/i);
    fireEvent.change(parentInput, { target: { value: 'Nonexistent' } });
    
    await waitFor(() => {
      expect(screen.getByText(/No pages found/i)).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('closes dropdown when clicking outside', async () => {
    const mockPages = [
      { id: 'page-1', title: 'Parent Page 1' },
    ];
    pagesApi.searchPages.mockResolvedValue(mockPages);
    
    render(<MetadataForm />);
    
    const parentInput = screen.getByPlaceholderText(/Search for parent page/i);
    fireEvent.change(parentInput, { target: { value: 'Parent' } });
    
    await waitFor(() => {
      expect(screen.getByText('Parent Page 1')).toBeInTheDocument();
    });
    
    // Click outside
    fireEvent.mouseDown(document.body);
    
    await waitFor(() => {
      expect(screen.queryByText('Parent Page 1')).not.toBeInTheDocument();
    });
  });

  it('debounces slug validation', async () => {
    pagesApi.validateSlug.mockResolvedValue({ valid: true });
    
    render(<MetadataForm />);
    
    const slugInput = screen.getByLabelText(/Slug/i);
    fireEvent.change(slugInput, { target: { value: 'test' } });
    
    // Wait for debounce delay plus a bit
    await waitFor(() => {
      // Should call validateSlug after debounce
      expect(pagesApi.validateSlug).toHaveBeenCalled();
    }, { timeout: 2000 });
  });

  it('debounces parent search', async () => {
    pagesApi.searchPages.mockResolvedValue([]);
    
    render(<MetadataForm />);
    
    const parentInput = screen.getByPlaceholderText(/Search for parent page/i);
    fireEvent.change(parentInput, { target: { value: 'Parent' } });
    
    // Wait for debounce delay plus a bit
    await waitFor(() => {
      // Should call searchPages after debounce
      expect(pagesApi.searchPages).toHaveBeenCalled();
    }, { timeout: 2000 });
  });

  it('excludes current page from slug validation', async () => {
    pagesApi.validateSlug.mockResolvedValue({ valid: true });
    
    render(<MetadataForm excludePageId="current-page-id" />);
    
    const slugInput = screen.getByLabelText(/Slug/i);
    fireEvent.change(slugInput, { target: { value: 'test-slug' } });
    
    await waitFor(() => {
      expect(pagesApi.validateSlug).toHaveBeenCalledWith('test-slug', 'current-page-id');
    }, { timeout: 1000 });
  });

  it('updates form when initialData changes', () => {
    const { rerender } = render(<MetadataForm initialData={{ title: 'Initial' }} />);
    
    expect(screen.getByDisplayValue('Initial')).toBeInTheDocument();
    
    rerender(<MetadataForm initialData={{ title: 'Updated' }} />);
    
    expect(screen.getByDisplayValue('Updated')).toBeInTheDocument();
  });

  it('handles null/undefined initial data gracefully', () => {
    render(<MetadataForm initialData={null} />);
    
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Slug/i)).toBeInTheDocument();
    
    // Form should render without errors
    expect(screen.getByTestId).toBeDefined();
  });

  it('handles undefined initial data', () => {
    render(<MetadataForm initialData={undefined} />);
    
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Slug/i)).toBeInTheDocument();
  });

  it('shows help text for order field', () => {
    render(<MetadataForm />);
    
    expect(screen.getByText(/Lower numbers appear first/i)).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    pagesApi.validateSlug.mockRejectedValue(new Error('Network error'));
    
    render(<MetadataForm />);
    
    const slugInput = screen.getByLabelText(/Slug/i);
    fireEvent.change(slugInput, { target: { value: 'test' } });
    
    // Should not crash on error
    await waitFor(() => {
      expect(screen.getByLabelText(/Slug/i)).toBeInTheDocument();
    });
  });

  it('does not auto-generate slug if slug was manually edited', async () => {
    slugUtils.generateSlug.mockReturnValue('auto-generated-slug');

    render(<MetadataForm isNewPage={true} />);

    const titleInput = screen.getByLabelText(/Title/i);
    const slugInput = screen.getByLabelText(/Slug/i);

    // Set title - should auto-generate slug
    fireEvent.change(titleInput, { target: { value: 'New Title' } });
    
    // Wait for slug to be generated
    await waitFor(() => {
      expect(slugInput).toHaveValue('auto-generated-slug');
    });

    // Manually edit slug
    fireEvent.change(slugInput, { target: { value: 'custom-slug' } });

    // Change title again - slug should NOT change (because it was manually edited)
    fireEvent.change(titleInput, { target: { value: 'Updated Title' } });

    // Wait a bit to ensure no auto-generation happens
    await waitFor(() => {
      expect(slugInput).toHaveValue('custom-slug');
    }, { timeout: 500 });
  });

  it('handles order input with decimal values', () => {
    render(<MetadataForm />);

    const orderInput = screen.getByLabelText(/Order/i);
    fireEvent.change(orderInput, { target: { value: '10.5' } });

    // The component accepts the input but parseInt converts it to integer
    // The input value will be '10.5' as a string, but parseInt will be used for validation
    // Since the component allows it (parseInt('10.5') = 10 >= 0), the value stays
    // This test checks that decimals are handled (they're converted to int in processing)
    expect(orderInput).toHaveValue('10.5');
  });

  it('handles very long section names', () => {
    const longSection = 'A'.repeat(200);
    
    render(<MetadataForm />);
    
    const sectionInput = screen.getByLabelText(/Section/i);
    fireEvent.change(sectionInput, { target: { value: longSection } });
    
    expect(sectionInput).toHaveValue(longSection);
  });

  it('handles parent selection with multiple pages', async () => {
    const mockPages = [
      { id: 'page-1', title: 'Page 1', section: 'Section 1' },
      { id: 'page-2', title: 'Page 2', section: 'Section 1' },
      { id: 'page-3', title: 'Page 3', section: 'Section 2' },
    ];
    pagesApi.searchPages.mockResolvedValue(mockPages);
    
    render(<MetadataForm />);
    
    const parentInput = screen.getByPlaceholderText(/Search for parent page/i);
    fireEvent.change(parentInput, { target: { value: 'Page' } });
    
    await waitFor(() => {
      expect(screen.getByText('Page 1')).toBeInTheDocument();
      expect(screen.getByText('Page 2')).toBeInTheDocument();
      expect(screen.getByText('Page 3')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('handles parent page with no section', async () => {
    const mockPages = [
      { id: 'page-1', title: 'Page Without Section' },
    ];
    pagesApi.searchPages.mockResolvedValue(mockPages);
    
    render(<MetadataForm />);
    
    const parentInput = screen.getByPlaceholderText(/Search for parent page/i);
    fireEvent.change(parentInput, { target: { value: 'Page' } });
    
    await waitFor(() => {
      expect(screen.getByText('Page Without Section')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('handles status change from draft to published', () => {
    render(<MetadataForm initialData={{ status: 'draft' }} />);
    
    expect(screen.getByLabelText(/Draft/i)).toBeChecked();
    
    fireEvent.click(screen.getByLabelText(/Published/i));
    
    expect(screen.getByLabelText(/Published/i)).toBeChecked();
    expect(screen.getByLabelText(/Draft/i)).not.toBeChecked();
  });

  it('handles order value of zero', () => {
    render(<MetadataForm initialData={{ order: 0 }} />);
    
    const orderInput = screen.getByLabelText(/Order/i);
    expect(orderInput).toHaveValue(0);
  });

  it('handles empty order value', () => {
    // When order is null, the component should handle it gracefully
    // The initial state sets order to '' if order is undefined, but null might cause issues
    render(<MetadataForm initialData={{ order: undefined }} />);

    const orderInput = screen.getByLabelText(/Order/i);
    // When order is undefined, it defaults to empty string
    expect(orderInput).toHaveValue('');
  });

  it('prevents negative order values', () => {
    render(<MetadataForm />);
    
    const orderInput = screen.getByLabelText(/Order/i);
    fireEvent.change(orderInput, { target: { value: '-5' } });
    
    // Should not accept negative values
    expect(orderInput).not.toHaveValue(-5);
  });

  it('handles slug with only numbers', async () => {
    pagesApi.validateSlug.mockResolvedValue({ valid: true });
    
    render(<MetadataForm />);
    
    const slugInput = screen.getByLabelText(/Slug/i);
    fireEvent.change(slugInput, { target: { value: '123' } });
    
    await waitFor(() => {
      expect(pagesApi.validateSlug).toHaveBeenCalledWith('123', null);
    }, { timeout: 2000 });
  });

  it('handles slug with only hyphens', async () => {
    pagesApi.validateSlug.mockResolvedValue({ 
      valid: false, 
      message: 'Slug can only contain lowercase letters, numbers, and hyphens' 
    });
    
    render(<MetadataForm />);
    
    const slugInput = screen.getByLabelText(/Slug/i);
    fireEvent.change(slugInput, { target: { value: '---' } });
    
    await waitFor(() => {
      expect(pagesApi.validateSlug).toHaveBeenCalled();
    }, { timeout: 2000 });
  });
});
