/**
 * Day04 - 异步编程（回调与事件循环）
 * 文件：event-loop-order.js
 * 主题：微任务与宏任务执行顺序演示
 *
 * 混用以下 API，用 console.log 标号展示执行顺序：
 *   宏任务：setTimeout、setImmediate
 *   微任务：Promise.then、queueMicrotask、process.nextTick
 *
 * 优先级口诀（同一阶段内）：
 *   同步代码 > process.nextTick > Promise.then ≈ queueMicrotask > setTimeout > setImmediate
 *
 * 注意：
 *   - setTimeout 与 setImmediate 在主模块内的相对顺序不确定（受进程启动耗时影响）
 *   - 本文件用标号 + 注释帮助理解，实际运行可能因为环境差异略有不同
 */

'use strict';

console.log('=== 微任务与宏任务执行顺序演示 ===\n');

// ============== 同步代码（最先执行） ==============
console.log('① 同步代码：最先执行');

// ============== 宏任务注册 ==============
// setTimeout 进入 timers 阶段队列
setTimeout(() => {
  console.log('⑦ setTimeout 宏任务（timers 阶段）');
}, 0);

// setImmediate 进入 check 阶段队列
setImmediate(() => {
  console.log('⑧ setImmediate 宏任务（check 阶段）');
});

// ============== 微任务注册 ==============
// process.nextTick 优先级最高，在所有微任务前执行
process.nextTick(() => {
  console.log('③ process.nextTick 微任务（最高优先级）');
});

// Promise.then 与 queueMicrotask 同属微任务队列，按注册顺序执行（FIFO）
Promise.resolve().then(() => {
  console.log('④ Promise.then 微任务');
});

queueMicrotask(() => {
  console.log('⑤ queueMicrotask 微任务（与 Promise.then 同队列，FIFO）');
});

// ============== 同步代码继续 ==============
console.log('② 同步代码：继续执行\n');

/**
 * 预期输出顺序：
 *
 *   ① 同步代码：最先执行
 *   ② 同步代码：继续执行
 *   ③ process.nextTick 微任务（最高优先级）
 *   ④ Promise.then 微任务
 *   ⑤ queueMicrotask 微任务（与 Promise.then 同队列，FIFO）
 *   ⑦ setTimeout 宏任务（timers 阶段）
 *   ⑧ setImmediate 宏任务（check 阶段）
 *
 * 说明：
 *   - ①②：同步代码在主线程立即执行
 *   - 同步代码结束后、事件循环启动前，先清空微任务：
 *       nextTick 优先 → ③
 *       然后是 Promise/queueMicrotask 队列，按 FIFO → ④⑤
 *   - 进入 timers 阶段执行 setTimeout → ⑦
 *   - 进入 check 阶段执行 setImmediate → ⑧
 *   - ⑦ 和 ⑧ 在主模块内的相对顺序"通常"是 setTimeout 先，但不保证
 *     （取决于进程启动后是否已经超过 setTimeout 的 1ms 最小延迟）
 */

// ============== 进阶演示：在微任务里再注册微任务 ==============
console.log('\n=== 进阶演示：微任务里嵌套注册微任务 ===\n');

console.log('A: 同步');

process.nextTick(() => {
  console.log('B: nextTick 第一层');
  // 在 nextTick 回调里再注册一个 nextTick
  // 它会在当前微任务清空阶段继续执行（nextTick 队列会递归清空）
  process.nextTick(() => {
    console.log('C: nextTick 第二层（递归清空）');
  });
  // 再注册一个 Promise 微任务
  Promise.resolve().then(() => {
    console.log('D: Promise 微任务（在 nextTick 回调里注册）');
  });
});

Promise.resolve().then(() => {
  console.log('E: Promise 微任务（顶层注册）');
});

console.log('F: 同步\n');

/**
 * 进阶预期输出：
 *   A: 同步
 *   F: 同步
 *   B: nextTick 第一层
 *   C: nextTick 第二层（递归清空）   ← nextTick 队列会一直清空，直到为空
 *   E: Promise 微任务（顶层注册）     ← 然后才轮到 Promise 队列
 *   D: Promise 微任务（在 nextTick 回调里注册）
 *
 * 关键点：
 *   - nextTick 队列优先级高于 Promise 队列
 *   - 每次清空 nextTick 队列时，如果新增了 nextTick，会继续清空（可能"饿死"I/O）
 *   - 在 nextTick 回调里新增的 Promise 微任务，要等 nextTick 队列完全清空后才执行
 */

// ============== ⚠️ 警告：nextTick 递归会"饿死"事件循环 ==============
// 下面这段代码注释掉，仅作演示，运行会让进程卡死：
//
// process.nextTick(function recurse() {
//   process.nextTick(recurse);  // 永远在 nextTick 队列里追加，事件循环永远进不到 poll
// });
// console.log('这行之后，setTimeout 永远不会执行');

console.log('（演示结束，等待所有异步任务完成...）\n');

/**
 * 运行：node event-loop-order.js
 */
