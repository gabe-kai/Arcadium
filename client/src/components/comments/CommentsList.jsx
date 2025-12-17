import React, { useState } from 'react';
import { CommentItem } from './CommentItem';
import { CommentForm } from './CommentForm';
import { useCreateComment, useUpdateComment, useDeleteComment } from '../../services/api/comments';
import { useAuth } from '../../services/auth/AuthContext';
import './CommentsList.css';

/**
 * CommentsList component - Displays all comments for a page with threading
 */
export function CommentsList({ pageId, comments = [] }) {
  const { isAuthenticated } = useAuth();
  const createCommentMutation = useCreateComment(pageId);
  const updateCommentMutation = useUpdateComment(pageId);
  const deleteCommentMutation = useDeleteComment(pageId);

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
        <div className="arc-comments-list">
          {comments.map((comment) => (
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
      )}

      {createCommentMutation.isError && (
        <div className="arc-comments-error">
          {createCommentMutation.error?.response?.data?.error || 'Failed to create comment'}
        </div>
      )}
    </section>
  );
}
