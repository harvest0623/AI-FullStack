/**
 * Day11 - env.d.ts
 *
 * 为环境变量补充类型：扩展 NodeJS.ProcessEnv 与 Vite 的 ImportMetaEnv。
 *
 * 痛点：
 * - process.env.MY_API_KEY 默认类型是 string | undefined，访问任何键都不报错，
 *   拼写错误（如 process.env.APLY_KEY）只能靠运行时发现。
 * - 通过扩展 ProcessEnv 接口，让 TS 知道哪些环境变量是「项目约定存在的」，
 *   既能自动补全，又能在拼写错误时立即报错。
 *
 * 本文件是「脚本文件」（无顶层 import / export），声明位于全局。
 */

// ============================================================
// 1. 扩展 NodeJS.ProcessEnv：为 Node.js 的环境变量补充类型
// ============================================================
//
// @types/node 已定义了 NodeJS.ProcessEnv 接口（索引签名 [key: string]: string | undefined）。
// 这里通过声明合并追加项目特定的环境变量，让它们获得精确类型。
//
// 注意：声明合并后，这些键仍然受 [key: string] 索引签名约束，
// 但显式声明的键会获得更精确的类型，且支持 IDE 自动补全。

declare namespace NodeJS {
  interface ProcessEnv {
    // Node 运行环境
    readonly NODE_ENV: 'development' | 'production' | 'test';

    // 服务端口
    readonly PORT?: string;

    // 数据库连接
    readonly DATABASE_URL: string;
    readonly DATABASE_POOL_SIZE?: string;

    // 鉴权密钥
    readonly JWT_SECRET: string;
    readonly JWT_EXPIRES_IN?: string;

    // 第三方服务
    readonly REDIS_URL?: string;
    readonly OSS_ACCESS_KEY?: string;
    readonly OSS_SECRET_KEY?: string;
    readonly OSS_BUCKET?: string;

    // 日志
    readonly LOG_LEVEL?: 'debug' | 'info' | 'warn' | 'error';

    // 前端可访问的公共变量（以 PUBLIC_ 前缀约定）
    readonly PUBLIC_API_BASE?: string;
    readonly PUBLIC_CDN_URL?: string;
  }
}


// ============================================================
// 2. 扩展 ImportMetaEnv：为 Vite 的 import.meta.env 补充类型
// ============================================================
//
// Vite 通过 import.meta.env 暴露环境变量，默认类型只含 BASE_URL / MODE / DEV / PROD 等内置字段。
// 自定义的 VITE_xxx 变量需要通过扩展 ImportMetaEnv 接口来获得类型。
//
// 使用前提：tsconfig 的 module 设置为 ESNext 或 NodeNext（import.meta 仅在 ESM 可用）。
// 本项目为 CommonJS，import.meta 在运行时不可用，但类型声明仍可演示。

interface ImportMetaEnv {
  // Vite 内置变量（已由 vite/client 类型声明，这里仅作对照）
  readonly MODE: string;
  readonly BASE_URL: string;
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly SSR: boolean;

  // 项目自定义的 VITE_ 前缀变量（Vite 只暴露 VITE_ 前缀的变量给前端）
  readonly VITE_API_BASE: string;
  readonly VITE_APP_TITLE: string;
  readonly VITE_CDN_URL?: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_GA_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}


// ============================================================
// 3. 三斜线指令引用（呼应 Day10）
// ============================================================
//
// 在 .d.ts 文件中，三斜线指令用于声明对其他类型包的依赖。
// 现代项目通常用 tsconfig 的 types / lib 替代，但在维护老 .d.ts 时仍会遇到。
//
// 下面两行（注释状态）分别引用 @types/node 和 ES2020 标准库：
//   /// <reference types="node" />
//   /// <reference lib="ES2020" />
//
// 由于本项目 tsconfig.json 已通过 lib: ["ES2020", "DOM"] 与安装 @types/node
// 自动包含这些类型，因此无需在此显式声明三斜线依赖。
// 仅在「独立分发的 .d.ts 文件」（如发布到 npm 的类型补丁）中才需要显式写。


// ============================================================
// 4. 配合 dotenv 使用的类型约定
// ============================================================
//
// 如果项目用 dotenv 加载 .env 文件，process.env 的类型扩展同样适用：
//
//   // .env
//   DATABASE_URL=postgres://localhost:5432/mydb
//   JWT_SECRET=super-secret-key
//   NODE_ENV=development
//
//   // app.ts
//   import 'dotenv/config';
//
//   const dbUrl = process.env.DATABASE_URL;   // 类型：string（非 undefined）
//   const jwtSecret = process.env.JWT_SECRET; // 类型：string
//   const env = process.env.NODE_ENV;         // 类型：'development' | 'production' | 'test'
//
// 由于上面已将 DATABASE_URL / JWT_SECRET 声明为必填（非 readonly?），
// TS 会把它们推断为 string（而非 string | undefined），调用方无需再做非空断言。
