/**
 * esm-vs-cjs.ts
 * 演示 CommonJS 与 ESM 在 Node.js 中的差异：
 *   - __dirname / __filename 在 CJS 中可用
 *   - import.meta.url + fileURLToPath 是 ESM 中的替代方案
 *   - createRequire 在 ESM 中桥接 require
 *
 * 注意：本文件由 tsx 以 CJS 模式运行，因此可直接使用 __dirname。
 *      ESM 等价写法以代码块注释形式给出，便于对照。
 *
 * 运行：tsx esm-vs-cjs.ts
 */

import { join, dirname, resolve } from 'node:path';

// ============================================================
// 1. CommonJS 模式（当前文件运行所在模式）
// ============================================================

// 在 CJS 中，__dirname / __filename / require 都是「全局注入」的局部变量
// 它们不是 globalThis 的属性，而是 Node 的 CJS 包装函数注入的局部变量
console.log('--- CommonJS 模式 ---');
console.log('当前模块系统: CommonJS');
console.log('__dirname  =', __dirname);
console.log('__filename =', __filename);
console.log('process.cwd() =', process.cwd());

// 路径拼接演示
const dataFile: string = join(__dirname, 'data', 'sample.json');
console.log('dataFile   =', dataFile);

// ============================================================
// 2. ESM 模式下的等价写法（注释展示，便于对照）
// ============================================================

/*
// ── ESM 写法 ───────────────────────────────────────────
// 当 package.json 设置 "type": "module" 或文件后缀为 .mts/.mjs 时
// __dirname / __filename / require 都不可用，会抛 ReferenceError

import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { createRequire } from 'node:module';

// 用 import.meta.url 替代 __filename
const __filename: string = fileURLToPath(import.meta.url);
// 用 dirname(fileURLToPath(import.meta.url)) 替代 __dirname
const __dirname: string = dirname(__filename);

// 用 createRequire(import.meta.url) 在 ESM 中拿到 require
const require = createRequire(import.meta.url);
const someCjs = require('./some-legacy.cjs');

console.log(import.meta.url);  // file:///path/to/file.ts
console.log(__dirname, __filename);
*/

// ============================================================
// 3. 模块系统检测：跨 CJS / ESM 都能跑
// ============================================================

type ModuleSystem = 'commonjs' | 'esm';

function detectModuleSystem(): ModuleSystem {
  // __dirname 是 CJS 注入的局部变量，ESM 下访问会 ReferenceError
  try {
    // 使用 eval 防止 TS 在 ESM 模式下直接拒绝编译
    // eslint-disable-next-line no-eval
    eval('__dirname');
    return 'commonjs';
  } catch {
    return 'esm';
  }
}

const system: ModuleSystem = detectModuleSystem();
console.log('\n--- 模块系统检测 ---');
console.log('detectModuleSystem() =', system);

// ============================================================
// 4. import 语法编译对比
// ============================================================

/*
// tsconfig 中 module 字段决定编译产物：

module: "commonjs"
  ─────────────────
  import { join } from 'node:path';
  // 编译为：
  // const { join } = require('node:path');

module: "nodenext" / "esnext" / "es2022"
  ─────────────────
  import { join } from 'node:path';
  // 保留 import（输出 .mjs 或 type: module 的 .js）

module: "preserve" (TS 5.4+)
  ─────────────────
  // 完全保留 import 语法，交给下游打包器/运行器决定
*/

// ============================================================
// 5. 跨模块系统的路径解析：写一份代码两边都能跑
// ============================================================

/**
 * 返回当前文件所在目录，CJS 与 ESM 都能用
 * - CJS：直接用 __dirname
 * - ESM：用 import.meta.url + fileURLToPath（在调用方传递）
 */
function getDirname(cjsDirname: string | undefined): string {
  if (cjsDirname !== undefined) {
    return cjsDirname;
  }
  // ESM 模式下调用方需自己传入 fileURLToPath 后的结果
  throw new Error('ESM 模式下请使用 fileURLToPath(import.meta.url) 获取路径');
}

console.log('\n--- 跨模块路径 ---');
console.log('当前目录 =', getDirname(__dirname));
console.log('resolve =', resolve(__dirname, '..', 'package.json'));

// ============================================================
// 6. .mts / .cts 扩展名说明
// ============================================================

/*
.cjs  → 强制 CommonJS（即使 package.json type: module）
.mjs  → 强制 ESM（即使 package.json type: commonjs）
.cts  → TS 的 CJS 源文件，编译产物为 .cjs
.mts  → TS 的 ESM 源文件，编译产物为 .mjs

当 package.json 同时混合 CJS + ESM 时，推荐显式使用 .cts / .mts 后缀，
避免「type 字段一刀切」带来的模块判别歧义。
*/

console.log('\n[done] esm-vs-cjs demo finished.');
