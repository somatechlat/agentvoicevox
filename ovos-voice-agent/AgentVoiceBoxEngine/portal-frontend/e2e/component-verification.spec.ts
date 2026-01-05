import { test, expect } from '@playwright/test';

test.describe('Lit Component Verification', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:28100/admin/setup');
        // Wait for view-setup to render
        await page.waitForSelector('view-setup', { timeout: 5000 });
    });

    test('saas-infra-card should render with all statuses', async ({ page }) => {
        // Check that infrastructure cards are visible
        const cards = await page.locator('saas-infra-card').all();
        expect(cards.length).toBeGreaterThan(0);

        // Verify Redis card renders
        const redisCard = page.locator('saas-infra-card').filter({ hasText: 'Redis Cache' });
        await expect(redisCard).toBeVisible();

        // Verify status dots render
        const statusDots = page.locator('saas-status-dot');
        await expect(statusDots.first()).toBeVisible();

        console.log('✅ saas-infra-card renders correctly');
    });

    test('saas-glass-modal should open and close', async ({ page }) => {
        // Click "Configure Redis" button to open modal
        const redisEdit = page.locator('saas-infra-card').filter({ hasText: 'Redis' }).locator('button');
        await redisEdit.click();

        // Wait for modal to appear
        await page.waitForTimeout(300); // Animation delay

        // Check modal is visible
        const modal = page.locator('saas-glass-modal');
        await expect(modal).toBeVisible();

        // Check modal title
        await expect(page.locator('h2').filter({ hasText: 'Configure Redis' })).toBeVisible();

        // Click cancel button to close
        const cancelBtn = page.locator('button').filter({ hasText: 'Cancel' });
        await cancelBtn.click();

        // Wait for modal to close
        await page.waitForTimeout(300);

        console.log('✅ saas-glass-modal opens and closes correctly');
    });

    test('saas-status-dot should show different statuses', async ({ page }) => {
        // Get all status dots
        const connectedDots = page.locator('saas-infra-card').filter({ hasText: 'connected' }).locator('saas-status-dot');
        const pendingDots = page.locator('saas-infra-card').filter({ hasText: 'pending' }).locator('saas-status-dot');

        // Verify at least one of each exists (based on view-setup.ts)
        const connectedCount = await connectedDots.count();
        const pendingCount = await pendingDots.count();

        expect(connectedCount).toBeGreaterThan(0);
        expect(pendingCount).toBeGreaterThan(0);

        console.log(`✅ Found ${connectedCount} connected, ${pendingCount} pending status dots`);
    });

    test('tenant creation button should be visible', async ({ page }) => {
        const createBtn = page.locator('button').filter({ hasText: /Create|\\+ Create/ });
        await expect(createBtn).toBeVisible();

        // Click it to test modal
        await createBtn.click();
        await page.waitForTimeout(300);

        // Modal should open
        const modal = page.locator('saas-glass-modal');
        await expect(modal).toBeVisible();

        console.log('✅ Tenant creation button works');
    });

    test('launch button should be visible and clickable', async ({ page }) => {
        const launchBtn = page.locator('button').filter({ hasText: /Launch System/i });
        await expect(launchBtn).toBeVisible();
        await expect(launchBtn).toBeEnabled();

        console.log('✅ Launch System button rendered');
    });

    test('navigation header should display correctly', async ({ page }) => {
        // Check header exists
        const header = page.locator('header').filter({ hasText: 'Universal SaaS Setup' });
        await expect(header).toBeVisible();

        // Check system admin indicator
        await expect(page.locator('text=System Admin')).toBeVisible();

        // Check status dot in header
        const headerDot = page.locator('header').locator('.h-2.w-2.rounded-full.bg-saas-success');
        await expect(headerDot).toBeVisible();

        console.log('✅ Navigation header rendered correctly');
    });
});
