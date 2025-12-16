import React from 'react';
import { Link } from 'react-router-dom';

/**
 * PageNavigation component displays previous/next page navigation buttons
 * 
 * @param {Object} navigation - { previous: { id, title, slug } | null, next: { id, title, slug } | null }
 */
export function PageNavigation({ navigation }) {
  if (!navigation || (!navigation.previous && !navigation.next)) {
    return null;
  }

  return (
    <nav className="arc-page-navigation" aria-label="Page navigation">
      <div className="arc-page-navigation-inner">
        {navigation.previous ? (
          <Link
            to={`/pages/${navigation.previous.id}`}
            className="arc-page-nav-link arc-page-nav-prev"
          >
            <span className="arc-page-nav-label">Previous</span>
            <span className="arc-page-nav-title">{navigation.previous.title}</span>
          </Link>
        ) : (
          <div className="arc-page-nav-link arc-page-nav-prev arc-page-nav-disabled">
            <span className="arc-page-nav-label">Previous</span>
            <span className="arc-page-nav-title">—</span>
          </div>
        )}

        {navigation.next ? (
          <Link
            to={`/pages/${navigation.next.id}`}
            className="arc-page-nav-link arc-page-nav-next"
          >
            <span className="arc-page-nav-label">Next</span>
            <span className="arc-page-nav-title">{navigation.next.title}</span>
          </Link>
        ) : (
          <div className="arc-page-nav-link arc-page-nav-next arc-page-nav-disabled">
            <span className="arc-page-nav-label">Next</span>
            <span className="arc-page-nav-title">—</span>
          </div>
        )}
      </div>
    </nav>
  );
}
