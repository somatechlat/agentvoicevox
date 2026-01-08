
import { test, expect } from '@playwright/test';

test('Capture Universal SaaS Setup Screen', async ({ page }) => {
    // Direct navigation to setup screen (bypassing auth for visual check)
    await page.goto('http://localhost:65027/admin/setup');

    // Wait for component to render
    await page.waitForSelector('view-setup');

    // Wait a bit for fonts/styles
    await page.waitForTimeout(2000);

    // Capture screenshot
    await page.screenshot({ path: 'setup-screen.png', fullPage: true });

    console.log('Screenshot captured: setup-screen.png');
});
