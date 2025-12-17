import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Backlinks component displays pages that link to the current page
 * 
 * Features:
 * - Display pages that link to current page
 * - Click to navigate to linking page
 * - Display backlink count
 * - Show context snippet (where link appears) if available
 * - Styled list with hover effects
 */
export function Backlinks({ backlinks }) {
  if (!backlinks || backlinks.length === 0) {
    return null;
  }

  return (
    <nav className="arc-backlinks" aria-label="Pages linking here">
      <h3 className="arc-backlinks-title">
        Pages Linking Here
        <span className="arc-backlinks-count">({backlinks.length})</span>
      </h3>
      <ul className="arc-backlinks-list">
        {backlinks.map((backlink) => (
          <li key={backlink.page_id} className="arc-backlinks-item">
            <Link
              to={`/pages/${backlink.page_id}`}
              className="arc-backlinks-link"
            >
              <span className="arc-backlinks-link-title">{backlink.title}</span>
              {backlink.context && (
                <span className="arc-backlinks-context" title="Context where link appears">
                  {backlink.context}
                </span>
              )}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
