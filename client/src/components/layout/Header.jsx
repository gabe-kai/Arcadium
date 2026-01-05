import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../services/auth/AuthContext';
import { ThemeToggle } from '../common/ThemeToggle';
import { ServiceStatusIndicator } from '../common/ServiceStatusIndicator';

const RECENT_SEARCHES_KEY = 'arcadium_recent_searches';
const MAX_RECENT_SEARCHES = 10;

function getRecentSearches() {
  try {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveRecentSearch(query) {
  if (!query || !query.trim()) return;
  const trimmed = query.trim();
  try {
    const recent = getRecentSearches();
    // Remove if already exists
    const filtered = recent.filter(q => q.toLowerCase() !== trimmed.toLowerCase());
    // Add to front
    const updated = [trimmed, ...filtered].slice(0, MAX_RECENT_SEARCHES);
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
  } catch {
    // Ignore localStorage errors
  }
}

export function Header({ onMenuToggle, isLeftSidebarOpen }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, signOut } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [showRecentSearches, setShowRecentSearches] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const searchInputRef = useRef(null);
  const searchFormRef = useRef(null);

  // Load search query from URL if on search page
  useEffect(() => {
    if (location.pathname === '/search') {
      const params = new URLSearchParams(location.search);
      const query = params.get('q') || '';
      setSearchQuery(query);
    }
  }, [location]);

  // Load recent searches
  useEffect(() => {
    setRecentSearches(getRecentSearches());
  }, []);

  // Close recent searches dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchFormRef.current && !searchFormRef.current.contains(event.target)) {
        setShowRecentSearches(false);
      }
    };

    if (showRecentSearches) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showRecentSearches]);

  // Keyboard shortcut: Ctrl+K / Cmd+K to focus search
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSignInClick = () => {
    // Store current location to redirect back after login
    const currentPath = location.pathname + location.search;
    sessionStorage.setItem('redirectAfterLogin', currentPath);
    navigate('/signin');
  };

  const handleSignOut = () => {
    signOut();
    // Stay on current page after sign-out (don't redirect to home)
    // The page will automatically update to reflect the new unauthenticated state
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const query = searchQuery.trim();
    if (query) {
      saveRecentSearch(query);
      setRecentSearches(getRecentSearches());
      setShowRecentSearches(false);
      navigate(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
    setShowRecentSearches(true);
  };

  const handleSearchFocus = () => {
    if (recentSearches.length > 0) {
      setShowRecentSearches(true);
    }
  };

  const handleRecentSearchClick = (query) => {
    setSearchQuery(query);
    saveRecentSearch(query);
    setRecentSearches(getRecentSearches());
    setShowRecentSearches(false);
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    searchInputRef.current?.focus();
  };

  return (
    <header className="arc-header">
      <div className="arc-header-left">
        {onMenuToggle && (
          <button
            className="arc-mobile-menu-toggle"
            onClick={onMenuToggle}
            aria-label="Toggle navigation menu"
            aria-expanded={isLeftSidebarOpen}
            title="Menu"
          >
            {isLeftSidebarOpen ? '✕' : '☰'}
          </button>
        )}
        <Link to="/" className="arc-logo">
          <span className="arc-logo-mark">A</span>
          <span className="arc-logo-text">Arcadium Wiki</span>
        </Link>
      </div>
      <div className="arc-header-center">
        <form ref={searchFormRef} onSubmit={handleSearchSubmit} className="arc-search-form arc-header-search">
          <div className="arc-search-input-wrapper">
            <input
              ref={searchInputRef}
              type="search"
              className="arc-search-input arc-header-search-input"
              placeholder="Search the wiki... (Ctrl+K / Cmd+K)"
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={handleSearchFocus}
              aria-label="Search the wiki"
            />
            {searchQuery && (
              <button
                type="button"
                className="arc-search-clear"
                onClick={handleClearSearch}
                aria-label="Clear search"
              >
                ×
              </button>
            )}
            {showRecentSearches && recentSearches.length > 0 && (
              <div className="arc-search-recent-dropdown">
                <div className="arc-search-recent-header">Recent searches</div>
                {recentSearches.map((query, index) => (
                  <button
                    key={index}
                    type="button"
                    className="arc-search-recent-item"
                    onClick={() => handleRecentSearchClick(query)}
                  >
                    {query}
                  </button>
                ))}
              </div>
            )}
          </div>
        </form>
      </div>
      <div className="arc-header-right">
        <ServiceStatusIndicator />
        {isAuthenticated && (user?.role === 'writer' || user?.role === 'admin') && (
          <Link
            to="/pages/new/edit"
            className="arc-header-button arc-header-button-new-page"
            title="Create new page"
          >
            + New Page
          </Link>
        )}
        <ThemeToggle />
        {isAuthenticated ? (
          <div className="arc-user-menu">
            <Link
              to="/profile"
              className="arc-username"
              style={{ cursor: 'pointer', textDecoration: 'none' }}
              title="View profile"
            >
              {user?.username || 'User'}
            </Link>
            <button
              className="arc-header-button"
              type="button"
              onClick={handleSignOut}
            >
              Sign out
            </button>
          </div>
        ) : (
          <button
            className="arc-header-button"
            type="button"
            onClick={handleSignInClick}
          >
            Sign in
          </button>
        )}
      </div>
    </header>
  );
}
