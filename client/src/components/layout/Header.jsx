import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../services/auth/AuthContext';

export function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, signOut } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = useRef(null);

  // Load search query from URL if on search page
  useEffect(() => {
    if (location.pathname === '/search') {
      const params = new URLSearchParams(location.search);
      const query = params.get('q') || '';
      setSearchQuery(query);
    }
  }, [location]);

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
    navigate('/signin');
  };

  const handleSignOut = () => {
    signOut();
    navigate('/');
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const query = searchQuery.trim();
    if (query) {
      navigate(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  return (
    <header className="arc-header">
      <div className="arc-header-left">
        <Link to="/" className="arc-logo">
          <span className="arc-logo-mark">A</span>
          <span className="arc-logo-text">Arcadium Wiki</span>
        </Link>
      </div>
      <div className="arc-header-right">
        <form onSubmit={handleSearchSubmit} className="arc-search-form">
          <input
            ref={searchInputRef}
            type="search"
            className="arc-search-input"
            placeholder="Search the wiki... (Ctrl+K / Cmd+K)"
            value={searchQuery}
            onChange={handleSearchChange}
            aria-label="Search the wiki"
          />
        </form>
        {isAuthenticated && (user?.role === 'writer' || user?.role === 'admin') && (
          <Link
            to="/pages/new/edit"
            className="arc-header-button arc-header-button-new-page"
            title="Create new page"
          >
            + New Page
          </Link>
        )}
        {isAuthenticated ? (
          <div className="arc-user-menu">
            <span className="arc-username">{user?.username || 'User'}</span>
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
