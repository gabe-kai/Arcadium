import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../../services/api/client';
import { fetchPage, fetchBreadcrumb, fetchPageNavigation } from '../../services/api/pages';

// Mock the API client
vi.mock('../../services/api/client', () => ({
  apiClient: {
    get: vi.fn(),
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
  });
});
