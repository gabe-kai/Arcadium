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
