import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('login page loads', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText('KnowledgeBase');
    await expect(page.locator('text=Local')).toBeVisible();
    await expect(page.locator('text=Cloud')).toBeVisible();
  });

  test('setup page loads', async ({ page }) => {
    await page.goto('/setup');
    await expect(page.locator('h1')).toContainText('Initial Setup');
  });

  test('unauthenticated redirect to login', async ({ page }) => {
    await page.goto('/library');
    await expect(page).toHaveURL(/\/login/);
  });
});
