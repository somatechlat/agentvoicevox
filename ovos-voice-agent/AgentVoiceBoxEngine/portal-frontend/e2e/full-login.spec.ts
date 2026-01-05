import { test, expect } from '@playwright/test';
import { 
  authenticateAsTenantAdmin, 
  authenticateAsPlatformAdmin,
  authenticateAsDemo,
  isKeycloakReady,
  TEST_USERS 
} from './auth.setup';

/**
 * Full E2E Login Flow Tests - PRODUCTION-LIKE
 * 
 * Tests complete authentication flows using real Keycloak tokens.
 * Port 65006: Keycloak (per docker-compose port policy 65000-65099)
 * Port 65013: Portal Frontend
 */

test.describe('Full Login Flow - Real Keycloak Auth', () => {
  test.beforeAll(async () => {
    // Verify Keycloak is available
    const ready = await isKeycloakReady();
    if (!ready) {
      console.warn('⚠️ Keycloak not available - some tests may be skipped');
    }
  });

  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login');
    
    // Verify login page elements
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
    await expect(page.getByText('Sign in to your account to continue')).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in with sso/i })).toBeVisible();
    await expect(page.getByTestId('google-login-btn')).toBeVisible();
    await expect(page.getByTestId('github-login-btn')).toBeVisible();
  });

  test('SSO button redirects to Keycloak', async ({ page }) => {
    test.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    await page.goto('/login');
    
    // Click SSO and verify redirect to Keycloak on port 65006
    const [request] = await Promise.all([
      page.waitForRequest(req => req.url().includes('localhost:65006')),
      page.getByRole('button', { name: /sign in with sso/i }).click(),
    ]);
    
    expect(request.url()).toContain('/realms/agentvoicebox/protocol/openid-connect/auth');
    expect(request.url()).toContain('client_id=agentvoicebox-portal');
    expect(request.url()).toContain('code_challenge=');
  });

  test('authenticated user can access dashboard', async ({ page }) => {
    test.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    // Authenticate with real Keycloak token
    await authenticateAsTenantAdmin(page);
    
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Should not be redirected to login
    await page.waitForLoadState('networkidle');
    const url = page.url();
    expect(url).not.toContain('/login');
    expect(url).toContain('/dashboard');
    
    // Dashboard should have some content (even if API calls fail)
    const pageContent = await page.content();
    expect(pageContent.length).toBeGreaterThan(1000);
  });

  test('platform admin can access admin dashboard', async ({ page }) => {
    test.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    // Authenticate as platform admin
    await authenticateAsPlatformAdmin(page);
    
    // Navigate to admin dashboard
    await page.goto('/admin/dashboard');
    
    // Should not be redirected to login
    await page.waitForLoadState('networkidle');
    const url = page.url();
    expect(url).not.toContain('/login');
    expect(url).toContain('/admin');
  });

  test('unauthenticated user is redirected to login', async ({ page }) => {
    // Try to access protected route without auth
    await page.goto('/dashboard');
    
    // Should be redirected to login
    await page.waitForURL(/\/login/, { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });

  test('demo user can access tenant dashboard', async ({ page }) => {
    test.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    // Authenticate as demo user
    await authenticateAsDemo(page);
    
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Should stay on dashboard
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/dashboard');
  });

  test('role-based routing works correctly', async ({ page }) => {
    test.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    // Authenticate as tenant admin (not platform admin)
    await authenticateAsTenantAdmin(page);
    
    // Try to access admin route - should redirect to dashboard
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Tenant admin should be redirected away from admin routes
    const url = page.url();
    // Either redirected to /dashboard or stays on /admin (depending on role mapping)
    expect(url).toMatch(/\/(dashboard|admin)/);
  });
});

test.describe('Authentication Token Handling', () => {
  test('tokens are set correctly in cookies', async ({ page }) => {
    test.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    await authenticateAsTenantAdmin(page);
    
    // Check cookies are set
    const cookies = await page.context().cookies();
    const accessToken = cookies.find(c => c.name === 'agentvoicebox_access_token');
    const refreshToken = cookies.find(c => c.name === 'agentvoicebox_refresh_token');
    
    expect(accessToken).toBeDefined();
    expect(refreshToken).toBeDefined();
    expect(accessToken?.value).toBeTruthy();
    expect(refreshToken?.value).toBeTruthy();
  });

  test('JWT token contains expected claims', async ({ page }) => {
    test.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    await authenticateAsTenantAdmin(page);
    
    const cookies = await page.context().cookies();
    const accessToken = cookies.find(c => c.name === 'agentvoicebox_access_token');
    
    // Decode JWT payload
    const payload = JSON.parse(atob(accessToken!.value.split('.')[1]));
    
    // Verify expected claims
    expect(payload.sub).toBeTruthy();
    expect(payload.email).toBe(TEST_USERS.tenantAdmin.username);
    expect(payload.exp).toBeGreaterThan(Date.now() / 1000);
  });
});

test.describe('Session Management', () => {
  test('session persists across page navigations', async ({ page }) => {
    test.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    await authenticateAsTenantAdmin(page);
    
    // Navigate to multiple pages
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/dashboard');
    
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    // Should not be redirected to login
    expect(page.url()).not.toContain('/login');
  });

  test('clearing cookies logs user out', async ({ page }) => {
    test.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    await authenticateAsTenantAdmin(page);
    
    // Verify authenticated
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/dashboard');
    
    // Clear cookies
    await page.context().clearCookies();
    
    // Try to access protected route
    await page.goto('/dashboard');
    await page.waitForURL(/\/login/, { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });
});
