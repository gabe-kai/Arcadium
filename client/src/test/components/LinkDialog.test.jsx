import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LinkDialog } from '../../components/editor/LinkDialog';
import * as pagesApi from '../../services/api/pages';

// Mock the API
vi.mock('../../services/api/pages', () => ({
  searchPages: vi.fn(),
}));

describe('LinkDialog', () => {
  const mockOnClose = vi.fn();
  const mockOnInsert = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    render(
      <LinkDialog
        isOpen={false}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    expect(screen.queryByText('Insert Link')).not.toBeInTheDocument();
  });

  it('renders dialog when isOpen is true', () => {
    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    // Dialog should be visible - check for heading (h3) to avoid multiple matches
    expect(screen.getByRole('heading', { name: 'Insert Link' })).toBeInTheDocument();
  });

  it('closes dialog when close button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const closeButton = screen.getByLabelText('Close');
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('closes dialog when clicking outside', async () => {
    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const overlay = document.querySelector('.arc-link-dialog-overlay');
    fireEvent.mouseDown(overlay);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('displays external URL input by default', () => {
    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    expect(screen.getByLabelText(/URL:/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/https:\/\/example.com/i)).toBeInTheDocument();
  });

  it('switches to internal page search when internal radio is selected', async () => {
    const user = userEvent.setup();
    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const internalRadio = screen.getByLabelText(/Internal Page/i);
    await user.click(internalRadio);

    expect(screen.getByLabelText(/Search for page:/i)).toBeInTheDocument();
  });

  it('searches pages when typing in internal search', async () => {
    const user = userEvent.setup();
    pagesApi.searchPages.mockResolvedValue([
      { id: 'page-1', title: 'Test Page', slug: 'test-page', section: 'test' },
    ]);

    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const internalRadio = screen.getByLabelText(/Internal Page/i);
    await user.click(internalRadio);

    const searchInput = screen.getByPlaceholderText(/Type to search pages/i);
    await user.type(searchInput, 'test');

    await waitFor(() => {
      expect(pagesApi.searchPages).toHaveBeenCalledWith('test');
    }, { timeout: 1000 });
  });

  it('displays search results when pages are found', async () => {
    const user = userEvent.setup();
    pagesApi.searchPages.mockResolvedValue([
      { id: 'page-1', title: 'Test Page', slug: 'test-page', section: 'test' },
      { id: 'page-2', title: 'Another Page', slug: 'another', section: null },
    ]);

    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const internalRadio = screen.getByLabelText(/Internal Page/i);
    await user.click(internalRadio);

    const searchInput = screen.getByPlaceholderText(/Type to search pages/i);
    await user.type(searchInput, 'test');

    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
      expect(screen.getByText('Another Page')).toBeInTheDocument();
    });
  });

  it('selects page when clicking on search result', async () => {
    const user = userEvent.setup();
    pagesApi.searchPages.mockResolvedValue([
      { id: 'page-1', title: 'Test Page', slug: 'test-page', section: 'test' },
    ]);

    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const internalRadio = screen.getByLabelText(/Internal Page/i);
    await user.click(internalRadio);

    const searchInput = screen.getByPlaceholderText(/Type to search pages/i);
    await user.type(searchInput, 'test');

    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });

    const resultItem = screen.getByText('Test Page').closest('button');
    await user.click(resultItem);

    const urlInput = screen.getByPlaceholderText(/\/pages\/page-id/i);
    expect(urlInput).toHaveValue('/pages/page-1');
  });

  it('displays "No pages found" when search returns empty', async () => {
    const user = userEvent.setup();
    pagesApi.searchPages.mockResolvedValue([]);

    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const internalRadio = screen.getByLabelText(/Internal Page/i);
    await user.click(internalRadio);

    const searchInput = screen.getByPlaceholderText(/Type to search pages/i);
    await user.type(searchInput, 'nonexistent');

    await waitFor(() => {
      expect(screen.getByText('No pages found')).toBeInTheDocument();
    });
  });

  it('inserts external URL when form is submitted', async () => {
    const user = userEvent.setup();
    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const urlInput = screen.getByPlaceholderText(/https:\/\/example.com/i);
    await user.type(urlInput, 'https://example.com');

    const insertButton = screen.getByRole('button', { name: 'Insert Link' });
    await user.click(insertButton);

    expect(mockOnInsert).toHaveBeenCalledWith('https://example.com');
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('inserts internal page URL when form is submitted', async () => {
    const user = userEvent.setup();
    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const internalRadio = screen.getByLabelText(/Internal Page/i);
    await user.click(internalRadio);

    const urlInput = screen.getByPlaceholderText(/\/pages\/page-id/i);
    await user.type(urlInput, '/pages/page-1');

    const insertButton = screen.getByRole('button', { name: 'Insert Link' });
    await user.click(insertButton);

    expect(mockOnInsert).toHaveBeenCalledWith('/pages/page-1');
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('disables insert button when URL is empty', () => {
    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    // "Insert Link" appears in header (h3) and button - get the submit button specifically
    const submitButton = screen.getByRole('button', { name: 'Insert Link' });
    expect(submitButton).toBeDisabled();
  });

  it('pre-fills URL from initialUrl prop', () => {
    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
        initialUrl="https://example.com"
      />
    );

    const urlInput = screen.getByPlaceholderText(/https:\/\/example.com/i);
    expect(urlInput).toHaveValue('https://example.com');
  });

  it('debounces search requests', async () => {
    const user = userEvent.setup();
    pagesApi.searchPages.mockResolvedValue([]);

    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const internalRadio = screen.getByLabelText(/Internal Page/i);
    await user.click(internalRadio);

    const searchInput = screen.getByPlaceholderText(/Type to search pages/i);
    await user.type(searchInput, 'test', { delay: 50 });

    // Should debounce, so not called immediately
    await waitFor(() => {
      expect(pagesApi.searchPages).toHaveBeenCalled();
    }, { timeout: 500 });

    // Should only be called once after debounce
    expect(pagesApi.searchPages).toHaveBeenCalledTimes(1);
  });

  it('handles search errors gracefully', async () => {
    const user = userEvent.setup();
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    pagesApi.searchPages.mockRejectedValue(new Error('Search failed'));

    render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const internalRadio = screen.getByLabelText(/Internal Page/i);
    await user.click(internalRadio);

    const searchInput = screen.getByPlaceholderText(/Type to search pages/i);
    await user.type(searchInput, 'test');

    // Should not crash on error - wait for search to be called
    await waitFor(() => {
      expect(pagesApi.searchPages).toHaveBeenCalled();
    }, { timeout: 1000 });

    // Error should be logged but component should still be functional
    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it('resets state when dialog closes and reopens', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    const urlInput = screen.getByPlaceholderText(/https:\/\/example.com/i);
    await user.type(urlInput, 'https://test.com');

    // Close dialog
    rerender(
      <LinkDialog
        isOpen={false}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    // Reopen dialog
    rerender(
      <LinkDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );

    // URL should be reset
    const newUrlInput = screen.getByPlaceholderText(/https:\/\/example.com/i);
    expect(newUrlInput).toHaveValue('');
  });
});
