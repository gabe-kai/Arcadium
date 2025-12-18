import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';

/**
 * Search pages by query string
 * @param {string} query - Search query
 * @param {Object} options - Search options
 * @param {string} options.section - Filter by section
 * @param {boolean} options.includeDrafts - Include draft pages
 * @param {number} options.limit - Number of results (default: 20)
 */
export function searchPages(query, options = {}) {
  if (!query || query.trim().length === 0) {
    return Promise.resolve({ results: [], total: 0, query: '' });
  }

  const params = {
    q: query.trim(),
    limit: options.limit || 20,
  };

  if (options.section) {
    params.section = options.section;
  }

  if (options.includeDrafts) {
    params.include_drafts = 'true';
  }

  return apiClient
    .get('/search', { params })
    .then((res) => res.data)
    .catch(() => ({ results: [], total: 0, query: query.trim() }));
}

/**
 * React Query hook for searching pages
 */
export function useSearch(query, options = {}) {
  return useQuery({
    queryKey: ['search', query, options],
    queryFn: () => searchPages(query, options),
    enabled: Boolean(query && query.trim().length > 0),
    staleTime: 30 * 1000, // Cache for 30 seconds
  });
}

/**
 * Get master index (alphabetical listing)
 */
export function fetchIndex() {
  return apiClient.get('/index').then((res) => res.data);
}

/**
 * React Query hook for getting index
 */
export function useIndex() {
  return useQuery({
    queryKey: ['index'],
    queryFn: fetchIndex,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
