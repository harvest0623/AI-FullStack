'use strict';

/**
 * Day05 - 并发 vs 串行 耗时对比
 * 主题：for...of await（串行）vs Promise.all（并发）vs 带并发上限的分批
 * 用 setTimeout 模拟 3 个各 500ms 的任务
 * 运行：node parallel-vs-serial.js
 */

// 一个耗时 500ms 的任务
function task(name) {
  return new Promise(resolve => {
    setTimeout(() => {
      console.log(`  [${name}] 完成 @ ${new Date().toISOString().slice(11, 23)}`);
      resolve(name);
    }, 500);
  });
}

const tasks = ['A', 'B', 'C'];

// ---------------------------------------------------------------
// 1. 串行：for...of + await，前一个完成才启动下一个
// ---------------------------------------------------------------
async function serial() {
  console.log('--- 串行 for...of await ---');
  const t0 = Date.now();
  const results = [];
  for (const name of tasks) {
    results.push(await task(name));
  }
  const cost = Date.now() - t0;
  console.log(`串行总耗时：${cost}ms（预期 ≈ 1500ms = 500×3）\n`);
  return results;
}

// ---------------------------------------------------------------
// 2. 并发：Promise.all，同时启动，等最慢的
// ---------------------------------------------------------------
async function parallel() {
  console.log('--- 并发 Promise.all ---');
  const t0 = Date.now();
  const results = await Promise.all(tasks.map(name => task(name)));
  const cost = Date.now() - t0;
  console.log(`并发总耗时：${cost}ms（预期 ≈ 500ms = max(500,500,500)）\n`);
  return results;
}

// ---------------------------------------------------------------
// 3. 进阶：带并发上限的分批执行（生产中常用，应对限流/资源约束）
// 思路：维护一个正在执行的 Promise 集合，达到上限就用 Promise.race 等最快的一个腾位置
// ---------------------------------------------------------------
async function parallelWithLimit(items, limit, worker) {
  const results = [];              // 保存每个任务对应 Promise（保持顺序）
  const executing = new Set();     // 当前正在执行的任务集合

  for (const item of items) {
    const p = Promise.resolve().then(() => worker(item));
    results.push(p);
    executing.add(p);
    p.finally(() => executing.delete(p)); // 完成后从集合移除

    if (executing.size >= limit) {
      await Promise.race(executing);      // 达到上限，等最快的一个完成再继续塞
    }
  }
  return Promise.all(results);            // 等所有任务完成
}

async function bounded() {
  console.log('--- 并发上限 = 2 的分批执行（5 个任务）---');
  const t0 = Date.now();
  const items = ['T1', 'T2', 'T3', 'T4', 'T5'];
  // 并发上限 2：约 ceil(5/2) = 3 批 → ≈ 1500ms
  await parallelWithLimit(items, 2, name => task(name));
  const cost = Date.now() - t0;
  console.log(`分批(限2)总耗时：${cost}ms（预期 ≈ 1500ms = ceil(5/2)×500）\n`);
}

// ---------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------
(async () => {
  await serial();
  await parallel();
  await bounded();

  console.log('=== 结论 ===');
  console.log('1. 串行耗时 = 任务耗时之和（1500ms）');
  console.log('2. 并发耗时 = 最慢任务耗时（500ms，约 3 倍提速）');
  console.log('3. 生产中遇到限流（如 LLM API 的 RPM 限制）或资源约束时，');
  console.log('   用“并发上限”分批执行，兼顾速度与稳定性。');
  console.log('4. AI 场景：批量向大模型发送 prompt，串行太慢、无脑并发被限流，');
  console.log('   分批 + Promise.all 是常见解法。');
})();
