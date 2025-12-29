import React, { useState, useMemo } from 'react';
import { CommentItem } from './CommentItem';
import { CommentForm } from './CommentForm';
import { useCreateComment, useUpdateComment, useDeleteComment } from '../../services/api/comments';
import { useAuth } from '../../services/auth/AuthContext';
import './CommentsList.css';

const COMMENTS_PER_PAGE = 10;

/**
 * CommentsList component - Displays all comments for a page with threading
 *
 * Features:
 * - Threaded comments display
 * - Pagination for long threads
 * - Load more / page navigation
 */
export function CommentsList({ pageId, comments = [] }) {
  const { isAuthenticated } = useAuth();
  const [currentPage, setCurrentPage] = useState(1);
  const createCommentMutation = useCreateComment(pageId);
  const updateCommentMutation = useUpdateComment(pageId);
  const deleteCommentMutation = useDeleteComment(pageId);

  // Paginate top-level comments only (replies are always shown)
  const topLevelComments = useMemo(() => {
    return comments.filter((comment) => !comment.parent_comment_id);
  }, [comments]);

  const totalPages = Math.ceil(topLevelComments.length / COMMENTS_PER_PAGE);
  const paginatedComments = useMemo(() => {
    const startIndex = (currentPage - 1) * COMMENTS_PER_PAGE;
    const endIndex = startIndex + COMMENTS_PER_PAGE;
    return topLevelComments.slice(startIndex, endIndex);
  }, [topLevelComments, currentPage]);

  // Reset to page 1 when comments change (e.g., after new comment)
  React.useEffect(() => {
    setCurrentPage(1);
  }, [pageId]);

  const handleReply = async (parentCommentId, commentData) => {
    if (commentData) {
      // This is a reply submission
      await createCommentMutation.mutateAsync(commentData);
    }
    // If no commentData, it's just opening the reply form (handled by CommentItem)
  };

  const handleSubmitComment = async (commentData) => {
    await createCommentMutation.mutateAsync(commentData);
  };

  const handleEdit = async (commentId, content) => {
    await updateCommentMutation.mutateAsync({ commentId, content });
  };

  const handleDelete = async (commentId) => {
    await deleteCommentMutation.mutateAsync(commentId);
  };

  return (
    <section className="arc-comments-section" aria-label="Comments">
      <h2 className="arc-comments-title">Comments</h2>

      {!isAuthenticated && (
        <div className="arc-comments-signin-prompt">
          <p>Please sign in to view and leave comments.</p>
        </div>
      )}

      {isAuthenticated && (
        <div className="arc-comments-form-wrapper">
          <CommentForm
            pageId={pageId}
            onSubmit={handleSubmitComment}
          />
        </div>
      )}

      {comments.length === 0 ? (
        <div className="arc-comments-empty">
          <p>No comments yet. Be the first to comment!</p>
        </div>
      ) : (
        <>
          <div className="arc-comments-list">
            {paginatedComments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                onReply={handleReply}
                onEdit={handleEdit}
                onDelete={handleDelete}
                depth={0}
                pageId={pageId}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="arc-comments-pagination">
              <button
                type="button"
                className="arc-comments-pagination-button"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                aria-label="Previous page"
              >
                Previous
              </button>

              <span className="arc-comments-pagination-info">
                Page {currentPage} of {totalPages} ({topLevelComments.length} comment{topLevelComments.length !== 1 ? 's' : ''})
              </span>

              <button
                type="button"
                className="arc-comments-pagination-button"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                aria-label="Next page"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {createCommentMutation.isError && (
        <div className="arc-comments-error">
          {createCommentMutation.error?.response?.data?.error || 'Failed to create comment'}
        </div>
      )}
    </section>
  );
}
