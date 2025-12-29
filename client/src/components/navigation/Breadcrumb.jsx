import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Breadcrumb component displays navigation trail from root to current page
 *
 * @param {Array} breadcrumb - Array of { id, title, slug } objects from root to current
 * @param {string} currentPageId - ID of the current page (to disable link on last item)
 */
export function Breadcrumb({ breadcrumb, currentPageId }) {
  if (!breadcrumb || breadcrumb.length === 0) {
    return null;
  }

  // Don't show breadcrumb if only one item (just the current page at root)
  if (breadcrumb.length === 1) {
    return null;
  }

  return (
    <nav className="arc-breadcrumb" aria-label="Breadcrumb">
      <ol className="arc-breadcrumb-list">
        {breadcrumb.map((item, index) => {
          const isLast = index === breadcrumb.length - 1;
          const isCurrent = item.id === currentPageId;

          return (
            <li key={item.id} className="arc-breadcrumb-item">
              {isLast || isCurrent ? (
                <span className="arc-breadcrumb-current" aria-current="page">
                  {item.title}
                </span>
              ) : (
                <>
                  <Link to={`/pages/${item.id}`} className="arc-breadcrumb-link">
                    {item.title}
                  </Link>
                  <span className="arc-breadcrumb-separator" aria-hidden="true">
                    {' > '}
                  </span>
                </>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
