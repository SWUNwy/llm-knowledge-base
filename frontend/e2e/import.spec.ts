import { test, expect } from '@playwright/test';

// Login helper
async function login(page) {
  await page.goto('/login');
  await page.getByLabel(/username/i).fill('testuser');
  await page.getByLabel(/password/i).fill('testpass123');
  await page.getByRole('button', { name: /login|sign in/i }).click();
  await expect(page).toHaveURL('/import', { timeout: 10000 });
}

test.describe('Import Flow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should import from URL', async ({ page }) => {
    // Should be on import page
    await expect(page.getByText('Import')).toBeVisible();

    // Fill URL import form
    await page.getByPlaceholder(/https?:\/\//i).first().fill('https://example.com');

    // Add tags
    await page.getByPlaceholder(/comma separated/i).fill('test, example');

    // Click import
    await page.getByRole('button', { name: /import url/i }).click();

    // Should show success in recent imports
    await expect(page.getByText(/example\.com|untitled/i)).toBeVisible({
      timeout: 30000,
    });
  });

  test('should import from file', async ({ page }) => {
    // Fill file path
    await page.getByPlaceholder(/\/path\/to/i).fill('/tmp/test-import.csv');

    // Click import file
    await page.getByRole('button', { name: /import file/i }).click();

    // Should show result in recent imports
    await expect(page.locator('[class*="rounded-lg"]')).toBeVisible({
      timeout: 15000,
    });
  });

  test('should show error for invalid file path', async ({ page }) => {
    await page.getByPlaceholder(/\/path\/to/i).fill('/nonexistent/file.pdf');
    await page.getByRole('button', { name: /import file/i }).click();

    // Should show error
    await expect(page.getByText(/not found|error/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test('should navigate between import types', async ({ page }) => {
    // All import forms should be visible
    await expect(page.getByText('Import from URL')).toBeVisible();
    await expect(page.getByText('Import from File')).toBeVisible();
    await expect(page.getByText('Import from Video')).toBeVisible();
    await expect(page.getByText('Import from GitHub')).toBeVisible();
  });
});
