import React, { useState, useEffect } from 'react';
import { CommentsList } from './CommentsList';
import './CommentsPanel.css';

/**
 * CommentsPanel component - Collapsible comments panel that splits the content area
 *
 * Features:
 * - Collapsed: One-row height bar at bottom of content pane
 * - Expanded: Splits content area, showing comments in bottom panel
 * - Smooth transitions between states
 */
export function CommentsPanel({ pageId, comments = [] }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const panelRef = React.useRef(null);

  const commentCount = comments?.length || 0;

  // Update content wrapper class when expanded/collapsed
  useEffect(() => {
    const wrapper = panelRef.current?.closest('.arc-content-wrapper');
    if (wrapper) {
      if (isExpanded) {
        wrapper.classList.add('arc-content-wrapper-with-comments');
      } else {
        wrapper.classList.remove('arc-content-wrapper-with-comments');
      }
    }
  }, [isExpanded]);

  return (
    <div
      ref={panelRef}
      className={`arc-comments-panel ${isExpanded ? 'arc-comments-panel-expanded' : ''}`}
    >
      <button
        type="button"
        className="arc-comments-panel-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-label={isExpanded ? 'Collapse comments' : 'Expand comments'}
      >
        <span className="arc-comments-panel-title">
          Comments {commentCount > 0 && <span className="arc-comments-panel-count">({commentCount})</span>}
        </span>
        <span className="arc-comments-panel-icon">
          {isExpanded ? '▼' : '▲'}
        </span>
      </button>
      {isExpanded && (
        <div className="arc-comments-panel-content">
          <CommentsList pageId={pageId} comments={comments} />
        </div>
      )}
    </div>
  );
}
