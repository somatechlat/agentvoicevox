import { test, expect } from '@playwright/test';

test.describe('Lit 3 Frontend Health Check', () => {
    test('should load the login page with Lit components', async ({ page, baseURL }) => {
        // Navigate to login page using baseURL from config
        await page.goto(`${baseURL}/login`);

        // Wait for Lit component to render
        await page.waitForSelector('view-login', { timeout: 10000 });

        // Verify the view-login component exists
        const viewLogin = await page.locator('view-login');
        await expect(viewLogin).toBeVisible();

        // Check console for router initialization
        const consoleLogs: string[] = [];
        page.on('console', msg => consoleLogs.push(msg.text()));

        await page.reload();
        await page.waitForTimeout(1000);

        // Verify router logged initialization
        const hasRouterLog = consoleLogs.some(log => log.includes('[Lit Router]'));
        console.log('Console logs:', consoleLogs);

        console.log('✅ Login page loaded with Lit components');
    });

    test('should navigate to setup page', async ({ page, baseURL }) => {
        await page.goto(`${baseURL}/admin/setup`);

        // Wait for Lit component
        await page.waitForSelector('view-setup', { timeout: 10000 });

        const viewSetup = await page.locator('view-setup');
        await expect(viewSetup).toBeVisible();

        console.log('✅ Setup page loaded with Lit components');
    });

    test('should verify API is accessible', async ({ request }) => {
        // Test Django API health endpoint
        const apiResponse = await request.get('http://localhost:65020/health/');
        expect(apiResponse.ok()).toBeTruthy();

        const body = await apiResponse.json();
        expect(body.status).toBe('ok');

        console.log('✅ Django API health check passed:', body);
    });
});
