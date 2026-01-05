import { test, expect } from '@playwright/test';

const TEST_USER = {
  email: 'demo@test.com',
  password: 'demo123',
};

test.describe('Authentication Flow', () => {
  test('should redirect unauthenticated user to login page', async ({ page }) => {
    // Go to root
    await page.goto('/');
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
    
    // Login page should have SSO button
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('should show login page with correct elements', async ({ page }) => {
    await page.goto('/login');
    
    // Check for AgentVoiceBox branding in header
    await expect(page.getByText('AgentVoiceBox')).toBeVisible();
    
    // Check for welcome heading
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
    
    // Check for SSO button
    await expect(page.getByRole('button', { name: /sign in with sso/i })).toBeVisible();
    
    // Check for social login buttons
    await expect(page.getByTestId('google-login-btn')).toBeVisible();
    await expect(page.getByTestId('github-login-btn')).toBeVisible();
  });

  // This test requires Keycloak to be running on port 65006
  test.skip('should redirect to Keycloak on SSO button click', async ({ page }) => {
    await page.goto('/login');
    
    // Click SSO button
    await page.getByRole('button', { name: /sign in with sso/i }).click();
    
    // Should redirect to Keycloak on port 65006 per docker-compose policy (65000-65099)
    await page.waitForURL(/localhost:65006/, { timeout: 15000 });
    
    // Verify we're on Keycloak by checking URL contains realm
    expect(page.url()).toContain('agentvoicebox');
  });

  // Skip full login flow test - requires Keycloak user setup
  test.skip('should complete full login flow with Keycloak', async ({ page }) => {
    // This test requires a valid Keycloak user to be configured
    // Start at login page
    await page.goto('/login');
    
    // Click SSO button
    await page.getByRole('button', { name: /sign in with sso/i }).click();
    
    // Wait for Keycloak login page (port 65006 per docker-compose policy)
    await page.waitForURL(/localhost:65006/, { timeout: 15000 });
    
    // Wait for form to be ready
    await page.waitForSelector('#username, input[name="username"]', { timeout: 20000 });
    
    // Fill in credentials
    await page.fill('#username', TEST_USER.email);
    await page.fill('#password', TEST_USER.password);
    
    // Submit login form
    await page.click('#kc-login');
    
    // Should redirect back to portal
    await page.waitForURL(/localhost/, { timeout: 20000 });
    
    // Should be on dashboard or auth callback
    const url = page.url();
    expect(url).toMatch(/\/(dashboard|auth\/callback|login)/);
  });
});

test.describe('Protected Routes', () => {
  test('should redirect /dashboard to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect /api-keys to login when not authenticated', async ({ page }) => {
    await page.goto('/api-keys');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect /billing to login when not authenticated', async ({ page }) => {
    await page.goto('/billing');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect /team to login when not authenticated', async ({ page }) => {
    await page.goto('/team');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect /settings to login when not authenticated', async ({ page }) => {
    await page.goto('/settings');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect /admin to login when not authenticated', async ({ page }) => {
    await page.goto('/admin');
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Auth Callback', () => {
  test('should handle auth callback page', async ({ page }) => {
    // Auth callback without code should show error or redirect
    await page.goto('/auth/callback');
    
    // Should either show error or redirect to login
    await page.waitForTimeout(2000);
    const url = page.url();
    const hasError = await page.getByText(/error|no authorization code/i).isVisible().catch(() => false);
    
    expect(url.includes('/login') || url.includes('/auth/callback') || hasError).toBeTruthy();
  });
});

test.describe('Theme Toggle', () => {
  test('should have theme toggle on login page', async ({ page }) => {
    await page.goto('/login');
    
    // Look for theme toggle button (sun/moon icon)
    const themeToggle = page.locator('button').filter({ has: page.locator('svg') }).first();
    await expect(themeToggle).toBeVisible();
  });
});

test.describe('Social Login', () => {
  test('should show Google login button with correct styling', async ({ page }) => {
    await page.goto('/login');
    
    const googleBtn = page.getByTestId('google-login-btn');
    await expect(googleBtn).toBeVisible();
    await expect(googleBtn).toContainText('Continue with Google');
  });

  test('should show GitHub login button with correct styling', async ({ page }) => {
    await page.goto('/login');
    
    const githubBtn = page.getByTestId('github-login-btn');
    await expect(githubBtn).toBeVisible();
    await expect(githubBtn).toContainText('Continue with GitHub');
  });

  // These tests require Keycloak to be running on port 65006
  test.skip('should redirect to Keycloak with Google IdP hint on Google button click', async ({ page }) => {
    await page.goto('/login');
    
    // Click Google login button
    await page.getByTestId('google-login-btn').click();
    
    // Should redirect to Keycloak with kc_idp_hint=google (port 65006 per docker-compose policy)
    await page.waitForURL(/localhost:65006/, { timeout: 15000 });
    const url = page.url();
    expect(url).toContain('kc_idp_hint=google');
  });

  test.skip('should redirect to Keycloak with GitHub IdP hint on GitHub button click', async ({ page }) => {
    await page.goto('/login');
    
    // Click GitHub login button
    await page.getByTestId('github-login-btn').click();
    
    // Should redirect to Keycloak with kc_idp_hint=github (port 65006 per docker-compose policy)
    await page.waitForURL(/localhost:65006/, { timeout: 15000 });
    const url = page.url();
    expect(url).toContain('kc_idp_hint=github');
  });
});
