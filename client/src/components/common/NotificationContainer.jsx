import React from 'react';
import { Notification } from './Notification';
import './NotificationContainer.css';

export function NotificationContainer({ notifications, onRemove }) {
  if (!notifications || notifications.length === 0) {
    return null;
  }

  return (
    <div className="arc-notification-container" aria-live="polite" aria-atomic="false">
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          message={notification.message}
          type={notification.type}
          onClose={() => onRemove(notification.id)}
          duration={notification.duration}
        />
      ))}
    </div>
  );
}
