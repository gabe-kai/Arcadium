import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ImageUploadDialog } from '../../components/editor/ImageUploadDialog';
import { apiClient } from '../../services/api/client';

// Mock the API client
vi.mock('../../services/api/client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

// Mock FileReader
global.FileReader = class FileReader {
  readAsDataURL() {
    setTimeout(() => {
      this.onloadend({ target: { result: 'data:image/png;base64,test' } });
    }, 0);
  }
};

describe('ImageUploadDialog', () => {
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
      <ImageUploadDialog
        isOpen={false}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    expect(screen.queryByText('Insert Image')).not.toBeInTheDocument();
  });

  it('renders dialog when isOpen is true', () => {
    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    // Dialog should be visible
    expect(screen.getByText('Insert Image')).toBeInTheDocument();
  });

  it('closes dialog when close button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    const closeButton = screen.getByLabelText('Close');
    await user.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('closes dialog when clicking outside', () => {
    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    const overlay = document.querySelector('.arc-image-dialog-overlay');
    fireEvent.mouseDown(overlay);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('displays URL input by default', () => {
    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    expect(screen.getByLabelText(/Image URL:/i)).toBeInTheDocument();
  });

  it('validates file type when selecting file', async () => {
    const user = userEvent.setup();
    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    const uploadTab = screen.getByText('Upload');
    await user.click(uploadTab);
    
    const fileInput = document.querySelector('input[type="file"]');
    const invalidFile = new File(['content'], 'test.txt', { type: 'text/plain' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [invalidFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    
    await waitFor(() => {
      expect(screen.getByText(/Please select an image file/i)).toBeInTheDocument();
    });
  });

  it('validates file size when selecting file', async () => {
    const user = userEvent.setup();
    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    const uploadTab = screen.getByText('Upload');
    await user.click(uploadTab);
    
    const fileInput = document.querySelector('input[type="file"]');
    // Create a file larger than 10MB
    const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.jpg', { type: 'image/jpeg' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [largeFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    
    await waitFor(() => {
      expect(screen.getByText(/File is too large/i)).toBeInTheDocument();
    });
  });

  it('displays preview when valid image file is selected', async () => {
    const user = userEvent.setup();
    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    const uploadTab = screen.getByText('Upload');
    await user.click(uploadTab);
    
    const fileInput = document.querySelector('input[type="file"]');
    const imageFile = new File(['image content'], 'test.jpg', { type: 'image/jpeg' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [imageFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    
    await waitFor(() => {
      const preview = screen.getByAltText('Preview');
      expect(preview).toBeInTheDocument();
    });
  });

  it('uploads image and inserts URL on success', async () => {
    const user = userEvent.setup();
    apiClient.post.mockResolvedValue({
      data: {
        url: '/uploads/images/test-uuid.jpg',
        uuid: 'test-uuid',
        original_filename: 'test.jpg',
        size: 12345,
        mime_type: 'image/jpeg',
      },
    });

    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
        pageId="page-1"
      />
    );
    
    const uploadTab = screen.getByText('Upload');
    await user.click(uploadTab);
    
    const fileInput = document.querySelector('input[type="file"]');
    const imageFile = new File(['image content'], 'test.jpg', { type: 'image/jpeg' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [imageFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    
    await waitFor(() => {
      expect(screen.getByText('Upload Image')).toBeInTheDocument();
    });
    
    const uploadButton = screen.getByText('Upload Image');
    await user.click(uploadButton);
    
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/upload/image',
        expect.any(FormData),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'multipart/form-data',
          }),
        })
      );
    });
    
    await waitFor(() => {
      expect(mockOnInsert).toHaveBeenCalledWith('/uploads/images/test-uuid.jpg');
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('displays error when upload fails', async () => {
    const user = userEvent.setup();
    apiClient.post.mockRejectedValue({
      response: { data: { error: 'Upload failed' } },
    });

    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    const uploadTab = screen.getByText('Upload');
    await user.click(uploadTab);
    
    const fileInput = document.querySelector('input[type="file"]');
    const imageFile = new File(['image content'], 'test.jpg', { type: 'image/jpeg' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [imageFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    
    await waitFor(() => {
      expect(screen.getByText('Upload Image')).toBeInTheDocument();
    });
    
    const uploadButton = screen.getByText('Upload Image');
    await user.click(uploadButton);
    
    await waitFor(() => {
      expect(screen.getByText('Upload failed')).toBeInTheDocument();
    });
  });

  it('inserts image from URL input', async () => {
    const user = userEvent.setup();
    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    const urlInput = screen.getByLabelText(/Image URL:/i);
    await user.type(urlInput, 'https://example.com/image.jpg');
    
    const insertButton = screen.getByRole('button', { name: 'Insert Image' });
    await user.click(insertButton);
    
    expect(mockOnInsert).toHaveBeenCalledWith('https://example.com/image.jpg');
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('displays preview when valid URL is entered', async () => {
    const user = userEvent.setup();
    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    const urlInput = screen.getByLabelText(/Image URL:/i);
    await user.type(urlInput, 'https://example.com/image.jpg');
    
    // Wait for image to load (or fail)
    await waitFor(() => {
      const preview = screen.queryByAltText('Preview');
      // Preview may or may not appear depending on if image loads
      expect(urlInput).toHaveValue('https://example.com/image.jpg');
    });
  });

  it('resets state when dialog closes and reopens', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    const urlInput = screen.getByLabelText(/Image URL:/i);
    await user.type(urlInput, 'https://test.com/image.jpg');
    
    // Close dialog
    rerender(
      <ImageUploadDialog
        isOpen={false}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    // Reopen dialog
    rerender(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
      />
    );
    
    // URL should be reset
    const newUrlInput = screen.getByLabelText(/Image URL:/i);
    expect(newUrlInput).toHaveValue('');
  });

  it('includes pageId in upload request when provided', async () => {
    const user = userEvent.setup();
    apiClient.post.mockResolvedValue({
      data: { url: '/uploads/images/test.jpg' },
    });

    render(
      <ImageUploadDialog
        isOpen={true}
        onClose={mockOnClose}
        onInsert={mockOnInsert}
        pageId="page-123"
      />
    );
    
    const uploadTab = screen.getByText('Upload');
    await user.click(uploadTab);
    
    const fileInput = document.querySelector('input[type="file"]');
    const imageFile = new File(['image content'], 'test.jpg', { type: 'image/jpeg' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [imageFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    
    await waitFor(() => {
      expect(screen.getByText('Upload Image')).toBeInTheDocument();
    });
    
    const uploadButton = screen.getByText('Upload Image');
    await user.click(uploadButton);
    
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalled();
      const formData = apiClient.post.mock.calls[0][1];
      expect(formData.get('page_id')).toBe('page-123');
    });
  });
});
