import React from 'react';
import './DeleteArchiveDialog.css';

/**
 * DeleteArchiveDialog component - Confirmation dialog for delete/archive actions
 */
export function DeleteArchiveDialog({
  isOpen,
  onClose,
  onConfirm,
  action, // 'delete' or 'archive' or 'unarchive'
  pageTitle,
  isProcessing = false
}) {
  if (!isOpen) return null;

  const getActionText = () => {
    switch (action) {
      case 'delete':
        return {
          title: 'Delete Page',
          message: `Are you sure you want to delete "${pageTitle}"? This action cannot be undone.`,
          confirmText: 'Delete',
          confirmClass: 'arc-delete-archive-dialog-button-delete'
        };
      case 'archive':
        return {
          title: 'Archive Page',
          message: `Are you sure you want to archive "${pageTitle}"? Archived pages are hidden from normal views but can be restored.`,
          confirmText: 'Archive',
          confirmClass: 'arc-delete-archive-dialog-button-archive'
        };
      case 'unarchive':
        return {
          title: 'Unarchive Page',
          message: `Are you sure you want to unarchive "${pageTitle}"? The page will be restored to published status.`,
          confirmText: 'Unarchive',
          confirmClass: 'arc-delete-archive-dialog-button-unarchive'
        };
      default:
        return {
          title: 'Confirm Action',
          message: `Are you sure you want to perform this action on "${pageTitle}"?`,
          confirmText: 'Confirm',
          confirmClass: 'arc-delete-archive-dialog-button-confirm'
        };
    }
  };

  const actionText = getActionText();

  const handleConfirm = () => {
    onConfirm();
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="arc-delete-archive-dialog-overlay"
      onClick={handleOverlayClick}
    >
      <div className="arc-delete-archive-dialog">
        <div className="arc-delete-archive-dialog-header">
          <h3>{actionText.title}</h3>
          <button
            type="button"
            className="arc-delete-archive-dialog-close"
            onClick={onClose}
            aria-label="Close"
            disabled={isProcessing}
          >
            ×
          </button>
        </div>

        <div className="arc-delete-archive-dialog-content">
          <p>{actionText.message}</p>
          {action === 'delete' && (
            <div className="arc-delete-archive-dialog-warning">
              <strong>Warning:</strong> If this page has child pages, they will be moved to the orphanage.
            </div>
          )}
        </div>

        <div className="arc-delete-archive-dialog-actions">
          <button
            type="button"
            className="arc-delete-archive-dialog-button arc-delete-archive-dialog-button-cancel"
            onClick={onClose}
            disabled={isProcessing}
          >
            Cancel
          </button>
          <button
            type="button"
            className={`arc-delete-archive-dialog-button ${actionText.confirmClass}`}
            onClick={handleConfirm}
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : actionText.confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
