/**
 * Day11 - module-declare.d.ts
 *
 * 为无类型 JS 模块编写声明文件。
 *
 * 本文件演示两种典型场景：
 * 1. 用 declare module 'xxx' 为「裸导入的第三方 JS 库」补充类型（ambient module）
 * 2. 为本地 JS 文件（如 utils.js）编写同名 utils.d.ts 补充类型（local declaration）
 *
 * ──────────────────────────────────────────────────────────
 * 场景背景：假设有一个用纯 JS 编写的工具库 utils.js，内容如下：
 *
 *   // utils.js（虚构，本目录中并不实际存在）
 *   exports.formatNumber = function(value, options) { ... }
 *   exports.formatDate = function(date, locale) { ... }
 *   exports.clamp = function(value, min, max) { ... }
 *   exports.VERSION = '1.0.0'
 *   exports.detectType = function(value) { ... }
 *
 * 它没有 TypeScript 类型，import 时会报 TS7016。
 * 解决方式见下方两种写法。
 * ──────────────────────────────────────────────────────────
 */

// ============================================================
// 方式一：declare module 为「裸导入」的 JS 库补充类型
// ============================================================
//
// 适合：从 node_modules 安装的 JS 库，或用别名 / 别名路径引入的 JS 模块。
// 语法：declare module '模块名' { ... }
// 文件中的所有 export 都会作为该模块的对外类型。

declare module 'fictional-utils' {
  // 导出接口：外部 import type { FormatOptions } from 'fictional-utils' 可用
  export interface FormatOptions {
    precision?: number;
    locale?: string;
    currency?: string;
  }

  // 导出类型别名
  export type ValueType = 'number' | 'string' | 'boolean' | 'date' | 'null';

  // 导出函数声明（只声明签名，不含实现）
  export function formatNumber(value: number, options?: FormatOptions): string;
  export function formatDate(date: Date | string, locale?: string): string;
  export function clamp(value: number, min: number, max: number): number;
  export function detectType(value: unknown): ValueType;

  // 导出常量
  export const VERSION: string;

  // 导出命名导出对象
  export const defaultLocale: string;

  // 支持默认导出（如果 JS 文件有 module.exports = ... 或 export default）
  const _default: {
    formatNumber: typeof formatNumber;
    formatDate: typeof formatDate;
    clamp: typeof clamp;
    detectType: typeof detectType;
    VERSION: string;
  };
  export default _default;
}

// ============================================================
// 方式二：为本地 JS 文件编写同名 .d.ts（演示用，文件名为 module-declare.d.ts）
// ============================================================
//
// 适合：项目内用 JS 编写的本地工具文件。
// 规则：utils.js 旁边放一个 utils.d.ts，TS 会自动把它当作 utils.js 的类型声明。
//
// 真实项目中应新建 utils.d.ts（而非本文件），内容如下方注释所示：
//
//   // utils.d.ts（与 utils.js 同目录同名）
//   export interface FormatOptions {
//     precision?: number;
//     locale?: string;
//   }
//   export type ValueType = 'number' | 'string' | 'boolean' | 'date' | 'null';
//   export declare function formatNumber(value: number, options?: FormatOptions): string;
//   export declare function formatDate(date: Date | string, locale?: string): string;
//   export declare function clamp(value: number, min: number, max: number): number;
//   export declare function detectType(value: unknown): ValueType;
//   export declare const VERSION: string;
//
// 注意：
// - 在 .d.ts 中，function / const 前的 declare 关键字可省略（.d.ts 默认全部为声明）
// - 与 declare module 'xxx' 不同，这里不包外层 declare module，直接 export

// 为了让本文件既作为「演示文档」又能被 use-declare.ts 实际消费，
// 上面方式一的 declare module 'fictional-utils' 已提供完整可用的类型。
// use-declare.ts 会通过 `import type { ... } from 'fictional-utils'` 消费它。


// ============================================================
// 方式三：declare module 配合通配符，为非 JS 资源补充类型
// ============================================================

// 让 TS 认识 .css / .svg / .png 等非 JS 资源的导入（常见于前端项目）
declare module '*.css' {
  const classes: Record<string, string>;
  export default classes;
}

declare module '*.svg' {
  const src: string;
  export default src;
}

declare module '*.png' {
  const src: string;
  export default src;
}

// 导入 JSON 模块时（需 tsconfig 开启 resolveJsonModule）
declare module '*.json' {
  const value: Record<string, unknown>;
  export default value;
}
