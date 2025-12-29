import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CommentForm } from '../../components/comments/CommentForm';
import { useAuth } from '../../services/auth/AuthContext';

// Mock Auth
vi.mock('../../services/auth/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('CommentForm', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();

    useAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 'user-1', username: 'testuser', role: 'player' },
    });
  });

  const renderCommentForm = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CommentForm
            pageId={props.pageId || 'page-1'}
            parentCommentId={props.parentCommentId || null}
            onSubmit={props.onSubmit || vi.fn().mockResolvedValue({})}
            onCancel={props.onCancel || vi.fn()}
            initialContent={props.initialContent || ''}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  it('renders comment form', () => {
    renderCommentForm();
    expect(screen.getByPlaceholderText(/Write a comment/i)).toBeInTheDocument();
  });

  it('renders reply form when parentCommentId is provided', () => {
    renderCommentForm({ parentCommentId: 'comment-1' });
    expect(screen.getByPlaceholderText(/Write a reply/i)).toBeInTheDocument();
  });

  it('shows sign-in prompt when not authenticated', () => {
    useAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
    });

    renderCommentForm();
    expect(screen.getByText(/Please sign in to leave a comment/i)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/Write a comment/i)).not.toBeInTheDocument();
  });

  it('shows recommendation checkbox for players', () => {
    useAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 'user-1', username: 'testuser', role: 'player' },
    });

    renderCommentForm();
    expect(screen.getByLabelText(/Recommend update/i)).toBeInTheDocument();
  });

  it('does not show recommendation checkbox for non-players', () => {
    useAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 'user-1', username: 'testuser', role: 'writer' },
    });

    renderCommentForm();
    expect(screen.queryByLabelText(/Recommend update/i)).not.toBeInTheDocument();
  });

  it('calls onSubmit with correct data when form is submitted', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue({});

    renderCommentForm({ onSubmit });

    const textarea = screen.getByPlaceholderText(/Write a comment/i);
    await user.type(textarea, 'Test comment');

    const submitButton = screen.getByText('Post Comment');
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        content: 'Test comment',
        is_recommendation: false,
        parent_comment_id: null,
      });
    });
  });

  it('includes recommendation flag when checkbox is checked', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue({});

    renderCommentForm({ onSubmit });

    const checkbox = screen.getByLabelText(/Recommend update/i);
    await user.click(checkbox);

    const textarea = screen.getByPlaceholderText(/Write a comment/i);
    await user.type(textarea, 'Recommendation comment');

    const submitButton = screen.getByText('Post Comment');
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        content: 'Recommendation comment',
        is_recommendation: true,
        parent_comment_id: null,
      });
    });
  });

  it('includes parent_comment_id for replies', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue({});

    renderCommentForm({ parentCommentId: 'comment-1', onSubmit });

    const textarea = screen.getByPlaceholderText(/Write a reply/i);
    await user.type(textarea, 'Reply content');

    const submitButton = screen.getByText('Post Reply');
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        content: 'Reply content',
        is_recommendation: false,
        parent_comment_id: 'comment-1',
      });
    });
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    renderCommentForm({ onCancel });

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(onCancel).toHaveBeenCalled();
  });

  it('shows cancel button when onCancel is provided', () => {
    renderCommentForm({ onCancel: vi.fn() });
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('handles undefined onCancel gracefully', () => {
    // Component should work even if onCancel is undefined
    // Cancel button may or may not appear - component handles both cases
    renderCommentForm({ onCancel: undefined });
    expect(screen.getByPlaceholderText(/Write a comment/i)).toBeInTheDocument();
    // Form should be functional regardless of cancel button presence
    expect(screen.getByText('Post Comment')).toBeInTheDocument();
  });

  it('disables submit button when content is empty', () => {
    renderCommentForm();
    const submitButton = screen.getByText('Post Comment');
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when content is entered', async () => {
    const user = userEvent.setup();
    renderCommentForm();

    const textarea = screen.getByPlaceholderText(/Write a comment/i);
    await user.type(textarea, 'Test');

    const submitButton = screen.getByText('Post Comment');
    expect(submitButton).not.toBeDisabled();
  });

  it('shows error message on submission failure', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockRejectedValue(new Error('Network error'));

    renderCommentForm({ onSubmit });

    const textarea = screen.getByPlaceholderText(/Write a comment/i);
    await user.type(textarea, 'Test comment');

    const submitButton = screen.getByText('Post Comment');
    await user.click(submitButton);

    await waitFor(() => {
      // Error message should appear (could be "Network error" or "Failed to submit comment")
      const errorElement = screen.queryByText(/Network error|Failed to submit comment/i);
      expect(errorElement).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('trims content before submission', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue({});

    renderCommentForm({ onSubmit });

    const textarea = screen.getByPlaceholderText(/Write a comment/i);
    await user.type(textarea, '  Test comment  ');

    const submitButton = screen.getByText('Post Comment');
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          content: 'Test comment', // Should be trimmed
        })
      );
    });
  });

  it('resets form after successful submission', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue({});

    renderCommentForm({ onSubmit });

    const textarea = screen.getByPlaceholderText(/Write a comment/i);
    await user.type(textarea, 'Test comment');

    const submitButton = screen.getByText('Post Comment');
    await user.click(submitButton);

    await waitFor(() => {
      expect(textarea).toHaveValue('');
    });
  });
});
