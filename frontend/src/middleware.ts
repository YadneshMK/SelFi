import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const isAuthPage = request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/register';
  const token = request.cookies.get('auth-token');
  
  // If user is on auth page and has token, redirect to dashboard
  if (isAuthPage && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
  
  // If user is on protected route and no token, redirect to login
  if (!isAuthPage && !token) {
    const response = NextResponse.redirect(new URL('/login', request.url));
    // Save the attempted URL to redirect back after login
    response.cookies.set('redirect-url', request.nextUrl.pathname, {
      httpOnly: true,
      sameSite: 'lax',
      path: '/'
    });
    return response;
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/login', '/register']
};