import React, { useState } from 'react';
import { copyPageLink, sharePage } from '../../utils/share';
import { useNotificationContext } from './NotificationProvider';
import './ShareButton.css';

export function ShareButton({ pageId, pageTitle }) {
  const { showSuccess, showError } = useNotificationContext();
  const [isSharing, setIsSharing] = useState(false);

  const handleShare = async () => {
    setIsSharing(true);
    try {
      if (navigator.share) {
        await sharePage(pageId, pageTitle);
        showSuccess('Page shared successfully');
      } else {
        await copyPageLink(pageId);
        showSuccess('Link copied to clipboard');
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        // User cancelled share, don't show error
        showError('Failed to share page. Please try copying the link manually.');
      }
    } finally {
      setIsSharing(false);
    }
  };

  return (
    <button
      className="arc-share-button"
      onClick={handleShare}
      disabled={isSharing}
      aria-label="Share page"
      title="Share this page"
    >
      {isSharing ? '...' : '🔗'}
    </button>
  );
}
