import { test, expect } from '@playwright/test';

test.describe('Lit 3 Frontend Health Check', () => {
    test('should load the login page with Lit components', async ({ page }) => {
        // Navigate to login page
        await page.goto('http://localhost:28100/login');

        // Wait for Lit component to render
        await page.waitForSelector('view-login', { timeout: 5000 });

        // Verify the view-login component exists
        const viewLogin = await page.locator('view-login');
        await expect(viewLogin).toBeVisible();

        // Take screenshot
        await page.screenshot({ path: 'e2e-screenshots/lit-login.png', fullPage: true });

        // Check console for router initialization
        const consoleLogs: string[] = [];
        page.on('console', msg => consoleLogs.push(msg.text()));

        await page.reload();
        await page.waitForTimeout(1000);

        // Verify router logged initialization
        const hasRouterLog = consoleLogs.some(log => log.includes('[Lit Router]'));
        expect(hasRouterLog).toBeTruthy();

        console.log('✅ Login page loaded with Lit components');
    });

    test('should navigate to setup page', async ({ page }) => {
        await page.goto('http://localhost:28100/admin/setup');

        // Wait for Lit component
        await page.waitForSelector('view-setup', { timeout: 5000 });

        const viewSetup = await page.locator('view-setup');
        await expect(viewSetup).toBeVisible();

        console.log('✅ Setup page loaded with Lit components');
    });
});
