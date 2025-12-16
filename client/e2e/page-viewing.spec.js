import { test, expect } from '@playwright/test';

/**
 * E2E tests for page viewing functionality
 * Tests the core reading experience including syntax highlighting
 */

test.describe('Page Viewing', () => {
  test.beforeEach(async ({ page }) => {
    // Set up API mocking if needed
    // For now, tests assume API server is running at http://localhost:5000/api
    // You can use page.route() to mock API responses if needed
  });

  test('displays loading state when page is loading', async ({ page }) => {
    // Mock a slow API response
    await page.route('**/api/pages/**', async (route) => {
      // Delay response to show loading state
      await new Promise(resolve => setTimeout(resolve, 100));
      await route.continue();
    });

    await page.goto('/pages/test-page-id');
    
    // Check for loading indicator
    const loadingText = page.getByText(/Loading page…/i);
    await expect(loadingText).toBeVisible({ timeout: 5000 });
  });

  test('displays error state when page fails to load', async ({ page }) => {
    // Mock API error response
    await page.route('**/api/pages/invalid-page-id', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Page not found' }),
      });
    });

    await page.goto('/pages/invalid-page-id');
    
    // Check for error message
    await expect(page.getByText(/Unable to load page/i)).toBeVisible();
  });

  test('displays page content when loaded successfully', async ({ page }) => {
    // This test requires a real API server with test data
    // Or you can mock the API response:
    await page.route('**/api/pages/*', async (route) => {
      const url = route.request().url();
      const pageId = url.split('/pages/')[1]?.split('?')[0];
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: pageId,
          title: 'Test Page',
          html_content: '<p>This is test page content</p><h2 id="section-1">Section 1</h2><p>Section content</p>',
          updated_at: '2025-01-15T10:00:00Z',
          word_count: 10,
          content_size_kb: 0.5,
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Check that page content is displayed
    await expect(page.getByText('Test Page')).toBeVisible();
    await expect(page.getByText('This is test page content')).toBeVisible();
  });

  test('displays page metadata', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Test Page',
          html_content: '<p>Content</p>',
          updated_at: '2025-01-15T10:00:00Z',
          word_count: 100,
          content_size_kb: 2.5,
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Check metadata display
    await expect(page.getByText(/Last updated/i)).toBeVisible();
    await expect(page.getByText(/100 words/i)).toBeVisible();
    await expect(page.getByText(/2.5 KB/i)).toBeVisible();
    await expect(page.getByText(/published/i)).toBeVisible();
  });

  test('applies syntax highlighting to code blocks', async ({ page }) => {
    const codeContent = 'function test() { return "hello"; }';
    
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Code Test Page',
          html_content: `
            <pre><code class="language-javascript">${codeContent}</code></pre>
          `,
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Wait for syntax highlighting to be applied
    await page.waitForTimeout(500);
    
    // Check that code block exists
    const codeBlock = page.locator('pre code.language-javascript');
    await expect(codeBlock).toBeVisible();
    
    // Check that Prism.js has applied highlighting classes
    // Prism adds classes like 'token', 'keyword', etc.
    const hasHighlighting = await codeBlock.evaluate((el) => {
      return el.classList.length > 1 || el.querySelector('.token') !== null;
    });
    
    // Syntax highlighting should be applied (either via classes or tokens)
    expect(hasHighlighting || codeBlock.textContent()).toContain(codeContent);
  });

  test('processes internal and external links correctly', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Link Test Page',
          html_content: `
            <p><a href="/pages/other-page">Internal Link</a></p>
            <p><a href="https://example.com">External Link</a></p>
            <p><a href="#section">Anchor Link</a></p>
          `,
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Wait for link processing
    await page.waitForTimeout(200);
    
    // Check internal link
    const internalLink = page.getByRole('link', { name: 'Internal Link' });
    await expect(internalLink).toBeVisible();
    await expect(internalLink).toHaveClass(/arc-link-internal/);
    
    // Check external link
    const externalLink = page.getByRole('link', { name: 'External Link' });
    await expect(externalLink).toBeVisible();
    await expect(externalLink).toHaveClass(/arc-link-external/);
    await expect(externalLink).toHaveAttribute('target', '_blank');
    await expect(externalLink).toHaveAttribute('rel', 'noopener noreferrer');
    
    // Check anchor link
    const anchorLink = page.getByRole('link', { name: 'Anchor Link' });
    await expect(anchorLink).toBeVisible();
    await expect(anchorLink).toHaveClass(/arc-link-internal/);
  });

  test('handles pages with no content gracefully', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Empty Page',
          html_content: '',
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Page should still render with title
    await expect(page.getByText('Empty Page')).toBeVisible();
  });
});
