import React, { useEffect } from 'react';
import './Notification.css';

export function Notification({ message, type = 'info', onClose, duration = 5000 }) {
  useEffect(() => {
    if (duration > 0 && onClose) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  return (
    <div className={`arc-notification arc-notification-${type}`} role="alert">
      <div className="arc-notification-content">
        <span className="arc-notification-icon">
          {type === 'success' && '✓'}
          {type === 'error' && '✕'}
          {type === 'warning' && '⚠'}
          {type === 'info' && 'ℹ'}
        </span>
        <span className="arc-notification-message">{message}</span>
      </div>
      {onClose && (
        <button
          className="arc-notification-close"
          onClick={onClose}
          aria-label="Close notification"
        >
          ×
        </button>
      )}
    </div>
  );
}
