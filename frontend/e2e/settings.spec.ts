import { test, expect } from '@playwright/test';

async function login(page) {
  await page.goto('/login');
  await page.getByLabel(/username/i).fill('testuser');
  await page.getByLabel(/password/i).fill('testpass123');
  await page.getByRole('button', { name: /login|sign in/i }).click();
  await expect(page).toHaveURL('/import', { timeout: 10000 });
}

test.describe('Settings Flow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.getByRole('link', { name: /settings/i }).click();
    await expect(page).toHaveURL('/settings');
  });

  test('should display settings page', async ({ page }) => {
    await expect(page.getByText('Settings')).toBeVisible();
  });

  test('should show LLM provider selector', async ({ page }) => {
    await expect(page.getByLabel(/LLM Provider/i)).toBeVisible();
    await expect(page.getByRole('option', { name: 'OpenAI' })).toBeVisible();
  });

  test('should show model selector', async ({ page }) => {
    await expect(page.getByLabel(/Model/i)).toBeVisible();
  });

  test('should show API key input', async ({ page }) => {
    await expect(page.getByLabel(/API Key/i)).toBeVisible();
  });

  test('should toggle API key visibility', async ({ page }) => {
    const apiKeyInput = page.getByLabel(/API Key/i);
    const toggleButton = page.getByRole('button', { name: /show/i });

    // Should be password type initially
    await expect(apiKeyInput).toHaveAttribute('type', 'password');

    // Click show
    await toggleButton.click();
    await expect(apiKeyInput).toHaveAttribute('type', 'text');

    // Click hide
    await toggleButton.click();
    await expect(apiKeyInput).toHaveAttribute('type', 'password');
  });

  test('should test connection button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /test connection/i })).toBeVisible();
  });

  test('should save settings button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /save settings/i })).toBeVisible();
  });
});
