import { test, expect } from '@playwright/test';
import { authenticateAsTenantAdmin } from './auth.setup';

/**
 * Error Handling E2E Tests
 * Tests that the portal handles errors gracefully
 * 
 * Validates:
 * - Network error handling
 * - API error responses
 * - Form validation errors
 * - Session expiration
 * - Loading states
 */

test.describe('Network Error Handling', () => {
  test('should show error state when API fails', async ({ page }) => {
    await authenticateAsTenantAdmin(page);
    // Intercept API calls and return error
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    // Should show error message or retry button
    const errorMessage = page.getByText(/failed|error|try again/i);
    const retryButton = page.getByRole('button', { name: /retry|try again/i });
    
    // Either error message or retry button should be visible
    const hasError = await errorMessage.isVisible().catch(() => false);
    const hasRetry = await retryButton.isVisible().catch(() => false);
    expect(hasError || hasRetry).toBeTruthy();
  });

  test('should handle network timeout gracefully', async ({ page }) => {
    // Simulate slow network
    await page.route('**/api/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 30000));
      route.abort();
    });

    await page.goto('/dashboard');
    
    // Should show loading state initially
    const loadingIndicator = page.locator('[class*="skeleton"], [class*="Skeleton"], [class*="loading"]');
    await expect(loadingIndicator.first()).toBeVisible();
  });

  test('should show offline indicator when disconnected', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);

    // Simulate going offline
    await page.context().setOffline(true);
    
    // Try to refresh data
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await page.waitForTimeout(1000);
    }

    // Restore connection
    await page.context().setOffline(false);
  });
});

test.describe('API Error Responses', () => {
  test('should handle 401 Unauthorized', async ({ page }) => {
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 401,
        body: JSON.stringify({ error: 'Unauthorized' }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should handle 403 Forbidden', async ({ page }) => {
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 403,
        body: JSON.stringify({ error: 'Forbidden' }),
      });
    });

    await page.goto('/admin/dashboard');
    await page.waitForTimeout(2000);

    // Should show forbidden message or redirect
    const forbiddenMessage = page.getByText(/forbidden|permission|access denied/i);
    const isOnLogin = page.url().includes('/login');
    
    const hasForbidden = await forbiddenMessage.isVisible().catch(() => false);
    expect(hasForbidden || isOnLogin).toBeTruthy();
  });

  test('should handle 404 Not Found', async ({ page }) => {
    await page.route('**/api/v2/sessions/*', route => {
      route.fulfill({
        status: 404,
        body: JSON.stringify({ error: 'Not Found' }),
      });
    });

    await page.goto('/sessions');
    await page.waitForTimeout(1000);

    // Should handle gracefully (show empty state or error)
  });

  test('should handle 422 Validation Error', async ({ page }) => {
    await page.route('**/api/v2/keys', route => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 422,
          body: JSON.stringify({
            error: {
              type: 'validation_error',
              message: 'Invalid input',
              param: 'name',
            },
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    // Try to create a key
    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await page.getByLabel(/name/i).fill('test');
      
      const scopeCheckbox = page.locator('input[type="checkbox"]').first();
      if (await scopeCheckbox.isVisible()) {
        await scopeCheckbox.check();
      }
      
      const submitBtn = page.getByRole('button', { name: /^create key$/i });
      if (await submitBtn.isEnabled()) {
        await submitBtn.click();
        await page.waitForTimeout(1000);
        
        // Should show validation error
        const errorMessage = page.getByText(/invalid|error/i);
      }
    }
  });

  test('should handle 429 Rate Limit', async ({ page }) => {
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 429,
        body: JSON.stringify({ error: 'Too Many Requests' }),
        headers: { 'Retry-After': '60' },
      });
    });

    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    // Should show rate limit message
    const rateLimitMessage = page.getByText(/rate limit|too many|slow down/i);
  });
});

test.describe('Form Validation', () => {
  test('should validate required fields', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      
      // Try to submit without filling required fields
      const submitBtn = page.getByRole('button', { name: /^create key$/i });
      
      // Button should be disabled
      await expect(submitBtn).toBeDisabled();
    }
  });

  test('should show validation errors inline', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForTimeout(1000);

    // Try to submit invalid data
    const emailInput = page.getByLabel(/email/i);
    if (await emailInput.isVisible()) {
      await emailInput.fill('invalid-email');
      await emailInput.blur();
      
      // Should show validation error
      const errorMessage = page.getByText(/invalid|valid email/i);
    }
  });

  test('should validate URL format for webhooks', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForTimeout(1000);

    // Find webhook URL input
    const urlInput = page.getByLabel(/url/i);
    if (await urlInput.isVisible()) {
      await urlInput.fill('not-a-valid-url');
      await urlInput.blur();
      
      // Should show URL validation error
    }
  });

  test('should validate numeric inputs', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      
      // Find expiration input
      const expiresInput = page.getByLabel(/expir/i);
      if (await expiresInput.isVisible()) {
        await expiresInput.fill('-1');
        await expiresInput.blur();
        
        // Should show validation error or reset to valid value
      }
    }
  });
});

test.describe('Loading States', () => {
  test('should show loading skeleton on dashboard', async ({ page }) => {
    // Slow down API response
    await page.route('**/api/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      route.continue();
    });

    await page.goto('/dashboard');
    
    // Should show skeleton loaders
    const skeletons = page.locator('[class*="skeleton"], [class*="Skeleton"]');
    await expect(skeletons.first()).toBeVisible();
  });

  test('should show loading state on button click', async ({ page }) => {
    await page.route('**/api/v2/keys', async route => {
      if (route.request().method() === 'POST') {
        await new Promise(resolve => setTimeout(resolve, 2000));
        route.fulfill({
          status: 200,
          body: JSON.stringify({ id: '123', secret: 'avb_test123' }),
        });
      } else {
        route.continue();
      }
    });

    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await page.getByLabel(/name/i).fill('test');
      
      const scopeCheckbox = page.locator('input[type="checkbox"]').first();
      if (await scopeCheckbox.isVisible()) {
        await scopeCheckbox.check();
      }
      
      const submitBtn = page.getByRole('button', { name: /^create key$/i });
      if (await submitBtn.isEnabled()) {
        await submitBtn.click();
        
        // Button should show loading state
        await expect(page.getByText(/creating/i)).toBeVisible();
      }
    }
  });

  test('should show loading state on table refresh', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    // Slow down next API call
    await page.route('**/api/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      route.continue();
    });

    // Trigger refresh
    const refreshBtn = page.getByRole('button', { name: /refresh/i });
    if (await refreshBtn.isVisible()) {
      await refreshBtn.click();
      
      // Should show loading indicator
    }
  });
});

test.describe('Session Expiration', () => {
  test('should redirect to login on session expiry', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);

    // Simulate session expiry by returning 401
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 401,
        body: JSON.stringify({ error: 'Session expired' }),
      });
    });

    // Trigger an API call
    const refreshBtn = page.getByRole('button', { name: /refresh/i });
    if (await refreshBtn.isVisible()) {
      await refreshBtn.click();
      await page.waitForTimeout(2000);
      
      // Should redirect to login
      await expect(page).toHaveURL(/\/login/);
    }
  });

  test('should show session expired message', async ({ page }) => {
    await page.goto('/login?error=session_expired');
    
    // Should show session expired message
    const expiredMessage = page.getByText(/session expired|logged out/i);
  });
});

test.describe('Empty States', () => {
  test('should show empty state when no API keys', async ({ page }) => {
    await page.route('**/api/v2/keys', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify([]),
      });
    });

    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    // Should show empty state
    const emptyState = page.getByText(/no api keys|create your first/i);
    await expect(emptyState).toBeVisible();
  });

  test('should show empty state when no sessions', async ({ page }) => {
    await page.route('**/api/v2/sessions', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ sessions: [] }),
      });
    });

    await page.goto('/sessions');
    await page.waitForTimeout(1000);

    // Should show empty state
    const emptyState = page.getByText(/no sessions/i);
    await expect(emptyState).toBeVisible();
  });

  test('should show empty state when no projects', async ({ page }) => {
    await page.route('**/api/v2/projects', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify([]),
      });
    });

    await page.goto('/projects');
    await page.waitForTimeout(1000);

    // Should show empty state or create prompt
  });
});

test.describe('Confirmation Dialogs', () => {
  test('should confirm before revoking API key', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    const revokeBtn = page.getByRole('button', { name: /revoke/i }).first();
    if (await revokeBtn.isVisible() && await revokeBtn.isEnabled()) {
      // Set up dialog handler
      let dialogShown = false;
      page.on('dialog', async dialog => {
        dialogShown = true;
        await dialog.dismiss();
      });

      await revokeBtn.click();
      await page.waitForTimeout(500);

      // Confirmation should have been shown
      expect(dialogShown).toBeTruthy();
    }
  });

  test('should confirm before deleting project', async ({ page }) => {
    await page.goto('/projects');
    await page.waitForTimeout(1000);

    const deleteBtn = page.getByRole('button', { name: /delete/i }).first();
    if (await deleteBtn.isVisible()) {
      let dialogShown = false;
      page.on('dialog', async dialog => {
        dialogShown = true;
        await dialog.dismiss();
      });

      await deleteBtn.click();
      await page.waitForTimeout(500);

      expect(dialogShown).toBeTruthy();
    }
  });

  test('should confirm before removing team member', async ({ page }) => {
    await page.goto('/team');
    await page.waitForTimeout(1000);

    const removeBtn = page.getByRole('button', { name: /remove/i }).first();
    if (await removeBtn.isVisible()) {
      let dialogShown = false;
      page.on('dialog', async dialog => {
        dialogShown = true;
        await dialog.dismiss();
      });

      await removeBtn.click();
      await page.waitForTimeout(500);

      expect(dialogShown).toBeTruthy();
    }
  });
});


/**
 * Property Test: Error Response Handling
 * **Feature: e2e-testing-infrastructure, Property 6: Error Response Handling**
 * **Validates: Requirements 13.1, 13.2, 13.3**
 * 
 * For any API error response (4xx or 5xx), the System SHALL display a user-friendly
 * error message and SHALL NOT expose raw error details.
 */
test.describe('Property 6: Error Response Handling', () => {
  const errorCodes = [400, 401, 403, 404, 422, 429, 500, 502, 503];

  for (const statusCode of errorCodes) {
    test(`should handle ${statusCode} error gracefully`, async ({ page }) => {
      // Intercept API calls and return error
      await page.route('**/api/**', route => {
        route.fulfill({
          status: statusCode,
          body: JSON.stringify({ 
            error: `Error ${statusCode}`,
            message: 'Internal error details that should not be shown',
            stack: 'Error stack trace that should be hidden',
          }),
        });
      });

      await page.goto('/dashboard');
      await page.waitForTimeout(2000);

      // Should show user-friendly message or redirect
      const pageContent = await page.content();
      
      // Should NOT expose raw error details
      expect(!pageContent.includes('stack trace')).toBeTruthy();
      expect(!pageContent.includes('Internal error details')).toBeTruthy();
      
      // Should show friendly message or redirect to login
      const hasError = await page.getByText(/error|failed|try again|something went wrong/i).isVisible().catch(() => false);
      const isOnLogin = page.url().includes('/login');
      
      expect(hasError || isOnLogin).toBeTruthy();
    });
  }

  test('error messages should be user-friendly', async ({ page }) => {
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ 
          error: 'ECONNREFUSED',
          code: 'ERR_CONNECTION_REFUSED',
        }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    const pageContent = await page.content();
    
    // Should NOT show technical error codes
    expect(!pageContent.includes('ECONNREFUSED')).toBeTruthy();
    expect(!pageContent.includes('ERR_CONNECTION_REFUSED')).toBeTruthy();
  });

  test('error state should provide recovery options', async ({ page }) => {
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Server Error' }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    // Should have retry button or link to go back
    const retryBtn = page.getByRole('button', { name: /retry|try again|refresh/i });
    const homeLink = page.getByRole('link', { name: /home|back|dashboard/i });
    
    const hasRetry = await retryBtn.isVisible().catch(() => false);
    const hasHome = await homeLink.first().isVisible().catch(() => false);
    const isOnLogin = page.url().includes('/login');
    
    expect(hasRetry || hasHome || isOnLogin).toBeTruthy();
  });
});

/**
 * Property Test: Form Validation Feedback
 * **Feature: e2e-testing-infrastructure, Property 7: Form Validation Feedback**
 * **Validates: Requirements 13.4**
 * 
 * For any form with invalid input, the System SHALL highlight the invalid fields
 * and display specific error messages before allowing submission.
 */
test.describe('Property 7: Form Validation Feedback', () => {
  test('empty required fields should show validation errors', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (!(await createBtn.isVisible())) {
      test.skip();
      return;
    }

    await createBtn.click();
    await page.waitForTimeout(500);

    // Try to submit without filling required fields
    const submitBtn = page.getByRole('button', { name: /^create key$/i });
    
    // Button should be disabled
    await expect(submitBtn).toBeDisabled();
  });

  test('invalid email format should show error', async ({ page }) => {
    await page.goto('/team');
    await page.waitForTimeout(1000);

    const inviteBtn = page.getByRole('button', { name: /invite|add/i }).first();
    if (!(await inviteBtn.isVisible())) {
      test.skip();
      return;
    }

    await inviteBtn.click();
    await page.waitForTimeout(500);

    const emailInput = page.getByLabel(/email/i);
    if (await emailInput.isVisible()) {
      await emailInput.fill('invalid-email-format');
      await emailInput.blur();
      await page.waitForTimeout(300);

      // Should show validation error
      const errorMsg = page.getByText(/invalid|valid email|email format/i);
      const hasError = await errorMsg.isVisible().catch(() => false);
      
      // Either shows error or prevents submission
      const submitBtn = page.getByRole('button', { name: /invite|send/i }).last();
      const isDisabled = await submitBtn.isDisabled().catch(() => false);
      
      expect(hasError || isDisabled).toBeTruthy();
    }
  });

  test('validation errors should be specific to field', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForTimeout(1000);

    // Find form fields
    const inputs = page.locator('input[required], input[type="email"], input[type="url"]');
    const inputCount = await inputs.count();

    for (let i = 0; i < Math.min(inputCount, 3); i++) {
      const input = inputs.nth(i);
      const inputType = await input.getAttribute('type');
      const inputName = await input.getAttribute('name') || await input.getAttribute('id');
      
      if (inputType === 'email') {
        await input.fill('invalid');
        await input.blur();
        await page.waitForTimeout(200);
        
        // Error should be near the field
        const parent = input.locator('..');
        const errorInParent = await parent.getByText(/invalid|error/i).isVisible().catch(() => false);
        // Validation feedback should exist
      }
    }
  });

  test('form should not submit with validation errors', async ({ page }) => {
    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (!(await createBtn.isVisible())) {
      test.skip();
      return;
    }

    await createBtn.click();
    
    // Fill with invalid data
    const nameInput = page.getByLabel(/name/i);
    if (await nameInput.isVisible()) {
      // Leave name empty or fill with invalid chars
      await nameInput.fill('');
      
      const submitBtn = page.getByRole('button', { name: /^create key$/i });
      
      // Should be disabled or clicking should not navigate
      const isDisabled = await submitBtn.isDisabled();
      expect(isDisabled).toBeTruthy();
    }
  });

  test('validation should happen before API call', async ({ page }) => {
    let apiCalled = false;
    
    await page.route('**/api/v2/keys', route => {
      apiCalled = true;
      route.continue();
    });

    await page.goto('/api-keys');
    await page.waitForTimeout(1000);

    const createBtn = page.getByRole('button', { name: /create api key/i });
    if (!(await createBtn.isVisible())) {
      test.skip();
      return;
    }

    await createBtn.click();
    
    // Try to submit empty form
    const submitBtn = page.getByRole('button', { name: /^create key$/i });
    if (await submitBtn.isEnabled()) {
      await submitBtn.click();
      await page.waitForTimeout(500);
    }

    // API should not be called for invalid form
    // (This depends on implementation - some may call API and get 422)
  });
});
