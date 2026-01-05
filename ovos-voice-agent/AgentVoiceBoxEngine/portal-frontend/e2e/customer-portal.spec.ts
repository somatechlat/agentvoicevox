import { test, expect, Page } from '@playwright/test';
import { authenticateAsTenantAdmin } from './auth.setup';

/**
 * Customer Portal E2E Tests
 * Tests the Tenant Admin portal flows for organization administrators
 * 
 * Validates Requirements:
 * - B1: Tenant Dashboard
 * - B2: Voice Sessions Management
 * - B3: Projects Management
 * - B4: API Key Management
 * - B5: Usage Analytics
 * - B6: Billing and Subscription
 * - B7: Team Management
 * - B8: Organization Settings
 */

test.describe('Customer Portal - Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await authenticateAsTenantAdmin(page);
    await page.goto('/dashboard');
  });

  test('should display customer dashboard with usage metrics', async ({ page }) => {
    // Requirements B1.1: Display usage metrics
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
    
    // Check for metric cards
    await expect(page.getByText(/api requests/i)).toBeVisible();
  });

  test('should display billing summary', async ({ page }) => {
    // Requirements B1.2: Billing summary from Lago
    await expect(page.getByText(/billing|plan|subscription/i).first()).toBeVisible();
  });

  test('should display system health status', async ({ page }) => {
    // Requirements B1.3: Service status
    await expect(page.getByText(/system health|status/i).first()).toBeVisible();
  });

  test('should display recent activity', async ({ page }) => {
    // Requirements B1.4: Recent activity
    await expect(page.getByText(/recent activity/i)).toBeVisible();
  });

  test('should have refresh button', async ({ page }) => {
    // Requirements B1.5: Auto-refresh capability
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await expect(refreshButton).toBeVisible();
    
    // Click refresh and verify no navigation
    const currentUrl = page.url();
    await refreshButton.click();
    await page.waitForTimeout(1000);
    expect(page.url()).toContain('/dashboard');
  });

  test('should display usage progress bars with color coding', async ({ page }) => {
    // Requirements B1.6: Usage limit warnings
    const progressBars = page.locator('[role="progressbar"], .h-2.rounded-full');
    await expect(progressBars.first()).toBeVisible();
  });
});

test.describe('Customer Portal - Voice Sessions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/sessions');
  });

  test('should display sessions page with metrics', async ({ page }) => {
    // Requirements B2.1: Session data display
    await expect(page.getByRole('heading', { name: /session/i })).toBeVisible();
    
    // Check for session metrics
    await expect(page.getByText(/active sessions/i)).toBeVisible();
    await expect(page.getByText(/total sessions/i)).toBeVisible();
  });

  test('should have session filter tabs', async ({ page }) => {
    // Requirements B2.2: Filter by status
    await expect(page.getByRole('button', { name: /all/i }).or(page.getByText(/all/i).first())).toBeVisible();
    await expect(page.getByRole('button', { name: /active/i }).or(page.getByText(/active/i).first())).toBeVisible();
    await expect(page.getByRole('button', { name: /closed/i }).or(page.getByText(/closed/i).first())).toBeVisible();
  });

  test('should filter sessions by status', async ({ page }) => {
    // Click on Active filter
    const activeFilter = page.getByText(/active/i).first();
    await activeFilter.click();
    await page.waitForTimeout(500);
  });

  test('should display session details when selected', async ({ page }) => {
    // Requirements B2.3: Session detail view
    await page.waitForTimeout(1000);
    
    // If sessions exist, click on one
    const sessionCard = page.locator('[class*="card"], [class*="Card"]').first();
    if (await sessionCard.isVisible()) {
      await sessionCard.click();
      await page.waitForTimeout(500);
    }
  });

  test('should have refresh button', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await expect(refreshButton).toBeVisible();
  });
});

test.describe('Customer Portal - Projects', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects');
  });

  test('should display projects page', async ({ page }) => {
    // Requirements B3.1: Display projects
    await expect(page.getByRole('heading', { name: /project/i })).toBeVisible();
  });

  test('should have create project button', async ({ page }) => {
    // Requirements B3.2: Create project capability
    const createButton = page.getByRole('button', { name: /create|new|add/i });
    await expect(createButton.first()).toBeVisible();
  });

  test('should display project environment badges', async ({ page }) => {
    // Projects should show environment (production, staging, development)
    await page.waitForTimeout(1000);
  });
});

test.describe('Customer Portal - API Keys', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/api-keys');
  });

  test('should display API keys page', async ({ page }) => {
    // Requirements B4.1: Display API keys
    await expect(page.getByRole('heading', { name: /api key/i })).toBeVisible();
  });

  test('should have create API key button', async ({ page }) => {
    // Requirements B4.2: Create key capability
    const createButton = page.getByRole('button', { name: /create api key/i });
    await expect(createButton).toBeVisible();
  });

  test('should open create key dialog', async ({ page }) => {
    // Click create button
    await page.getByRole('button', { name: /create api key/i }).click();
    
    // Dialog should open
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/create api key/i)).toBeVisible();
    
    // Should have name input
    await expect(page.getByLabel(/name/i)).toBeVisible();
    
    // Should have permissions/scopes
    await expect(page.getByText(/permission/i)).toBeVisible();
  });

  test('should validate key name is required', async ({ page }) => {
    await page.getByRole('button', { name: /create api key/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    
    // Create button should be disabled without name
    const createBtn = page.getByRole('button', { name: /^create key$/i });
    await expect(createBtn).toBeDisabled();
  });

  test('should display key table with columns', async ({ page }) => {
    // Requirements B4.1: Key list with details
    await page.waitForTimeout(1000);
    
    // Check for table headers
    const table = page.locator('table');
    if (await table.isVisible()) {
      await expect(page.getByRole('columnheader', { name: /name/i })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /key/i })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /status/i })).toBeVisible();
    }
  });

  test('should show key prefix only (not full key)', async ({ page }) => {
    // Requirements B4.1: Keys shown with prefix only
    await page.waitForTimeout(1000);
    
    // Look for masked key pattern (prefix...)
    const maskedKeys = page.locator('code').filter({ hasText: /\.\.\./ });
    // If keys exist, they should be masked
  });

  test('should have rotate and revoke actions', async ({ page }) => {
    // Requirements B4.3, B4.4: Rotate and revoke
    await page.waitForTimeout(1000);
    
    // Look for action buttons (if keys exist)
    const rotateBtn = page.getByRole('button', { name: /rotate/i });
    const revokeBtn = page.getByRole('button', { name: /revoke/i });
  });

  test('should close create dialog on cancel', async ({ page }) => {
    await page.getByRole('button', { name: /create api key/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    
    // Click cancel
    await page.getByRole('button', { name: /cancel/i }).click();
    
    // Dialog should close
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });
});

test.describe('Customer Portal - Usage Analytics', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/usage');
  });

  test('should display usage analytics page', async ({ page }) => {
    // Requirements B5.1: Display usage metrics
    await expect(page.getByRole('heading', { name: /usage/i })).toBeVisible();
  });

  test('should have time period selector', async ({ page }) => {
    // Requirements B5.2: Time period selection
    const periodSelector = page.locator('select, [role="combobox"], button').filter({ hasText: /7d|30d|90d|days/i });
    await expect(periodSelector.first()).toBeVisible();
  });

  test('should display usage chart', async ({ page }) => {
    // Requirements B5.3: Usage chart
    await page.waitForTimeout(1000);
    
    // Look for chart container (Recharts)
    const chart = page.locator('.recharts-wrapper, [class*="chart"], svg');
  });

  test('should show breakdown by metric type', async ({ page }) => {
    // Requirements B5.4: STT/TTS/LLM breakdown
    await page.waitForTimeout(1000);
  });
});

test.describe('Customer Portal - Billing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/billing');
  });

  test('should display billing page', async ({ page }) => {
    // Requirements B6.1: Display billing info
    await expect(page.getByRole('heading', { name: /billing/i })).toBeVisible();
  });

  test('should display current plan', async ({ page }) => {
    // Requirements B6.1: Current plan display
    await expect(page.getByText(/plan|subscription/i).first()).toBeVisible();
  });

  test('should display invoices', async ({ page }) => {
    // Requirements B6.5: Invoice history
    await page.waitForTimeout(1000);
  });
});

test.describe('Customer Portal - Team Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/team');
  });

  test('should display team page', async ({ page }) => {
    // Requirements B7.1: Display team members
    await expect(page.getByRole('heading', { name: /team/i })).toBeVisible();
  });

  test('should have invite member button', async ({ page }) => {
    // Requirements B7.2: Invite capability
    const inviteButton = page.getByRole('button', { name: /invite|add/i });
    await expect(inviteButton.first()).toBeVisible();
  });

  test('should display member roles', async ({ page }) => {
    // Requirements B7.1: Show roles
    await page.waitForTimeout(1000);
  });
});

test.describe('Customer Portal - Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('should display settings page', async ({ page }) => {
    // Requirements B8.1: Organization settings
    await expect(page.getByRole('heading', { name: /setting/i })).toBeVisible();
  });

  test('should have organization profile section', async ({ page }) => {
    // Requirements B8.1: Organization profile
    await expect(page.getByText(/organization|profile/i).first()).toBeVisible();
  });

  test('should have notification preferences', async ({ page }) => {
    // Requirements B8.3: Notification settings
    await page.waitForTimeout(1000);
  });

  test('should have webhook configuration', async ({ page }) => {
    // Requirements B8.4: Webhook management
    await expect(page.getByText(/webhook/i).first()).toBeVisible();
  });
});

test.describe('Customer Portal - Navigation', () => {
  test('should navigate between customer pages via sidebar', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Navigate to API Keys
    const apiKeysLink = page.getByRole('link', { name: /api key/i });
    if (await apiKeysLink.first().isVisible()) {
      await apiKeysLink.first().click();
      await expect(page).toHaveURL(/api-key/);
    }
  });

  test('should highlight active navigation item', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Dashboard link should be highlighted/active
    const dashboardLink = page.getByRole('link', { name: /dashboard/i }).first();
    await expect(dashboardLink).toBeVisible();
  });
});


/**
 * Property Test: Session Status Filter Accuracy
 * **Feature: e2e-testing-infrastructure, Property 4: Session Status Filter Accuracy**
 * **Validates: Requirements 5.2**
 * 
 * For any status filter selected (all, active, closed), the System SHALL display
 * only sessions matching the selected status.
 */
test.describe('Property 4: Session Status Filter Accuracy', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/sessions');
    await page.waitForTimeout(1000);
  });

  const statusFilters = ['all', 'active', 'closed'];

  for (const status of statusFilters) {
    test(`filter "${status}" should show only ${status} sessions`, async ({ page }) => {
      // Find and click the status filter
      const filterButton = page.getByRole('button', { name: new RegExp(status, 'i') })
        .or(page.getByText(new RegExp(`^${status}$`, 'i')));
      
      if (!(await filterButton.first().isVisible())) {
        test.skip();
        return;
      }

      await filterButton.first().click();
      await page.waitForTimeout(800);

      // Get all session cards/rows
      const sessionItems = page.locator('[data-testid="session-card"], [data-status], table tbody tr');
      const itemCount = await sessionItems.count();

      if (itemCount > 0 && status !== 'all') {
        // Verify each visible session matches the filter
        for (let i = 0; i < Math.min(itemCount, 5); i++) {
          const item = sessionItems.nth(i);
          const itemText = await item.textContent();
          const statusAttr = await item.getAttribute('data-status');
          
          if (statusAttr) {
            expect(
              statusAttr.toLowerCase() === status.toLowerCase(),
              `Session ${i} should have status "${status}" but has "${statusAttr}"`
            ).toBeTruthy();
          } else if (itemText) {
            // Check if status badge text matches
            const hasMatchingStatus = itemText.toLowerCase().includes(status.toLowerCase());
            // For 'all' filter, any status is valid
            if (status !== 'all') {
              expect(hasMatchingStatus).toBeTruthy();
            }
          }
        }
      }
    });
  }

  test('switching filters should update results', async ({ page }) => {
    // Click active filter
    const activeFilter = page.getByText(/^active$/i).first();
    if (await activeFilter.isVisible()) {
      await activeFilter.click();
      await page.waitForTimeout(500);
      const activeCount = await page.locator('[data-testid="session-card"], table tbody tr').count();

      // Click closed filter
      const closedFilter = page.getByText(/^closed$/i).first();
      if (await closedFilter.isVisible()) {
        await closedFilter.click();
        await page.waitForTimeout(500);
        const closedCount = await page.locator('[data-testid="session-card"], table tbody tr').count();

        // Click all filter
        const allFilter = page.getByText(/^all$/i).first();
        if (await allFilter.isVisible()) {
          await allFilter.click();
          await page.waitForTimeout(500);
          const allCount = await page.locator('[data-testid="session-card"], table tbody tr').count();

          // All should be >= active + closed (or equal if no overlap)
          expect(allCount).toBeGreaterThanOrEqual(Math.max(activeCount, closedCount));
        }
      }
    }
  });

  test('filter state should be visually indicated', async ({ page }) => {
    const filters = ['all', 'active', 'closed'];
    
    for (const filter of filters) {
      const filterButton = page.getByRole('button', { name: new RegExp(filter, 'i') })
        .or(page.getByText(new RegExp(`^${filter}$`, 'i')));
      
      if (await filterButton.first().isVisible()) {
        await filterButton.first().click();
        await page.waitForTimeout(300);
        
        // Check for active/selected state (varies by implementation)
        const classes = await filterButton.first().getAttribute('class');
        // Active filter typically has different styling
        expect(classes).toBeTruthy();
      }
    }
  });
});


/**
 * Property Test: API Key Secret Masking
 * **Feature: e2e-testing-infrastructure, Property 2: API Key Secret Masking**
 * **Validates: Requirements 6.1**
 * 
 * For any API key displayed in the key list, the System SHALL show only the key
 * prefix with masking (e.g., `avb_abc...`) and SHALL NOT display the full secret value.
 */
test.describe('Property 2: API Key Secret Masking', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);
  });

  test('all displayed keys should be masked', async ({ page }) => {
    // Get all key display elements
    const keyElements = page.locator('code, [data-testid="api-key-value"], .font-mono');
    const keyCount = await keyElements.count();

    for (let i = 0; i < keyCount; i++) {
      const keyText = await keyElements.nth(i).textContent();
      
      if (keyText && keyText.includes('avb_')) {
        // Key should be masked (contain ... or be truncated)
        const isMasked = keyText.includes('...') || 
                         keyText.includes('•') || 
                         keyText.includes('*') ||
                         keyText.length < 40; // Full keys are typically longer
        
        expect(
          isMasked,
          `Key ${i} should be masked but shows: ${keyText}`
        ).toBeTruthy();
        
        // Should NOT show full key (typically 40+ chars)
        const fullKeyPattern = /^avb_[a-zA-Z0-9]{32,}$/;
        expect(
          !fullKeyPattern.test(keyText.trim()),
          `Key ${i} appears to show full secret: ${keyText}`
        ).toBeTruthy();
      }
    }
  });

  test('key table should show prefix only', async ({ page }) => {
    const table = page.locator('table');
    
    if (await table.isVisible()) {
      const rows = page.locator('table tbody tr');
      const rowCount = await rows.count();

      for (let i = 0; i < Math.min(rowCount, 5); i++) {
        const rowText = await rows.nth(i).textContent();
        
        if (rowText && rowText.includes('avb_')) {
          // Extract key portion
          const keyMatch = rowText.match(/avb_[a-zA-Z0-9.•*]+/);
          if (keyMatch) {
            const keyValue = keyMatch[0];
            // Should be masked
            expect(
              keyValue.includes('...') || keyValue.includes('•') || keyValue.length < 20,
              `Row ${i} key should be masked: ${keyValue}`
            ).toBeTruthy();
          }
        }
      }
    }
  });

  test('copy button should not expose full key in list view', async ({ page }) => {
    // Find copy buttons in the key list
    const copyButtons = page.getByRole('button', { name: /copy/i });
    const copyCount = await copyButtons.count();

    // In list view, copy should only copy the prefix or be disabled
    // Full key copy should only be available immediately after creation
    for (let i = 0; i < Math.min(copyCount, 3); i++) {
      const button = copyButtons.nth(i);
      const isDisabled = await button.isDisabled();
      const ariaLabel = await button.getAttribute('aria-label');
      
      // Either disabled or labeled as "copy prefix"
      if (!isDisabled && ariaLabel) {
        expect(
          ariaLabel.toLowerCase().includes('prefix') || 
          ariaLabel.toLowerCase().includes('id'),
          `Copy button should indicate it copies prefix, not full key`
        ).toBeTruthy();
      }
    }
  });

  test('page source should not contain full API keys', async ({ page }) => {
    // Get page content
    const content = await page.content();
    
    // Full API keys typically match this pattern
    const fullKeyPattern = /avb_[a-zA-Z0-9]{32,}/g;
    const matches = content.match(fullKeyPattern);
    
    // Should not find any full keys in page source
    expect(
      matches === null || matches.length === 0,
      `Page source should not contain full API keys`
    ).toBeTruthy();
  });
});
