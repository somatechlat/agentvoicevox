import { test, expect } from '@playwright/test';

/**
 * Test all portal pages have unified layout with sidebar
 */
test.describe('Unified Portal Layout', () => {
  const pages = [
    { path: '/dashboard', title: 'Dashboard' },
    { path: '/sessions', title: 'Voice Sessions' },
    { path: '/projects', title: 'Projects' },
    { path: '/api-keys', title: 'API Keys' },
    { path: '/usage', title: 'Usage Analytics' },
    { path: '/billing', title: 'Billing' },
    { path: '/team', title: 'Team' },
    { path: '/settings', title: 'Settings' },
  ];

  for (const page of pages) {
    test(`${page.path} should have sidebar navigation`, async ({ page: browserPage, isMobile }) => {
      await browserPage.goto(page.path);
      
      // Should not redirect to login (dev bypass enabled)
      await expect(browserPage).toHaveURL(new RegExp(page.path));
      
      // On mobile, sidebar is hidden by default - need to open it via hamburger menu
      if (isMobile) {
        // Mobile: check for hamburger menu button and open sidebar
        const menuButton = browserPage.getByRole('button', { name: /menu|toggle/i });
        if (await menuButton.isVisible()) {
          await menuButton.click();
          // Wait for sidebar to animate in
          await browserPage.waitForTimeout(300);
        }
      }
      
      // Should have sidebar with navigation links (visible on desktop, or after opening on mobile)
      const sidebar = browserPage.getByRole('navigation', { name: 'Main navigation' });
      await expect(sidebar).toBeVisible();
      
      // Should have AgentVoiceBox branding in sidebar (use first() for multiple matches)
      await expect(browserPage.getByText('AgentVoiceBox').first()).toBeVisible();
      
      // Should have Dashboard link in sidebar
      await expect(browserPage.getByRole('link', { name: 'Dashboard' }).first()).toBeVisible();
    });
  }
});
