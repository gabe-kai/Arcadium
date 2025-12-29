import React from 'react';
import { useTheme } from '../../hooks/useTheme';
import './ThemeToggle.css';

export function ThemeToggle() {
  const { theme, toggleTheme, effectiveTheme } = useTheme();

  return (
    <button
      className="arc-theme-toggle"
      onClick={toggleTheme}
      aria-label={`Switch to ${effectiveTheme === 'dark' ? 'light' : 'dark'} mode`}
      title={`Current theme: ${effectiveTheme}. Click to switch to ${effectiveTheme === 'dark' ? 'light' : 'dark'} mode.`}
    >
      {effectiveTheme === 'dark' ? (
        <span className="arc-theme-icon">☀️</span>
      ) : (
        <span className="arc-theme-icon">🌙</span>
      )}
    </button>
  );
}
