import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('should show login page by default', async ({ page }) => {
    await page.goto('/');
    // Should redirect to login since not authenticated
    await expect(page).toHaveURL(/\/(login|setup)/);
  });

  test('should complete setup and redirect to import', async ({ page }) => {
    await page.goto('/setup');

    // Fill in setup form
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('testpass123');
    await page.getByRole('button', { name: /setup|create|register/i }).click();

    // Should redirect to import page after setup
    await expect(page).toHaveURL('/import', { timeout: 10000 });

    // Should show user in sidebar
    await expect(page.getByText('testuser')).toBeVisible();
  });

  test('should login with existing credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('testpass123');
    await page.getByRole('button', { name: /login|sign in/i }).click();

    // Should redirect to import page
    await expect(page).toHaveURL('/import', { timeout: 10000 });
  });

  test('should logout and redirect to login', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('testpass123');
    await page.getByRole('button', { name: /login|sign in/i }).click();
    await expect(page).toHaveURL('/import', { timeout: 10000 });

    // Click logout
    await page.getByRole('button', { name: /logout/i }).click();

    // Should redirect to login
    await expect(page).toHaveURL(/\/(login|setup)/);
  });
});
