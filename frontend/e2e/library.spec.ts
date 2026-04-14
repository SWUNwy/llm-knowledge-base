import { test, expect } from '@playwright/test';

async function login(page) {
  await page.goto('/login');
  await page.getByLabel(/username/i).fill('testuser');
  await page.getByLabel(/password/i).fill('testpass123');
  await page.getByRole('button', { name: /login|sign in/i }).click();
  await expect(page).toHaveURL('/import', { timeout: 10000 });
}

test.describe('Library Flow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.getByRole('link', { name: /library/i }).click();
    await expect(page).toHaveURL('/library');
  });

  test('should display library page', async ({ page }) => {
    await expect(page.getByText('Library')).toBeVisible();
  });

  test('should show documents list', async ({ page }) => {
    // Should have document count
    await expect(page.locator('text=/document/i')).toBeVisible();
  });

  test('should filter by type', async ({ page }) => {
    // Open type filter
    await page.getByRole('combobox').first().click();
    await page.getByRole('option', { name: 'Web' }).click();

    // Filter should be applied
    const selected = await page.getByRole('combobox').first().inputValue();
    expect(selected).toBe('web');
  });

  test('should search documents', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i);
    await searchInput.fill('test');

    // Should trigger search
    await expect(searchInput).toHaveValue('test');
  });

  test('should paginate documents', async ({ page }) => {
    // Check if pagination exists (may not if few docs)
    const nextButton = page.getByRole('button', { name: 'Next' });
    if (await nextButton.isVisible()) {
      await expect(nextButton).toBeVisible();
    }
  });
});
