/**
 * Day11 - use-declare.ts
 *
 * 演示如何消费本目录下的四个 .d.ts 声明文件：
 * - global-declare.d.ts：全局变量、window 属性、全局函数
 * - module-declare.d.ts：无类型 JS 模块的声明
 * - express-augment.d.ts：Express.Request 扩展
 * - env.d.ts：process.env 与 import.meta.env 类型扩展
 *
 * 运行方式：npx ts-node use-declare.ts
 *
 * 注意：本文件演示的重点是「类型安全」而非运行时行为。
 * 全局变量（如 APP_VERSION）在实际运行时可能未定义，因此用 typeof 守卫安全访问。
 * 模块声明（如 fictional-utils）用 import type 消费，编译后被擦除，不产生运行时导入。
 */

// ============================================================
// 1. 消费全局声明（global-declare.d.ts）
// ============================================================
//
// global-declare.d.ts 是「脚本文件」（无 import/export），声明位于全局。
// 这里无需 import，直接使用即可。

console.log('=== 1. 全局声明消费 ===\n');

// 1.1 全局常量：declare const APP_VERSION / BUILD_TIME / IS_PRODUCTION
// 运行时这些变量可能由构建工具注入，未注入时用 typeof 守卫安全访问
const appVersion = typeof APP_VERSION !== 'undefined' ? APP_VERSION : '0.0.0-dev';
const buildTime = typeof BUILD_TIME !== 'undefined' ? BUILD_TIME : new Date().toISOString();
const isProd = typeof IS_PRODUCTION !== 'undefined' ? IS_PRODUCTION : false;

console.log(`APP_VERSION  = ${appVersion}`);
console.log(`BUILD_TIME   = ${buildTime}`);
console.log(`IS_PRODUCTION = ${isProd}`);

// 1.2 全局函数：declare function gtag / track / __debug
// 函数类型由声明文件提供，运行时用 typeof 守卫判断是否已加载
if (typeof gtag === 'function') {
  gtag('config', 'GA-XXXXXX', { page_title: 'home' });
}
if (typeof track === 'function') {
  track('page_view', { path: '/home' });
}
// __debug 在开发环境常用
if (typeof __debug === 'function') {
  __debug('use-declare', '全局调试函数可用');
}
console.log('全局函数类型检查通过（gtag / track / __debug 均有类型）');

// 1.3 全局命名空间：declare namespace AppConfig / Sentry
// 类型层面：AppConfig.FeatureFlags 可用作类型注解
const flags: AppConfig.FeatureFlags = {
  newDashboard: true,
  darkMode: false,
  experimentalAPI: true,
};
console.log('FeatureFlags:', flags);

// 运行时：AppConfig 可能由 SDK 注入，用 typeof 守卫
if (typeof AppConfig !== 'undefined' && typeof AppConfig.getFeatureFlags === 'function') {
  const runtimeFlags = AppConfig.getFeatureFlags();
  console.log('Runtime FeatureFlags:', runtimeFlags);
}

// 1.4 全局类：declare class LegacyModal
// 类型层面可用作类型注解；运行时用 typeof 守卫
function openLegacyModal(content: string): LegacyModal | null {
  if (typeof LegacyModal === 'function') {
    return LegacyModal.create({ content });
  }
  console.log('  [skip] LegacyModal 未加载');
  return null;
}
openLegacyModal('Hello from LegacyModal');

// 1.5 window 属性扩展：interface Window 声明合并
// TS 已知道 window.__APP_NAME__ 是 string，无需断言
if (typeof window !== 'undefined') {
  // window.__APP_NAME__ 类型为 string（由 global-declare.d.ts 声明）
  const appName: string = window.__APP_NAME__;
  console.log(`window.__APP_NAME__ = ${appName}`);

  // window.__BROWSER_INFO__ 类型为可选对象
  if (window.__BROWSER_INFO__) {
    console.log(`Browser: ${window.__BROWSER_INFO__.name} ${window.__BROWSER_INFO__.version}`);
  }

  // window.wx 类型为可选的微信 SDK
  if (window.wx) {
    window.wx.ready(() => console.log('WeChat JS-SDK ready'));
  }
} else {
  console.log('  [skip] window 不存在（Node 环境），window 属性声明仅作类型演示');
}


// ============================================================
// 2. 消费模块声明（module-declare.d.ts）
// ============================================================
//
// module-declare.d.ts 用 declare module 'fictional-utils' 提供了类型。
// 用 import type 消费：仅导入类型，编译后被擦除，不产生运行时 import。

console.log('\n=== 2. 模块声明消费 ===\n');

import type { FormatOptions, ValueType } from 'fictional-utils';

// 2.1 使用声明的接口作为类型注解
const fmtOpt: FormatOptions = {
  precision: 2,
  locale: 'zh-CN',
  currency: 'CNY',
};
console.log('FormatOptions:', fmtOpt);

// 2.2 使用声明的类型别名
const detected: ValueType = 'number';
console.log('ValueType:', detected);

// 2.3 模拟函数签名：用声明的类型约束本地实现
// 真实项目中 formatNumber 由 fictional-utils 提供，这里用本地实现演示类型匹配
const localFormatNumber = (value: number, options?: FormatOptions): string => {
  const precision = options?.precision ?? 0;
  const locale = options?.locale ?? 'en-US';
  return value.toLocaleString(locale, {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
  });
};

console.log('formatNumber(1234.567, {precision:2}):', localFormatNumber(1234.567, fmtOpt));
console.log('formatNumber(1234.567):', localFormatNumber(1234.567));

// 2.4 通配符模块声明：*.css / *.svg / *.png 的类型
// 这些声明让 TS 认识非 JS 资源的导入（仅类型演示，不实际 import）
// 实际使用：import logo from './logo.svg'   // logo 的类型为 string


// ============================================================
// 3. 消费 Express 扩展（express-augment.d.ts）
// ============================================================
//
// express-augment.d.ts 通过模块扩增给 Request 添加了 user 字段。
// 用 import type 消费类型，编写类型安全的中间件。

console.log('\n=== 3. Express 扩展消费 ===\n');

import type { Request, Response, NextFunction, RequestHandler, AuthUser } from 'express-serve-static-core';

// 3.1 认证中间件：把用户信息挂到 req.user
//     由于 express-augment.d.ts 扩展了 Request，req.user 类型为 AuthUser | undefined
const authMiddleware: RequestHandler = (req: Request, res: Response, next: NextFunction) => {
  const token = req.headers['authorization'];
  if (!token) {
    res.status(401).json({ error: 'No token provided' });
    return;
  }

  // 模拟解析 token 得到用户信息
  const user: AuthUser = {
    id: 'u-1001',
    name: 'Alice',
    email: 'alice@example.com',
    roles: ['admin'],
    loginAt: new Date(),
  };

  // 把用户挂到 req.user——类型安全，因为 Request 已被扩展
  req.user = user;
  next();
};

// 3.2 路由处理函数：使用扩展后的 req.user
const getUserProfile: RequestHandler = (req: Request, res: Response, next: NextFunction) => {
  // req.user 类型为 AuthUser | undefined（扩展声明中 user 是可选的）
  if (!req.user) {
    res.status(401).json({ error: 'Not authenticated' });
    return;
  }

  // 类型收窄后，req.user 是 AuthUser，可安全访问 id / name / roles 等
  res.json({
    id: req.user.id,
    name: req.user.name,
    email: req.user.email,
    roles: req.user.roles,
    loginAt: req.user.loginAt.toISOString(),
  });
};

// 3.3 使用扩展后的 Response.sendSuccess / sendError
const sendSuccessDemo: RequestHandler = (req: Request, res: Response) => {
  // sendSuccess 是 express-augment.d.ts 扩展到 Response 的方法
  res.sendSuccess({ message: 'ok' }, '操作成功');
};

console.log('authMiddleware 类型检查通过：', typeof authMiddleware);
console.log('getUserProfile 类型检查通过：', typeof getUserProfile);
console.log('sendSuccessDemo 类型检查通过：', typeof sendSuccessDemo);

// 3.4 模拟一次请求处理，演示类型安全
function simulateRequest(handler: RequestHandler, mockReq: Partial<Request> = {}): void {
  const req = {
    body: {},
    params: {},
    query: {},
    headers: {},
    method: 'GET',
    url: '/',
    path: '/',
    ip: '127.0.0.1',
    cookies: {},
    ...mockReq,
  } as Request;

  // 用闭包变量维护状态，避免 this 推断问题
  let statusCode = 200;
  const res = {
    status(code: number) { statusCode = code; return res; },
    json(body: unknown) { console.log('  [response]', statusCode, JSON.stringify(body)); return res; },
    send(body: unknown) { console.log('  [response]', statusCode, body); return res; },
    end() { return res; },
    setHeader() { return res; },
    cookie() { return res; },
    sendSuccess<T>(data: T, message?: string) {
      console.log('  [response]', 200, JSON.stringify({ code: 0, message: message ?? 'ok', data }));
      return res;
    },
    sendError(code: number, message: string) {
      console.log('  [response]', code, JSON.stringify({ code, message }));
      return res;
    },
  } as unknown as Response;

  handler(req, res, () => { console.log('  [next] called'); });
}

console.log('\n--- 模拟未带 token 的请求 ---');
simulateRequest(authMiddleware, { headers: { authorization: '' } });

console.log('\n--- 模拟带 token 的请求（认证 + 获取 profile）---');
simulateRequest(authMiddleware, { headers: { authorization: 'Bearer xxx' } });
simulateRequest(getUserProfile, { user: { id: 'u-1001', name: 'Alice', email: 'a@b.com', roles: ['admin'], loginAt: new Date() } });

console.log('\n--- 模拟 sendSuccess 扩展方法 ---');
simulateRequest(sendSuccessDemo);


// ============================================================
// 4. 消费环境变量声明（env.d.ts）
// ============================================================
//
// env.d.ts 扩展了 NodeJS.ProcessEnv，让 process.env 的自定义变量获得类型。

console.log('\n=== 4. 环境变量声明消费 ===\n');

// 4.1 process.env.NODE_ENV：类型为 'development' | 'production' | 'test'
//     声明为 readonly + 联合类型，赋值错误会被 TS 拦截
const nodeEnv = process.env.NODE_ENV;
console.log(`NODE_ENV = ${nodeEnv}`);

// 4.2 必填变量：DATABASE_URL / JWT_SECRET 声明为 string（非 undefined）
//     运行时可能未设置，但类型层面 TS 认为是 string
const dbUrl = process.env.DATABASE_URL;
const jwtSecret = process.env.JWT_SECRET;
console.log(`DATABASE_URL = ${dbUrl ? dbUrl.replace(/\/\/.*@/, '//***@') : '(未设置)'}`);
console.log(`JWT_SECRET   = ${jwtSecret ? '***' : '(未设置)'}`);

// 4.3 可选变量：PORT / LOG_LEVEL 等声明为 string | undefined（通过 ? 标记）
const port = process.env.PORT ?? '3000';
const logLevel = process.env.LOG_LEVEL ?? 'info';
console.log(`PORT      = ${port}`);
console.log(`LOG_LEVEL = ${logLevel}`);

// 4.4 联合类型变量：LOG_LEVEL 限定为特定值
// 如果写成 process.env.LOG_LEVEL = 'verbose' 会报 TS 类型错误
const validLogLevels: Array<'debug' | 'info' | 'warn' | 'error'> = ['debug', 'info', 'warn', 'error'];
console.log('validLogLevels:', validLogLevels);

// 4.5 ImportMetaEnv 类型演示（仅类型层面，CommonJS 运行时无 import.meta）
// 在 Vite 项目中：import.meta.env.VITE_API_BASE 类型为 string
// 这里仅展示类型可用，不实际访问 import.meta
type ViteApiBase = ImportMetaEnv['VITE_API_BASE'];  // string
type ViteAppTitle = ImportMetaEnv['VITE_APP_TITLE']; // string
console.log(`ImportMetaEnv['VITE_API_BASE'] 类型: ${'' as ViteApiBase}string`);
console.log(`ImportMetaEnv['VITE_APP_TITLE'] 类型: ${'' as ViteAppTitle}string`);


console.log('\n--- use-declare.ts 执行完毕 ---');
