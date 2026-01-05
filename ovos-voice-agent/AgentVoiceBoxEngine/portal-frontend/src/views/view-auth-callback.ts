import { LitElement, html } from 'lit';
import { customElement } from 'lit/decorators.js';

/**
 * Auth Callback Handler
 * 
 * This page handles the OAuth callback from Keycloak.
 * After Keycloak authentication, user is redirected here with auth code.
 * The auth-service exchanges code for tokens and redirects to dashboard.
 */

@customElement('view-auth-callback')
export class ViewAuthCallback extends LitElement {
    createRenderRoot() { return this; }

    async connectedCallback() {
        super.connectedCallback();

        // auth-service.init() will handle the callback automatically
        // Just show loading state while it processes
    }

    render() {
        return html`
      <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-white">
        <div class="text-center">
          <div class="mb-4 flex justify-center">
            <svg class="animate-spin h-12 w-12 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">Completing Sign In...</h1>
          <p class="text-sm text-gray-600">Please wait while we authenticate you</p>
        </div>
      </div>
    `;
    }
}
