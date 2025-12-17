import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../services/auth/AuthContext';

export function Header() {
  const navigate = useNavigate();
  const { isAuthenticated, user, signOut } = useAuth();

  const handleSignInClick = () => {
    navigate('/signin');
  };

  const handleSignOut = () => {
    signOut();
    navigate('/');
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
        <input
          type="search"
          className="arc-search-input"
          placeholder="Search the wiki..."
        />
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
