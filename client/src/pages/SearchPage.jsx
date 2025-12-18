import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { useSearch, searchPages } from '../services/api/search';

/**
 * Highlight search terms in text
 */
function highlightSearchTerms(text, query) {
  if (!query || !text) return text;
  
  const terms = query.trim().toLowerCase().split(/\s+/);
  let highlighted = text;
  
  terms.forEach((term) => {
    if (term.length > 0) {
      const regex = new RegExp(`(${term})`, 'gi');
      highlighted = highlighted.replace(regex, '<mark>$1</mark>');
    }
  });
  
  return <span dangerouslySetInnerHTML={{ __html: highlighted }} />;
}

/**
 * SearchPage component - Displays search results
 */
const RESULTS_PER_PAGE = 20;

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const pageParam = searchParams.get('page');
  const currentPage = pageParam ? (parseInt(pageParam, 10) || 1) : 1;
  const [localQuery, setLocalQuery] = useState(query);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const suggestionsTimerRef = useRef(null);
  const searchFormRef = useRef(null);

  const { data: searchData, isLoading, isError, error } = useSearch(query, {
    limit: RESULTS_PER_PAGE,
    offset: (currentPage - 1) * RESULTS_PER_PAGE
  });

  // Update local query when URL changes
  useEffect(() => {
    setLocalQuery(query);
  }, [query]);

  // Debounced search suggestions
  useEffect(() => {
    if (suggestionsTimerRef.current) {
      clearTimeout(suggestionsTimerRef.current);
    }

    if (localQuery.trim().length > 2) {
      suggestionsTimerRef.current = setTimeout(() => {
        searchPages(localQuery.trim(), { limit: 5 }).then((data) => {
          if (data.results) {
            setSuggestions(data.results.slice(0, 5));
            setShowSuggestions(true);
          }
        }).catch(() => {
          setSuggestions([]);
        });
      }, 300);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }

    return () => {
      if (suggestionsTimerRef.current) {
        clearTimeout(suggestionsTimerRef.current);
      }
    };
  }, [localQuery]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchFormRef.current && !searchFormRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    if (showSuggestions) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showSuggestions]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const trimmedQuery = localQuery.trim();
    if (trimmedQuery) {
      setShowSuggestions(false);
      setSearchParams({ q: trimmedQuery, page: '1' });
    }
  };

  const handleQueryChange = (e) => {
    setLocalQuery(e.target.value);
  };

  const handleSuggestionClick = (suggestion) => {
    setLocalQuery(suggestion.title);
    setShowSuggestions(false);
    setSearchParams({ q: suggestion.title, page: '1' });
  };

  const handlePageChange = (newPage) => {
    setSearchParams({ q: query, page: newPage.toString() });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const totalResults = searchData?.total || 0;
  const totalPages = totalResults > 0 ? Math.ceil(totalResults / RESULTS_PER_PAGE) : 0;

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-search-page">
        <div className="arc-search-page-header">
          <h1 className="arc-search-page-title">Search</h1>
          <form ref={searchFormRef} onSubmit={handleSearchSubmit} className="arc-search-page-form">
            <div className="arc-search-page-input-wrapper">
              <input
                type="search"
                className="arc-search-page-input"
                placeholder="Search the wiki..."
                value={localQuery}
                onChange={handleQueryChange}
                onFocus={() => localQuery.trim().length > 2 && setShowSuggestions(true)}
                autoFocus
              />
              {localQuery && (
                <button
                  type="button"
                  className="arc-search-page-clear"
                  onClick={() => {
                    setLocalQuery('');
                    setShowSuggestions(false);
                  }}
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}
              {showSuggestions && suggestions.length > 0 && (
                <div className="arc-search-page-suggestions">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion.page_id}
                      type="button"
                      className="arc-search-page-suggestion-item"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      <span className="arc-search-page-suggestion-title">{suggestion.title}</span>
                      {suggestion.section && (
                        <span className="arc-search-page-suggestion-section">{suggestion.section}</span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button type="submit" className="arc-search-page-button">
              Search
            </button>
          </form>
        </div>

        {!query && (
          <div className="arc-search-page-empty">
            <p>Enter a search query to find pages.</p>
          </div>
        )}

        {query && isLoading && (
          <div className="arc-search-page-loading">
            <p>Searching...</p>
          </div>
        )}

        {query && !isLoading && !isError && !searchData && (
          <div className="arc-search-page-loading">
            <p>Searching...</p>
          </div>
        )}

        {query && isError && (
          <div className="arc-search-page-error">
            <p>Error searching: {error?.message || 'Unknown error'}</p>
          </div>
        )}

        {query && searchData && !isLoading && !isError && (
          <div className="arc-search-page-results">
            <div className="arc-search-page-results-header">
              <p className="arc-search-page-results-count">
                Found {totalResults} result{totalResults !== 1 ? 's' : ''} for "{searchData.query}"
                {totalPages > 1 && (
                  <span> (Page {currentPage} of {totalPages})</span>
                )}
              </p>
            </div>

            {searchData.results && searchData.results.length > 0 ? (
              <ul className="arc-search-page-results-list">
                {searchData.results.map((result) => (
                  <li key={result.page_id} className="arc-search-page-result-item">
                    <Link
                      to={`/pages/${result.page_id}`}
                      className="arc-search-page-result-link"
                    >
                      <div className="arc-search-page-result-header">
                        <h3 className="arc-search-page-result-title">
                          {result.title}
                        </h3>
                        {result.section && (
                          <span className="arc-search-page-result-section">
                            {result.section}
                          </span>
                        )}
                      </div>
                      {result.snippet && (
                        <p className="arc-search-page-result-snippet">
                          {highlightSearchTerms(result.snippet, query)}
                        </p>
                      )}
                      {result.relevance_score !== undefined && result.relevance_score > 0 && (
                        <span className="arc-search-page-result-score">
                          {Math.round(result.relevance_score * 100)}% match
                        </span>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="arc-search-page-no-results">
                <p>No results found for "{searchData.query}".</p>
                <p>Try different keywords or check your spelling.</p>
              </div>
            )}
          </div>
        )}

        {query && searchData && !isLoading && !isError && totalPages > 1 && (
          <div className="arc-search-page-pagination">
            <button
              type="button"
              className="arc-search-page-pagination-button"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <span className="arc-search-page-pagination-info">
              Page {currentPage} of {totalPages}
            </span>
            <button
              type="button"
              className="arc-search-page-pagination-button"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
