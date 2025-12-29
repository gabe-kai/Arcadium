import React, { useState, useEffect, useRef } from 'react';
import { searchPages } from '../../services/api/pages';
import './LinkDialog.css';

/**
 * LinkDialog component - Dialog for inserting links with page search
 */
export function LinkDialog({ isOpen, onClose, onInsert, initialUrl = '' }) {
  const [url, setUrl] = useState(initialUrl);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [linkType, setLinkType] = useState('external'); // 'external' or 'internal'
  const searchTimerRef = useRef(null);
  const dialogRef = useRef(null);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setUrl(initialUrl);
      setSearchQuery('');
      setSearchResults([]);
      setLinkType(initialUrl && !initialUrl.startsWith('http') ? 'internal' : 'external');
    }
  }, [isOpen, initialUrl]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dialogRef.current && !dialogRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  // Search pages when query changes
  useEffect(() => {
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }

    if (!searchQuery.trim() || linkType !== 'internal') {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    searchTimerRef.current = setTimeout(async () => {
      try {
        // Pages API search returns an array of pages
        const results = await searchPages(searchQuery.trim());
        setSearchResults(results || []);
      } catch (error) {
        console.error('Error searching pages:', error);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300); // Debounce 300ms

    return () => {
      if (searchTimerRef.current) {
        clearTimeout(searchTimerRef.current);
      }
    };
  }, [searchQuery, linkType]);

  // Normalize URL - add protocol if missing for external URLs
  const normalizeUrl = (urlString) => {
    const trimmed = urlString.trim();
    if (linkType === 'external') {
      // If it doesn't start with http:// or https://, add https://
      if (trimmed && !trimmed.match(/^https?:\/\//i)) {
        // Check if it looks like a domain (has dots and no spaces)
        if (trimmed.includes('.') && !trimmed.includes(' ')) {
          return `https://${trimmed}`;
        }
      }
    }
    return trimmed;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const normalizedUrl = normalizeUrl(url);
    if (normalizedUrl) {
      onInsert(normalizedUrl);
      onClose();
    }
  };

  const handleSelectPage = (page) => {
    // Search API returns page_id, pages API returns id
    const pageId = page.page_id || page.id;
    setUrl(`/pages/${pageId}`);
    setSearchQuery('');
    setSearchResults([]);
  };

  if (!isOpen) return null;

  return (
    <div className="arc-link-dialog-overlay">
      <div className="arc-link-dialog" ref={dialogRef}>
        <div className="arc-link-dialog-header">
          <h3>Insert Link</h3>
          <button
            type="button"
            className="arc-link-dialog-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="arc-link-dialog-form">
          <div className="arc-link-dialog-type">
            <label>
              <input
                type="radio"
                value="external"
                checked={linkType === 'external'}
                onChange={() => setLinkType('external')}
              />
              External URL
            </label>
            <label>
              <input
                type="radio"
                value="internal"
                checked={linkType === 'internal'}
                onChange={() => setLinkType('internal')}
              />
              Internal Page
            </label>
          </div>

          {linkType === 'internal' ? (
            <div className="arc-link-dialog-internal">
              <label htmlFor="link-search">Search for page:</label>
              <input
                id="link-search"
                type="text"
                className="arc-link-dialog-search"
                placeholder="Type to search pages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                autoFocus
              />
              
              {isSearching && (
                <div className="arc-link-dialog-loading">Searching...</div>
              )}
              
              {!isSearching && searchResults.length > 0 && (
                <ul className="arc-link-dialog-results">
                  {searchResults.map((page) => (
                    <li key={page.page_id || page.id}>
                      <button
                        type="button"
                        className="arc-link-dialog-result-item"
                        onClick={() => handleSelectPage(page)}
                      >
                        <span className="arc-link-dialog-result-title">{page.title}</span>
                        {page.section && (
                          <span className="arc-link-dialog-result-section">{page.section}</span>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              
              {!isSearching && searchQuery.trim() && searchResults.length === 0 && (
                <div className="arc-link-dialog-no-results">No pages found</div>
              )}

              <label htmlFor="link-url">Or enter page ID or slug:</label>
              <input
                id="link-url"
                type="text"
                className="arc-link-dialog-input"
                placeholder="/pages/page-id or page-slug"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
          ) : (
            <div className="arc-link-dialog-external">
              <label htmlFor="link-url">URL:</label>
              <input
                id="link-url"
                type="text"
                className="arc-link-dialog-input"
                placeholder="https://example.com or www.example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                autoFocus
              />
              <small className="arc-link-dialog-help">
                Protocol (https://) will be added automatically if missing
              </small>
            </div>
          )}

          <div className="arc-link-dialog-actions">
            <button
              type="button"
              className="arc-link-dialog-button arc-link-dialog-button-cancel"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="arc-link-dialog-button arc-link-dialog-button-insert"
              disabled={!url.trim()}
            >
              Insert Link
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
