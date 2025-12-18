import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';
import { useIndex } from '../services/api/search';

/**
 * IndexPage component - Displays alphabetical index of all pages
 */
export function IndexPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const letterFilter = searchParams.get('letter') || '';
  const sectionFilter = searchParams.get('section') || '';
  const [localSearch, setLocalSearch] = useState('');

  const { data: indexData, isLoading, isError } = useIndex();

  const handleLetterClick = (letter) => {
    const params = new URLSearchParams();
    if (letter) params.set('letter', letter);
    if (sectionFilter) params.set('section', sectionFilter);
    setSearchParams(params);
  };

  const handleSectionFilter = (section) => {
    const params = new URLSearchParams();
    if (letterFilter) params.set('letter', letterFilter);
    if (section) params.set('section', section);
    setSearchParams(params);
  };

  const handleSearchChange = (e) => {
    setLocalSearch(e.target.value.toLowerCase());
  };

  // Flatten index from {letter: [pages]} to flat array
  const getFlatIndex = () => {
    if (!indexData?.index) return [];
    const flat = [];
    Object.values(indexData.index).forEach((pages) => {
      flat.push(...pages);
    });
    return flat;
  };

  // Get all unique letters from index
  const getAllLetters = () => {
    if (!indexData?.index) return [];
    return Object.keys(indexData.index).sort();
  };

  // Filter index by letter and section
  const getFilteredIndex = () => {
    const flatIndex = getFlatIndex();
    if (flatIndex.length === 0) return [];
    
    let filtered = flatIndex;
    
    // Filter by letter
    if (letterFilter) {
      filtered = filtered.filter((entry) => {
        const firstLetter = entry.title?.[0]?.toUpperCase() || '#';
        return firstLetter === letterFilter.toUpperCase();
      });
    }
    
    // Filter by section
    if (sectionFilter) {
      filtered = filtered.filter((entry) => entry.section === sectionFilter);
    }
    
    // Filter by search query
    if (localSearch) {
      filtered = filtered.filter((entry) =>
        entry.title?.toLowerCase().includes(localSearch)
      );
    }
    
    return filtered.sort((a, b) => {
      const titleA = (a.title || '').toLowerCase();
      const titleB = (b.title || '').toLowerCase();
      return titleA.localeCompare(titleB);
    });
  };

  // Get unique sections
  const getSections = () => {
    const flatIndex = getFlatIndex();
    if (flatIndex.length === 0) return [];
    const sections = new Set();
    flatIndex.forEach((entry) => {
      if (entry.section) sections.add(entry.section);
    });
    return Array.from(sections).sort();
  };

  const letters = getAllLetters();
  const sections = getSections();
  const filteredIndex = getFilteredIndex();

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-index-page">
        <div className="arc-index-page-header">
          <h1 className="arc-index-page-title">Index</h1>
          <p className="arc-index-page-subtitle">
            Alphabetical listing of all pages
          </p>
        </div>

        <div className="arc-index-page-filters">
          <div className="arc-index-page-search">
            <input
              type="search"
              className="arc-index-page-search-input"
              placeholder="Search within index..."
              value={localSearch}
              onChange={handleSearchChange}
            />
          </div>
          
          {sections.length > 0 && (
            <div className="arc-index-page-section-filter">
              <label htmlFor="section-filter">Filter by section:</label>
              <select
                id="section-filter"
                className="arc-index-page-section-select"
                value={sectionFilter}
                onChange={(e) => handleSectionFilter(e.target.value)}
              >
                <option value="">All sections</option>
                {sections.map((section) => (
                  <option key={section} value={section}>
                    {section}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {isLoading && (
          <div className="arc-index-page-loading">
            <p>Loading index...</p>
          </div>
        )}

        {isError && (
          <div className="arc-index-page-error">
            <p>Error loading index.</p>
          </div>
        )}

        {indexData && !isLoading && !isError && (
          <>
            <div className="arc-index-page-letters">
              <button
                type="button"
                className={`arc-index-page-letter ${!letterFilter ? 'arc-index-page-letter-active' : ''}`}
                onClick={() => handleLetterClick('')}
              >
                All
              </button>
              {letters.map((letter) => {
                // Count pages for this letter
                const letterPages = indexData.index[letter] || [];
                const count = letterPages.length;
                return (
                  <button
                    key={letter}
                    type="button"
                    className={`arc-index-page-letter ${letterFilter === letter ? 'arc-index-page-letter-active' : ''}`}
                    onClick={() => handleLetterClick(letter)}
                    title={`${count} page${count !== 1 ? 's' : ''}`}
                  >
                    {letter}
                    <span className="arc-index-page-letter-count">({count})</span>
                  </button>
                );
              })}
            </div>

            <div className="arc-index-page-content">
              {filteredIndex.length > 0 ? (
                <ul className="arc-index-page-list">
                  {filteredIndex.map((entry) => (
                    <li key={entry.page_id} className="arc-index-page-item">
                      <Link
                        to={`/pages/${entry.page_id}`}
                        className="arc-index-page-link"
                      >
                        <span className="arc-index-page-item-title">
                          {entry.title}
                        </span>
                        {entry.section && (
                          <span className="arc-index-page-item-section">
                            {entry.section}
                          </span>
                        )}
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="arc-index-page-empty">
                  <p>
                    {localSearch || letterFilter || sectionFilter
                      ? 'No pages found matching your filters.'
                      : 'No pages in index.'}
                  </p>
                </div>
              )}
            </div>

            {indexData.index && (
              <div className="arc-index-page-stats">
                <p>
                  Showing {filteredIndex.length} of {getFlatIndex().length} page
                  {getFlatIndex().length !== 1 ? 's' : ''}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
