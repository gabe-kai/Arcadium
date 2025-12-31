import React, { useState, useEffect, useRef, useMemo } from 'react';
import { apiClient } from '../../services/api/client';
import './LinkDialog.css';

/**
 * LinkDialog component - Dialog for inserting links with page search
 */
export function LinkDialog({ isOpen, onClose, onInsert, initialUrl = '' }) {
  const [url, setUrl] = useState(initialUrl);
  const [searchQuery, setSearchQuery] = useState('');
  const [allPages, setAllPages] = useState([]);
  const [isLoadingPages, setIsLoadingPages] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [linkType, setLinkType] = useState('external'); // 'external' or 'internal'
  const dialogRef = useRef(null);
  const searchInputRef = useRef(null);

  // Fetch all pages when dialog opens and internal link type is selected
  useEffect(() => {
    if (isOpen && linkType === 'internal' && allPages.length === 0) {
      setIsLoadingPages(true);
      apiClient
        .get('/pages', { params: { limit: 1000 } }) // Get up to 1000 pages
        .then((res) => {
          const pages = res.data.pages || [];
          // Sort pages alphabetically by title
          pages.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
          setAllPages(pages);
        })
        .catch((error) => {
          console.error('Error fetching pages:', error);
          setAllPages([]);
        })
        .finally(() => {
          setIsLoadingPages(false);
        });
    }
  }, [isOpen, linkType, allPages.length]);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setUrl(initialUrl);
      setSearchQuery('');
      setShowDropdown(false);
      setLinkType(initialUrl && !initialUrl.startsWith('http') ? 'internal' : 'external');
    } else {
      // Reset all pages when dialog closes to refetch fresh data next time
      setAllPages([]);
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

  // Filter pages by title (client-side)
  // Case-insensitive and space/special-character forgiving
  const filteredPages = useMemo(() => {
    if (!searchQuery.trim()) {
      // No search query - show all pages, sorted alphabetically
      return allPages;
    }

    // Normalize search query: lowercase, remove spaces and special characters
    const normalize = (str) => {
      return (str || '')
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '');
    };

    const normalizedQuery = normalize(searchQuery);

    return allPages.filter((page) => {
      const normalizedTitle = normalize(page.title);
      // Check if normalized title contains normalized query
      return normalizedTitle.includes(normalizedQuery);
    });
  }, [allPages, searchQuery]);

  // Normalize URL - add protocol if missing for external URLs, resolve slugs for internal
  const normalizeUrl = async (urlString) => {
    const trimmed = urlString.trim();

    if (linkType === 'external') {
      // If it doesn't start with http:// or https://, add https://
      if (trimmed && !trimmed.match(/^https?:\/\//i)) {
        // Check if it looks like a domain (has dots and no spaces)
        if (trimmed.includes('.') && !trimmed.includes(' ')) {
          return `https://${trimmed}`;
        }
      }
      return trimmed;
    } else {
      // Internal link - handle different formats
      // If it's already /pages/{id}, return as-is
      if (trimmed.startsWith('/pages/')) {
        return trimmed;
      }

      // If it looks like a UUID, assume it's a page ID
      const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (uuidPattern.test(trimmed)) {
        return `/pages/${trimmed}`;
      }

      // Otherwise, treat it as a slug and look it up
      if (trimmed) {
        try {
          const response = await apiClient.get('/pages', { params: { slug: trimmed } });
          const pages = response.data.pages || [];
          if (pages.length > 0) {
            return `/pages/${pages[0].id}`;
          }
        } catch (error) {
          console.error('Error looking up page by slug:', error);
        }
      }

      // If lookup failed, return the original (might be invalid, but let the user try)
      return trimmed.startsWith('/') ? trimmed : `/pages/${trimmed}`;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const normalizedUrl = await normalizeUrl(url);
    if (normalizedUrl) {
      onInsert(normalizedUrl);
      onClose();
    }
  };

  const handleSelectPage = (page) => {
    const pageId = page.id;
    setUrl(`/pages/${pageId}`);
    setSearchQuery('');
    setShowDropdown(false);
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
              <div style={{ position: 'relative' }}>
                <input
                  ref={searchInputRef}
                  id="link-search"
                  type="text"
                  className="arc-link-dialog-search"
                  placeholder="Type to search pages..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setShowDropdown(true);
                  }}
                  onFocus={() => setShowDropdown(true)}
                  onBlur={(e) => {
                    // Delay hiding dropdown to allow click on results
                    setTimeout(() => setShowDropdown(false), 200);
                  }}
                  autoFocus
                />

                {showDropdown && (
                  <ul className="arc-link-dialog-results">
                    {isLoadingPages ? (
                      <li>
                        <div className="arc-link-dialog-loading">Loading pages...</div>
                      </li>
                    ) : filteredPages.length > 0 ? (
                      filteredPages.map((page) => (
                        <li key={page.id}>
                          <button
                            type="button"
                            className="arc-link-dialog-result-item"
                            onMouseDown={(e) => {
                              // Prevent input blur when clicking
                              e.preventDefault();
                              handleSelectPage(page);
                            }}
                          >
                            <span className="arc-link-dialog-result-title">{page.title}</span>
                            {page.section && (
                              <span className="arc-link-dialog-result-section">{page.section}</span>
                            )}
                          </button>
                        </li>
                      ))
                    ) : searchQuery.trim() ? (
                      <li>
                        <div className="arc-link-dialog-no-results">No pages found</div>
                      </li>
                    ) : null}
                  </ul>
                )}
              </div>

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
