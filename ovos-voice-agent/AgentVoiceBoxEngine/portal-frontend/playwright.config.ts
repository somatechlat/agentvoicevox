import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration
 * 
 * Test Suites:
 * - login.spec.ts: Login page rendering and SSO flow
 * - auth-flow.spec.ts: Authentication and protected routes
 * - all-pages.spec.ts: Unified layout verification
 * - admin-portal.spec.ts: SaaS Admin portal flows
 * - customer-portal.spec.ts: Customer/Tenant portal flows
 * - user-portal.spec.ts: User portal (read-only) flows
 * - voice-config.spec.ts: Voice configuration pages
 * - crud-flows.spec.ts: CRUD operations for entities
 * - role-routing.spec.ts: Role-based routing and permissions
 * - responsive-ui.spec.ts: Mobile/tablet/desktop responsiveness
 * - error-handling.spec.ts: Error states and edge cases
 */

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : 2,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  timeout: 60000,
  expect: {
    timeout: 10000,
  },
  use: {
    // Default to Docker cluster port 25007, fallback to dev server 3000
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:25007',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    ignoreHTTPSErrors: true,
    // Viewport for consistent testing
    viewport: { width: 1280, height: 720 },
    // Action timeout
    actionTimeout: 15000,
    // Navigation timeout
    navigationTimeout: 30000,
  },
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile browsers
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },
    // Tablet
    {
      name: 'tablet',
      use: { ...devices['iPad (gen 7)'] },
    },
  ],
  // Web server configuration (optional - for local dev)
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120000,
  },
});
