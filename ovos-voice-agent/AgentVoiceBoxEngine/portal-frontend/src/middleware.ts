/**
 * Next.js Middleware for Route Protection
 * Implements Requirements D1.2, D2.1: Role-based routing and navigation
 * Property 7: Role-Based Dashboard Routing
 * Property 8: Permission-Based Navigation
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Public routes that don't require authentication
const PUBLIC_ROUTES = [
  '/login',
  '/signup',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/auth/callback',
  '/api/auth/login',
  '/api/auth/register',
  '/api/auth/refresh',
  '/api/auth/mfa/verify',
];

// Admin-only routes (SaaS Admin Portal)
const ADMIN_ROUTES = ['/admin'];

// Customer routes (Tenant Portal)
const CUSTOMER_ROUTES = [
  '/dashboard',
  '/api-keys',
  '/billing',
  '/team',
  '/settings',
  '/sessions',
  '/projects',
  '/usage',
];

// User portal routes
const USER_ROUTES = ['/app'];

// Role definitions
const PLATFORM_ADMIN_ROLES = ['super_admin', 'tenant_admin', 'support_agent', 'billing_admin'];
const TENANT_ADMIN_ROLES = ['owner', 'admin'];
const USER_ROLES = ['developer', 'billing', 'viewer', 'user'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes
  if (PUBLIC_ROUTES.some(route => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Allow static files and Next.js internals
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/static') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // Check for auth token
  const token = request.cookies.get('agentvoicebox_access_token')?.value;
  
  if (!token) {
    // Redirect to login if no token
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Decode token to check roles
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const roles: string[] = payload.roles || [];
    
    // Determine user's highest role level
    const isPlatformAdmin = roles.some(r => PLATFORM_ADMIN_ROLES.includes(r));
    const isTenantAdmin = roles.some(r => TENANT_ADMIN_ROLES.includes(r));
    const isUser = roles.some(r => USER_ROLES.includes(r));

    // Property 7: Role-Based Dashboard Routing
    // Redirect root path to appropriate dashboard
    if (pathname === '/') {
      if (isPlatformAdmin) {
        return NextResponse.redirect(new URL('/admin/dashboard', request.url));
      } else if (isTenantAdmin) {
        return NextResponse.redirect(new URL('/dashboard', request.url));
      } else if (isUser) {
        return NextResponse.redirect(new URL('/app', request.url));
      } else {
        // Default to customer dashboard
        return NextResponse.redirect(new URL('/dashboard', request.url));
      }
    }

    // Check admin route access
    if (ADMIN_ROUTES.some(route => pathname.startsWith(route))) {
      if (!isPlatformAdmin) {
        // Redirect non-admins to their appropriate dashboard
        if (isTenantAdmin) {
          return NextResponse.redirect(new URL('/dashboard', request.url));
        } else {
          return NextResponse.redirect(new URL('/app', request.url));
        }
      }
    }

    // Check customer route access
    if (CUSTOMER_ROUTES.some(route => pathname.startsWith(route))) {
      // Platform admins and tenant admins can access customer routes
      const hasAccess = isPlatformAdmin || isTenantAdmin || isUser;
      
      if (!hasAccess) {
        return new NextResponse('Forbidden', { status: 403 });
      }
    }

    // Check user portal route access
    if (USER_ROUTES.some(route => pathname.startsWith(route))) {
      // All authenticated users can access user portal
      const hasAccess = isPlatformAdmin || isTenantAdmin || isUser;
      
      if (!hasAccess) {
        return new NextResponse('Forbidden', { status: 403 });
      }
    }

    return NextResponse.next();
  } catch {
    // Invalid token - redirect to login
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
