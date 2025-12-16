import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Backlinks component displays pages that link to the current page
 * 
 * Features:
 * - Display pages that link to current page
 * - Click to navigate to linking page
 * - Display backlink count
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
              {backlink.title}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
