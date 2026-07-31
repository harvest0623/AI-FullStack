/**
 * Day10 - index.ts (Barrel File)
 *
 * Barrel file：把多个内部模块的导出「聚合 re-export」到一个入口，
 * 外部只需 `import { add, capitalize } from './index'` 即可一次拿到所有工具，
 * 而无需关心内部目录结构。
 *
 * ⚠️ isolatedModules 下的硬性要求：
 *    类型的 re-export 必须使用 `export type`，否则单文件编译器无法判断
 *    MathOperation 是类型还是值，会报 TS1203 错误。
 */

// ============================================================
// 1. 值的 re-export（含默认导出重命名为命名导出）
// ============================================================

export { add, subtract, multiply, divide } from './math-utils';
export { default as mathToolkit } from './math-utils';

export { capitalize, truncate, toCase, slugify } from './string-utils';
export { default as stringToolkit } from './string-utils';

// ============================================================
// 2. 类型的 re-export —— isolatedModules 下必须用 export type
// ============================================================

export type { MathOperation, MathOptions } from './math-utils';
export type { StringCase, TruncateOptions } from './string-utils';

// ❌ 错误示范（取消注释会报错）：
// 在 isolatedModules 下，编译器无法判断 MathOperation 是类型还是值：
// export { MathOperation } from './math-utils';
//   ↑ TS1203: Re-exporting a type when 'isolatedModules' is enabled requires using 'export type'.


// ============================================================
// 3. 运行时演示（barrel 通常被别人 import，自身一般无副作用）
// ============================================================

if (require.main === module) {
  console.log('barrel file index.ts 已聚合以下模块导出：');
  console.log('  - math-utils:    add, subtract, multiply, divide, mathToolkit(default)');
  console.log('  - string-utils:  capitalize, truncate, toCase, slugify, stringToolkit(default)');
  console.log('  - 类型:           MathOperation, MathOptions, StringCase, TruncateOptions');
  console.log('\n外部用法示例：');
  console.log("  import { add, capitalize, type MathOptions } from './index';");
  console.log('\n--- index.ts 执行完毕 ---');
}
