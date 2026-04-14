import { test, expect } from '@playwright/test';

async function login(page) {
  await page.goto('/login');
  await page.getByLabel(/username/i).fill('testuser');
  await page.getByLabel(/password/i).fill('testpass123');
  await page.getByRole('button', { name: /login|sign in/i }).click();
  await expect(page).toHaveURL('/import', { timeout: 10000 });
}

test.describe('Chat Flow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.getByRole('link', { name: /chat/i }).click();
    await expect(page).toHaveURL('/chat');
  });

  test('should display chat page', async ({ page }) => {
    await expect(page.getByText('Chat')).toBeVisible();
    await expect(page.getByPlaceholder(/ask a question/i)).toBeVisible();
  });

  test('should send a question', async ({ page }) => {
    const question = 'What is this project about?';

    await page.getByPlaceholder(/ask a question/i).fill(question);
    await page.getByRole('button', { name: /\[send\]/i }).click();

    // Should show user message
    await expect(page.getByText(question)).toBeVisible();

    // Should show bot response (may be error if no docs)
    await page.waitForTimeout(5000);
    const botMessages = page.locator('.rounded-xl').all();
    expect((await botMessages).length).toBeGreaterThan(0);
  });

  test('should show empty state initially', async ({ page }) => {
    await expect(page.getByText('No messages yet')).toBeVisible();
  });

  test('should have send button disabled when empty', async ({ page }) => {
    const sendButton = page.getByRole('button', { name: /\[send\]/i });
    await expect(sendButton).toBeDisabled();
  });

  test('should enable send button with input', async ({ page }) => {
    await page.getByPlaceholder(/ask a question/i).fill('test question');
    const sendButton = page.getByRole('button', { name: /\[send\]/i });
    await expect(sendButton).toBeEnabled();
  });
});
