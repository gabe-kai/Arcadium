import { useState, useEffect } from 'react';

const THEME_STORAGE_KEY = 'arcadium_theme';
const THEMES = {
  light: 'light',
  dark: 'dark',
  system: 'system',
};

function getSystemTheme() {
  if (typeof window === 'undefined') return 'dark';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getStoredTheme() {
  if (typeof window === 'undefined') return 'system';
  try {
    return localStorage.getItem(THEME_STORAGE_KEY) || 'system';
  } catch {
    return 'system';
  }
}

function setStoredTheme(theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Ignore localStorage errors
  }
}

function applyTheme(theme) {
  const root = document.documentElement;
  const effectiveTheme = theme === 'system' ? getSystemTheme() : theme;

  root.setAttribute('data-theme', effectiveTheme);
  root.classList.toggle('theme-light', effectiveTheme === 'light');
  root.classList.toggle('theme-dark', effectiveTheme === 'dark');
}

export function useTheme() {
  const [theme, setTheme] = useState(() => getStoredTheme());

  useEffect(() => {
    applyTheme(theme);

    // Listen for system theme changes
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => applyTheme('system');
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [theme]);

  const setThemeAndStore = (newTheme) => {
    setTheme(newTheme);
    setStoredTheme(newTheme);
    applyTheme(newTheme);
  };

  const toggleTheme = () => {
    const currentEffective = theme === 'system' ? getSystemTheme() : theme;
    const newTheme = currentEffective === 'dark' ? 'light' : 'dark';
    setThemeAndStore(newTheme);
  };

  return {
    theme,
    setTheme: setThemeAndStore,
    toggleTheme,
    themes: THEMES,
    effectiveTheme: theme === 'system' ? getSystemTheme() : theme,
  };
}
