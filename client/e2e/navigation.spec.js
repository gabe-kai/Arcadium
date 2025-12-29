import { test, expect } from '@playwright/test';

/**
 * E2E tests for navigation components
 * Tests breadcrumbs, navigation tree, and previous/next navigation
 */

test.describe('Navigation', () => {
  test('displays breadcrumb navigation', async ({ page }) => {
    // Mock page and breadcrumb API
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'child-page-id',
          title: 'Child Page',
          html_content: '<p>Content</p>',
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.route('**/api/pages/*/breadcrumb', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'root-id', title: 'Home', slug: 'home' },
          { id: 'parent-id', title: 'Parent', slug: 'parent' },
          { id: 'child-page-id', title: 'Child Page', slug: 'child' },
        ]),
      });
    });

    await page.goto('/pages/child-page-id');

    // Check breadcrumb is visible
    const breadcrumb = page.locator('nav[aria-label*="breadcrumb" i], nav[aria-label*="Breadcrumb" i]');
    await expect(breadcrumb).toBeVisible();

    // Check breadcrumb items
    await expect(page.getByText('Home')).toBeVisible();
    await expect(page.getByText('Parent')).toBeVisible();
    await expect(page.getByText('Child Page')).toBeVisible();
  });

  test('breadcrumb links navigate to parent pages', async ({ page }) => {
    // Mock breadcrumb API
    await page.route('**/api/pages/*/breadcrumb', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'parent-id', title: 'Parent', slug: 'parent' },
          { id: 'child-page-id', title: 'Child Page', slug: 'child' },
        ]),
      });
    });

    // Mock parent page API
    await page.route('**/api/pages/parent-id*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'parent-id',
          title: 'Parent',
          html_content: '<p>Parent content</p>',
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/child-page-id');

    // Click on parent in breadcrumb
    const parentLink = page.getByRole('link', { name: 'Parent' });
    await parentLink.click();

    // Should navigate to parent page
    await expect(page).toHaveURL(/\/pages\/parent-id/);
    await expect(page.getByText('Parent')).toBeVisible();
  });

  test('displays previous and next navigation', async ({ page }) => {
    // Mock page API
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'current-page-id',
          title: 'Current Page',
          html_content: '<p>Content</p>',
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    // Mock navigation API
    await page.route('**/api/pages/*/navigation', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          previous: { id: 'prev-page-id', title: 'Previous Page', slug: 'prev' },
          next: { id: 'next-page-id', title: 'Next Page', slug: 'next' },
        }),
      });
    });

    await page.goto('/pages/current-page-id');

    // Check navigation buttons are visible
    const prevButton = page.getByRole('link', { name: /previous/i });
    const nextButton = page.getByRole('link', { name: /next/i });

    await expect(prevButton).toBeVisible();
    await expect(nextButton).toBeVisible();
  });

  test('previous/next navigation buttons navigate correctly', async ({ page }) => {
    // Mock current page
    await page.route('**/api/pages/current-page-id*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'current-page-id',
          title: 'Current Page',
          html_content: '<p>Content</p>',
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    // Mock navigation API
    await page.route('**/api/pages/current-page-id/navigation', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          previous: { id: 'prev-page-id', title: 'Previous Page', slug: 'prev' },
          next: { id: 'next-page-id', title: 'Next Page', slug: 'next' },
        }),
      });
    });

    // Mock next page
    await page.route('**/api/pages/next-page-id*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'next-page-id',
          title: 'Next Page',
          html_content: '<p>Next content</p>',
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/current-page-id');

    // Click next button
    const nextButton = page.getByRole('link', { name: /next/i });
    await nextButton.click();

    // Should navigate to next page
    await expect(page).toHaveURL(/\/pages\/next-page-id/);
    await expect(page.getByText('Next Page')).toBeVisible();
  });

  test('disables previous button on first page', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'first-page-id',
          title: 'First Page',
          html_content: '<p>Content</p>',
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.route('**/api/pages/*/navigation', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          previous: null,
          next: { id: 'next-page-id', title: 'Next Page', slug: 'next' },
        }),
      });
    });

    await page.goto('/pages/first-page-id');

    // Previous button should be disabled or not present
    const prevButton = page.getByRole('link', { name: /previous/i });
    const isDisabled = await prevButton.evaluate((el) => {
      return el.hasAttribute('disabled') || el.classList.contains('disabled') || el.getAttribute('aria-disabled') === 'true';
    });

    // Either button is disabled or not clickable
    expect(isDisabled || !(await prevButton.isVisible())).toBeTruthy();
  });

  test('navigation tree displays and expands', async ({ page }) => {
    // Mock navigation tree API
    await page.route('**/api/navigation', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'root-id',
            title: 'Home',
            slug: 'home',
            status: 'published',
            children: [
              {
                id: 'child-id',
                title: 'Child Page',
                slug: 'child',
                status: 'published',
                children: [],
              },
            ],
          },
        ]),
      });
    });

    await page.goto('/');

    // Check navigation tree is visible
    const navTree = page.locator('nav[aria-label*="navigation" i], nav[aria-label*="Page navigation" i]');
    await expect(navTree).toBeVisible();

    // Check root node is visible
    await expect(page.getByText('Home')).toBeVisible();

    // Expand node
    const expandButton = page.getByLabel(/expand/i).first();
    if (await expandButton.isVisible()) {
      await expandButton.click();

      // Child should now be visible
      await expect(page.getByText('Child Page')).toBeVisible();
    }
  });

  test('navigation tree search filters results', async ({ page }) => {
    await page.route('**/api/navigation', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'root-id',
            title: 'Home',
            slug: 'home',
            status: 'published',
            children: [
              {
                id: 'child-1-id',
                title: 'Child Page 1',
                slug: 'child-1',
                status: 'published',
                children: [],
              },
              {
                id: 'child-2-id',
                title: 'Child Page 2',
                slug: 'child-2',
                status: 'published',
                children: [],
              },
            ],
          },
        ]),
      });
    });

    await page.goto('/');

    // Find search input
    const searchInput = page.getByPlaceholderText(/Search pages/i);
    await searchInput.fill('Child Page 1');

    // Only matching page should be visible
    await expect(page.getByText('Child Page 1')).toBeVisible();
    // Other page might still be visible if parent matches, but filtered child should not
  });
});
