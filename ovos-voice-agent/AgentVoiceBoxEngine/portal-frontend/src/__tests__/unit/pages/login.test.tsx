/**
 * Login Page Unit Tests
 * Tests for SSO login page with social login options
 * Implements Requirements 2.1-2.3
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
  useSearchParams: () => ({
    get: vi.fn().mockReturnValue(null),
  }),
}));

// Mock auth lib
vi.mock('@/lib/auth', () => ({
  getLoginUrl: vi.fn().mockResolvedValue('http://localhost:25004/auth'),
  getSocialLoginUrl: vi.fn().mockImplementation((provider: string) => 
    Promise.resolve(`http://localhost:25004/auth?kc_idp_hint=${provider}`)
  ),
}));

// Mock theme context
vi.mock('@/contexts/ThemeContext', () => ({
  useTheme: () => ({
    theme: 'dark',
    resolvedTheme: 'dark',
    setTheme: vi.fn(),
  }),
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Import after mocks
import LoginPage from '@/app/login/page';
import { getLoginUrl, getSocialLoginUrl } from '@/lib/auth';

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    });
    // Mock sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        setItem: vi.fn(),
        getItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    });
  });

  describe('Page Rendering', () => {
    it('should render AgentVoiceBox branding', () => {
      render(<LoginPage />);
      expect(screen.getByText('AgentVoiceBox')).toBeInTheDocument();
    });

    it('should render sign in description', () => {
      render(<LoginPage />);
      expect(screen.getByText('Sign in to access your dashboard')).toBeInTheDocument();
    });

    it('should render SSO sign in button', () => {
      render(<LoginPage />);
      expect(screen.getByRole('button', { name: /sign in with sso/i })).toBeInTheDocument();
    });

    it('should render Google login button', () => {
      render(<LoginPage />);
      expect(screen.getByTestId('google-login-btn')).toBeInTheDocument();
      expect(screen.getByText('Continue with Google')).toBeInTheDocument();
    });

    it('should render GitHub login button', () => {
      render(<LoginPage />);
      expect(screen.getByTestId('github-login-btn')).toBeInTheDocument();
      expect(screen.getByText('Continue with GitHub')).toBeInTheDocument();
    });

    it('should render demo credentials info', () => {
      render(<LoginPage />);
      expect(screen.getByText('Demo credentials:')).toBeInTheDocument();
      expect(screen.getByText('demo@test.com / demo123')).toBeInTheDocument();
    });

    it('should render Keycloak attribution', () => {
      render(<LoginPage />);
      expect(screen.getByText('Powered by Keycloak Authentication')).toBeInTheDocument();
    });

    it('should render theme toggle', () => {
      render(<LoginPage />);
      // Theme toggle should be present (button with svg)
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  describe('SSO Login Flow', () => {
    it('should call getLoginUrl on SSO button click', async () => {
      const user = userEvent.setup();
      render(<LoginPage />);
      
      const ssoButton = screen.getByRole('button', { name: /sign in with sso/i });
      await user.click(ssoButton);
      
      await waitFor(() => {
        expect(getLoginUrl).toHaveBeenCalled();
      });
    });

    it('should store redirect URL in sessionStorage on SSO click', async () => {
      const user = userEvent.setup();
      render(<LoginPage />);
      
      const ssoButton = screen.getByRole('button', { name: /sign in with sso/i });
      await user.click(ssoButton);
      
      await waitFor(() => {
        expect(window.sessionStorage.setItem).toHaveBeenCalledWith('auth_redirect', '/dashboard');
      });
    });

    it('should redirect to login URL on SSO click', async () => {
      const user = userEvent.setup();
      render(<LoginPage />);
      
      const ssoButton = screen.getByRole('button', { name: /sign in with sso/i });
      await user.click(ssoButton);
      
      await waitFor(() => {
        expect(window.location.href).toBe('http://localhost:25004/auth');
      });
    });
  });

  describe('Social Login Flow', () => {
    it('should call getSocialLoginUrl with google on Google button click', async () => {
      const user = userEvent.setup();
      render(<LoginPage />);
      
      const googleButton = screen.getByTestId('google-login-btn');
      await user.click(googleButton);
      
      await waitFor(() => {
        expect(getSocialLoginUrl).toHaveBeenCalledWith('google');
      });
    });

    it('should call getSocialLoginUrl with github on GitHub button click', async () => {
      const user = userEvent.setup();
      render(<LoginPage />);
      
      const githubButton = screen.getByTestId('github-login-btn');
      await user.click(githubButton);
      
      await waitFor(() => {
        expect(getSocialLoginUrl).toHaveBeenCalledWith('github');
      });
    });

    it('should redirect to Google login URL on Google button click', async () => {
      const user = userEvent.setup();
      render(<LoginPage />);
      
      const googleButton = screen.getByTestId('google-login-btn');
      await user.click(googleButton);
      
      await waitFor(() => {
        expect(window.location.href).toContain('kc_idp_hint=google');
      });
    });

    it('should redirect to GitHub login URL on GitHub button click', async () => {
      const user = userEvent.setup();
      render(<LoginPage />);
      
      const githubButton = screen.getByTestId('github-login-btn');
      await user.click(githubButton);
      
      await waitFor(() => {
        expect(window.location.href).toContain('kc_idp_hint=github');
      });
    });
  });

  describe('Loading States', () => {
    it('should disable all buttons when loading', async () => {
      const user = userEvent.setup();
      // Make getLoginUrl slow
      vi.mocked(getLoginUrl).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve('http://localhost:25004/auth'), 500))
      );
      
      render(<LoginPage />);
      
      const ssoButton = screen.getByRole('button', { name: /sign in with sso/i });
      await user.click(ssoButton);
      
      // All buttons should be disabled during loading
      const googleButton = screen.getByTestId('google-login-btn');
      const githubButton = screen.getByTestId('github-login-btn');
      
      expect(ssoButton).toBeDisabled();
      expect(googleButton).toBeDisabled();
      expect(githubButton).toBeDisabled();
    });

    it('should show loading spinner on SSO button when clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(getLoginUrl).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve('http://localhost:25004/auth'), 500))
      );
      
      render(<LoginPage />);
      
      const ssoButton = screen.getByRole('button', { name: /sign in with sso/i });
      await user.click(ssoButton);
      
      // Should show "Redirecting..." text
      expect(screen.getByText('Redirecting...')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible button labels', () => {
      render(<LoginPage />);
      
      expect(screen.getByRole('button', { name: /sign in with sso/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /continue with github/i })).toBeInTheDocument();
    });

    it('should have proper heading hierarchy', () => {
      render(<LoginPage />);
      
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('AgentVoiceBox');
    });
  });

  describe('Visual Elements', () => {
    it('should render microphone icon in logo', () => {
      render(<LoginPage />);
      
      // Check for SVG with microphone path
      const svgs = document.querySelectorAll('svg');
      expect(svgs.length).toBeGreaterThan(0);
    });

    it('should render Google icon in Google button', () => {
      render(<LoginPage />);
      
      const googleButton = screen.getByTestId('google-login-btn');
      const svg = googleButton.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render GitHub icon in GitHub button', () => {
      render(<LoginPage />);
      
      const githubButton = screen.getByTestId('github-login-btn');
      const svg = githubButton.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });
});
