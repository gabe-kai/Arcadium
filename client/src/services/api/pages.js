import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';

export function fetchPage(pageId) {
  if (!pageId) return null;
  return apiClient.get(`/pages/${pageId}`).then((res) => res.data);
}

export function usePage(pageId) {
  return useQuery({
    queryKey: ['page', pageId],
    queryFn: () => fetchPage(pageId),
    enabled: Boolean(pageId),
  });
}

export function fetchBreadcrumb(pageId) {
  if (!pageId) return null;
  return apiClient.get(`/pages/${pageId}/breadcrumb`).then((res) => res.data.breadcrumb);
}

export function useBreadcrumb(pageId) {
  return useQuery({
    queryKey: ['breadcrumb', pageId],
    queryFn: () => fetchBreadcrumb(pageId),
    enabled: Boolean(pageId),
  });
}

export function fetchPageNavigation(pageId) {
  if (!pageId) return null;
  return apiClient.get(`/pages/${pageId}/navigation`).then((res) => res.data);
}

export function usePageNavigation(pageId) {
  return useQuery({
    queryKey: ['pageNavigation', pageId],
    queryFn: () => fetchPageNavigation(pageId),
    enabled: Boolean(pageId),
  });
}

export function fetchNavigationTree() {
  return apiClient.get('/navigation').then((res) => res.data.tree);
}

export function useNavigationTree() {
  return useQuery({
    queryKey: ['navigationTree'],
    queryFn: fetchNavigationTree,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

// Mutations for creating and updating pages
export function createPage(pageData) {
  return apiClient.post('/pages', pageData).then((res) => res.data);
}

export function updatePage(pageId, pageData) {
  return apiClient.put(`/pages/${pageId}`, pageData).then((res) => res.data);
}

// Search pages for parent selection
export function searchPages(query) {
  if (!query || query.trim().length === 0) {
    return Promise.resolve([]);
  }
  return apiClient
    .get('/pages', { params: { search: query.trim(), limit: 20 } })
    .then((res) => res.data.pages || [])
    .catch(() => []); // Return empty array on error
}

// Validate slug uniqueness (for new pages or when slug changes)
export function validateSlug(slug, excludePageId = null) {
  const trimmedSlug = slug ? slug.trim() : '';
  
  if (!trimmedSlug || trimmedSlug.length === 0) {
    return Promise.resolve({ valid: false, message: 'Slug is required' });
  }
  
  // Basic validation
  if (!/^[a-z0-9-]+$/.test(trimmedSlug)) {
    return Promise.resolve({ 
      valid: false, 
      message: 'Slug can only contain lowercase letters, numbers, and hyphens' 
    });
  }
  
  // Check uniqueness via API (would need a dedicated endpoint or use search)
  // For now, we'll use a simple approach - check if a page with this slug exists
  return apiClient
    .get('/pages', { params: { slug: trimmedSlug } })
    .then((res) => {
      const pages = res.data.pages || [];
      const conflictingPage = pages.find(p => p.id !== excludePageId);
      
      if (conflictingPage) {
        return { 
          valid: false, 
          message: `Slug "${trimmedSlug}" is already in use by another page` 
        };
      }
      
      return { valid: true };
    })
    .catch(() => ({ valid: true })); // Assume valid on error (optimistic)
}

// Version history API functions
export function fetchVersionHistory(pageId) {
  if (!pageId) return null;
  return apiClient.get(`/pages/${pageId}/versions`).then((res) => res.data.versions || []);
}

export function useVersionHistory(pageId) {
  return useQuery({
    queryKey: ['versionHistory', pageId],
    queryFn: () => fetchVersionHistory(pageId),
    enabled: Boolean(pageId),
  });
}

export function fetchVersion(pageId, version) {
  if (!pageId || !version) return null;
  return apiClient.get(`/pages/${pageId}/versions/${version}`).then((res) => res.data);
}

export function useVersion(pageId, version) {
  return useQuery({
    queryKey: ['version', pageId, version],
    queryFn: () => fetchVersion(pageId, version),
    enabled: Boolean(pageId && version),
  });
}

export function compareVersions(pageId, version1, version2) {
  if (!pageId || !version1 || !version2) return null;
  return apiClient
    .get(`/pages/${pageId}/versions/compare`, {
      params: { from: version1, to: version2 },
    })
    .then((res) => res.data);
}

export function restoreVersion(pageId, version) {
  if (!pageId || !version) return null;
  return apiClient.post(`/pages/${pageId}/versions/${version}/restore`).then((res) => res.data);
}
