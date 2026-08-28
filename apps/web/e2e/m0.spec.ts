import { expect, test } from '@playwright/test';

async function resetMockApi(page: import('@playwright/test').Page) {
  await page.request.post('/v1/_test/reset');
}

async function login(
  page: import('@playwright/test').Page,
  email: string,
  password: string,
) {
  await page.goto('/login');
  await page.getByTestId('login-email').fill(email);
  await page.getByTestId('login-password').fill(password);
  await page.getByTestId('login-submit').click();
  await expect(page.getByTestId('empty-agents')).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await resetMockApi(page);
});

test('accept invite → shell → logout → / requires /login', async ({ page }) => {
  await login(page, 'owner@example.com', 'password123!');

  await page.getByTestId('nav-invite').click();
  const inviteEmail = `newuser-${Date.now()}@example.com`;
  await page.locator('#invite-email').fill(inviteEmail);
  await page.getByRole('button', { name: 'Send invite' }).click();

  const tokenText = await page.locator('code').textContent();
  const token = tokenText?.replace('/invite/', '') ?? '';
  expect(token.length).toBeGreaterThan(0);

  await page.getByTestId('logout').click();
  await expect(page).toHaveURL(/\/login$/);

  await page.goto(`/invite/${token}`);
  await page.getByTestId('invite-password').fill('newpassword12');
  await page.getByTestId('invite-submit').click();

  await expect(page.getByTestId('empty-agents')).toBeVisible();

  await page.getByTestId('logout').click();
  await expect(page).toHaveURL(/\/login$/);

  await page.goto('/');
  await expect(page).toHaveURL(/\/login$/);
});

test('two workspaces switcher isolation', async ({ page }) => {
  await login(page, 'owner@example.com', 'password123!');

  const switcher = page.getByTestId('workspace-switcher').locator('select');
  await expect(switcher).toBeVisible();

  const options = await switcher.locator('option').allTextContents();
  expect(options).toContain('Alpha');
  expect(options).toContain('Bravo');

  await switcher.selectOption({ label: 'Alpha' });
  await expect(page.getByRole('heading', { level: 1, name: 'Alpha' })).toBeVisible();
  await expect(page.getByText('Role: owner')).toBeVisible();

  await switcher.selectOption({ label: 'Bravo' });
  await expect(page.getByRole('heading', { level: 1, name: 'Bravo' })).toBeVisible();
  await expect(page.getByText('Role: owner')).toBeVisible();
});

test('editor cannot see nav-invite', async ({ page }) => {
  await login(page, 'editor@example.com', 'password123!');

  await expect(page.getByTestId('nav-agents')).toBeVisible();
  await expect(page.getByTestId('nav-runs')).toBeVisible();
  await expect(page.getByTestId('nav-invite')).toHaveCount(0);

  const switcher = page.getByTestId('workspace-switcher').locator('select');
  const options = await switcher.locator('option').allTextContents();
  expect(options).toEqual(['Alpha']);
});
