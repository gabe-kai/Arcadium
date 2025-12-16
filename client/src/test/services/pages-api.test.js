import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../services/api/client';
import { fetchPage, fetchBreadcrumb, fetchPageNavigation, createPage, updatePage } from '../../services/api/pages';

// Mock the API client
vi.mock('../../services/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

describe('Pages API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetchPage', () => {
    it('returns null when pageId is null', async () => {
      const result = await fetchPage(null);
      expect(result).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('returns null when pageId is undefined', async () => {
      const result = await fetchPage(undefined);
      expect(result).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('fetches page data successfully', async () => {
      const mockPage = { id: 'page-1', title: 'Test Page', content: 'Content' };
      apiClient.get.mockResolvedValue({ data: mockPage });

      const result = await fetchPage('page-1');

      expect(apiClient.get).toHaveBeenCalledWith('/pages/page-1');
      expect(result).toEqual(mockPage);
    });

    it('handles API errors', async () => {
      apiClient.get.mockRejectedValue(new Error('Network error'));

      await expect(fetchPage('page-1')).rejects.toThrow('Network error');
    });
  });

  describe('fetchBreadcrumb', () => {
    it('returns null when pageId is null', async () => {
      const result = await fetchBreadcrumb(null);
      expect(result).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('fetches breadcrumb data successfully', async () => {
      const mockBreadcrumb = [
        { id: 'page-1', title: 'Home', slug: 'home' },
        { id: 'page-2', title: 'Section', slug: 'section' },
      ];
      apiClient.get.mockResolvedValue({ data: { breadcrumb: mockBreadcrumb } });

      const result = await fetchBreadcrumb('page-2');

      expect(apiClient.get).toHaveBeenCalledWith('/pages/page-2/breadcrumb');
      expect(result).toEqual(mockBreadcrumb);
    });

    it('extracts breadcrumb from response', async () => {
      const mockResponse = {
        data: {
          breadcrumb: [{ id: 'page-1', title: 'Home' }],
          other: 'data',
        },
      };
      apiClient.get.mockResolvedValue(mockResponse);

      const result = await fetchBreadcrumb('page-1');
      expect(result).toEqual([{ id: 'page-1', title: 'Home' }]);
    });
  });

  describe('fetchPageNavigation', () => {
    it('returns null when pageId is null', async () => {
      const result = await fetchPageNavigation(null);
      expect(result).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('fetches navigation data successfully', async () => {
      const mockNavigation = {
        previous: { id: 'page-1', title: 'Previous', slug: 'prev' },
        next: { id: 'page-3', title: 'Next', slug: 'next' },
      };
      apiClient.get.mockResolvedValue({ data: mockNavigation });

      const result = await fetchPageNavigation('page-2');

      expect(apiClient.get).toHaveBeenCalledWith('/pages/page-2/navigation');
      expect(result).toEqual(mockNavigation);
    });

    it('handles navigation with only previous', async () => {
      const mockNavigation = {
        previous: { id: 'page-1', title: 'Previous', slug: 'prev' },
        next: null,
      };
      apiClient.get.mockResolvedValue({ data: mockNavigation });

      const result = await fetchPageNavigation('page-2');
      expect(result).toEqual(mockNavigation);
    });

    it('handles navigation with only next', async () => {
      const mockNavigation = {
        previous: null,
        next: { id: 'page-3', title: 'Next', slug: 'next' },
      };
      apiClient.get.mockResolvedValue({ data: mockNavigation });

      const result = await fetchPageNavigation('page-2');
      expect(result).toEqual(mockNavigation);
    });

    it('handles API errors for navigation', async () => {
      apiClient.get.mockRejectedValue(new Error('Network error'));

      await expect(fetchPageNavigation('page-1')).rejects.toThrow('Network error');
    });

    it('handles malformed navigation response', async () => {
      apiClient.get.mockResolvedValue({ data: null });

      const result = await fetchPageNavigation('page-1');
      expect(result).toBeNull();
    });
  });

  describe('createPage', () => {
    it('creates page successfully', async () => {
      const pageData = {
        title: 'New Page',
        content: '# Content',
        status: 'draft',
      };
      const mockResponse = {
        id: 'new-page-id',
        title: 'New Page',
        content: '# Content',
      };
      apiClient.post.mockResolvedValue({ data: mockResponse });

      const result = await createPage(pageData);

      expect(apiClient.post).toHaveBeenCalledWith('/pages', pageData);
      expect(result).toEqual(mockResponse);
    });

    it('handles API errors when creating page', async () => {
      const pageData = { title: 'New Page', content: 'Content' };
      apiClient.post.mockRejectedValue(new Error('Creation failed'));

      await expect(createPage(pageData)).rejects.toThrow('Creation failed');
    });

    it('handles validation errors from API', async () => {
      const pageData = { title: '', content: 'Content' }; // Invalid: empty title
      const error = new Error('Title is required');
      error.response = { status: 400, data: { error: 'Title is required' } };
      apiClient.post.mockRejectedValue(error);

      await expect(createPage(pageData)).rejects.toThrow('Title is required');
    });

    it('handles network timeout errors', async () => {
      const pageData = { title: 'New Page', content: 'Content' };
      const timeoutError = new Error('timeout of 10000ms exceeded');
      timeoutError.code = 'ECONNABORTED';
      apiClient.post.mockRejectedValue(timeoutError);

      await expect(createPage(pageData)).rejects.toThrow();
    });
  });

  describe('updatePage', () => {
    it('updates page successfully', async () => {
      const pageId = 'existing-page-id';
      const pageData = {
        title: 'Updated Page',
        content: '# Updated Content',
      };
      const mockResponse = {
        id: pageId,
        title: 'Updated Page',
        content: '# Updated Content',
      };
      apiClient.put.mockResolvedValue({ data: mockResponse });

      const result = await updatePage(pageId, pageData);

      expect(apiClient.put).toHaveBeenCalledWith(`/pages/${pageId}`, pageData);
      expect(result).toEqual(mockResponse);
    });

    it('handles API errors when updating page', async () => {
      const pageId = 'existing-page-id';
      const pageData = { title: 'Updated Page' };
      apiClient.put.mockRejectedValue(new Error('Update failed'));

      await expect(updatePage(pageId, pageData)).rejects.toThrow('Update failed');
    });

    it('handles 404 when page does not exist', async () => {
      const pageId = 'non-existent-id';
      const pageData = { title: 'Updated Page' };
      const error = new Error('Page not found');
      error.response = { status: 404, data: { error: 'Page not found' } };
      apiClient.put.mockRejectedValue(error);

      await expect(updatePage(pageId, pageData)).rejects.toThrow('Page not found');
    });

    it('handles 403 when user lacks permission', async () => {
      const pageId = 'existing-page-id';
      const pageData = { title: 'Updated Page' };
      const error = new Error('Forbidden');
      error.response = { status: 403, data: { error: 'Forbidden' } };
      apiClient.put.mockRejectedValue(error);

      await expect(updatePage(pageId, pageData)).rejects.toThrow('Forbidden');
    });

    it('handles partial update (only title)', async () => {
      const pageId = 'existing-page-id';
      const pageData = { title: 'Updated Title' };
      apiClient.put.mockResolvedValue({ data: { id: pageId, title: 'Updated Title' } });

      const result = await updatePage(pageId, pageData);

      expect(apiClient.put).toHaveBeenCalledWith(`/pages/${pageId}`, pageData);
      expect(result.title).toBe('Updated Title');
    });

    it('handles partial update (only content)', async () => {
      const pageId = 'existing-page-id';
      const pageData = { content: '# New Content' };
      apiClient.put.mockResolvedValue({ data: { id: pageId, content: '# New Content' } });

      const result = await updatePage(pageId, pageData);

      expect(apiClient.put).toHaveBeenCalledWith(`/pages/${pageId}`, pageData);
      expect(result.content).toBe('# New Content');
    });
  });
});
