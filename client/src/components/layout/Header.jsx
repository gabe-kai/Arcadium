import React from 'react';
import { Link } from 'react-router-dom';

export function Header() {
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
        <button className="arc-header-button" type="button">
          Sign in
        </button>
      </div>
    </header>
  );
}
