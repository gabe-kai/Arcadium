import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import {
  fetchComments,
  createComment,
  updateComment,
  deleteComment,
} from '../../services/api/comments';

// Mock axios
vi.mock('axios');
const mockedAxios = axios;

// Mock apiClient
vi.mock('../../services/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

import { apiClient } from '../../services/api/client';

describe('Comments API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetchComments', () => {
    it('fetches comments for a page', async () => {
      const mockComments = [
        {
          id: 'comment-1',
          user: { id: 'user-1', username: 'user1' },
          content: 'Test comment',
          replies: [],
        },
      ];

      apiClient.get.mockResolvedValue({
        data: { comments: mockComments },
      });

      const result = await fetchComments('page-1');

      expect(apiClient.get).toHaveBeenCalledWith('/pages/page-1/comments', {
        params: { include_replies: true },
      });
      expect(result).toEqual(mockComments);
    });

    it('returns empty array when pageId is null', async () => {
      const result = await fetchComments(null);
      expect(result).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('handles API errors gracefully', async () => {
      apiClient.get.mockRejectedValue(new Error('Network error'));

      await expect(fetchComments('page-1')).rejects.toThrow('Network error');
    });
  });

  describe('createComment', () => {
    it('creates a new comment', async () => {
      const commentData = {
        content: 'New comment',
        is_recommendation: false,
        parent_comment_id: null,
      };

      const mockResponse = {
        id: 'comment-1',
        content: 'New comment',
      };

      apiClient.post.mockResolvedValue({ data: mockResponse });

      const result = await createComment('page-1', commentData);

      expect(apiClient.post).toHaveBeenCalledWith('/pages/page-1/comments', commentData);
      expect(result).toEqual(mockResponse);
    });

    it('creates a reply when parent_comment_id is provided', async () => {
      const commentData = {
        content: 'Reply comment',
        is_recommendation: false,
        parent_comment_id: 'comment-1',
      };

      apiClient.post.mockResolvedValue({ data: { id: 'comment-2' } });

      await createComment('page-1', commentData);

      expect(apiClient.post).toHaveBeenCalledWith('/pages/page-1/comments', commentData);
    });
  });

  describe('updateComment', () => {
    it('updates a comment', async () => {
      const mockResponse = {
        id: 'comment-1',
        content: 'Updated content',
      };

      apiClient.put.mockResolvedValue({ data: mockResponse });

      const result = await updateComment('comment-1', 'Updated content');

      expect(apiClient.put).toHaveBeenCalledWith('/comments/comment-1', {
        content: 'Updated content',
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('deleteComment', () => {
    it('deletes a comment', async () => {
      const mockResponse = { message: 'Comment deleted successfully' };

      apiClient.delete.mockResolvedValue({ data: mockResponse });

      const result = await deleteComment('comment-1');

      expect(apiClient.delete).toHaveBeenCalledWith('/comments/comment-1');
      expect(result).toEqual(mockResponse);
    });
  });
});
