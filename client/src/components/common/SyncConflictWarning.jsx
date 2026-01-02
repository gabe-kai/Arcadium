import React from 'react';
import './SyncConflictWarning.css';

/**
 * SyncConflictWarning component - Displays warnings about file sync conflicts
 *
 * Shows a warning banner when there's a potential conflict between file-based
 * edits and browser edits.
 */
export function SyncConflictWarning({ conflict }) {
  if (!conflict || !conflict.has_conflict) {
    return null;
  }

  return (
    <div className="arc-sync-conflict-warning" role="alert">
      <div className="arc-sync-conflict-warning-icon">⚠️</div>
      <div className="arc-sync-conflict-warning-content">
        <div className="arc-sync-conflict-warning-title">File Sync Conflict Warning</div>
        <div className="arc-sync-conflict-warning-message">{conflict.message}</div>
        {conflict.grace_period_remaining && conflict.grace_period_remaining > 0 && (
          <div className="arc-sync-conflict-warning-detail">
            Your browser edits are protected from file sync for{' '}
            {Math.round(conflict.grace_period_remaining / 60)} more{' '}
            {Math.round(conflict.grace_period_remaining / 60) === 1 ? 'minute' : 'minutes'}.
          </div>
        )}
      </div>
    </div>
  );
}
