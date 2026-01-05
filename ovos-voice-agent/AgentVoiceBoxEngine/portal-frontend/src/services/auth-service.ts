/**
 * Authentication Service
 * 
 * USES EXISTING INFRASTRUCTURE:
 * - jwt-utils.ts for token parsing and validation
 * - api-client.ts for HTTP requests (when needed)
 * 
 * Handles Keycloak OAuth2/OIDC:
 * - Login (redirect to Keycloak)
 * - Token exchange and storage
 * - Token refresh
 * - Logout
 */

import { decodeJWT, isJWTExpired, getJWTTimeToExpiry, extractUserFromJWT, JWTClaims } from './jwt-utils';
import { apiClient } from './api-client';

// Get environment variables from Vite (same pattern as admin-api.ts)
const getEnv = (name: string, defaultValue: string): string => {
  const envVar = (import.meta as any).env?.[name];
  return envVar || defaultValue;
};

interface KeycloakConfig {
  url: string;
  realm: string;
  clientId: string;
}

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  idToken?: string;
  expiresAt: number;
}

// Storage keys
const STORAGE_KEYS = {
  TOKENS: 'auth_tokens',
  STATE: 'auth_state',
  REDIRECT_URI: 'auth_redirect_uri'
} as const;

class AuthService {
  private config: KeycloakConfig = {
    url: getEnv('VITE_KEYCLOAK_URL', 'http://localhost:65006'),
    realm: getEnv('VITE_KEYCLOAK_REALM', 'agentvoicebox'),
    clientId: getEnv('VITE_KEYCLOAK_CLIENT_ID', 'portal-frontend')
  };

  private tokens: AuthTokens | null = null;
  private refreshTimer: number | null = null;

  /**
   * Get Keycloak configuration (for use by other components like view-login)
   */
  getKeycloakConfig(): KeycloakConfig {
    return this.config;
  }

  /**
   * Initialize authentication - check for existing session or handle callback
   */
  async init(): Promise<boolean> {
    // Check if we have tokens in localStorage
    const stored = localStorage.getItem(STORAGE_KEYS.TOKENS);
    if (stored) {
      try {
        this.tokens = JSON.parse(stored);

        // Use existing jwt-utils to check token validity
        if (this.tokens && !isJWTExpired(this.tokens.accessToken)) {
          // Set token on API client
          apiClient.setAuthToken(this.tokens.accessToken);
          this.scheduleTokenRefresh();
          return true;
        }

        // Token expired, try to refresh
        return await this.refreshToken();
      } catch (e) {
        console.error('Failed to parse stored tokens:', e);
        this.clearTokens();
      }
    }

    // Check if we're returning from Keycloak with auth code
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
      return await this.handleCallback(code);
    }

    return false;
  }

  /**
   * Redirect to Keycloak login page
   */
  login(redirectUri?: string): void {
    const callbackUri = `${window.location.origin}/auth/callback`;
    const state = this.generateState();

    // Store state for CSRF protection
    localStorage.setItem(STORAGE_KEYS.STATE, state);

    // Store intended destination
    if (redirectUri) {
      localStorage.setItem(STORAGE_KEYS.REDIRECT_URI, redirectUri);
    }

    const params = new URLSearchParams({
      client_id: this.config.clientId,
      redirect_uri: callbackUri,
      response_type: 'code',
      scope: 'openid profile email',
      state: state
    });

    const loginUrl = `${this.config.url}/realms/${this.config.realm}/protocol/openid-connect/auth?${params}`;
    window.location.href = loginUrl;
  }

  /**
   * Handle callback from Keycloak - exchange code for tokens
   */
  private async handleCallback(code: string): Promise<boolean> {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const state = urlParams.get('state');
      const storedState = localStorage.getItem(STORAGE_KEYS.STATE);

      // CSRF protection
      if (state !== storedState) {
        console.error('State mismatch - potential CSRF attack');
        return false;
      }

      const redirectUri = `${window.location.origin}/auth/callback`;

      // Exchange code for tokens
      const response = await fetch(
        `${this.config.url}/realms/${this.config.realm}/protocol/openid-connect/token`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: new URLSearchParams({
            grant_type: 'authorization_code',
            code: code,
            client_id: this.config.clientId,
            redirect_uri: redirectUri
          })
        }
      );

      if (!response.ok) {
        console.error('Token exchange failed:', response.status);
        return false;
      }

      const data = await response.json();

      // Store tokens
      this.tokens = {
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        idToken: data.id_token,
        expiresAt: Date.now() + (data.expires_in * 1000)
      };

      localStorage.setItem(STORAGE_KEYS.TOKENS, JSON.stringify(this.tokens));
      localStorage.removeItem(STORAGE_KEYS.STATE);

      // Set token on API client for all subsequent requests
      apiClient.setAuthToken(this.tokens.accessToken);

      // Schedule token refresh
      this.scheduleTokenRefresh();

      // Clean URL and redirect
      const intendedUri = localStorage.getItem(STORAGE_KEYS.REDIRECT_URI) || '/admin/setup';
      localStorage.removeItem(STORAGE_KEYS.REDIRECT_URI);

      window.history.replaceState({}, document.title, intendedUri);
      window.location.href = intendedUri;

      return true;
    } catch (error) {
      console.error('Authentication callback error:', error);
      return false;
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(): Promise<boolean> {
    if (!this.tokens?.refreshToken) {
      return false;
    }

    try {
      const response = await fetch(
        `${this.config.url}/realms/${this.config.realm}/protocol/openid-connect/token`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: new URLSearchParams({
            grant_type: 'refresh_token',
            refresh_token: this.tokens.refreshToken,
            client_id: this.config.clientId
          })
        }
      );

      if (!response.ok) {
        console.error('Token refresh failed:', response.status);
        this.logout(false); // Don't redirect to Keycloak, just clear local state
        return false;
      }

      const data = await response.json();

      this.tokens = {
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        idToken: data.id_token,
        expiresAt: Date.now() + (data.expires_in * 1000)
      };

      localStorage.setItem(STORAGE_KEYS.TOKENS, JSON.stringify(this.tokens));

      // Update API client with new token
      apiClient.setAuthToken(this.tokens.accessToken);

      // Reschedule refresh
      this.scheduleTokenRefresh();

      return true;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.logout(false);
      return false;
    }
  }

  /**
   * Schedule automatic token refresh before expiry
   */
  private scheduleTokenRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (!this.tokens) return;

    // Use jwt-utils to get time to expiry
    const timeToExpiry = getJWTTimeToExpiry(this.tokens.accessToken);

    // Refresh 60 seconds before expiry
    const refreshIn = Math.max(0, timeToExpiry - 60000);

    if (refreshIn > 0) {
      this.refreshTimer = window.setTimeout(() => {
        this.refreshToken();
      }, refreshIn);
    }
  }

  /**
   * Logout user
   */
  logout(redirectToKeycloak: boolean = true): void {
    // Clear refresh timer
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }

    // Clear API client token
    apiClient.clearAuthToken();

    // Store ID token for logout
    const idToken = this.tokens?.idToken;

    // Clear local storage
    this.clearTokens();

    if (redirectToKeycloak && idToken) {
      // Redirect to Keycloak logout
      const redirectUri = `${window.location.origin}/`;
      const logoutUrl = `${this.config.url}/realms/${this.config.realm}/protocol/openid-connect/logout?id_token_hint=${idToken}&post_logout_redirect_uri=${encodeURIComponent(redirectUri)}`;
      window.location.href = logoutUrl;
    } else {
      // Just redirect to login
      window.location.href = '/';
    }
  }

  /**
   * Clear tokens from memory and storage
   */
  private clearTokens(): void {
    this.tokens = null;
    localStorage.removeItem(STORAGE_KEYS.TOKENS);
    localStorage.removeItem(STORAGE_KEYS.STATE);
    localStorage.removeItem(STORAGE_KEYS.REDIRECT_URI);
  }

  /**
   * Get current access token (auto-refresh if needed)
   */
  async getAccessToken(): Promise<string | null> {
    if (!this.tokens) {
      return null;
    }

    // Use jwt-utils to check expiry
    if (isJWTExpired(this.tokens.accessToken, 60)) {
      const refreshed = await this.refreshToken();
      if (!refreshed) {
        return null;
      }
    }

    return this.tokens.accessToken;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (!this.tokens) {
      return false;
    }

    return !isJWTExpired(this.tokens.accessToken);
  }

  /**
   * Get current user info from JWT claims (using jwt-utils)
   */
  getCurrentUser() {
    if (!this.tokens) {
      return null;
    }

    return extractUserFromJWT(this.tokens.accessToken);
  }

  /**
   * Get raw JWT claims (using jwt-utils)
   */
  getTokenClaims(): JWTClaims | null {
    if (!this.tokens) {
      return null;
    }

    return decodeJWT(this.tokens.accessToken);
  }

  /**
   * Generate random state for CSRF protection
   */
  private generateState(): string {
    return Array.from(crypto.getRandomValues(new Uint8Array(16)))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }
}

// Export singleton instance
export const authService = new AuthService();
