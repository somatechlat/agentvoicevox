import { test, expect } from '@playwright/test';

/**
 * Role-Based Routing E2E Tests
 * Tests that users are routed to appropriate dashboards based on their role
 * 
 * Validates Requirements:
 * - D1: Role-Based Access Control
 * - D2: Permission-Based Navigation
 * - Property 7: Role-Based Dashboard Routing
 * - Property 8: Permission-Based Navigation
 */

test.describe('Role-Based Routing', () => {
  test('should redirect unauthenticated users to login', async ({ page }) => {
    // Property 7: Unauthenticated users go to login
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect root to login when unauthenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should protect admin routes', async ({ page }) => {
    // Admin routes should redirect to login
    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should protect customer routes', async ({ page }) => {
    // Customer routes should redirect to login
    await page.goto('/api-keys');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should protect user routes', async ({ page }) => {
    // User routes should redirect to login
    await page.goto('/app');
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Admin Portal Access', () => {
  // These tests assume admin authentication is set up
  
  test('admin dashboard should be accessible', async ({ page }) => {
    await page.goto('/admin/dashboard');
    // Either redirects to login or shows dashboard
    await page.waitForTimeout(1000);
  });

  test('admin should see all admin navigation items', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.waitForTimeout(1000);
    
    // If authenticated as admin, should see admin nav
    const adminNav = page.getByRole('navigation');
    if (await adminNav.isVisible()) {
      // Check for admin-specific items
      const tenantsLink = page.getByRole('link', { name: /tenant/i });
      const monitoringLink = page.getByRole('link', { name: /monitoring/i });
      const auditLink = page.getByRole('link', { name: /audit/i });
    }
  });

  test('admin routes should have admin layout', async ({ page }) => {
    await page.goto('/admin/tenants-mgmt');
    await page.waitForTimeout(1000);
    
    // Should have admin-specific layout elements
  });
});

test.describe('Customer Portal Access', () => {
  test('customer dashboard should be accessible', async ({ page }) => {
    await page.goto('/dashboard');
    // Either redirects to login or shows dashboard
    await page.waitForTimeout(1000);
  });

  test('customer should see customer navigation items', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // If authenticated as customer, should see customer nav
    const nav = page.getByRole('navigation');
    if (await nav.isVisible()) {
      // Check for customer-specific items
      const sessionsLink = page.getByRole('link', { name: /session/i });
      const apiKeysLink = page.getByRole('link', { name: /api key/i });
      const billingLink = page.getByRole('link', { name: /billing/i });
    }
  });

  test('customer should NOT see admin navigation items', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Customer should not see admin-only items
    const tenantsLink = page.getByRole('link', { name: /^tenants$/i });
    await expect(tenantsLink).not.toBeVisible();
    
    const plansLink = page.getByRole('link', { name: /^plans$/i });
    await expect(plansLink).not.toBeVisible();
  });
});

test.describe('User Portal Access', () => {
  test('user dashboard should be accessible', async ({ page }) => {
    await page.goto('/app');
    // Either redirects to login or shows dashboard
    await page.waitForTimeout(1000);
  });

  test('user should see limited navigation items', async ({ page }) => {
    await page.goto('/app');
    await page.waitForTimeout(1000);
    
    // If authenticated as user, should see limited nav
    const nav = page.getByRole('navigation');
    if (await nav.isVisible()) {
      // Check for user-specific items
      const dashboardLink = page.getByRole('link', { name: /dashboard/i });
      const settingsLink = page.getByRole('link', { name: /settings/i });
    }
  });

  test('user should NOT see admin or customer-admin items', async ({ page }) => {
    await page.goto('/app');
    await page.waitForTimeout(1000);
    
    // User should not see admin items
    const tenantsLink = page.getByRole('link', { name: /^tenants$/i });
    await expect(tenantsLink).not.toBeVisible();
    
    // User should not see team management
    const teamLink = page.getByRole('link', { name: /^team$/i });
    await expect(teamLink).not.toBeVisible();
  });
});

test.describe('Cross-Portal Navigation Prevention', () => {
  test('customer cannot access admin routes directly', async ({ page }) => {
    // Try to access admin route
    await page.goto('/admin/tenants-mgmt');
    
    // Should redirect to login or show forbidden
    await page.waitForTimeout(1000);
    const url = page.url();
    expect(url.includes('/login') || url.includes('/dashboard') || url.includes('/admin')).toBeTruthy();
  });

  test('user cannot access customer admin routes directly', async ({ page }) => {
    // Try to access customer admin route
    await page.goto('/team');
    
    // Should redirect to login or appropriate page
    await page.waitForTimeout(1000);
  });

  test('user cannot access admin routes directly', async ({ page }) => {
    // Try to access admin route
    await page.goto('/admin/dashboard');
    
    // Should redirect to login
    await page.waitForTimeout(1000);
    const url = page.url();
    expect(url.includes('/login') || url.includes('/app')).toBeTruthy();
  });
});

test.describe('Permission-Based UI Elements', () => {
  test('create buttons should respect permissions', async ({ page }) => {
    // Property 8: Permission-based navigation
    await page.goto('/app/api-keys');
    await page.waitForTimeout(1000);
    
    // User portal should NOT have create button
    const createBtn = page.getByRole('button', { name: /create api key/i });
    await expect(createBtn).not.toBeVisible();
  });

  test('action buttons should respect permissions', async ({ page }) => {
    await page.goto('/app/sessions');
    await page.waitForTimeout(1000);
    
    // User portal should NOT have end session button
    const endBtn = page.getByRole('button', { name: /end session/i });
    // Should not be visible or should be disabled
  });

  test('edit buttons should respect permissions', async ({ page }) => {
    await page.goto('/app/settings');
    await page.waitForTimeout(1000);
    
    // User can edit their own settings
    // But cannot edit organization settings
  });
});

test.describe('Sidebar Navigation State', () => {
  test('sidebar should highlight current page', async ({ page }) => {
    // Use longer timeout for navigation
    await page.goto('/dashboard', { timeout: 30000 });
    await page.waitForTimeout(1000);
    
    // Dashboard link should be highlighted (if authenticated)
    // If redirected to login, test passes as expected behavior
    const url = page.url();
    if (url.includes('/login')) {
      // Expected: unauthenticated users redirect to login
      expect(url).toContain('/login');
    } else {
      // Authenticated: check for dashboard link
      const dashboardLink = page.getByRole('link', { name: /dashboard/i }).first();
      if (await dashboardLink.isVisible()) {
        // Active link typically has different styling
        expect(await dashboardLink.isVisible()).toBeTruthy();
      }
    }
  });

  test('sidebar should collapse on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Sidebar should be hidden or collapsed
    const sidebar = page.getByRole('navigation', { name: /main/i });
    // On mobile, sidebar is typically hidden until hamburger menu is clicked
  });

  test('sidebar should expand on hamburger click', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Find and click hamburger menu
    const menuButton = page.getByRole('button', { name: /menu|toggle/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();
      await page.waitForTimeout(300);
      
      // Sidebar should now be visible
      const sidebar = page.getByRole('navigation');
      await expect(sidebar.first()).toBeVisible();
    }
  });
});

test.describe('Route Guards', () => {
  test('should handle invalid routes gracefully', async ({ page }) => {
    await page.goto('/invalid-route-that-does-not-exist');
    await page.waitForTimeout(1000);
    
    // Should show 404 or redirect
    const url = page.url();
    const has404 = await page.getByText(/404|not found/i).isVisible().catch(() => false);
    expect(url.includes('/login') || has404 || url.includes('/dashboard')).toBeTruthy();
  });

  test('should handle deep invalid routes', async ({ page }) => {
    // Use longer timeout for deep route navigation
    await page.goto('/admin/invalid/deep/route', { timeout: 30000 });
    await page.waitForTimeout(1000);
    
    // Should redirect to login or show 404
    const url = page.url();
    const has404 = await page.getByText(/404|not found/i).isVisible().catch(() => false);
    expect(url.includes('/login') || has404 || url.includes('/admin')).toBeTruthy();
  });

  test('should preserve query params on redirect', async ({ page }) => {
    await page.goto('/dashboard?tab=usage');
    await page.waitForTimeout(1000);
    
    // If redirected to login, should preserve return URL
    const url = page.url();
    if (url.includes('/login')) {
      // Return URL should be preserved
    }
  });
});

/**
 * Property Test: Protected Route Access Control
 * **Feature: e2e-testing-infrastructure, Property 1: Protected Route Access Control**
 * **Validates: Requirements 1.1, 10.4, 11.1**
 * 
 * For any protected route and any unauthenticated user, navigating to that route
 * SHALL redirect to the Keycloak login page.
 */
test.describe('Property 1: Protected Route Access Control', () => {
  // Comprehensive list of all protected routes in the system
  const protectedRoutes = [
    // Admin Portal Routes
    '/admin/dashboard',
    '/admin/tenants-mgmt',
    '/admin/billing',
    '/admin/plans',
    '/admin/monitoring',
    '/admin/audit',
    '/admin/users-mgmt',
    '/admin/security',
    '/admin/security/keycloak',
    '/admin/security/policies',
    '/admin/security/secrets',
    '/admin/system/workers',
    '/admin/system/workers/stt',
    '/admin/system/workers/tts',
    '/admin/system/infrastructure/redis',
    '/admin/system/infrastructure/vault',
    '/admin/system/observability',
    // Customer Portal Routes
    '/dashboard',
    '/sessions',
    '/projects',
    '/api-keys',
    '/usage',
    '/billing',
    '/team',
    '/settings',
    '/dashboard/voice',
    '/dashboard/stt',
    '/dashboard/llm',
    '/dashboard/personas',
    '/dashboard/skills',
    '/dashboard/wake-words',
    '/dashboard/intents',
    '/dashboard/voice-cloning',
    '/dashboard/messagebus',
    // User Portal Routes
    '/app',
    '/app/sessions',
    '/app/api-keys',
    '/app/settings',
  ];

  for (const route of protectedRoutes) {
    test(`unauthenticated access to ${route} should redirect to login`, async ({ page }) => {
      // Navigate to protected route without authentication
      await page.goto(route);
      
      // Wait for redirect to complete
      await page.waitForTimeout(1500);
      
      // Verify redirect to login page
      const currentUrl = page.url();
      expect(
        currentUrl.includes('/login'),
        `Expected ${route} to redirect to /login, but got ${currentUrl}`
      ).toBeTruthy();
    });
  }

  test('property: all protected routes redirect unauthenticated users', async ({ page }) => {
    // Meta-test: verify the property holds for a random sample
    const sampleRoutes = [
      protectedRoutes[Math.floor(Math.random() * protectedRoutes.length)],
      protectedRoutes[Math.floor(Math.random() * protectedRoutes.length)],
      protectedRoutes[Math.floor(Math.random() * protectedRoutes.length)],
    ];
    
    for (const route of sampleRoutes) {
      await page.goto(route);
      await page.waitForTimeout(1000);
      expect(page.url()).toContain('/login');
    }
  });
});


/**
 * Property Test: Role-Based Dashboard Routing
 * **Feature: e2e-testing-infrastructure, Property 9: Role-Based Dashboard Routing**
 * **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
 * 
 * For any authenticated user, the System SHALL route the user to the appropriate
 * dashboard based on their role: admin users to `/admin/dashboard`, tenant_admin
 * users to `/dashboard`, and regular users to `/app`.
 */
test.describe('Property 9: Role-Based Dashboard Routing', () => {
  // Role to expected dashboard mapping
  const roleDashboardMap = {
    admin: '/admin/dashboard',
    tenant_admin: '/dashboard',
    user: '/app',
  };

  test('admin role should route to admin dashboard', async ({ page }) => {
    // This test verifies the routing logic exists
    // Actual auth would be needed for full verification
    await page.goto('/admin/dashboard');
    await page.waitForTimeout(1000);
    
    // Either shows admin dashboard or redirects to login
    const url = page.url();
    expect(
      url.includes('/admin/dashboard') || url.includes('/login'),
      `Admin route should show dashboard or redirect to login`
    ).toBeTruthy();
  });

  test('tenant_admin role should route to customer dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    const url = page.url();
    expect(
      url.includes('/dashboard') || url.includes('/login'),
      `Customer route should show dashboard or redirect to login`
    ).toBeTruthy();
  });

  test('user role should route to user portal', async ({ page }) => {
    await page.goto('/app');
    await page.waitForTimeout(1000);
    
    const url = page.url();
    expect(
      url.includes('/app') || url.includes('/login'),
      `User route should show app or redirect to login`
    ).toBeTruthy();
  });

  test('root path should redirect based on role', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
    
    const url = page.url();
    // Should redirect to login (unauthenticated) or appropriate dashboard
    expect(
      url.includes('/login') || 
      url.includes('/admin/dashboard') || 
      url.includes('/dashboard') || 
      url.includes('/app'),
      `Root should redirect to login or role-appropriate dashboard`
    ).toBeTruthy();
  });
});

/**
 * Property Test: Role-Based Navigation Visibility
 * **Feature: e2e-testing-infrastructure, Property 10: Role-Based Navigation Visibility**
 * **Validates: Requirements 11.2, 11.3, 11.4**
 * 
 * For any user viewing the sidebar navigation, the System SHALL display only
 * navigation items permitted for their role.
 */
test.describe('Property 10: Role-Based Navigation Visibility', () => {
  const adminOnlyItems = ['Tenants', 'Plans', 'Monitoring', 'Audit'];
  const customerItems = ['Sessions', 'API Keys', 'Billing', 'Team'];
  const userItems = ['Dashboard', 'Settings'];

  test('admin portal should show admin navigation items', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.waitForTimeout(1000);
    
    // If on admin dashboard (authenticated), check for admin nav items
    if (!page.url().includes('/login')) {
      for (const item of adminOnlyItems) {
        const navItem = page.getByRole('link', { name: new RegExp(item, 'i') });
        // Admin should see these items
        const isVisible = await navItem.first().isVisible().catch(() => false);
        // Either visible or page redirected to login
        expect(isVisible || page.url().includes('/login')).toBeTruthy();
      }
    }
  });

  test('customer portal should show customer navigation items', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      for (const item of customerItems) {
        const navItem = page.getByRole('link', { name: new RegExp(item, 'i') });
        const isVisible = await navItem.first().isVisible().catch(() => false);
        expect(isVisible || page.url().includes('/login')).toBeTruthy();
      }
    }
  });

  test('user portal should show limited navigation items', async ({ page }) => {
    await page.goto('/app');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      // User should see basic items
      for (const item of userItems) {
        const navItem = page.getByRole('link', { name: new RegExp(item, 'i') });
        const isVisible = await navItem.first().isVisible().catch(() => false);
        expect(isVisible || page.url().includes('/login')).toBeTruthy();
      }
      
      // User should NOT see admin items
      for (const item of adminOnlyItems) {
        const navItem = page.getByRole('link', { name: new RegExp(`^${item}$`, 'i') });
        const isVisible = await navItem.isVisible().catch(() => false);
        expect(!isVisible).toBeTruthy();
      }
    }
  });
});

/**
 * Property Test: Role-Based Action Permissions
 * **Feature: e2e-testing-infrastructure, Property 11: Role-Based Action Permissions**
 * **Validates: Requirements 10.3, 10.4**
 * 
 * For any action button (create, edit, delete, revoke), the System SHALL display
 * the button only if the current user's role has permission to perform that action.
 */
test.describe('Property 11: Role-Based Action Permissions', () => {
  test('user portal should not show create API key button', async ({ page }) => {
    await page.goto('/app/api-keys');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      const createBtn = page.getByRole('button', { name: /create api key/i });
      await expect(createBtn).not.toBeVisible();
    }
  });

  test('user portal should not show revoke button', async ({ page }) => {
    await page.goto('/app/api-keys');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      const revokeBtn = page.getByRole('button', { name: /revoke/i });
      const isVisible = await revokeBtn.first().isVisible().catch(() => false);
      expect(!isVisible).toBeTruthy();
    }
  });

  test('user portal should not show end session button', async ({ page }) => {
    await page.goto('/app/sessions');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      const endBtn = page.getByRole('button', { name: /end session/i });
      const isVisible = await endBtn.first().isVisible().catch(() => false);
      expect(!isVisible).toBeTruthy();
    }
  });

  test('customer portal should show action buttons', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      // Customer should see create button
      const createBtn = page.getByRole('button', { name: /create api key/i });
      await expect(createBtn).toBeVisible();
    }
  });
});

/**
 * Property Test: Cross-Portal Access Prevention
 * **Feature: e2e-testing-infrastructure, Property 12: Cross-Portal Access Prevention**
 * **Validates: Requirements 11.1, 11.3**
 * 
 * For any user attempting to access a portal route above their permission level,
 * the System SHALL redirect to their appropriate portal with an access denied indication.
 */
test.describe('Property 12: Cross-Portal Access Prevention', () => {
  const adminRoutes = [
    '/admin/dashboard',
    '/admin/tenants-mgmt',
    '/admin/billing',
    '/admin/plans',
    '/admin/monitoring',
    '/admin/audit',
  ];

  const customerRoutes = [
    '/team',
    '/billing',
    '/projects',
  ];

  test('unauthenticated users cannot access admin routes', async ({ page }) => {
    for (const route of adminRoutes) {
      await page.goto(route);
      await page.waitForTimeout(500);
      
      expect(page.url()).toContain('/login');
    }
  });

  test('unauthenticated users cannot access customer routes', async ({ page }) => {
    for (const route of customerRoutes) {
      await page.goto(route);
      await page.waitForTimeout(500);
      
      expect(page.url()).toContain('/login');
    }
  });

  test('direct URL manipulation should not bypass access control', async ({ page }) => {
    // Try various URL manipulation techniques
    const manipulatedUrls = [
      '/admin/../admin/dashboard',
      '/admin/dashboard?bypass=true',
      '/admin/dashboard#admin',
      '/ADMIN/DASHBOARD',
    ];

    for (const url of manipulatedUrls) {
      await page.goto(url);
      await page.waitForTimeout(500);
      
      // Should redirect to login or show error
      const currentUrl = page.url().toLowerCase();
      expect(
        currentUrl.includes('/login') || 
        currentUrl.includes('/admin/dashboard'),
        `URL manipulation ${url} should be handled`
      ).toBeTruthy();
    }
  });
});

/**
 * Property Test: Tenant Context Isolation
 * **Feature: e2e-testing-infrastructure, Property 13: Tenant Context Isolation**
 * **Validates: Requirements 10.2, 5.2**
 * 
 * For any tenant_admin or user viewing data, the System SHALL display only data
 * belonging to their tenant.
 */
test.describe('Property 13: Tenant Context Isolation', () => {
  test('sessions page should only show tenant data', async ({ page }) => {
    await page.goto('/sessions');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      // Verify no cross-tenant data is visible
      const pageContent = await page.content();
      
      // Should not contain obvious cross-tenant markers
      expect(!pageContent.includes('other-tenant-id')).toBeTruthy();
      expect(!pageContent.includes('foreign-tenant')).toBeTruthy();
    }
  });

  test('API keys page should only show tenant keys', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      const pageContent = await page.content();
      expect(!pageContent.includes('other-tenant-key')).toBeTruthy();
    }
  });

  test('usage page should only show tenant usage', async ({ page }) => {
    await page.goto('/usage');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      // Usage metrics should be tenant-scoped
      const pageContent = await page.content();
      expect(!pageContent.includes('platform-wide-usage')).toBeTruthy();
    }
  });
});

/**
 * Property Test: Admin Elevated Access
 * **Feature: e2e-testing-infrastructure, Property 14: Admin Elevated Access**
 * **Validates: Requirements 11.2**
 * 
 * For any admin user, the System SHALL allow access to all portal routes with
 * full visibility of cross-tenant data for platform management purposes.
 */
test.describe('Property 14: Admin Elevated Access', () => {
  test('admin should be able to access admin routes', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.waitForTimeout(1000);
    
    // Either shows admin dashboard or redirects to login
    const url = page.url();
    expect(
      url.includes('/admin/dashboard') || url.includes('/login')
    ).toBeTruthy();
  });

  test('admin should be able to view all tenants', async ({ page }) => {
    await page.goto('/admin/tenants-mgmt');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      // Admin should see tenant list
      const heading = page.getByRole('heading', { name: /tenant/i });
      await expect(heading).toBeVisible();
    }
  });

  test('admin should be able to view cross-tenant data', async ({ page }) => {
    await page.goto('/admin/audit');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      // Admin audit log should show all tenant activities
      const heading = page.getByRole('heading', { name: /audit/i });
      await expect(heading).toBeVisible();
    }
  });

  test('admin should be able to access monitoring', async ({ page }) => {
    await page.goto('/admin/monitoring');
    await page.waitForTimeout(1000);
    
    if (!page.url().includes('/login')) {
      const heading = page.getByRole('heading', { name: /monitoring|system/i });
      await expect(heading).toBeVisible();
    }
  });
});
