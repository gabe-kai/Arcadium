import React, { useState } from 'react';
import { useAuth } from '../../services/auth/AuthContext';
import { formatDistanceToNow } from 'date-fns';
import { CommentForm } from './CommentForm';
import './CommentsList.css';

/**
 * CommentItem component - Displays a single comment with replies
 * Supports nested threading up to 5 levels deep
 */
export function CommentItem({ comment, onReply, onEdit, onDelete, depth = 0, pageId }) {
  const { user } = useAuth();
  const [isReplying, setIsReplying] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [showReplies, setShowReplies] = useState(true);

  const isOwner = user && user.id && comment.user?.id && String(user.id) === String(comment.user.id);
  const canReply = depth < 4; // Max depth is 5, so can reply up to depth 4
  const hasReplies = comment.replies && comment.replies.length > 0;

  const handleReplyClick = () => {
    setIsReplying(true);
    // Also notify parent if needed (for tracking which comment is being replied to)
    if (onReply) {
      onReply(comment.id);
    }
  };

  const handleEditClick = () => {
    setIsEditing(true);
    setEditContent(comment.content);
  };

  const handleEditCancel = () => {
    setIsEditing(false);
    setEditContent(comment.content);
  };

  const handleEditSave = () => {
    if (onEdit && editContent.trim()) {
      onEdit(comment.id, editContent.trim());
      setIsEditing(false);
    }
  };

  const handleDeleteClick = () => {
    if (window.confirm('Are you sure you want to delete this comment?')) {
      if (onDelete) {
        onDelete(comment.id);
      }
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return dateString;
    }
  };

  const formatAbsoluteDate = (dateString) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="arc-comment-wrapper">
      <div
        className={`arc-comment-item ${comment.is_recommendation ? 'arc-comment-recommendation' : ''}`}
        style={{ marginLeft: `${depth * 2}rem` }}
      >
        <div className="arc-comment-header">
          <div className="arc-comment-author">
          <span className="arc-comment-username">{comment.user?.username || 'Anonymous'}</span>
          {comment.is_recommendation && (
            <span className="arc-comment-recommendation-badge" title="Recommendation">
              💡
            </span>
          )}
        </div>
        <div className="arc-comment-meta">
            <time
              dateTime={comment.created_at}
              title={formatAbsoluteDate(comment.created_at)}
            >
              {formatDate(comment.created_at)}
            </time>
            {comment.updated_at !== comment.created_at && (
              <span className="arc-comment-edited" title={`Edited ${formatAbsoluteDate(comment.updated_at)}`}>
                (edited)
              </span>
            )}
          </div>
        </div>

        <div className="arc-comment-content">
          {isEditing ? (
            <div className="arc-comment-edit-form">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="arc-comment-edit-textarea"
                rows={3}
              />
              <div className="arc-comment-edit-actions">
                <button
                  type="button"
                  onClick={handleEditCancel}
                  className="arc-comment-button arc-comment-button-cancel"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleEditSave}
                  className="arc-comment-button arc-comment-button-save"
                  disabled={!editContent.trim()}
                >
                  Save
                </button>
              </div>
            </div>
          ) : (
            <div className="arc-comment-text">{comment.content}</div>
          )}
        </div>

        {!isEditing && (
          <div className="arc-comment-actions">
            {canReply && (
              <button
                type="button"
                onClick={handleReplyClick}
                className="arc-comment-action-link"
              >
                Reply
              </button>
            )}
            {isOwner && (
              <>
                <button
                  type="button"
                  onClick={handleEditClick}
                  className="arc-comment-action-link"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={handleDeleteClick}
                  className="arc-comment-action-link arc-comment-action-delete"
                >
                  Delete
                </button>
              </>
            )}
          </div>
        )}

        {hasReplies && (
          <div className="arc-comment-replies">
            <button
              type="button"
              onClick={() => setShowReplies(!showReplies)}
              className="arc-comment-toggle-replies"
            >
              {showReplies ? '▼' : '▶'} {comment.replies.length} {comment.replies.length === 1 ? 'reply' : 'replies'}
            </button>
            {showReplies && (
              <div className="arc-comment-replies-list">
                {comment.replies.map((reply) => (
                  <CommentItem
                    key={reply.id}
                    comment={reply}
                    onReply={onReply}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    depth={depth + 1}
                    pageId={pageId}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {isReplying && canReply && pageId && (
          <div className="arc-comment-reply-form">
            <CommentForm
              pageId={pageId}
              parentCommentId={comment.id}
              onSubmit={async (commentData) => {
                if (onReply) {
                  await onReply(comment.id, commentData);
                }
                setIsReplying(false);
              }}
              onCancel={() => {
                setIsReplying(false);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
