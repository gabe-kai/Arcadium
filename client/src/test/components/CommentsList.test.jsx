import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CommentsList } from '../../components/comments/CommentsList';
import { useComments, useCreateComment, useUpdateComment, useDeleteComment } from '../../services/api/comments';
import { useAuth } from '../../services/auth/AuthContext';

// Mock API
vi.mock('../../services/api/comments', () => ({
  useComments: vi.fn(),
  useCreateComment: vi.fn(),
  useUpdateComment: vi.fn(),
  useDeleteComment: vi.fn(),
}));

// Mock Auth
vi.mock('../../services/auth/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('CommentsList', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();

    // Default mocks
    useAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 'user-1', username: 'testuser', role: 'player' },
    });

    useComments.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    useCreateComment.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({}),
      isError: false,
      error: null,
    });

    useUpdateComment.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({}),
    });

    useDeleteComment.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({}),
    });
  });

  const renderCommentsList = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CommentsList pageId="page-1" comments={props.comments || []} />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  it('renders comments section title', () => {
    renderCommentsList();
    expect(screen.getByText('Comments')).toBeInTheDocument();
  });

  it('displays sign-in prompt when not authenticated', () => {
    useAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
    });

    renderCommentsList();
    expect(screen.getByText(/Please sign in to view and leave comments/i)).toBeInTheDocument();
  });

  it('displays comment form when authenticated', () => {
    renderCommentsList();
    expect(screen.getByPlaceholderText(/Write a comment/i)).toBeInTheDocument();
  });

  it('displays empty state when no comments', () => {
    renderCommentsList();
    expect(screen.getByText(/No comments yet/i)).toBeInTheDocument();
  });

  it('displays comments list when comments exist', () => {
    const comments = [
      {
        id: 'comment-1',
        user: { id: 'user-1', username: 'user1' },
        content: 'First comment',
        is_recommendation: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        replies: [],
      },
    ];

    renderCommentsList({ comments });
    expect(screen.getByText('First comment')).toBeInTheDocument();
    expect(screen.getByText('user1')).toBeInTheDocument();
  });

  it('displays nested replies', () => {
    const comments = [
      {
        id: 'comment-1',
        user: { id: 'user-1', username: 'user1' },
        content: 'Parent comment',
        is_recommendation: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        replies: [
          {
            id: 'comment-2',
            user: { id: 'user-2', username: 'user2' },
            content: 'Reply comment',
            is_recommendation: false,
            created_at: '2024-01-01T01:00:00Z',
            updated_at: '2024-01-01T01:00:00Z',
            replies: [],
          },
        ],
      },
    ];

    renderCommentsList({ comments });
    expect(screen.getByText('Parent comment')).toBeInTheDocument();
    expect(screen.getByText('Reply comment')).toBeInTheDocument();
  });

  it('displays recommendation badge for recommendations', () => {
    const comments = [
      {
        id: 'comment-1',
        user: { id: 'user-1', username: 'user1' },
        content: 'Recommendation comment',
        is_recommendation: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        replies: [],
      },
    ];

    renderCommentsList({ comments });
    expect(screen.getByText('Recommendation comment')).toBeInTheDocument();
    // Recommendation badge should be present (💡 emoji)
    const commentItem = screen.getByText('Recommendation comment').closest('.arc-comment-item');
    expect(commentItem).toHaveClass('arc-comment-recommendation');
  });
});
