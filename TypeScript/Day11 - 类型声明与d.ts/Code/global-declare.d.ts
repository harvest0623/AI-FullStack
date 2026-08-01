/**
 * Day11 - global-declare.d.ts
 *
 * 全局声明文件：为全局变量、window 属性、自定义全局函数补充类型。
 *
 * 本文件是「脚本文件」（无顶层 import / export），因此所有声明都位于全局作用域。
 * 这是 .d.ts 声明文件最经典的形态——任何 TS 文件无需 import 即可直接使用这些类型。
 *
 * 对应理论：
 * - declare var / let / const：声明全局变量
 * - declare function：声明全局函数
 * - interface Window：通过声明合并扩展 window 属性
 * - declare namespace：声明全局命名空间
 */

// ============================================================
// 1. 全局常量：declare const
// ============================================================

// 由构建工具（webpack DefinePlugin / Vite define）注入的全局常量
declare const APP_VERSION: string;
declare const BUILD_TIME: string;
declare const IS_PRODUCTION: boolean;

// 由 CDN 引入的库挂载到全局的变量（如 jQuery 的 $）
declare const $$: <T extends HTMLElement>(selector: string) => T | null;


// ============================================================
// 2. 全局变量：declare var / let
// ============================================================

// var 与 let 声明的全局变量可重新赋值
declare var __DEV__: boolean;
declare let __APP_CONFIG__: {
  apiBase: string;
  timeout: number;
  retryTimes: number;
};


// ============================================================
// 3. 全局函数：declare function
// ============================================================

// Google Analytics 的 gtag 函数（通过 <script> 标签注入全局）
declare function gtag(
  command: 'config' | 'event' | 'set' | 'consent',
  targetIdOrEventName: string,
  params?: Record<string, unknown>
): void;

// 埋点上报函数（由内部 SDK 挂载到全局）
declare function track(event: string, properties?: Record<string, unknown>): void;

// 调试用的全局日志函数
declare function __debug(tag: string, ...args: unknown[]): void;


// ============================================================
// 4. 扩展 window 属性：interface Window 声明合并
// ============================================================

// TypeScript 内置的 lib.dom.d.ts 已定义了 Window 接口。
// 在 .d.ts 脚本文件中重新声明同名 interface 会触发「声明合并」，
// 给 Window 追加自定义属性而不覆盖原有成员。

interface Window {
  // 自定义全局属性
  __APP_NAME__: string;
  __APP_VERSION__: string;

  // 内嵌 SDK 挂载的对象
  __BROWSER_INFO__?: {
    name: string;
    version: string;
    os: string;
    isMobile: boolean;
  };

  // 自定义全局方法
  __reloadConfig__(): Promise<void>;

  // 第三方 SDK 通过 window 暴露的入口（如微信 JS-SDK）
  wx?: {
    config(config: Record<string, unknown>): void;
    ready(callback: () => void): void;
    error(handler: (res: { errMsg: string }) => void): void;
  };
}

// 同样可以扩展 Document、HTMLElement 等内置接口
interface Document {
  __customProperty__: string;
}


// ============================================================
// 5. 全局命名空间：declare namespace
// ============================================================

// 当一个全局对象包含多个子属性 / 方法时，用 namespace 组织更清晰
declare namespace AppConfig {
  const version: string;
  const env: 'development' | 'staging' | 'production';

  interface FeatureFlags {
    newDashboard: boolean;
    darkMode: boolean;
    experimentalAPI: boolean;
  }

  function getFeatureFlags(): FeatureFlags;
  function refresh(): Promise<void>;
}

// 全局的错误上报命名空间
declare namespace Sentry {
  function captureException(error: Error | string): void;
  function captureMessage(message: string, level?: 'info' | 'warning' | 'error'): void;
  function setUser(user: { id: string; email?: string } | null): void;
}


// ============================================================
// 6. 全局类：declare class
// ============================================================

// 由旧版 JS 库挂载到全局的构造函数（如未走模块化的早期组件库）
declare class LegacyModal {
  constructor(options: {
    title?: string;
    content: string;
    width?: number;
    onClose?: () => void;
  });

  open(): void;
  close(): void;
  setTitle(title: string): void;
  static create(options: { content: string }): LegacyModal;
}
