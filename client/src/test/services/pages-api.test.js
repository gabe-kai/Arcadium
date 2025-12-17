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

  describe('searchPages', () => {
    it('returns empty array for empty query', async () => {
      const { searchPages } = await import('../../services/api/pages');
      const result = await searchPages('');
      expect(result).toEqual([]);
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('returns empty array for null query', async () => {
      const { searchPages } = await import('../../services/api/pages');
      const result = await searchPages(null);
      expect(result).toEqual([]);
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('searches pages successfully', async () => {
      const { searchPages } = await import('../../services/api/pages');
      const mockPages = [
        { id: 'page-1', title: 'Test Page 1' },
        { id: 'page-2', title: 'Test Page 2' },
      ];
      apiClient.get.mockResolvedValue({ data: { pages: mockPages } });

      const result = await searchPages('Test');

      expect(apiClient.get).toHaveBeenCalledWith('/pages', { params: { search: 'Test', limit: 20 } });
      expect(result).toEqual(mockPages);
    });

    it('trims query before searching', async () => {
      const { searchPages } = await import('../../services/api/pages');
      apiClient.get.mockResolvedValue({ data: { pages: [] } });

      await searchPages('  Test  ');

      expect(apiClient.get).toHaveBeenCalledWith('/pages', { params: { search: 'Test', limit: 20 } });
    });

    it('handles API errors gracefully', async () => {
      const { searchPages } = await import('../../services/api/pages');
      apiClient.get.mockRejectedValue(new Error('Network error'));

      const result = await searchPages('Test');

      expect(result).toEqual([]);
    });

    it('handles missing pages in response', async () => {
      const { searchPages } = await import('../../services/api/pages');
      apiClient.get.mockResolvedValue({ data: {} });

      const result = await searchPages('Test');

      expect(result).toEqual([]);
    });
  });

  describe('validateSlug', () => {
    it('returns invalid for empty slug', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      const result = await validateSlug('');
      expect(result).toEqual({ valid: false, message: 'Slug is required' });
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('returns invalid for null slug', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      const result = await validateSlug(null);
      expect(result).toEqual({ valid: false, message: 'Slug is required' });
    });

    it('returns invalid for slug with invalid characters', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      const result = await validateSlug('invalid slug!');
      expect(result).toEqual({ 
        valid: false, 
        message: 'Slug can only contain lowercase letters, numbers, and hyphens' 
      });
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('validates unique slug successfully', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      apiClient.get.mockResolvedValue({ data: { pages: [] } });

      const result = await validateSlug('test-slug');

      expect(apiClient.get).toHaveBeenCalledWith('/pages', { params: { slug: 'test-slug' } });
      expect(result).toEqual({ valid: true });
    });

    it('returns invalid for duplicate slug', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      const mockPages = [
        { id: 'other-page-id', title: 'Other Page', slug: 'test-slug' },
      ];
      apiClient.get.mockResolvedValue({ data: { pages: mockPages } });

      const result = await validateSlug('test-slug');

      expect(result).toEqual({ 
        valid: false, 
        message: 'Slug "test-slug" is already in use by another page' 
      });
    });

    it('excludes specified page from validation', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      const mockPages = [
        { id: 'current-page-id', title: 'Current Page', slug: 'test-slug' },
      ];
      apiClient.get.mockResolvedValue({ data: { pages: mockPages } });

      const result = await validateSlug('test-slug', 'current-page-id');

      expect(result).toEqual({ valid: true });
    });

    it('handles API errors optimistically', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      apiClient.get.mockRejectedValue(new Error('Network error'));

      const result = await validateSlug('test-slug');

      expect(result).toEqual({ valid: true });
    });

    it('trims slug before validation', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      apiClient.get.mockResolvedValue({ data: { pages: [] } });

      const result = await validateSlug('  test-slug  ');

      expect(apiClient.get).toHaveBeenCalledWith('/pages', { params: { slug: 'test-slug' } });
      expect(result.valid).toBe(true);
    });

    it('validates slug with hyphens', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      apiClient.get.mockResolvedValue({ data: { pages: [] } });

      const result = await validateSlug('test-slug-123');

      expect(result).toEqual({ valid: true });
    });

    it('validates slug with numbers', async () => {
      const { validateSlug } = await import('../../services/api/pages');
      apiClient.get.mockResolvedValue({ data: { pages: [] } });

      const result = await validateSlug('page123');

      expect(result).toEqual({ valid: true });
    });
  });

  describe('fetchVersionHistory', () => {
    it('returns null when pageId is null', async () => {
      const { fetchVersionHistory } = await import('../../services/api/pages');
      const result = await fetchVersionHistory(null);
      expect(result).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('fetches version history successfully', async () => {
      const mockVersions = [
        {
          version: 5,
          created_at: '2024-01-15T10:30:00Z',
          changed_by: { id: 'user-1', username: 'writer1' },
        },
      ];

      apiClient.get.mockResolvedValue({ data: { versions: mockVersions } });

      const { fetchVersionHistory } = await import('../../services/api/pages');
      const result = await fetchVersionHistory('page-1');

      expect(apiClient.get).toHaveBeenCalledWith('/pages/page-1/versions');
      expect(result).toEqual(mockVersions);
    });

    it('returns empty array when no versions exist', async () => {
      apiClient.get.mockResolvedValue({ data: { versions: [] } });

      const { fetchVersionHistory } = await import('../../services/api/pages');
      const result = await fetchVersionHistory('page-1');

      expect(result).toEqual([]);
    });

    it('handles API errors', async () => {
      apiClient.get.mockRejectedValue(new Error('Network error'));

      const { fetchVersionHistory } = await import('../../services/api/pages');
      await expect(fetchVersionHistory('page-1')).rejects.toThrow('Network error');
    });
  });

  describe('fetchVersion', () => {
    it('returns null when pageId is null', async () => {
      const { fetchVersion } = await import('../../services/api/pages');
      const result = await fetchVersion(null, 5);
      expect(result).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('returns null when version is null', async () => {
      const { fetchVersion } = await import('../../services/api/pages');
      const result = await fetchVersion('page-1', null);
      expect(result).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('fetches specific version successfully', async () => {
      const mockVersion = {
        version: 5,
        content: '# Content',
        created_at: '2024-01-15T10:30:00Z',
      };

      apiClient.get.mockResolvedValue({ data: mockVersion });

      const { fetchVersion } = await import('../../services/api/pages');
      const result = await fetchVersion('page-1', 5);

      expect(apiClient.get).toHaveBeenCalledWith('/pages/page-1/versions/5');
      expect(result).toEqual(mockVersion);
    });
  });

  describe('compareVersions', () => {
    it('returns null when pageId is null', async () => {
      const { compareVersions } = await import('../../services/api/pages');
      const result = await compareVersions(null, 1, 2);
      expect(result).toBeNull();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('compares two versions successfully', async () => {
      const mockComparison = {
        from_version: 3,
        to_version: 5,
        diff: {
          additions: 10,
          deletions: 5,
        },
      };

      apiClient.get.mockResolvedValue({ data: mockComparison });

      const { compareVersions } = await import('../../services/api/pages');
      const result = await compareVersions('page-1', 3, 5);

      expect(apiClient.get).toHaveBeenCalledWith('/pages/page-1/versions/compare', {
        params: { from: 3, to: 5 },
      });
      expect(result).toEqual(mockComparison);
    });
  });

  describe('restoreVersion', () => {
    it('returns null when pageId is null', async () => {
      const { restoreVersion } = await import('../../services/api/pages');
      const result = await restoreVersion(null, 5);
      expect(result).toBeNull();
      expect(apiClient.post).not.toHaveBeenCalled();
    });

    it('returns null when version is null', async () => {
      const { restoreVersion } = await import('../../services/api/pages');
      const result = await restoreVersion('page-1', null);
      expect(result).toBeNull();
      expect(apiClient.post).not.toHaveBeenCalled();
    });

    it('restores version successfully', async () => {
      const mockResponse = {
        message: 'Version restored successfully',
        new_version: 6,
        page: { id: 'page-1', version: 6 },
      };

      apiClient.post.mockResolvedValue({ data: mockResponse });

      const { restoreVersion } = await import('../../services/api/pages');
      const result = await restoreVersion('page-1', 5);

      expect(apiClient.post).toHaveBeenCalledWith('/pages/page-1/versions/5/restore');
      expect(result).toEqual(mockResponse);
    });
  });
});
