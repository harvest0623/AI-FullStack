// Day13 - middleware.ts  路由保护中间件示例
// 落位：项目根目录 middleware.ts（与 app/ 同级）

import { NextResponse, type NextRequest } from 'next/server';

// 需要登录才能访问的前缀
const protectedPrefixes = ['/dashboard', '/chat'];

// 需要管理员角色的前缀
const adminPrefixes = ['/admin'];

export function middleware(req: NextRequest) {
  const token = req.cookies.get('session')?.value;
  const role = req.cookies.get('role')?.value;
  const path = req.nextUrl.pathname;

  const needsAuth = protectedPrefixes.some((p) => path.startsWith(p));
  const needsAdmin = adminPrefixes.some((p) => path.startsWith(p));

  // 1. 受保护但未登录 → 重定向登录页（带上原目标以便登录后回跳）
  if (needsAuth && !token) {
    const login = new URL('/login', req.url);
    login.searchParams.set('callback', path);
    return NextResponse.redirect(login);
  }

  // 2. 仅管理员且角色不符 → 403
  if (needsAdmin && role !== 'admin') {
    return NextResponse.redirect(new URL('/403', req.url));
  }

  // 3. 剩余请求正常放行
  return NextResponse.next();
}

// 排除静态资源、图片、favicon，其余都过中间件
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};