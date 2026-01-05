/**
 * E2E Test Authentication Setup - PRODUCTION-LIKE TESTING
 * 
 * Uses REAL Keycloak authentication with actual tokens.
 * Test users are defined in the Keycloak realm configuration.
 * 
 * Port 65006: Keycloak (per docker-compose port policy 65000-65099)
 * Port 65013: Portal Frontend
 */

import { test as setup, expect } from '@playwright/test';
import { Page, BrowserContext } from '@playwright/test';

// Keycloak configuration - matches portal-frontend/src/lib/auth.ts
const KEYCLOAK_URL = process.env.KEYCLOAK_URL || 'http://localhost:65006';
const KEYCLOAK_REALM = 'agentvoicebox';
const KEYCLOAK_CLIENT_ID = 'agentvoicebox-portal'; // Public client with direct access grants

// Test user credentials from keycloak/realms/agentvoicebox-realm.json
export const TEST_USERS = {
  saasAdmin: {
    username: 'saasadmin@agentvoicebox.com',
    password: 'saasadmin123',
    roles: ['saas_admin'],
    tenantId: '00000000-0000-0000-0000-000000000000',
  },
  tenantAdmin: {
    username: 'admin@agentvoicebox.com',
    password: 'admin123',
    roles: ['tenant_admin'],
    tenantId: '00000000-0000-0000-0000-000000000001',
  },
  agentAdmin: {
    username: 'agentadmin@agentvoicebox.com',
    password: 'agentadmin123',
    roles: ['agent_admin'],
    tenantId: '00000000-0000-0000-0000-000000000001',
  },
  supervisor: {
    username: 'supervisor@agentvoicebox.com',
    password: 'supervisor123',
    roles: ['supervisor'],
    tenantId: '00000000-0000-0000-0000-000000000001',
  },
  operator: {
    username: 'operator@agentvoicebox.com',
    password: 'operator123',
    roles: ['operator'],
    tenantId: '00000000-0000-0000-0000-000000000001',
  },
  developer: {
    username: 'developer@agentvoicebox.com',
    password: 'dev123',
    roles: ['agent_admin'],
    tenantId: '00000000-0000-0000-0000-000000000001',
  },
  demo: {
    username: 'demo@test.com',
    password: 'demo123',
    roles: ['tenant_admin'],
    tenantId: '00000000-0000-0000-0000-000000000002',
  },
  billing: {
    username: 'billing@agentvoicebox.com',
    password: 'billing123',
    roles: ['billing_admin'],
    tenantId: '00000000-0000-0000-0000-000000000001',
  },
} as const;

export type TestUserType = keyof typeof TEST_USERS;

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  refresh_expires_in: number;
  token_type: string;
}

/**
 * Get real tokens from Keycloak using Resource Owner Password Credentials grant
 * This is production-like authentication - no mocks!
 */
export async function getKeycloakTokens(
  username: string,
  password: string
): Promise<TokenResponse> {
  const tokenUrl = `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token`;
  
  const response = await fetch(tokenUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'password',
      client_id: KEYCLOAK_CLIENT_ID,
      username,
      password,
      scope: 'openid profile email roles',
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Keycloak authentication failed for ${username}: ${response.status} - ${errorText}`);
  }

  return response.json();
}

/**
 * Set authentication cookies on the browser context
 */
export async function setAuthCookies(
  context: BrowserContext,
  tokens: TokenResponse
): Promise<void> {
  await context.addCookies([
    {
      name: 'agentvoicebox_access_token',
      value: tokens.access_token,
      domain: 'localhost',
      path: '/',
      httpOnly: false,
      secure: false,
      sameSite: 'Lax',
      expires: Math.floor(Date.now() / 1000) + tokens.expires_in,
    },
    {
      name: 'agentvoicebox_refresh_token',
      value: tokens.refresh_token,
      domain: 'localhost',
      path: '/',
      httpOnly: false,
      secure: false,
      sameSite: 'Lax',
      expires: Math.floor(Date.now() / 1000) + tokens.refresh_expires_in,
    },
  ]);
}

/**
 * Authenticate a page with real Keycloak tokens
 */
export async function authenticateWithKeycloak(
  page: Page,
  userType: TestUserType
): Promise<TokenResponse> {
  const user = TEST_USERS[userType];
  const tokens = await getKeycloakTokens(user.username, user.password);
  await setAuthCookies(page.context(), tokens);
  return tokens;
}

// Convenience functions for specific roles
export async function authenticateAsPlatformAdmin(page: Page): Promise<TokenResponse> {
  return authenticateWithKeycloak(page, 'saasAdmin');
}

export async function authenticateAsTenantAdmin(page: Page): Promise<TokenResponse> {
  return authenticateWithKeycloak(page, 'tenantAdmin');
}

export async function authenticateAsAgentAdmin(page: Page): Promise<TokenResponse> {
  return authenticateWithKeycloak(page, 'agentAdmin');
}

export async function authenticateAsSupervisor(page: Page): Promise<TokenResponse> {
  return authenticateWithKeycloak(page, 'supervisor');
}

export async function authenticateAsOperator(page: Page): Promise<TokenResponse> {
  return authenticateWithKeycloak(page, 'operator');
}

export async function authenticateAsDeveloper(page: Page): Promise<TokenResponse> {
  return authenticateWithKeycloak(page, 'developer');
}

export async function authenticateAsDemo(page: Page): Promise<TokenResponse> {
  return authenticateWithKeycloak(page, 'demo');
}

export async function authenticateAsBilling(page: Page): Promise<TokenResponse> {
  return authenticateWithKeycloak(page, 'billing');
}

// Alias for backward compatibility
export async function authenticateAsViewer(page: Page): Promise<TokenResponse> {
  // Use operator as viewer (lowest role with access)
  return authenticateWithKeycloak(page, 'operator');
}

/**
 * Check if Keycloak is available
 */
export async function isKeycloakReady(): Promise<boolean> {
  try {
    const response = await fetch(`${KEYCLOAK_URL}/health/ready`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Wait for Keycloak to be ready
 */
export async function waitForKeycloak(maxAttempts = 30, delayMs = 2000): Promise<void> {
  for (let i = 0; i < maxAttempts; i++) {
    if (await isKeycloakReady()) {
      console.log('Keycloak is ready');
      return;
    }
    console.log(`Waiting for Keycloak... (attempt ${i + 1}/${maxAttempts})`);
    await new Promise(resolve => setTimeout(resolve, delayMs));
  }
  throw new Error('Keycloak did not become ready in time');
}

// Setup tests to create authenticated state files for reuse
setup.describe('Auth Setup - Real Keycloak', () => {
  setup.beforeAll(async () => {
    // Verify Keycloak is available before running auth setup
    const ready = await isKeycloakReady();
    if (!ready) {
      console.warn('Keycloak not ready - auth setup tests may fail');
    }
  });

  setup('create platform admin auth state', async ({ page }) => {
    setup.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    await authenticateAsPlatformAdmin(page);
    await page.goto('/admin/dashboard');
    await page.context().storageState({ path: 'e2e/.auth/platform-admin.json' });
  });

  setup('create tenant admin auth state', async ({ page }) => {
    setup.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    await authenticateAsTenantAdmin(page);
    await page.goto('/dashboard');
    await page.context().storageState({ path: 'e2e/.auth/tenant-admin.json' });
  });

  setup('create demo user auth state', async ({ page }) => {
    setup.skip(!(await isKeycloakReady()), 'Keycloak not available');
    
    await authenticateAsDemo(page);
    await page.goto('/dashboard');
    await page.context().storageState({ path: 'e2e/.auth/demo-user.json' });
  });
});
