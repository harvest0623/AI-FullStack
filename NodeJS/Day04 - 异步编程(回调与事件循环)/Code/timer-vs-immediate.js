/**
 * Day04 - 异步编程（回调与事件循环）
 * 文件：timer-vs-immediate.js
 * 主题：setTimeout(fn, 0) 与 setImmediate 顺序对比
 *
 * 核心结论：
 *   情况 A（主模块内）：两者顺序"不确定"
 *     - setTimeout(fn, 0) 在 Node 中实际被强制为 setTimeout(fn, 1)（最小 1ms）
 *     - 进入 timers 阶段时是否到达 1ms，取决于进程启动耗时
 *     - 多次运行可能看到不同顺序
 *
 *   情况 B（I/O 回调内）：setImmediate 一定先于 setTimeout 执行
 *     - I/O 回调在 poll 阶段执行
 *     - poll 阶段结束后必然先进入 check 阶段（执行 setImmediate）
 *     - 然后才进入下一轮的 timers 阶段（执行 setTimeout）
 *     - 这是 setImmediate 存在的核心意义：在 I/O 完成后"立即"继续
 */

'use strict';

const fs = require('fs');
const path = require('path');

console.log('=== setTimeout vs setImmediate 顺序对比 ===\n');

// ============================================================
// 情况 A：主模块内调用 —— 顺序不确定
// ============================================================
console.log('--- 情况 A：主模块内调用 ---');
console.log('（顺序不确定，多次运行可能不同）\n');

setTimeout(() => {
  console.log('  A1: setTimeout（timers 阶段）');
}, 0);

setImmediate(() => {
  console.log('  A2: setImmediate（check 阶段）');
});

console.log('  A0: 同步代码（先于所有异步）\n');

// ============================================================
// 情况 B：I/O 回调内调用 —— 顺序确定（setImmediate 先）
// ============================================================
console.log('--- 情况 B：I/O 回调内调用 ---');
console.log('（顺序确定：setImmediate 一定先于 setTimeout）\n');

// 用 fs.readFile 模拟一次 I/O 操作
const tmpFile = path.join(__dirname, '.tmp-io-test.txt');

// 先写入一个临时文件，再读取它，触发 I/O 回调
fs.writeFile(tmpFile, 'hello', (writeErr) => {
  if (writeErr) {
    console.error('  写入失败:', writeErr.message);
    return;
  }

  console.log('  B0: I/O 回调开始（poll 阶段）');

  // 在 I/O 回调内同时注册 setTimeout 和 setImmediate
  setTimeout(() => {
    console.log('  B1: setTimeout（下一轮 timers 阶段）');
  }, 0);

  setImmediate(() => {
    console.log('  B2: setImmediate（当前轮 check 阶段）');
  });

  console.log('  B0: I/O 回调结束\n');

  // 清理临时文件
  try {
    fs.unlinkSync(tmpFile);
  } catch (_) {
    /* 忽略 */
  }
});

// ============================================================
// 验证：多次运行情况 A，观察顺序差异
// ============================================================
console.log('--- 多次运行情况 A，观察顺序差异 ---\n');

let runCount = 0;
const totalRuns = 5;
const results = [];

function runOnce() {
  runCount++;
  let order = [];

  setTimeout(() => {
    order.push('timeout');
    if (order.length === 2) {
      results.push(order.join(' → '));
      if (runCount < totalRuns) {
        runOnce();
      } else {
        printResults();
      }
    }
  }, 0);

  setImmediate(() => {
    order.push('immediate');
    if (order.length === 2) {
      results.push(order.join(' → '));
      if (runCount < totalRuns) {
        runOnce();
      } else {
        printResults();
      }
    }
  });
}

function printResults() {
  console.log(`  运行 ${totalRuns} 次主模块内 setTimeout vs setImmediate 的结果：`);
  results.forEach((r, i) => {
    console.log(`  第 ${i + 1} 次: ${r}`);
  });
  console.log('\n  结论：主模块内顺序不确定，受进程启动耗时影响');
  console.log('       但 I/O 回调内 setImmediate 一定先于 setTimeout\n');
  console.log('=== 演示结束 ===');
}

// 启动多次运行（在 I/O 回调之后开始，避免干扰）
setTimeout(() => {
  console.log('  开始多次运行测试...\n');
  runOnce();
}, 100);

/**
 * 运行：node timer-vs-immediate.js
 *
 * 预期输出（情况 A 顺序可能不同）：
 *
 *   === setTimeout vs setImmediate 顺序对比 ===
 *
 *   --- 情况 A：主模块内调用 ---
 *   （顺序不确定，多次运行可能不同）
 *
 *     A0: 同步代码（先于所有异步）
 *     A1: setTimeout（timers 阶段）       ← 可能先也可能后
 *     A2: setImmediate（check 阶段）       ← 可能先也可能后
 *
 *   --- 情况 B：I/O 回调内调用 ---
 *   （顺序确定：setImmediate 一定先于 setTimeout）
 *
 *     B0: I/O 回调开始（poll 阶段）
 *     B0: I/O 回调结束
 *     B2: setImmediate（当前轮 check 阶段）  ← 一定先
 *     B1: setTimeout（下一轮 timers 阶段）   ← 一定后
 *
 *   --- 多次运行情况 A，观察顺序差异 ---
 *     ...
 *
 * 关键点：
 *   1. setTimeout(fn, 0) 实际最小延迟 1ms（Node 强制）
 *   2. 主模块内顺序不确定：取决于进程启动到进入 timers 阶段是否超过 1ms
 *   3. I/O 回调内顺序确定：poll → check（setImmediate） → 下一轮 timers（setTimeout）
 *   4. setImmediate 的设计初衷：在 I/O 完成后立即继续处理，保证在下一轮 timers 之前执行
 */
