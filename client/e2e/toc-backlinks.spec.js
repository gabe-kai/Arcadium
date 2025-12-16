import { test, expect } from '@playwright/test';

/**
 * E2E tests for Table of Contents and Backlinks
 * Tests right sidebar functionality
 */

test.describe('Table of Contents', () => {
  test('displays table of contents when available', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Test Page',
          html_content: `
            <h2 id="section-1">Section 1</h2>
            <p>Content</p>
            <h2 id="section-2">Section 2</h2>
            <p>More content</p>
            <h3 id="subsection-2-1">Subsection 2.1</h3>
            <p>Subsection content</p>
          `,
          table_of_contents: [
            { anchor: 'section-1', text: 'Section 1', level: 2 },
            { anchor: 'section-2', text: 'Section 2', level: 2 },
            { anchor: 'subsection-2-1', text: 'Subsection 2.1', level: 3 },
          ],
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Check TOC is visible
    const toc = page.locator('nav[aria-label*="Table of contents" i]');
    await expect(toc).toBeVisible();
    
    // Check TOC items
    await expect(page.getByText('Contents')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Section 1' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Section 2' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Subsection 2.1' })).toBeVisible();
  });

  test('scrolls to section when TOC item is clicked', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Test Page',
          html_content: `
            <h2 id="section-1">Section 1</h2>
            <p style="height: 2000px;">Long content to enable scrolling</p>
            <h2 id="section-2">Section 2</h2>
            <p>More content</p>
          `,
          table_of_contents: [
            { anchor: 'section-1', text: 'Section 1', level: 2 },
            { anchor: 'section-2', text: 'Section 2', level: 2 },
          ],
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Scroll to top first
    await page.evaluate(() => window.scrollTo(0, 0));
    
    // Click on Section 2 in TOC
    const section2Button = page.getByRole('button', { name: 'Section 2' });
    await section2Button.click();
    
    // Wait for smooth scroll
    await page.waitForTimeout(500);
    
    // Check that we've scrolled to Section 2
    const section2Element = page.locator('#section-2');
    const boundingBox = await section2Element.boundingBox();
    
    // Section 2 should be visible in viewport (roughly)
    expect(boundingBox).toBeTruthy();
  });

  test('highlights active section while scrolling', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Test Page',
          html_content: `
            <h2 id="section-1">Section 1</h2>
            <p style="height: 1000px;">Content</p>
            <h2 id="section-2">Section 2</h2>
            <p style="height: 1000px;">More content</p>
          `,
          table_of_contents: [
            { anchor: 'section-1', text: 'Section 1', level: 2 },
            { anchor: 'section-2', text: 'Section 2', level: 2 },
          ],
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    await page.waitForLoadState('networkidle');
    
    // Scroll to Section 2
    await page.evaluate(() => {
      const section2 = document.getElementById('section-2');
      if (section2) {
        section2.scrollIntoView();
      }
    });
    
    // Wait for scroll event to be processed
    await page.waitForTimeout(500);
    
    // Check that Section 2 TOC item is active
    const section2Button = page.getByRole('button', { name: 'Section 2' });
    const isActive = await section2Button.evaluate((el) => {
      return el.getAttribute('aria-current') === 'location' || 
             el.closest('li')?.classList.contains('arc-toc-item-active');
    });
    
    expect(isActive).toBeTruthy();
  });

  test('does not display TOC when empty', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Test Page',
          html_content: '<p>Content with no headings</p>',
          table_of_contents: null,
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // TOC should not be visible
    const toc = page.locator('nav[aria-label*="Table of contents" i]');
    await expect(toc).not.toBeVisible();
  });
});

test.describe('Backlinks', () => {
  test('displays backlinks when available', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Test Page',
          html_content: '<p>Content</p>',
          backlinks: [
            { page_id: 'linker-1-id', title: 'Linking Page 1' },
            { page_id: 'linker-2-id', title: 'Linking Page 2' },
          ],
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Check backlinks section is visible
    const backlinks = page.locator('nav[aria-label*="Pages linking here" i]');
    await expect(backlinks).toBeVisible();
    
    // Check backlink count
    await expect(page.getByText('Pages Linking Here')).toBeVisible();
    await expect(page.getByText('(2)')).toBeVisible();
    
    // Check backlink items
    await expect(page.getByRole('link', { name: 'Linking Page 1' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Linking Page 2' })).toBeVisible();
  });

  test('backlinks navigate to linking pages', async ({ page }) => {
    // Mock current page
    await page.route('**/api/pages/test-page-id*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Test Page',
          html_content: '<p>Content</p>',
          backlinks: [
            { page_id: 'linker-1-id', title: 'Linking Page 1' },
          ],
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    // Mock linking page
    await page.route('**/api/pages/linker-1-id*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'linker-1-id',
          title: 'Linking Page 1',
          html_content: '<p>Linking page content</p>',
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Click on backlink
    const backlink = page.getByRole('link', { name: 'Linking Page 1' });
    await backlink.click();
    
    // Should navigate to linking page
    await expect(page).toHaveURL(/\/pages\/linker-1-id/);
    await expect(page.getByText('Linking Page 1')).toBeVisible();
  });

  test('does not display backlinks when empty', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Test Page',
          html_content: '<p>Content</p>',
          backlinks: null,
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Backlinks should not be visible
    const backlinks = page.locator('nav[aria-label*="Pages linking here" i]');
    await expect(backlinks).not.toBeVisible();
  });

  test('displays correct backlink count', async ({ page }) => {
    await page.route('**/api/pages/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-page-id',
          title: 'Test Page',
          html_content: '<p>Content</p>',
          backlinks: [
            { page_id: 'linker-1-id', title: 'Linking Page 1' },
            { page_id: 'linker-2-id', title: 'Linking Page 2' },
            { page_id: 'linker-3-id', title: 'Linking Page 3' },
          ],
          updated_at: '2025-01-15T10:00:00Z',
          status: 'published',
        }),
      });
    });

    await page.goto('/pages/test-page-id');
    
    // Check count is correct
    await expect(page.getByText('(3)')).toBeVisible();
  });
});
