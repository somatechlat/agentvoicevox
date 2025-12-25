/**
 * Google OAuth Callback API Route
 * Exchanges Google authorization code for tokens
 */

import { NextRequest, NextResponse } from "next/server";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET || "";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { code, redirect_uri } = body;

    if (!code) {
      return NextResponse.json(
        { error: "Missing authorization code" },
        { status: 400 }
      );
    }

    if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET) {
      return NextResponse.json(
        { error: "Google OAuth not configured" },
        { status: 500 }
      );
    }

    // Exchange code for tokens with Google
    const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        code,
        client_id: GOOGLE_CLIENT_ID,
        client_secret: GOOGLE_CLIENT_SECRET,
        redirect_uri,
        grant_type: "authorization_code",
      }),
    });

    if (!tokenResponse.ok) {
      const errorText = await tokenResponse.text();
      console.error("Google token exchange failed:", errorText);
      return NextResponse.json(
        { error: "Failed to exchange code for tokens" },
        { status: 400 }
      );
    }

    const tokens = await tokenResponse.json();

    // Get user info from Google
    const userInfoResponse = await fetch(
      "https://www.googleapis.com/oauth2/v2/userinfo",
      {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      }
    );

    if (!userInfoResponse.ok) {
      console.error("Failed to get user info from Google");
    }

    const userInfo = userInfoResponse.ok ? await userInfoResponse.json() : null;

    // Return tokens in a format compatible with our auth system
    return NextResponse.json({
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token || "",
      expires_in: tokens.expires_in || 3600,
      refresh_expires_in: 86400, // 24 hours
      token_type: "Bearer",
      id_token: tokens.id_token,
      user_info: userInfo,
      provider: "google",
    });
  } catch (error) {
    console.error("Google OAuth callback error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
