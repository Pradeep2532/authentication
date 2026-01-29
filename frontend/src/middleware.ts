import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 🔒 Protected routes
  const isProtected =
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/admin");

  if (!isProtected) {
    return NextResponse.next();
  }

  // 🍪 Check refresh token cookie
  const refreshToken = request.cookies.get("refresh_token");

  if (!refreshToken) {
    // ❌ Not authenticated → redirect to login
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  // ✅ Authenticated (cookie exists)
  return NextResponse.next();
}
