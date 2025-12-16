# E2E Testing with Playwright

This directory contains end-to-end (E2E) tests for the Arcadium Wiki UI using [Playwright](https://playwright.dev/).

## Overview

E2E tests verify that the entire application works correctly from a user's perspective, including:
- Page viewing and content rendering
- Syntax highlighting for code blocks
- Navigation (breadcrumbs, navigation tree, previous/next)
- Table of Contents scrolling and highlighting
- Backlinks navigation
- Link processing (internal vs external)

## Running Tests

### Prerequisites

1. **Install Playwright browsers** (first time only):
   ```bash
   npx playwright install
   ```

2. **Start the development server** (if not using `webServer` in config):
   ```bash
   npm run dev
   ```

   The Playwright config includes a `webServer` that automatically starts the dev server, so you typically don't need to run this manually.

### Run All E2E Tests

```bash
npm run test:e2e
```

### Run Tests in UI Mode

Interactive mode with a visual test runner:

```bash
npm run test:e2e:ui
```

### Run Tests in Headed Mode

See the browser while tests run:

```bash
npm run test:e2e:headed
```

### Debug Tests

Step through tests with the Playwright Inspector:

```bash
npm run test:e2e:debug
```

### View Test Report

After running tests, view the HTML report:

```bash
npm run test:e2e:report
```

## Test Structure

```
e2e/
├── README.md              # This file
├── fixtures.js            # Test fixtures and utilities
├── example.spec.js        # Example test (can be removed)
├── page-viewing.spec.js   # Tests for page viewing and syntax highlighting
├── navigation.spec.js     # Tests for navigation components
└── toc-backlinks.spec.js # Tests for TOC and backlinks
```

## Test Files

### `page-viewing.spec.js`
Tests the core reading experience:
- Loading and error states
- Page content rendering
- Metadata display
- Syntax highlighting for code blocks
- Internal/external link processing
- Empty content handling

### `navigation.spec.js`
Tests navigation components:
- Breadcrumb navigation and linking
- Previous/Next navigation buttons
- Navigation tree display and expansion
- Tree search functionality
- Disabled states for edge cases

### `toc-backlinks.spec.js`
Tests right sidebar features:
- Table of Contents display
- TOC scrolling to sections
- Active section highlighting
- Backlinks display and navigation
- Empty state handling

## API Mocking

The tests use Playwright's `page.route()` to mock API responses. This allows tests to:
- Run without a real API server
- Test specific scenarios (errors, edge cases)
- Run faster and more reliably

To modify API responses in tests, use:

```javascript
await page.route('**/api/pages/*', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      // Your mock data
    }),
  });
});
```

## Configuration

E2E tests are configured in `playwright.config.js` at the project root. Key settings:

- **Base URL**: `http://localhost:3000` (configurable via `PLAYWRIGHT_BASE_URL`)
- **Web Server**: Automatically starts `npm run dev` before tests
- **Browsers**: Tests run on Chromium, Firefox, and WebKit
- **Retries**: 2 retries on CI, 0 locally
- **Screenshots**: Captured on failure
- **Traces**: Collected on retry

## Writing New Tests

1. Create a new test file in `e2e/` with `.spec.js` extension
2. Import test utilities:
   ```javascript
   import { test, expect } from '@playwright/test';
   ```
3. Use `test.describe()` to group related tests
4. Use `test.beforeEach()` for setup
5. Mock API responses as needed
6. Use Playwright's [best practices](https://playwright.dev/docs/best-practices)

Example:

```javascript
import { test, expect } from '@playwright/test';

test.describe('My Feature', () => {
  test('does something', async ({ page }) => {
    // Mock API
    await page.route('**/api/endpoint', async (route) => {
      await route.fulfill({ /* ... */ });
    });

    // Navigate
    await page.goto('/my-page');

    // Assert
    await expect(page.getByText('Expected Text')).toBeVisible();
  });
});
```

## CI/CD Integration

For CI/CD pipelines:

1. Install dependencies: `npm ci`
2. Install Playwright browsers: `npx playwright install --with-deps`
3. Run tests: `npm run test:e2e`

The config automatically:
- Fails the build if `test.only` is left in code
- Retries failed tests (2 times on CI)
- Generates HTML reports
- Captures screenshots on failure

## Troubleshooting

### Tests fail with "Navigation timeout"
- Ensure the dev server is running on port 3000
- Check that `VITE_WIKI_API_BASE_URL` is set correctly if using a real API

### Tests fail with "Element not found"
- Increase timeout: `await expect(element).toBeVisible({ timeout: 10000 })`
- Check that API mocks are set up correctly
- Verify selectors match the actual DOM structure

### Browser not found
- Run `npx playwright install` to install browsers
- Check that Playwright is installed: `npm list @playwright/test`

## Best Practices

1. **Mock API responses** - Don't rely on a real API server
2. **Use data-testid** - Prefer stable selectors over CSS classes
3. **Wait for network idle** - Use `page.waitForLoadState('networkidle')` when needed
4. **Test user flows** - Focus on what users actually do
5. **Keep tests independent** - Each test should be able to run alone
6. **Use meaningful assertions** - Test behavior, not implementation

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright API Reference](https://playwright.dev/docs/api/class-playwright)
