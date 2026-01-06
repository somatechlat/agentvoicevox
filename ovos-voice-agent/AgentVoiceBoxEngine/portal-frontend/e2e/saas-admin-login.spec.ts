import { test, expect } from '@playwright/test';

/**
 * SaaS Admin Login Flow Test
 * 
 * Tests the complete login flow for the default SaaS admin user:
 * - Email: saasadmin@somatech.dev
 * - Password: saasadmin
 * 
 * All tests run in HEADLESS mode (no browser window)
 */

// Service URLs from environment variables
const KEYCLOAK_URL = process.env.E2E_KEYCLOAK_URL || 'http://localhost:65006';

test.describe('SaaS Admin Login Flow', () => {
    test('should display login page on portal', async ({ page, baseURL }) => {
        // Navigate to portal
        await page.goto(`${baseURL}/login`);

        // Wait for Lit component to render
        await page.waitForSelector('view-login', { timeout: 10000 });

        // Verify login page elements
        await expect(page.getByText('AgentVoiceBox')).toBeVisible();
        await expect(page.getByText('Welcome')).toBeVisible();

        console.log('✅ Login page rendered with Lit components');
    });

    test('should redirect to Keycloak on SSO click', async ({ page, baseURL }) => {
        // Navigate to login page
        await page.goto(`${baseURL}/login`);
        await page.waitForSelector('view-login', { timeout: 10000 });

        // Find the SSO login button by text content
        const ssoButton = page.locator('button', { hasText: 'Sign in with SSO' });
        await expect(ssoButton).toBeVisible();

        console.log('📍 Found SSO button, clicking...');

        // Click and wait for navigation simultaneously
        await Promise.all([
            page.waitForURL(/localhost:65006/, { timeout: 30000 }),
            ssoButton.click(),
        ]);

        // Verify we're on Keycloak login page
        const url = page.url();
        console.log('✅ Redirected to Keycloak:', url);
        expect(url).toContain('agentvoicebox');
    });

    test('should complete full login with saasadmin credentials', async ({ page, baseURL }) => {
        // Navigate to login page
        await page.goto(`${baseURL}/login`);
        await page.waitForSelector('view-login', { timeout: 10000 });

        // Click SSO login and wait for navigation
        const ssoButton = page.locator('button', { hasText: 'Sign in with SSO' });
        await Promise.all([
            page.waitForURL(/localhost:65006/, { timeout: 30000 }),
            ssoButton.click(),
        ]);

        // Wait for login form to be ready
        await page.waitForSelector('#username, input[name="username"]', { timeout: 20000 });

        // Fill in SaaS admin credentials
        await page.fill('#username', 'saasadmin@somatech.dev');
        await page.fill('#password', 'saasadmin');

        console.log('📝 Entering credentials for saasadmin@somatech.dev');

        // Submit login form
        await page.click('#kc-login');

        // Wait for redirect back to portal (with auth code or to dashboard)
        await page.waitForURL(/localhost/, { timeout: 30000 });

        // Check if we're authenticated (either at callback or dashboard)
        const url = page.url();
        console.log('🔄 Redirected to:', url);

        // Should be redirected to /admin/setup or auth callback
        expect(url).toMatch(/\/(admin|auth|dashboard|callback)/);

        console.log('✅ Login flow completed successfully');
    });

    test('should verify Keycloak token exchange works', async ({ request }) => {
        // Test token exchange with password grant (for API testing)
        const tokenResponse = await request.post(`${KEYCLOAK_URL}/realms/agentvoicebox/protocol/openid-connect/token`, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            form: {
                grant_type: 'password',
                client_id: 'portal-frontend',
                username: 'saasadmin@somatech.dev',
                password: 'saasadmin',
                scope: 'openid profile email'
            }
        });

        expect(tokenResponse.ok()).toBeTruthy();

        const tokens = await tokenResponse.json();
        expect(tokens.access_token).toBeDefined();
        expect(tokens.refresh_token).toBeDefined();

        console.log('✅ Token exchange successful');
        console.log('   Token type:', tokens.token_type);
        console.log('   Expires in:', tokens.expires_in, 'seconds');
    });
});
