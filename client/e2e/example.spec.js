import { test, expect } from '@playwright/test';

/**
 * Example E2E test - can be removed or used as a template
 */
test('homepage loads', async ({ page }) => {
  await page.goto('/');
  
  // Check that the homepage content is visible
  await expect(page.getByText(/Welcome to the Arcadium Wiki/i)).toBeVisible();
});
