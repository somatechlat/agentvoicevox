import { test, expect } from '@playwright/test';

test.describe('Login Page - Rendering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display welcome heading and subtitle', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
    await expect(page.getByText('Sign in to your account to continue')).toBeVisible();
  });

  test('should display AgentVoiceBox branding in header', async ({ page }) => {
    await expect(page.getByText('AgentVoiceBox')).toBeVisible();
  });

  test('should display SSO sign in button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /sign in with sso/i })).toBeVisible();
  });

  test('should display Google login button', async ({ page }) => {
    await expect(page.getByTestId('google-login-btn')).toBeVisible();
  });

  test('should display GitHub login button', async ({ page }) => {
    await expect(page.getByTestId('github-login-btn')).toBeVisible();
  });

  test('should display terms and privacy footer', async ({ page }) => {
    await expect(page.getByText(/terms of service/i)).toBeVisible();
  });
});

test.describe('Login Page - SSO Flow', () => {
  // This test requires Keycloak to be running on port 65006
  test.skip('should redirect to Keycloak on SSO click', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /sign in with sso/i }).click();
    // Port 65006 per docker-compose policy (65000-65099)
    await page.waitForURL(/localhost:65006/, { timeout: 15000 });
  });

  test('should include PKCE in redirect URL', async ({ page }) => {
    await page.goto('/login');
    const [request] = await Promise.all([
      page.waitForRequest(req => req.url().includes('/protocol/openid-connect/auth')),
      page.getByRole('button', { name: /sign in with sso/i }).click(),
    ]);
    expect(request.url()).toContain('code_challenge=');
    expect(request.url()).toContain('code_challenge_method=S256');
  });

  test('should include client_id in redirect URL', async ({ page }) => {
    await page.goto('/login');
    const [request] = await Promise.all([
      page.waitForRequest(req => req.url().includes('/protocol/openid-connect/auth')),
      page.getByRole('button', { name: /sign in with sso/i }).click(),
    ]);
    expect(request.url()).toContain('client_id=agentvoicebox-portal');
  });
});

test.describe('Login Page - Social Login', () => {
  test('should redirect with Google IdP hint', async ({ page }) => {
    await page.goto('/login');
    const [request] = await Promise.all([
      page.waitForRequest(req => req.url().includes('/protocol/openid-connect/auth')),
      page.getByTestId('google-login-btn').click(),
    ]);
    expect(request.url()).toContain('kc_idp_hint=google');
  });

  test('should redirect with GitHub IdP hint', async ({ page }) => {
    await page.goto('/login');
    const [request] = await Promise.all([
      page.waitForRequest(req => req.url().includes('/protocol/openid-connect/auth')),
      page.getByTestId('github-login-btn').click(),
    ]);
    expect(request.url()).toContain('kc_idp_hint=github');
  });
});

test.describe('Login Page - Theme Toggle', () => {
  test('should have theme toggle visible', async ({ page }) => {
    await page.goto('/login');
    // Theme toggle has aria-label for accessibility
    const themeToggle = page.getByRole('button', { name: /switch to .* mode/i });
    await expect(themeToggle).toBeVisible();
  });

  test('should toggle theme when clicked', async ({ page }) => {
    await page.goto('/login');
    const themeToggle = page.getByRole('button', { name: /switch to .* mode/i });
    const initialIsDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
    await themeToggle.click();
    await page.waitForTimeout(300);
    const newIsDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
    expect(newIsDark).not.toBe(initialIsDark);
  });
});


test.describe('Login Page - Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/login');
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();
    await expect(h1).toHaveText('Welcome back');
  });

  test('should have accessible button labels', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('button', { name: /sign in with sso/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /continue with google/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /continue with github/i })).toBeVisible();
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/login');
    const ssoButton = page.getByRole('button', { name: /sign in with sso/i });
    await ssoButton.focus();
    await expect(ssoButton).toBeFocused();
  });
});

test.describe('Login Page - Responsive Design', () => {
  test('should display on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in with sso/i })).toBeVisible();
  });

  test('should display on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  });

  test('should display on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  });
});

test.describe('Login Page - Edge Cases', () => {
  // This test requires Keycloak to be running on port 65006
  test.skip('should handle browser back button', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /sign in with sso/i }).click();
    // Port 65006 per docker-compose policy (65000-65099)
    await page.waitForURL(/localhost:65006/, { timeout: 15000 });
    await page.goBack();
    await page.waitForURL(/\/login/, { timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  });

  test('should handle page refresh', async ({ page }) => {
    await page.goto('/login');
    await page.reload();
    await expect(page.getByRole('button', { name: /sign in with sso/i })).toBeVisible();
  });

  test('should not expose sensitive data in URL', async ({ page }) => {
    await page.goto('/login');
    const url = page.url();
    expect(url).not.toContain('password');
    expect(url).not.toContain('token');
  });
});
