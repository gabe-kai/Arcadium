import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { useSearch } from '../services/api/search';

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
export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [localQuery, setLocalQuery] = useState(query);

  const { data: searchData, isLoading, isError, error } = useSearch(query);

  // Update local query when URL changes
  useEffect(() => {
    setLocalQuery(query);
  }, [query]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const trimmedQuery = localQuery.trim();
    if (trimmedQuery) {
      setSearchParams({ q: trimmedQuery });
    }
  };

  const handleQueryChange = (e) => {
    setLocalQuery(e.target.value);
  };

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-search-page">
        <div className="arc-search-page-header">
          <h1 className="arc-search-page-title">Search</h1>
          <form onSubmit={handleSearchSubmit} className="arc-search-page-form">
            <input
              type="search"
              className="arc-search-page-input"
              placeholder="Search the wiki..."
              value={localQuery}
              onChange={handleQueryChange}
              autoFocus
            />
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
                Found {searchData.total || 0} result{searchData.total !== 1 ? 's' : ''} for "{searchData.query}"
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
      </div>
    </Layout>
  );
}
