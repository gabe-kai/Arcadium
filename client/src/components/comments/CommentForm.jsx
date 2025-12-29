import React, { useState, useEffect } from 'react';
import { useAuth } from '../../services/auth/AuthContext';
import './CommentsList.css';

/**
 * CommentForm component - Form for creating new comments or replies
 */
export function CommentForm({ pageId, parentCommentId = null, onSubmit, onCancel, initialContent = '' }) {
  const { isAuthenticated, user } = useAuth();
  const [content, setContent] = useState(initialContent);
  const [isRecommendation, setIsRecommendation] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setContent(initialContent);
  }, [initialContent, parentCommentId]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isAuthenticated) {
      setError('You must be signed in to comment');
      return;
    }

    if (!content.trim()) {
      setError('Comment cannot be empty');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onSubmit({
        content: content.trim(),
        is_recommendation: isRecommendation,
        parent_comment_id: parentCommentId,
      });

      // Reset form on success
      setContent('');
      setIsRecommendation(false);
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to submit comment');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setContent('');
    setIsRecommendation(false);
    setError(null);
    if (onCancel) {
      onCancel();
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="arc-comment-form-signin-prompt">
        <p>Please sign in to leave a comment.</p>
      </div>
    );
  }

  return (
    <form className="arc-comment-form" onSubmit={handleSubmit}>
      {error && <div className="arc-comment-form-error">{error}</div>}

      <div className="arc-comment-form-content">
        <textarea
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            setError(null);
          }}
          placeholder={parentCommentId ? 'Write a reply...' : 'Write a comment...'}
          className="arc-comment-form-textarea"
          rows={4}
          required
        />
      </div>

      <div className="arc-comment-form-options">
        {user?.role === 'player' && (
          <label className="arc-comment-form-recommendation">
            <input
              type="checkbox"
              checked={isRecommendation}
              onChange={(e) => setIsRecommendation(e.target.checked)}
            />
            <span>Recommend update</span>
          </label>
        )}
      </div>

      <div className="arc-comment-form-actions">
        {onCancel && (
          <button
            type="button"
            onClick={handleCancel}
            className="arc-comment-button arc-comment-button-cancel"
            disabled={isSubmitting}
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          className="arc-comment-button arc-comment-button-submit"
          disabled={isSubmitting || !content.trim()}
        >
          {isSubmitting ? 'Submitting...' : parentCommentId ? 'Post Reply' : 'Post Comment'}
        </button>
      </div>
    </form>
  );
}
