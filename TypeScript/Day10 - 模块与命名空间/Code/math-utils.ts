/**
 * Day10 - math-utils.ts
 *
 * 演示 ES Module 的「命名导出 + 默认导出 + 类型导出」三件套。
 * 本模块对外提供数学工具函数与相关类型，index.ts 会通过 re-export 聚合它。
 */

// ============================================================
// 1. 类型导出：export type / export interface
// ============================================================

/** 运算类型字面量联合 */
export type MathOperation = 'add' | 'subtract' | 'multiply' | 'divide';

/** 运算选项：精度与除零策略 */
export interface MathOptions {
  /** 小数保留位数，省略则不截断 */
  precision?: number;
  /** 除零时是否抛错，默认 true */
  throwOnZeroDivide?: boolean;
}

// ============================================================
// 2. 命名导出：export function / export const
// ============================================================

export function add(a: number, b: number): number {
  return a + b;
}

export function subtract(a: number, b: number): number {
  return a - b;
}

export function multiply(a: number, b: number): number {
  return a * b;
}

/** 带选项的除法，演示「类型与值同文件」协作 */
export function divide(a: number, b: number, options?: MathOptions): number {
  const throwOnZero = options?.throwOnZeroDivide ?? true;
  const precision = options?.precision;

  if (b === 0) {
    if (throwOnZero) throw new Error('除数不能为零');
    return 0;
  }

  const result = a / b;
  return precision !== undefined ? Number(result.toFixed(precision)) : result;
}

// ============================================================
// 3. 默认导出：export default
// ============================================================

/**
 * 计算器对象，作为本模块的默认导出。
 * 默认导出每模块仅一个，导入时无需花括号、可任意命名。
 */
const calculator = {
  add,
  subtract,
  multiply,
  divide,
  /** 根据 MathOperation 字面量分发运算 */
  compute(op: MathOperation, a: number, b: number, options?: MathOptions): number {
    switch (op) {
      case 'add':      return add(a, b);
      case 'subtract': return subtract(a, b);
      case 'multiply': return multiply(a, b);
      case 'divide':   return divide(a, b, options);
    }
  },
};

export default calculator;

// ============================================================
// 4. 运行时演示（仅在被直接 ts-node 执行时运行，被 import 时不运行）
// ============================================================

if (require.main === module) {
  console.log('add(1, 2) =', add(1, 2));
  console.log('divide(10, 3, { precision: 2 }) =', divide(10, 3, { precision: 2 }));
  console.log('divide(10, 0, { throwOnZeroDivide: false }) =', divide(10, 0, { throwOnZeroDivide: false }));
  console.log('calculator.compute("multiply", 3, 4) =', calculator.compute('multiply', 3, 4));
  console.log('\n--- math-utils.ts 执行完毕 ---');
}
