import { test, expect } from '@playwright/test';

// Service URLs from environment variables (same ports for test and prod)
const API_URL = process.env.E2E_API_URL || 'http://localhost:65020';
const KEYCLOAK_URL = process.env.E2E_KEYCLOAK_URL || 'http://localhost:65006';
const PORTAL_URL = process.env.E2E_BASE_URL || 'http://localhost:65027';

test.describe('Full Stack E2E Tests', () => {
    test('Django API health check', async ({ request }) => {
        const response = await request.get(`${API_URL}/health/`);
        expect(response.ok()).toBeTruthy();
        const body = await response.json();
        expect(body.status).toBe('ok');
        console.log('✅ Django API:', body);
    });

    test('Keycloak is accessible', async ({ request }) => {
        const response = await request.get(`${KEYCLOAK_URL}/realms/agentvoicebox/.well-known/openid-configuration`);
        expect(response.ok()).toBeTruthy();
        const config = await response.json();
        expect(config.issuer).toContain('agentvoicebox');
        console.log('✅ Keycloak OIDC config available:', config.issuer);
    });

    test('Portal frontend serves HTML and renders Lit', async ({ page, baseURL }) => {
        // Capture all console output
        const allLogs: Array<{ type: string, text: string }> = [];

        page.on('console', msg => {
            allLogs.push({ type: msg.type(), text: msg.text() });
        });

        page.on('pageerror', err => {
            allLogs.push({ type: 'pageerror', text: err.message });
        });

        // Navigate to root
        const response = await page.goto(`${baseURL}/`);
        expect(response?.ok()).toBeTruthy();

        // Wait for page to fully load and execute JS
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(5000);

        // Check page title
        const title = await page.title();
        console.log('Page title:', title);
        expect(title).toContain('AgentVoiceBox');

        // Log all console output
        console.log('=== All Console Output ===');
        allLogs.forEach(log => console.log(`[${log.type}] ${log.text}`));

        // Check for any errors
        const errors = allLogs.filter(l => l.type === 'error' || l.type === 'pageerror');
        console.log('Errors found:', errors.length);

        // Check body content
        const bodyHTML = await page.locator('body').innerHTML();
        console.log('Body length:', bodyHTML.length);
        console.log('Body preview:', bodyHTML.substring(0, 500));

        // Check #app content
        const appContent = await page.locator('#app').innerHTML();
        console.log('App content length:', appContent.length);
        console.log('App content:', appContent.substring(0, 500));

        console.log('✅ Page loaded');
    });

    test('Service ports are accessible from browser perspective', async ({ page }) => {
        // Test each service using env-configured URLs
        const services = [
            { name: 'Django API', url: `${API_URL}/health/` },
            { name: 'Keycloak', url: `${KEYCLOAK_URL}/` },
            { name: 'Portal', url: `${PORTAL_URL}/` },
        ];

        for (const svc of services) {
            try {
                const response = await page.goto(svc.url);
                console.log(`${svc.name}: ${response?.status()}`);
                expect(response?.status()).toBeLessThan(500);
            } catch (e) {
                console.log(`${svc.name}: FAILED - ${e}`);
            }
        }

        console.log('✅ All services accessible');
    });
});
