import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { App } from './App';
import './styles.css';
import './styles-animations-print.css';
import { queryClient } from './state/queryClient';
import { AuthProvider } from './services/auth/AuthContext';
import { initSyntaxHighlighting } from './utils/syntaxHighlight';
import 'prismjs/themes/prism-tomorrow.css';

// Initialize syntax highlighting
initSyntaxHighlighting();

const rootElement = document.getElementById('root');

if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </QueryClientProvider>
    </React.StrictMode>,
  );
} else {
  // Fallback in case the root element is missing
  console.error('Root element #root not found');
}
