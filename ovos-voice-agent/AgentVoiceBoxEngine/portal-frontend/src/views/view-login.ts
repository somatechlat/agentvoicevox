import { LitElement, html } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-layout';
import { authService } from '../services/auth-service';

/**
 * REAL LOGIN PAGE
 * 
 * Authentication via Keycloak OAuth2/OIDC:
 * - SSO Login (redirects to Keycloak)
 * - Register (redirects to Keycloak registration)
 * - Forgot Password (redirects to Keycloak password reset)
 * - Social Login (Google, GitHub via Keycloak)
 * 
 * NO MOCKING - All flows use real Keycloak server at localhost:65024
 */

type LoginView = 'login' | 'register' | 'forgot-password' | 'reset-password';

@customElement('view-login')
export class ViewLogin extends LitElement {
  @state() private view: LoginView = 'login';
  @state() private loading = false;
  @state() private error: string | null = null;

  createRenderRoot() { return this; }

  async connectedCallback() {
    super.connectedCallback();

    // Check if already authenticated
    const isAuth = await authService.init();
    if (isAuth) {
      // Already logged in, redirect to dashboard
      window.location.href = '/admin/setup';
    }
  }

  private handleSSOLogin() {
    this.loading = true;
    this.requestUpdate();
    // Redirect to Keycloak login
    authService.login();
  }

  private handleRegister() {
    this.loading = true;
    this.requestUpdate();
    // Redirect to Keycloak registration page (SHARED on 65006)
    const redirectUri = `${window.location.origin}/auth/callback`;
    const keycloakRegisterUrl = `http://localhost:65006/realms/agentvoicebox/protocol/openid-connect/registrations?client_id=portal-frontend&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=openid%20profile%20email`;
    window.location.href = keycloakRegisterUrl;
  }

  private handleForgotPassword() {
    this.loading = true;
    this.requestUpdate();
    // Redirect to Keycloak password reset (SHARED on 65006)
    const redirectUri = `${window.location.origin}/`;
    const keycloakResetUrl = `http://localhost:65006/realms/agentvoicebox/login-actions/reset-credentials?client_id=portal-frontend&redirect_uri=${encodeURIComponent(redirectUri)}`;
    window.location.href = keycloakResetUrl;
  }

  private handleSocialLogin(provider: 'google' | 'github') {
    this.loading = true;
    this.requestUpdate();
    const redirectUri = `${window.location.origin}/auth/callback`;
    const socialLoginUrl = `http://localhost:65006/realms/agentvoicebox/protocol/openid-connect/auth?client_id=portal-frontend&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=openid%20profile%20email&kc_idp_hint=${provider}`;
    window.location.href = socialLoginUrl;
  }

  render() {
    return html`
      <saas-layout>
        <!-- Header -->
        <header class="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-6 bg-white/80 backdrop-blur-sm">
          <div class="flex items-center gap-3">
            <div class="h-8 w-8 rounded-lg bg-gradient-to-br from-black to-gray-800 flex items-center justify-center shadow-sm">
              <div class="h-3 w-3 bg-white rounded-full"></div>
            </div>
            <span class="font-bold text-lg tracking-tight text-gray-900">AgentVoiceBox</span>
          </div>
          ${this.view !== 'login' ? html`
            <button 
              @click="${() => { this.view = 'login'; this.error = null; }}"
              class="text-sm text-gray-600 hover:text-gray-900 font-medium"
            >
              ← Back to Login
            </button>
          ` : ''}
        </header>

        <!-- Main Card -->
        <main class="flex min-h-screen flex-1 flex-col items-center justify-center px-4 bg-gradient-to-br from-gray-50 to-white">
          <div class="relative w-full max-w-[420px]">
            
            ${this.error ? html`
              <div class="mb-4 p-4 rounded-xl bg-red-50 border border-red-200">
                <p class="text-sm text-red-700">${this.error}</p>
              </div>
            ` : ''}

            <div class="overflow-hidden rounded-2xl bg-white p-10 shadow-2xl border border-gray-100">
              
              ${this.view === 'login' ? this.renderLoginView() : ''}
              ${this.view === 'register' ? this.renderRegisterView() : ''}
              ${this.view === 'forgot-password' ? this.renderForgotPasswordView() : ''}

              <!-- Footer -->
              <div class="mt-8 pt-6 border-t border-gray-100 text-center text-xs text-gray-400">
                <p>🔒 Secure Enterprise Gateway v2.0</p>
                <p class="mt-1">Powered by Keycloak OAuth2/OIDC</p>
              </div>
              
            </div>

            ${this.view === 'login' ? html`
              <div class="mt-6 text-center">
                <p class="text-sm text-gray-600">
                  Don't have an account? 
                  <button 
                    @click="${() => { this.view = 'register'; this.error = null; }}"
                    class="font-semibold text-black hover:underline"
                  >
                    Sign up
                  </button>
                </p>
              </div>
            ` : ''}
          </div>
        </main>
      </saas-layout>
    `;
  }

  private renderLoginView() {
    return html`
      <div class="mb-8 text-center">
        <h1 class="text-2xl font-bold tracking-tight text-gray-900 mb-2">Welcome Back</h1>
        <p class="text-sm text-gray-500">Sign in to access your platform</p>
      </div>

      <div class="space-y-4">
        <!-- SSO Login -->
        <button
          @click="${this.handleSSOLogin}"
          ?disabled="${this.loading}"
          class="relative flex w-full items-center justify-center gap-3 rounded-xl bg-black px-4 py-4 text-sm font-semibold text-white transition-all hover:bg-gray-900 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed shadow-lg shadow-black/20"
        >
          ${this.loading ? html`
            <span class="flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Redirecting to Keycloak...
            </span>
          ` : html`
            <svg xmlns="http://www.w3.org/2000/svg" height="18" viewBox="0 -960 960 960" width="18" fill="currentColor">
              <path d="M234-276q51-39 114-61.5T480-360q69 0 132 22.5T726-276q35-41 54.5-93T800-480q0-133-93.5-226.5T480-800q-133 0-226.5 93.5T160-480q0 59 19.5 111t54.5 93Zm246-164q-59 0-99.5-40.5T340-580q0-59 40.5-99.5T480-720q59 0 99.5 40.5T620-580q0 59-40.5 99.5T480-440Zm0 360q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Z"/>
            </svg>
            Sign in with SSO
          `}
        </button>

        <div class="relative py-2">
          <div class="absolute inset-0 flex items-center"><span class="w-full border-t border-gray-200"></span></div>
          <div class="relative flex justify-center text-xs uppercase"><span class="bg-white px-3 text-gray-400 font-medium">Or continue with</span></div>
        </div>

        <!-- Social Login -->
        <div class="grid grid-cols-2 gap-3">
          <button 
            @click="${() => this.handleSocialLogin('google')}"
            ?disabled="${this.loading}"
            class="flex h-12 items-center justify-center gap-2 rounded-xl border-2 border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50"
          >
            <svg class="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span class="text-sm font-medium text-gray-700">Google</span>
          </button>
          
          <button 
            @click="${() => this.handleSocialLogin('github')}"
            ?disabled="${this.loading}"
            class="flex h-12 items-center justify-center gap-2 rounded-xl border-2 border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50"
          >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span class="text-sm font-medium text-gray-700">GitHub</span>
          </button>
        </div>

        <!-- Forgot Password -->
        <div class="text-center pt-2">
          <button 
            @click="${() => { this.view = 'forgot-password'; this.error = null; }}"
            class="text-sm text-gray-600 hover:text-black font-medium"
          >
            Forgot password?
          </button>
        </div>
      </div>
    `;
  }

  private renderRegisterView() {
    return html`
      <div class="mb-8 text-center">
        <h1 class="text-2xl font-bold tracking-tight text-gray-900 mb-2">Create Account</h1>
        <p class="text-sm text-gray-500">Get started with AgentVoiceBox</p>
      </div>

      <div class="space-y-4">
        <button
          @click="${this.handleRegister}"
          ?disabled="${this.loading}"
          class="relative flex w-full items-center justify-center gap-3 rounded-xl bg-black px-4 py-4 text-sm font-semibold text-white transition-all hover:bg-gray-900 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed shadow-lg shadow-black/20"
        >
          ${this.loading ? html`
            <span class="flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Redirecting...
            </span>
          ` : html`
            <svg xmlns="http://www.w3.org/2000/svg" height="18" viewBox="0 -960 960 960" width="18" fill="currentColor">
              <path d="M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z"/>
            </svg>
            Create Account with SSO
          `}
        </button>

        <div class="relative py-2">
          <div class="absolute inset-0 flex items-center"><span class="w-full border-t border-gray-200"></span></div>
          <div class="relative flex justify-center text-xs uppercase"><span class="bg-white px-3 text-gray-400 font-medium">Or sign up with</span></div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <button 
            @click="${() => this.handleSocialLogin('google')}"
            ?disabled="${this.loading}"
            class="flex h-12 items-center justify-center gap-2 rounded-xl border-2 border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50"
          >
            <svg class="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span class="text-sm font-medium text-gray-700">Google</span>
          </button>
          
          <button 
            @click="${() => this.handleSocialLogin('github')}"
            ?disabled="${this.loading}"
            class="flex h-12 items-center justify-center gap-2 rounded-xl border-2 border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50"
          >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span class="text-sm font-medium text-gray-700">GitHub</span>
          </button>
        </div>
      </div>
    `;
  }

  private renderForgotPasswordView() {
    return html`
      <div class="mb-8 text-center">
        <h1 class="text-2xl font-bold tracking-tight text-gray-900 mb-2">Reset Password</h1>
        <p class="text-sm text-gray-500">We'll send you instructions to reset your password</p>
      </div>

      <div class="space-y-4">
        <button
          @click="${this.handleForgotPassword}"
          ?disabled="${this.loading}"
          class="relative flex w-full items-center justify-center gap-3 rounded-xl bg-black px-4 py-4 text-sm font-semibold text-white transition-all hover:bg-gray-900 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed shadow-lg shadow-black/20"
        >
          ${this.loading ? html`
            <span class="flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Redirecting...
            </span>
          ` : html`
            <svg xmlns="http://www.w3.org/2000/svg" height="18" viewBox="0 -960 960 960" width="18" fill="currentColor">
              <path d="M160-160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h640q33 0 56.5 23.5T880-720v480q0 33-23.5 56.5T800-160H160Zm320-280L160-640v400h640v-400L480-440Zm0-80 320-200H160l320 200ZM160-640v-80 480-400Z"/>
            </svg>
            Send Reset Instructions
          `}
        </button>

        <p class="text-xs text-center text-gray-500 pt-2">
          This will redirect you to Keycloak's secure password reset page
        </p>
      </div>
    `;
  }
}
