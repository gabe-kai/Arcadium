import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';

/**
 * Fetch comments for a page
 */
export function fetchComments(pageId) {
  if (!pageId) return null;
  return apiClient
    .get(`/pages/${pageId}/comments`, { params: { include_replies: true } })
    .then((res) => res.data.comments || []);
}

/**
 * React Query hook for fetching comments
 */
export function useComments(pageId) {
  return useQuery({
    queryKey: ['comments', pageId],
    queryFn: () => fetchComments(pageId),
    enabled: Boolean(pageId),
  });
}

/**
 * Create a new comment or reply
 */
export function createComment(pageId, commentData) {
  return apiClient.post(`/pages/${pageId}/comments`, commentData).then((res) => res.data);
}

/**
 * React Query mutation for creating comments
 */
export function useCreateComment(pageId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (commentData) => createComment(pageId, commentData),
    onSuccess: () => {
      // Invalidate comments query to refetch
      queryClient.invalidateQueries({ queryKey: ['comments', pageId] });
    },
  });
}

/**
 * Update a comment
 */
export function updateComment(commentId, content) {
  return apiClient.put(`/comments/${commentId}`, { content }).then((res) => res.data);
}

/**
 * React Query mutation for updating comments
 */
export function useUpdateComment(pageId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ commentId, content }) => updateComment(commentId, content),
    onSuccess: () => {
      // Invalidate comments query to refetch
      queryClient.invalidateQueries({ queryKey: ['comments', pageId] });
    },
  });
}

/**
 * Delete a comment
 */
export function deleteComment(commentId) {
  return apiClient.delete(`/comments/${commentId}`).then((res) => res.data);
}

/**
 * React Query mutation for deleting comments
 */
export function useDeleteComment(pageId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (commentId) => deleteComment(commentId),
    onSuccess: () => {
      // Invalidate comments query to refetch
      queryClient.invalidateQueries({ queryKey: ['comments', pageId] });
    },
  });
}
