import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CommentItem } from '../../components/comments/CommentItem';
import { useAuth } from '../../services/auth/AuthContext';

// Mock Auth
vi.mock('../../services/auth/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock date-fns
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn((date, options) => {
    return '2 hours ago';
  }),
}));

describe('CommentItem', () => {
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

  const mockComment = {
    id: 'comment-1',
    user: { id: 'user-1', username: 'testuser' },
    content: 'Test comment content',
    is_recommendation: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    replies: [],
  };

  const renderCommentItem = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CommentItem
            comment={props.comment || mockComment}
            onReply={props.onReply || vi.fn()}
            onEdit={props.onEdit || vi.fn()}
            onDelete={props.onDelete || vi.fn()}
            depth={props.depth || 0}
            pageId={props.pageId || 'page-1'}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  it('renders comment content', () => {
    renderCommentItem();
    expect(screen.getByText('Test comment content')).toBeInTheDocument();
  });

  it('renders username', () => {
    renderCommentItem();
    expect(screen.getByText('testuser')).toBeInTheDocument();
  });

  it('renders timestamp', () => {
    renderCommentItem();
    expect(screen.getByText(/2 hours ago/i)).toBeInTheDocument();
  });

  it('shows recommendation badge for recommendations', () => {
    const comment = { ...mockComment, is_recommendation: true };
    renderCommentItem({ comment });
    const commentItem = screen.getByText('Test comment content').closest('.arc-comment-item');
    expect(commentItem).toHaveClass('arc-comment-recommendation');
  });

  it('shows edit and delete buttons for comment owner', () => {
    renderCommentItem();
    expect(screen.getByText('Edit')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('does not show edit/delete buttons for non-owner', () => {
    useAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 'user-2', username: 'otheruser', role: 'player' },
    });

    renderCommentItem();
    expect(screen.queryByText('Edit')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete')).not.toBeInTheDocument();
  });

  it('shows reply button when depth allows', () => {
    renderCommentItem({ depth: 0 });
    expect(screen.getByText('Reply')).toBeInTheDocument();
  });

  it('hides reply button at max depth', () => {
    renderCommentItem({ depth: 4 }); // Max depth is 5, so depth 4 can't reply
    expect(screen.queryByText('Reply')).not.toBeInTheDocument();
  });

  it('opens reply form when reply button is clicked', async () => {
    const user = userEvent.setup();
    renderCommentItem();

    const replyButton = screen.getByText('Reply');
    await user.click(replyButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Write a reply/i)).toBeInTheDocument();
    });
  });

  it('opens edit form when edit button is clicked', async () => {
    const user = userEvent.setup();
    renderCommentItem();

    const editButton = screen.getByText('Edit');
    await user.click(editButton);

    await waitFor(() => {
      const textarea = screen.getByDisplayValue('Test comment content');
      expect(textarea).toBeInTheDocument();
      expect(screen.getByText('Save')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
  });

  it('calls onDelete when delete button is clicked', async () => {
    const onDelete = vi.fn();
    window.confirm = vi.fn(() => true);

    const user = userEvent.setup();
    renderCommentItem({ onDelete });

    const deleteButton = screen.getByText('Delete');
    await user.click(deleteButton);

    expect(window.confirm).toHaveBeenCalled();
    expect(onDelete).toHaveBeenCalledWith('comment-1');
  });

  it('displays nested replies', () => {
    const comment = {
      ...mockComment,
      replies: [
        {
          id: 'comment-2',
          user: { id: 'user-2', username: 'user2' },
          content: 'Reply content',
          is_recommendation: false,
          created_at: '2024-01-01T01:00:00Z',
          updated_at: '2024-01-01T01:00:00Z',
          replies: [],
        },
      ],
    };

    renderCommentItem({ comment });
    expect(screen.getByText('Reply content')).toBeInTheDocument();
    expect(screen.getByText(/1 reply/i)).toBeInTheDocument();
  });

  it('toggles replies visibility', async () => {
    const user = userEvent.setup();
    const comment = {
      ...mockComment,
      replies: [
        {
          id: 'comment-2',
          user: { id: 'user-2', username: 'user2' },
          content: 'Reply content',
          is_recommendation: false,
          created_at: '2024-01-01T01:00:00Z',
          updated_at: '2024-01-01T01:00:00Z',
          replies: [],
        },
      ],
    };

    renderCommentItem({ comment });

    // Replies should be visible by default
    expect(screen.getByText('Reply content')).toBeInTheDocument();

    // Click toggle
    const toggleButton = screen.getByText(/1 reply/i);
    await user.click(toggleButton);

    // Replies should be hidden
    await waitFor(() => {
      expect(screen.queryByText('Reply content')).not.toBeInTheDocument();
    });
  });

  it('shows edited indicator when updated_at differs from created_at', () => {
    const comment = {
      ...mockComment,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T02:00:00Z',
    };

    renderCommentItem({ comment });
    expect(screen.getByText('(edited)')).toBeInTheDocument();
  });

  it('does not show edited indicator when dates match', () => {
    renderCommentItem();
    expect(screen.queryByText('(edited)')).not.toBeInTheDocument();
  });
});
