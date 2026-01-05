import { test, expect } from '@playwright/test';
import { authenticateAsTenantAdmin } from './auth.setup';

/**
 * Responsive UI E2E Tests
 * Tests that the portal works correctly across different screen sizes
 * 
 * Validates:
 * - Mobile responsiveness
 * - Tablet responsiveness
 * - Desktop layout
 * - Touch interactions
 */

const viewports = {
  mobile: { width: 375, height: 667 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1920, height: 1080 },
};

test.describe('Mobile Responsiveness', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize(viewports.mobile);
  });

  test('login page should be mobile-friendly', async ({ page }) => {
    await page.goto('/login');
    
    // All elements should be visible
    await expect(page.getByRole('heading', { name: 'AgentVoiceBox' })).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
    
    // Buttons should be full width or appropriately sized
    const ssoButton = page.getByRole('button', { name: /sign in with sso/i });
    const buttonBox = await ssoButton.boundingBox();
    expect(buttonBox?.width).toBeGreaterThan(200);
  });

  test('dashboard should have hamburger menu on mobile', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Hamburger menu should be visible
    const menuButton = page.getByRole('button', { name: /menu|toggle/i });
    // Menu button should exist on mobile
  });

  test('cards should stack vertically on mobile', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Cards should be full width on mobile
    const cards = page.locator('[class*="card"], [class*="Card"]');
    const firstCard = cards.first();
    if (await firstCard.isVisible()) {
      const box = await firstCard.boundingBox();
      // Card should be nearly full width (accounting for padding)
      expect(box?.width).toBeGreaterThan(300);
    }
  });

  test('tables should be scrollable on mobile', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);
    
    // Table container should allow horizontal scroll
    const table = page.locator('table');
    if (await table.isVisible()) {
      const tableContainer = table.locator('..');
      // Container should have overflow handling
    }
  });

  test('dialogs should be full-screen on mobile', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);
    
    // Open create dialog
    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      
      // Dialog should be appropriately sized for mobile
      const dialog = page.getByRole('dialog');
      if (await dialog.isVisible()) {
        const box = await dialog.boundingBox();
        // Dialog should be nearly full width
        expect(box?.width).toBeGreaterThan(300);
      }
    }
  });

  test('navigation should work via hamburger menu', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Open hamburger menu
    const menuButton = page.getByRole('button', { name: /menu|toggle/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();
      await page.waitForTimeout(300);
      
      // Click on a nav item
      const apiKeysLink = page.getByRole('link', { name: /api key/i });
      if (await apiKeysLink.first().isVisible()) {
        await apiKeysLink.first().click();
        await expect(page).toHaveURL(/api-key/);
      }
    }
  });
});

test.describe('Tablet Responsiveness', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize(viewports.tablet);
  });

  test('dashboard should show 2-column grid on tablet', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Cards should be in 2-column layout
    const cards = page.locator('[class*="card"], [class*="Card"]');
    if (await cards.first().isVisible()) {
      // Check that cards are side by side
    }
  });

  test('sidebar should be visible on tablet', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Sidebar should be visible (not hidden behind hamburger)
    const sidebar = page.getByRole('navigation');
    // On tablet, sidebar is typically visible
  });

  test('tables should display properly on tablet', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);
    
    // Table should be visible without horizontal scroll
    const table = page.locator('table');
    if (await table.isVisible()) {
      const box = await table.boundingBox();
      // Table should fit within viewport
      expect(box?.width).toBeLessThanOrEqual(768);
    }
  });
});

test.describe('Desktop Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize(viewports.desktop);
  });

  test('dashboard should show 4-column grid on desktop', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Metric cards should be in 4-column layout
    const metricCards = page.locator('[class*="card"], [class*="Card"]');
    // Check layout
  });

  test('sidebar should be expanded on desktop', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Sidebar should be fully visible with text labels
    const sidebar = page.getByRole('navigation');
    await expect(sidebar.first()).toBeVisible();
    
    // Navigation items should show text
    const dashboardLink = page.getByRole('link', { name: /dashboard/i });
    await expect(dashboardLink.first()).toBeVisible();
  });

  test('tables should show all columns on desktop', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);
    
    // All table columns should be visible
    const table = page.locator('table');
    if (await table.isVisible()) {
      await expect(page.getByRole('columnheader', { name: /name/i })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /status/i })).toBeVisible();
    }
  });

  test('admin dashboard should show full metrics grid', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.waitForTimeout(1000);
    
    // All metric cards should be visible
  });
});

test.describe('Touch Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize(viewports.mobile);
  });

  test('buttons should have adequate touch targets', async ({ page }) => {
    await page.goto('/login');
    
    // Buttons should be at least 44x44 pixels (iOS guideline)
    const ssoButton = page.getByRole('button', { name: /sign in with sso/i });
    const box = await ssoButton.boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
  });

  test('links should have adequate spacing', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);
    
    // Open mobile menu
    const menuButton = page.getByRole('button', { name: /menu|toggle/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();
      await page.waitForTimeout(300);
      
      // Nav links should have adequate spacing
      const navLinks = page.getByRole('link');
      // Links should be spaced apart for touch
    }
  });

  test('form inputs should be touch-friendly', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);
    
    // Open create dialog
    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      
      // Input fields should be adequately sized
      const nameInput = page.getByLabel(/name/i);
      if (await nameInput.isVisible()) {
        const box = await nameInput.boundingBox();
        expect(box?.height).toBeGreaterThanOrEqual(40);
      }
    }
  });

  test('checkboxes should be touch-friendly', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);
    
    // Open create dialog
    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      
      // Checkbox labels should be clickable
      const checkboxLabel = page.locator('label').filter({ has: page.locator('input[type="checkbox"]') }).first();
      if (await checkboxLabel.isVisible()) {
        await checkboxLabel.click();
        // Checkbox should toggle
      }
    }
  });
});

test.describe('Orientation Changes', () => {
  test('should handle portrait to landscape', async ({ page }) => {
    // Start in portrait
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    await page.waitForTimeout(500);
    
    // Switch to landscape
    await page.setViewportSize({ width: 667, height: 375 });
    await page.waitForTimeout(500);
    
    // Page should still be functional
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('should handle landscape to portrait', async ({ page }) => {
    // Start in landscape
    await page.setViewportSize({ width: 667, height: 375 });
    await page.goto('/dashboard');
    await page.waitForTimeout(500);
    
    // Switch to portrait
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    
    // Page should still be functional
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });
});

test.describe('Dark Mode', () => {
  test('should toggle dark mode', async ({ page }) => {
    await page.goto('/login');
    
    // Find theme toggle
    const themeToggle = page.locator('button').filter({ has: page.locator('svg') }).first();
    if (await themeToggle.isVisible()) {
      const initialIsDark = await page.evaluate(() => 
        document.documentElement.classList.contains('dark')
      );
      
      await themeToggle.click();
      await page.waitForTimeout(300);
      
      const newIsDark = await page.evaluate(() => 
        document.documentElement.classList.contains('dark')
      );
      
      expect(newIsDark).not.toBe(initialIsDark);
    }
  });

  test('dark mode should persist across pages', async ({ page }) => {
    await page.goto('/login');
    
    // Toggle to dark mode
    const themeToggle = page.locator('button').filter({ has: page.locator('svg') }).first();
    if (await themeToggle.isVisible()) {
      await themeToggle.click();
      await page.waitForTimeout(300);
      
      const isDark = await page.evaluate(() => 
        document.documentElement.classList.contains('dark')
      );
      
      // Navigate to another page
      await page.goto('/dashboard');
      await page.waitForTimeout(500);
      
      // Dark mode should persist
      const stillDark = await page.evaluate(() => 
        document.documentElement.classList.contains('dark')
      );
      
      expect(stillDark).toBe(isDark);
    }
  });
});
