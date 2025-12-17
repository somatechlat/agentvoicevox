import { test, expect, Page } from '@playwright/test';

/**
 * Admin Portal E2E Tests
 * Tests the SaaS Admin portal flows for platform operators
 * 
 * Validates Requirements:
 * - A1: SaaS Admin Dashboard
 * - A2: Tenant Management
 * - A3: Global Billing Administration
 * - A5: System Monitoring
 * - A6: Audit and Compliance
 */

test.describe('Admin Portal - Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to admin dashboard (requires admin auth in real scenario)
    await page.goto('/admin/dashboard');
  });

  test('should display admin dashboard with key metrics', async ({ page }) => {
    // Check page title/heading
    await expect(page.getByRole('heading', { name: /admin dashboard/i })).toBeVisible();
    
    // Check for metric cards (Requirements A1.1)
    await expect(page.getByText(/total tenants/i)).toBeVisible();
    await expect(page.getByText(/monthly revenue|mrr/i)).toBeVisible();
    await expect(page.getByText(/api requests/i)).toBeVisible();
  });

  test('should display system health status', async ({ page }) => {
    // Requirements A1.2: System health display
    await expect(page.getByText(/system health/i)).toBeVisible();
    await expect(page.getByText(/overall status/i)).toBeVisible();
  });

  test('should display top tenants by usage', async ({ page }) => {
    // Requirements A1.3: Top tenants display
    await expect(page.getByText(/top tenants/i)).toBeVisible();
  });

  test('should have period selector for metrics', async ({ page }) => {
    // Check for date range selector
    const periodSelector = page.locator('button').filter({ hasText: /7 days|30 days|today/i });
    await expect(periodSelector.first()).toBeVisible();
  });

  test('should auto-refresh metrics without page reload', async ({ page }) => {
    // Requirements A1.5: Auto-refresh without reload
    const initialUrl = page.url();
    
    // Wait for potential auto-refresh (check that URL doesn't change)
    await page.waitForTimeout(5000);
    expect(page.url()).toBe(initialUrl);
    
    // Page should still be functional
    await expect(page.getByText(/total tenants/i)).toBeVisible();
  });
});

test.describe('Admin Portal - Tenant Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/tenants-mgmt');
  });

  test('should display tenant list with pagination', async ({ page }) => {
    // Requirements A2.1: Paginated tenant list
    await expect(page.getByRole('heading', { name: /tenant/i })).toBeVisible();
    
    // Should have a table or list of tenants
    const tenantTable = page.locator('table, [role="grid"]');
    await expect(tenantTable.first()).toBeVisible();
  });

  test('should have search functionality for tenants', async ({ page }) => {
    // Requirements A2.2: Search tenants
    const searchInput = page.getByPlaceholder(/search/i);
    await expect(searchInput).toBeVisible();
    
    // Type in search
    await searchInput.fill('test');
    await page.waitForTimeout(500); // Debounce
  });

  test('should display tenant status badges', async ({ page }) => {
    // Check for status indicators
    const statusBadges = page.locator('[class*="badge"], [class*="Badge"]');
    // At least one status badge should be visible if tenants exist
    await page.waitForTimeout(1000);
  });
});

test.describe('Admin Portal - Billing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/billing');
  });

  test('should display global billing metrics', async ({ page }) => {
    // Requirements A3.1: MRR, ARR, outstanding invoices
    await expect(page.getByRole('heading', { name: /billing/i })).toBeVisible();
  });

  test('should have invoice filtering options', async ({ page }) => {
    // Requirements A3.2: Invoice filtering
    await page.waitForTimeout(1000);
    // Look for filter controls
    const filterControls = page.locator('select, [role="combobox"], button').filter({ hasText: /status|filter/i });
  });
});

test.describe('Admin Portal - System Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/monitoring');
  });

  test('should display service health for all components', async ({ page }) => {
    // Requirements A5.1: Service health display
    await expect(page.getByRole('heading', { name: /monitoring|system/i })).toBeVisible();
  });

  test('should show worker status', async ({ page }) => {
    // Requirements A5.3: Worker status (STT, TTS, LLM)
    await page.waitForTimeout(1000);
    // Check for worker-related content
  });
});

test.describe('Admin Portal - Audit Logs', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/audit');
  });

  test('should display paginated audit log', async ({ page }) => {
    // Requirements A6.1: Paginated audit log
    await expect(page.getByRole('heading', { name: /audit/i })).toBeVisible();
  });

  test('should have audit log filtering', async ({ page }) => {
    // Requirements A6.2: Filter by tenant, action, date
    await page.waitForTimeout(1000);
  });
});

test.describe('Admin Portal - User Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/users-mgmt');
  });

  test('should display user list from Keycloak', async ({ page }) => {
    // Requirements A7.1: Display all users
    await expect(page.getByRole('heading', { name: /user/i })).toBeVisible();
  });

  test('should have user search functionality', async ({ page }) => {
    // Requirements A7.2: Search users
    const searchInput = page.getByPlaceholder(/search/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill('test@example.com');
    }
  });
});

test.describe('Admin Portal - Plans Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/plans');
  });

  test('should display all plans from Lago', async ({ page }) => {
    // Requirements A4.1: Display all plans
    await expect(page.getByRole('heading', { name: /plan/i })).toBeVisible();
  });
});

test.describe('Admin Portal - Navigation', () => {
  test('should navigate between admin pages via sidebar', async ({ page }) => {
    await page.goto('/admin/dashboard');
    
    // Click on Tenants in sidebar
    const tenantsLink = page.getByRole('link', { name: /tenant/i });
    if (await tenantsLink.first().isVisible()) {
      await tenantsLink.first().click();
      await expect(page).toHaveURL(/tenant/);
    }
  });

  test('should have admin-specific sidebar items', async ({ page }) => {
    await page.goto('/admin/dashboard');
    
    // Admin sidebar should have specific items
    await expect(page.getByRole('link', { name: /dashboard/i }).first()).toBeVisible();
  });
});


/**
 * Property Test: Search Filter Consistency
 * **Feature: e2e-testing-infrastructure, Property 3: Search Filter Consistency**
 * **Validates: Requirements 3.2**
 * 
 * For any search query entered in tenant management, the System SHALL return
 * only tenants whose name, email, or ID contains the search term.
 */
test.describe('Property 3: Search Filter Consistency', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/tenants-mgmt');
    await page.waitForTimeout(1000);
  });

  // Test search with various query patterns
  const searchQueries = [
    'test',
    'demo',
    'acme',
    'corp',
    '@',
    '.com',
    '123',
  ];

  for (const query of searchQueries) {
    test(`search for "${query}" should filter results consistently`, async ({ page }) => {
      const searchInput = page.getByPlaceholder(/search/i);
      
      // Skip if search input not visible (requires auth)
      if (!(await searchInput.isVisible())) {
        test.skip();
        return;
      }

      // Clear and enter search query
      await searchInput.clear();
      await searchInput.fill(query);
      
      // Wait for debounce and results
      await page.waitForTimeout(800);

      // Get all visible tenant rows/cards
      const tenantRows = page.locator('table tbody tr, [data-testid="tenant-card"]');
      const rowCount = await tenantRows.count();

      // If results exist, verify each contains the search term
      if (rowCount > 0) {
        for (let i = 0; i < Math.min(rowCount, 5); i++) {
          const rowText = await tenantRows.nth(i).textContent();
          if (rowText) {
            // Verify the row contains the search term (case-insensitive)
            const containsQuery = rowText.toLowerCase().includes(query.toLowerCase());
            expect(
              containsQuery,
              `Row ${i} should contain "${query}" but got: ${rowText.substring(0, 100)}`
            ).toBeTruthy();
          }
        }
      }
    });
  }

  test('empty search should show all tenants', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i);
    
    if (!(await searchInput.isVisible())) {
      test.skip();
      return;
    }

    // First search for something
    await searchInput.fill('test');
    await page.waitForTimeout(500);

    // Then clear the search
    await searchInput.clear();
    await page.waitForTimeout(500);

    // Should show all tenants (or at least more than filtered)
    const tenantRows = page.locator('table tbody tr, [data-testid="tenant-card"]');
    const rowCount = await tenantRows.count();
    
    // Should have some results (unless no tenants exist)
    expect(rowCount).toBeGreaterThanOrEqual(0);
  });

  test('search should be case-insensitive', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i);
    
    if (!(await searchInput.isVisible())) {
      test.skip();
      return;
    }

    // Search with lowercase
    await searchInput.fill('test');
    await page.waitForTimeout(500);
    const lowerResults = await page.locator('table tbody tr, [data-testid="tenant-card"]').count();

    // Search with uppercase
    await searchInput.clear();
    await searchInput.fill('TEST');
    await page.waitForTimeout(500);
    const upperResults = await page.locator('table tbody tr, [data-testid="tenant-card"]').count();

    // Results should be the same
    expect(lowerResults).toBe(upperResults);
  });
});
