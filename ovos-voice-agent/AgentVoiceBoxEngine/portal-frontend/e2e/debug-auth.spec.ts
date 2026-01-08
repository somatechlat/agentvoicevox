
import { test, expect } from '@playwright/test';

test('Debug Login URL Parameters', async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:65027');

    // Listen for navigation requests to Keycloak
    page.on('request', request => {
        const url = request.url();
        if (url.includes('/protocol/openid-connect/auth')) {
            console.log('--- AUTH REQUEST DETECTED ---');
            console.log('URL:', url);
            const urlObj = new URL(url);
            console.log('Params:', Object.fromEntries(urlObj.searchParams));

            if (!urlObj.searchParams.has('code_challenge_method')) {
                console.error('FAIL: Missing code_challenge_method');
            } else {
                console.log('SUCCESS: Found code_challenge_method =', urlObj.searchParams.get('code_challenge_method'));
            }
            console.log('-----------------------------');
        }
    });

    // Click Sign In button (assuming there is one, or it auto-redirects)
    // Check if we need to click
    const signInButton = page.locator('button:has-text("Sign In")').first();
    if (await signInButton.isVisible()) {
        console.log('Clicking Sign In button...');
        await signInButton.click();
    } else {
        console.log('No Sign In button found, waiting for auto-redirect...');
    }

    // Wait for redirect to happen
    try {
        await page.waitForTimeout(5000);
    } catch (e) {
        // Ignore timeout
    }
});
