/**
 * math-util.js
 * ------------------------------------------------------------------
 * Day03 示例模块：被 package.json 的 "main" 字段引用。
 * 当其他项目执行 require('day03-math-util') 时，实际加载的就是这个文件。
 *
 * 采用 CommonJS 风格（module.exports），因为 package.json 的 "type" 未设为 "module"。
 * Node 18+ 原生支持，无需任何编译步骤。
 * ------------------------------------------------------------------
 */

'use strict';

/**
 * 加法
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
function add(a, b) {
  return a + b;
}

/**
 * 减法
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
function subtract(a, b) {
  return a - b;
}

/**
 * 阶乘 n!（迭代实现，避免大数栈溢出）
 * @param {number} n 非负整数
 * @returns {number}
 */
function factorial(n) {
  if (!Number.isInteger(n) || n < 0) {
    throw new RangeError('factorial 入参必须为非负整数');
  }
  let result = 1;
  for (let i = 2; i <= n; i++) {
    result *= i;
  }
  return result;
}

/**
 * 判断素数
 * @param {number} n
 * @returns {boolean}
 */
function isPrime(n) {
  if (!Number.isInteger(n) || n < 2) return false;
  if (n === 2) return true;
  if (n % 2 === 0) return false;
  const limit = Math.floor(Math.sqrt(n));
  for (let i = 3; i <= limit; i += 2) {
    if (n % i === 0) return false;
  }
  return true;
}

/**
 * 生成 [min, max] 闭区间内的素数列表
 * @param {number} min
 * @param {number} max
 * @returns {number[]}
 */
function primesInRange(min, max) {
  const result = [];
  for (let i = min; i <= max; i++) {
    if (isPrime(i)) result.push(i);
  }
  return result;
}

module.exports = {
  add,
  subtract,
  factorial,
  isPrime,
  primesInRange
};

// ------------------------------------------------------------------
// 模块自检：直接 node math-util.js 时输出一段演示
// 被 require 时不会执行（require 只导入 module.exports）
// ------------------------------------------------------------------
if (require.main === module) {
  console.log('--- math-util 自检 ---');
  console.log('add(2, 3)        =', add(2, 3));
  console.log('subtract(10, 4)  =', subtract(10, 4));
  console.log('factorial(5)     =', factorial(5));
  console.log('isPrime(7)       =', isPrime(7));
  console.log('primesInRange(1, 20) =', primesInRange(1, 20));
  console.log('--- 自检结束 ---');
}
