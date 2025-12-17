import { test, expect } from '@playwright/test';

/**
 * E2E tests for authentication flow
 * Tests sign-in, registration, and sign-out functionality
 */

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock auth API
    await page.route('**/api/auth/**', async (route) => {
      const url = route.request().url();
      const method = route.request().method();
      const postData = route.request().postDataJSON();

      // Register endpoint
      if (url.includes('/auth/register') && method === 'POST') {
        if (postData.username === 'existinguser') {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Username already exists' }),
          });
        } else {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              user: {
                id: 'user-123',
                username: postData.username,
                email: postData.email,
                role: 'player',
                is_first_user: false,
              },
              token: 'mock-access-token',
              refresh_token: 'mock-refresh-token',
              expires_in: 3600,
            }),
          });
        }
        return;
      }

      // Login endpoint
      if (url.includes('/auth/login') && method === 'POST') {
        if (postData.username === 'wronguser' || postData.password === 'wrongpass') {
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Invalid username or password' }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              user: {
                id: 'user-123',
                username: postData.username,
                email: 'test@example.com',
                role: 'admin',
              },
              token: 'mock-access-token',
              refresh_token: 'mock-refresh-token',
              expires_in: 3600,
            }),
          });
        }
        return;
      }

      // Verify endpoint
      if (url.includes('/auth/verify') && method === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            valid: true,
            user: {
              id: 'user-123',
              username: 'testuser',
              role: 'admin',
            },
            expires_at: '2025-12-17T10:00:00Z',
          }),
        });
        return;
      }

      await route.continue();
    });
  });

  test('displays sign in button when not authenticated', async ({ page }) => {
    await page.goto('/');
    
    const signInButton = page.getByRole('button', { name: /sign in/i });
    await expect(signInButton).toBeVisible();
  });

  test('navigates to sign-in page when sign in button is clicked', async ({ page }) => {
    await page.goto('/');
    
    await page.getByRole('button', { name: /sign in/i }).click();
    
    await expect(page).toHaveURL(/\/signin/);
    await expect(page.getByText(/Sign In|Create Account/i)).toBeVisible();
  });

  test('displays login form by default', async ({ page }) => {
    await page.goto('/signin');
    
    await expect(page.getByLabel('Username')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.queryByLabel('Email')).not.toBeVisible();
  });

  test('successfully logs in with valid credentials', async ({ page }) => {
    await page.goto('/signin');
    
    await page.getByLabel('Username').fill('testuser');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Should navigate to home after login
    await expect(page).toHaveURL('/', { timeout: 2000 });
    
    // Should show user menu instead of sign in button
    await expect(page.getByText('testuser')).toBeVisible();
    await expect(page.getByRole('button', { name: /sign out/i })).toBeVisible();
  });

  test('displays error message on login failure', async ({ page }) => {
    await page.goto('/signin');
    
    await page.getByLabel('Username').fill('wronguser');
    await page.getByLabel('Password').fill('wrongpass');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    await expect(page.getByText(/Invalid username or password/i)).toBeVisible();
  });

  test('switches to register mode', async ({ page }) => {
    await page.goto('/signin');
    
    await page.getByRole('button', { name: /sign up/i }).click();
    
    await expect(page.getByText('Create Account')).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
  });

  test('successfully registers a new user', async ({ page }) => {
    await page.goto('/signin');
    
    // Switch to register
    await page.getByRole('button', { name: /sign up/i }).click();
    
    await page.getByLabel('Username').fill('newuser');
    await page.getByLabel('Email').fill('new@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: /create account/i }).click();
    
    // Should show success message
    await expect(page.getByText(/Registration successful/i)).toBeVisible({ timeout: 2000 });
    
    // Should navigate to home after delay
    await expect(page).toHaveURL('/', { timeout: 3000 });
  });

  test('displays error message on registration failure', async ({ page }) => {
    await page.goto('/signin');
    
    // Switch to register
    await page.getByRole('button', { name: /sign up/i }).click();
    
    await page.getByLabel('Username').fill('existinguser');
    await page.getByLabel('Email').fill('existing@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: /create account/i }).click();
    
    await expect(page.getByText(/Username already exists/i)).toBeVisible();
  });

  test('validates required fields in login form', async ({ page }) => {
    await page.goto('/signin');
    
    // Try to submit without filling fields
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // HTML5 validation should prevent submission
    const usernameInput = page.getByLabel('Username');
    await expect(usernameInput).toBeInvalid();
  });

  test('validates required fields in register form', async ({ page }) => {
    await page.goto('/signin');
    
    // Switch to register
    await page.getByRole('button', { name: /sign up/i }).click();
    
    // Try to submit without filling fields
    await page.getByRole('button', { name: /create account/i }).click();
    
    // HTML5 validation should prevent submission
    const usernameInput = page.getByLabel('Username');
    await expect(usernameInput).toBeInvalid();
  });

  test('signs out successfully', async ({ page }) => {
    // First login
    await page.goto('/signin');
    await page.getByLabel('Username').fill('testuser');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for navigation
    await expect(page).toHaveURL('/', { timeout: 2000 });
    
    // Sign out
    await page.getByRole('button', { name: /sign out/i }).click();
    
    // Should navigate to home
    await expect(page).toHaveURL('/');
    
    // Should show sign in button again
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
    await expect(page.queryByRole('button', { name: /sign out/i })).not.toBeVisible();
  });

  test('displays user menu when authenticated', async ({ page }) => {
    // First login
    await page.goto('/signin');
    await page.getByLabel('Username').fill('testuser');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for navigation
    await expect(page).toHaveURL('/', { timeout: 2000 });
    
    // Should show username
    await expect(page.getByText('testuser')).toBeVisible();
    
    // Should show sign out button
    await expect(page.getByRole('button', { name: /sign out/i })).toBeVisible();
  });
});
