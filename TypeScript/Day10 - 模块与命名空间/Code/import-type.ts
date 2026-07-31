/**
 * Day10 - import-type.ts
 *
 * 演示 import type 与 isolatedModules 的硬性要求。
 *
 * isolatedModules: true 模拟单文件编译器（Babel / esbuild / swc / ts-node transpileOnly）
 * 的行为：每个文件独立编译，无法跨文件推断某个名字是「类型」还是「值」。
 * 因此「仅类型」的导入必须显式用 import type，re-export 类型必须用 export type，
 * 否则编译器无法在编译期擦除它。
 */

// ============================================================
// 1. import type：纯类型导入，编译后被完全擦除
// ============================================================

import type { MathOptions } from './math-utils';

function describeOptions(options: MathOptions): string {
  return `precision=${options.precision ?? '默认'}, throwOnZeroDivide=${options.throwOnZeroDivide ?? true}`;
}

console.log(describeOptions({ precision: 2 }));


// ============================================================
// 2. 混合导入：值与类型一起导入，用 inline type 标记
// ============================================================

import { add, divide, type MathOperation } from './math-utils';

function describeOperation(op: MathOperation): string {
  return `运算类型：${op}`;
}

console.log('add(2, 3) =', add(2, 3));
console.log('divide(10, 4) =', divide(10, 4));
console.log(describeOperation('multiply'));


// ============================================================
// 3. isolatedModules 下的硬性要求：re-export 类型必须用 export type
// ============================================================

// ✅ 正确：类型 re-export 用 export type
export type { MathOperation } from './math-utils';

// ❌ 错误示范（取消注释会报 TS1203 错误）：
// 在 isolatedModules 下，编译器无法判断 MathOperation 是类型还是值：
// export { MathOperation } from './math-utils';
//   ↑ Re-exporting a type when 'isolatedModules' is enabled requires using 'export type'.


// ============================================================
// 4. import type 导入的名字只能出现在「类型位置」
// ============================================================

// 复用上面 import type 导入的 MathOptions
const sample: MathOptions = { precision: 3 };
console.log('sample =', sample);

// ❌ 以下两行取消注释会报错：
// const x = MathOptions;       // Error: 'MathOptions' cannot be used as a value
//                               // because it was imported using 'import type'.
// console.log(MathOptions);    // 同上

// 类型位置 ✅：作为类型注解、satisfies、as 断言、泛型参数等
const withDefault = { precision: 4, throwOnZeroDivide: false } satisfies MathOptions;
console.log('withDefault =', withDefault);


console.log('\n--- import-type.ts 执行完毕 ---');
