import { test, expect } from '@playwright/test';

test('Debug Lit rendering', async ({ page, baseURL }) => {
    // Capture all console messages
    const consoleLogs: string[] = [];
    const consoleErrors: string[] = [];

    page.on('console', msg => {
        const text = msg.text();
        consoleLogs.push(text);
        if (msg.type() === 'error') {
            consoleErrors.push(text);
        }
    });

    // Capture page errors
    const pageErrors: Error[] = [];
    page.on('pageerror', error => {
        pageErrors.push(error);
    });

    // Navigate using baseURL from config (env var: E2E_BASE_URL)
    await page.goto(`${baseURL}/login`);

    // Wait a bit for scripts to load
    await page.waitForTimeout(3000);

    // Get page HTML
    const html = await page.content();

    // Get #app div content
    const appContent = await page.locator('#app').innerHTML();

    console.log('=== PAGE HTML ===');
    console.log(html.substring(0, 500));

    console.log('\n=== #APP CONTENT ===');
    console.log(appContent);

    console.log('\n=== CONSOLE LOGS ===');
    consoleLogs.forEach(log => console.log(log));

    console.log('\n=== CONSOLE ERRORS ===');
    consoleErrors.forEach(err => console.log(err));

    console.log('\n=== PAGE ERRORS ===');
    pageErrors.forEach(err => console.log(err.message));

    // Check if view-login exists
    const viewLogin = page.locator('view-login');
    const exists = await viewLogin.count();
    console.log('\n=== view-login element count:', exists);

    // Screenshot
    await page.screenshot({ path: 'debug-screenshot.png', fullPage: true });
});

