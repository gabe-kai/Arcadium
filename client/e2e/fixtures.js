import { test as base } from '@playwright/test';

/**
 * Test fixtures for E2E tests
 * Provides common utilities and setup for tests
 */

/**
 * Mock API responses for testing
 * In a real scenario, you might want to use MSW (Mock Service Worker) or a test API server
 */
export const test = base.extend({
  // Add custom fixtures here if needed
  // For example: mockApi, testUser, etc.
});

export { expect } from '@playwright/test';
