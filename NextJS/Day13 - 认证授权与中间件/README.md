# Day13 - 认证授权与中间件

> 本章节为 AI 应用构建安全访问控制。掌握 `middleware.ts` 的统一鉴权入口、NextAuth（Auth.js）的集成方式、Session/Cookie 管理，以及基于角色的权限控制（RBAC），让关键路由与数据得到保护。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 认证 vs 授权](#21-认证-vs-授权)
  - [2.2 Session 与 Cookie 机制](#22-session-与-cookie-机制)
  - [2.3 middleware.ts 统一入口](#23-middlewarets-统一入口)
  - [2.4 NextAuth 集成](#24-nextauth-集成)
  - [2.5 路由保护](#25-路由保护)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 RBAC 角色权限](#31-rbac-角色权限)
  - [3.2 服务端读取会话](#32-服务端读取会话)
  - [3.3 中间件与边缘运行](#33-中间件与边缘运行)
  - [3.4 安全最佳实践](#34-安全最佳实践)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **区分认证与授权**：明白「是谁」与「能不能」的区别。
2. **理解会话机制**：用 Cookie/Session 维持登录状态。
3. **配置 middleware.ts**：在统一入口做全局鉴权与路由保护。
4. **集成 NextAuth**：实现登录、登出与会话读取。
5. **实现 RBAC**：基于角色控制页面与接口权限。

---

## 二、理论知识

### 2.1 认证 vs 授权

- **认证（Authentication）**：确认「你是谁」（登录验证身份）。
- **授权（Authorization）**：确认「你能做什么」（角色/权限判定）。

```
未登录用户 ──认证──▶ 已登录用户 ──授权──▶ 有权限执行操作
```

常见流程：用户登录 → 服务端核验 → 返回凭证（Cookie/Session）→ 后续请求携带凭证 → 服务端校验 → 判定权限。

### 2.2 Session 与 Cookie 机制

**Cookie** 是浏览器保存的小段数据，每次请求自动携带。**Session** 是服务端保存的登录状态，通过 Cookie 中的 Session ID 关联。

```
浏览器                        服务端
  │  登录(账号密码)              │
  │───────────────────────────▶│ 核验账号 → 生成 Session
  │  返回 Session Cookie        │
  │◀───────────────────────────│
  │  携带 Cookie 请求受保护页   │
  │───────────────────────────▶│ 查 Session → 判定是否登录
```

在 Next.js 中，可直接用 `cookies()` 读取 HttpOnly Cookie（安全，JS 无法读取）：

```tsx
import { cookies } from 'next/headers';

export async function getSession() {
  const cookieStore = await cookies();
  const token = cookieStore.get('session')?.value;
  // 解析/校验 token 得到用户信息
  return token ? { user: parseToken(token) } : null;
}
```

### 2.3 middleware.ts 统一入口

`middleware.ts` 放在**项目根**（`app/` 同级），在每个匹配请求上运行，是**全局鉴权与路由保护**的入口：

```tsx
// middleware.ts （项目根）
import { NextResponse, NextRequest } from 'next/server';

const protectedRoutes = ['/dashboard', '/chat', '/api/private'];

export function middleware(req: NextRequest) {
  const hasCookie = req.cookies.has('session');

  // 受保护但未登录 → 重定向到登录页
  if (protectedRoutes.some((p) => req.nextUrl.pathname.startsWith(p)) && !hasCookie) {
    const url = req.nextUrl.clone();
    url.pathname = '/login';
    url.searchParams.set('callback', req.nextUrl.pathname);
    return NextResponse.redirect(url);
  }

  // 已登录访问登录页 → 跳回首页（可选）
  if (req.nextUrl.pathname === '/login' && hasCookie) {
    return NextResponse.redirect(new URL('/', req.url));
  }

  return NextResponse.next();
}

// 指定匹配范围，其余请求不经过中间件（性能优化）
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

中间件逻辑运行在**边缘运行时**，需注意其 API 限制（不能直接用 Node 环境变量进程等方式）。

### 2.4 NextAuth 集成

**NextAuth.js / Auth.js** 是主流的认证解决方案。以 Credentials（账号密码）为例：

```bash
npm install next-auth
# 生成密钥：openssl rand -base64 32
```

配置（NextAuth v4 风格，先建立直观认知）：

```tsx
// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: '账号密码',
      credentials: {
        email: { label: '邮箱', type: 'email' },
        password: { label: '密码', type: 'password' },
      },
      async authorize(credentials) {
        // 调用数据库/接口核验，成功返回 user，失败返回 null
        if (credentials?.email === 'demo@ai.com' && credentials?.password === '123456') {
          return { id: '1', email: credentials.email, role: 'admin' };
        }
        return null;
      },
    }),
  ],
  pages: { signIn: '/login' },
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, user }) {
      if (user) token.role = (user as any).role;
      return token;
    },
    async session({ session, token }) {
      (session as any).user.role = token.role;
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
});

export { handler as GET, handler as POST };
```

Auth 流程由框架处理：登录会写入 Cookie/Session，`useSession()`/`getServerSession()` 可读取当前会话。

> 说明：NextAuth 同时支持 OAuth（GitHub/Google 等），把 provider 换成对应项即可。

### 2.5 路由保护

**页面级保护**（Server Component 用 `getServerSession`）：

```tsx
// app/dashboard/page.tsx
import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';

export default async function Dashboard() {
  const session = await getServerSession(authOptions);
  if (!session) redirect('/login');   // 未登录跳登录

  return <main>欢迎，{session.user?.email}</main>;
}
```

**接口级保护**（Route Handler 中校验）：

```tsx
import { getServerSession } from 'next-auth';

export async function POST() {
  const session = await getServerSession(authOptions);
  if (!session) return Response.json({ error: '未登录' }, { status: 401 });
  // ...执行业务
}
```

---

## 三、核心概念解析

### 3.1 RBAC 角色权限

在会话中加入**角色**，按角色控制可访问的内容：

```tsx
// 角色枚举
type Role = 'admin' | 'user' | 'guest';

// 校验是否具有角色
export function requireRole(role: Role[]) {
  return (req: NextRequest) => {
    const userRole = req.cookies.get('role')?.value as Role;
    if (!userRole || !role.includes(userRole)) {
      return NextResponse.redirect(new URL('/403', req.url));
    }
    return NextResponse.next();
  };
}
```

可配合页面判断生成不同 UI（管理员菜单、普通用户菜单）。

> 规范：前端只是体验层，真正的权限判定必须放在**服务端**（Server Action / middleware / Route Handler），不能只看前端隐藏按钮。

### 3.2 服务端读取会话

- **getServerSession**：在 Server Component / Route Handler / Server Action 中读取，最安全。
- **auth()**（NextAuth v5）：配合环境、在服务端调用。
- **cookies()**：直接读 Cookie（自定义会话方案时）。

不要在前端组件中放敏感会话逻辑；前端可读 `session` 用于 UI 展示，但权限判断以服务端为准。

### 3.3 中间件与边缘运行

`middleware.ts` 运行于**边缘/轻量运行时**，特点：
- 响应快、就近执行、适合全局快速判断。
- **无法直接使用大多数 Node.js API**与完整数据库驱动。
- 适合做「该不该放行 / 重定向」的顶层判断，重逻辑放 Server Component/Action。

### 3.4 安全最佳实践

1. **HttpOnly Cookie**：会话 Cookie 标记 `HttpOnly`，防止 XSS 窃取（JS 读不到）。
2. **密钥只存服务端**：`NEXTAUTH_SECRET`、JWT 密钥放 `.env`，不暴露。
3. **服务端权威判断**：RBAC 判定放服务端，前端仅体验层。
4. **敏感接口鉴权**：所有写操作（含 DELETE、LLM 调用）都要校验会话与角色。
5. **最小权限**：默认拒绝，按需放行。
6. **CSRF 防护**：使用框架自带防护，变更操作走正确方法。

---

## 四、关键知识点总结

- **认证=你是谁，授权=你能做什么**。
- **Cookie/Session**：HttpOnly Cookie 携带会话，服务端 `cookies()` 读取。
- **middleware.ts**：项目根的全局鉴权入口，可重定向/放行/改写请求。
- **config.matcher**：限定中间件作用范围，减少无谓执行。
- **NextAuth**：Speaker 登录/OAuth、jwt 会话、`getServerSession`/`useSession`。
- **路由保护**：Server Component 未登录 `redirect`；接口未登录返回 401。
- **RBAC**：角色存于会话，服务端判定，前端仅体验层。
- **安全**：HttpOnly、密钥服务端、权限服务端判定、最小权限。

---

## 五、实战练习

### 练习一：auth_middleware.js —— 认证与中间件流程演示

**任务描述**：运行脚本，模拟「登录 → 会话 → 中间件拦截 → 放行/重定向」的完整流程，展示 RBAC 角色判定。

**运行方式**

```bash
cd Code
node auth_middleware.js
```

### 练习二：配置 middleware 路由保护

在项目根创建 `middleware.ts`，保护 `/dashboard` 与 `/api/private`（未登录重定向到 `/login`），并为已登录访问 `/login` 时跳回首页。

### 练习三：NextAuth 登录（可选实战）

安装 next-auth，配置 Credentials provider，实现 `auth/[...nextauth]` 路由 + 登录页，用 `useSession` 展示登录态。

---

## 下节预告

下一节 **Day14** 将进入 **环境配置、AI 集成与生产部署**：管理 `.env` 环境变量、在 Route Handler 安全调用大模型（含 SSE 流式对话）、完成构建、Vercel 与 Docker 部署，并做性能优化——收官实战闭环。