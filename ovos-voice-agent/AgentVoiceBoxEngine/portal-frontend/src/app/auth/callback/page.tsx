"use client";

/**
 * OAuth Callback Page
 * Handles callbacks from Keycloak SSO and Google OAuth
 */

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { exchangeCodeForTokens, storeTokens, extractUserFromToken, getStoredTokens } from "@/lib/auth";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("Completing authentication...");

  useEffect(() => {
    async function handleCallback() {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const errorParam = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      if (errorParam) {
        setError(errorDescription || errorParam);
        return;
      }

      if (!code) {
        setError("No authorization code received");
        return;
      }

      try {
        setStatus("Exchanging authorization code...");
        const tokens = await exchangeCodeForTokens(code);
        
        // Determine provider from response or stored state
        const provider = (tokens as { provider?: string }).provider || "keycloak";
        
        setStatus("Storing credentials...");
        storeTokens(tokens, provider);

        // Verify we got a valid user
        const user = extractUserFromToken(tokens.access_token, provider);
        if (!user) {
          setError("Failed to extract user from token");
          return;
        }

        setStatus("Redirecting to dashboard...");

        // Redirect to original destination or appropriate dashboard
        let returnUrl = "/dashboard";
        
        // Check for stored redirect
        const storedRedirect = sessionStorage.getItem("auth_redirect");
        if (storedRedirect) {
          returnUrl = storedRedirect;
          sessionStorage.removeItem("auth_redirect");
        } else if (state) {
          try {
            const stateData = JSON.parse(atob(state));
            if (stateData.returnUrl) {
              returnUrl = stateData.returnUrl;
            }
          } catch {
            // Invalid state, use default
          }
        }

        // Check if user is admin and redirect accordingly
        if (user.roles.includes("super_admin") || user.roles.includes("tenant_admin")) {
          if (!returnUrl.startsWith("/admin")) {
            returnUrl = "/admin/dashboard";
          }
        }

        router.replace(returnUrl);
      } catch (err) {
        console.error("Auth callback error:", err);
        setError(err instanceof Error ? err.message : "Failed to complete authentication");
      }
    }

    handleCallback();
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-destructive/10 flex items-center justify-center">
            <svg className="w-8 h-8 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-foreground mb-2">Authentication Error</h1>
          <p className="text-muted-foreground mb-6">{error}</p>
          <button
            onClick={() => router.push("/login")}
            className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-colors"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="mb-4 h-8 w-8 animate-spin rounded-full border-2 border-foreground border-t-transparent mx-auto" />
        <p className="text-muted-foreground">{status}</p>
      </div>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-2 border-foreground border-t-transparent mx-auto" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  );
}
