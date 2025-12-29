import React, { createContext, useContext } from 'react';
import { useNotification } from '../../hooks/useNotification';
import { NotificationContainer } from './NotificationContainer';

const NotificationContext = createContext(null);

export function useNotificationContext() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotificationContext must be used within NotificationProvider');
  }
  return context;
}

export function NotificationProvider({ children }) {
  const notification = useNotification();

  return (
    <NotificationContext.Provider value={notification}>
      {children}
      <NotificationContainer
        notifications={notification.notifications}
        onRemove={notification.removeNotification}
      />
    </NotificationContext.Provider>
  );
}
