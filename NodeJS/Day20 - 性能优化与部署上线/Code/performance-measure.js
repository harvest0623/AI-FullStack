/**
 * performance-measure.js - 性能测量工具与事件循环阻塞对比
 * ------------------------------------------------------------
 * 运行: node performance-measure.js
 *
 * 演示内容:
 *   1. 用 console.time / performance.now / process.memoryUsage / process.cpuUsage
 *      测量同一段代码, 理解各工具的适用场景
 *   2. 对比 "同步长循环" vs "setImmediate 分片异步" 对事件循环的影响:
 *      - 同步循环期间, 定时器(setInterval)完全无法触发 → 事件循环被阻塞
 *      - 分片循环每完成一小块就 setImmediate 让出, 定时器能正常触发
 * ------------------------------------------------------------
 */

'use strict';

const { performance } = require('perf_hooks');

// ============================================================
// 一、四种测量工具速览
// ============================================================

// 1) console.time / console.timeEnd —— 最简单, 适合快速粗测
console.time('console.time 范围');
for (let i = 0; i < 1_000_000; i++) { /* 占位空循环 */ }
console.timeEnd('console.time 范围');

// 2) performance.now —— 毫秒级浮点, 适合精确对比两段代码
const t0 = performance.now();
for (let i = 0; i < 1_000_000; i++) { /* 占位空循环 */ }
const t1 = performance.now();
console.log(`performance.now 测量: ${(t1 - t0).toFixed(3)} ms`);

// 3) process.cpuUsage —— 测 CPU 占用(user 用户态 + system 内核态, 单位微秒)
//    返回 { user, system }, 调用时传一个基线值得到差值
const cpuBase = process.cpuUsage();
for (let i = 0; i < 1_000_000; i++) { /* 占位空循环 */ }
const cpuDiff = process.cpuUsage(cpuBase);
console.log(
  `process.cpuUsage: user=${(cpuDiff.user / 1000).toFixed(2)}ms ` +
  `system=${(cpuDiff.system / 1000).toFixed(2)}ms`
);

// 4) process.memoryUsage —— 测内存占用, 重点看 heapUsed(堆已用) 与 rss(常驻集)
//    生产监控内存泄漏的核心指标
function showMemory(tag) {
  const m = process.memoryUsage();
  console.log(
    `[内存 ${tag}] rss=${(m.rss / 1024 / 1024).toFixed(1)}MB ` +
    `heapUsed=${(m.heapUsed / 1024 / 1024).toFixed(1)}MB ` +
    `heapTotal=${(m.heapTotal / 1024 / 1024).toFixed(1)}MB ` +
    `external=${(m.external / 1024 / 1024).toFixed(1)}MB`
  );
}
showMemory('基线');

console.log('\n----------------------------------------');

// ============================================================
// 二、事件循环阻塞对比: 同步循环 vs setImmediate 分片
// ============================================================
// 思路: 同时启动一个每 50ms 打印一次的 setInterval 作为"事件循环探针".
//   - 同步循环跑 500ms 期间, 探针完全沉默 → 事件循环被阻塞
//   - 分片循环每跑一小块就 setImmediate 让出, 探针能持续触发 → 不阻塞
// ============================================================

function syncHeavyTask(iterations) {
  // 纯 CPU 同步计算, 占满事件循环
  let sum = 0;
  for (let i = 0; i < iterations; i++) sum += Math.sqrt(i);
  return sum;
}

// 把大任务切成小块, 每块跑完用 setImmediate 让出事件循环, 再继续下一块
function chunkedHeavyTask(iterations, chunkSize) {
  return new Promise((resolve) => {
    let i = 0;
    let sum = 0;

    function runChunk() {
      const end = Math.min(i + chunkSize, iterations);
      for (; i < end; i++) sum += Math.sqrt(i);

      if (i < iterations) {
        // 关键: setImmediate 把控制权交回事件循环, 让定时器/IO 有机会执行
        setImmediate(runChunk);
      } else {
        resolve(sum);
      }
    }
    runChunk();
  });
}

async function compare() {
  const ITERATIONS = 8_000_000;
  const CHUNK = 500_000; // 每片大小, 越小越"流畅"但总耗时略增

  // ---- 场景 A: 同步阻塞 ----
  console.log('场景 A: 同步长循环 (阻塞事件循环)');
  let probeCountA = 0;
  const probeA = setInterval(() => {
    probeCountA++;
    process.stdout.write('·'); // 探针触发标记
  }, 50);

  const a0 = performance.now();
  const sumA = syncHeavyTask(ITERATIONS);
  const a1 = performance.now();
  clearInterval(probeA);

  console.log(`\n  耗时: ${(a1 - a0).toFixed(1)}ms, 探针触发 ${probeCountA} 次`);
  console.log('  → 探针几乎没触发, 说明事件循环被同步任务"卡住"了\n');

  // ---- 场景 B: setImmediate 分片 ----
  console.log('场景 B: setImmediate 分片 (让出事件循环)');
  let probeCountB = 0;
  const probeB = setInterval(() => {
    probeCountB++;
    process.stdout.write('·');
  }, 50);

  const b0 = performance.now();
  const sumB = await chunkedHeavyTask(ITERATIONS, CHUNK);
  const b1 = performance.now();
  clearInterval(probeB);

  console.log(`\n  耗时: ${(b1 - b0).toFixed(1)}ms, 探针触发 ${probeCountB} 次`);
  console.log('  → 探针持续触发, 说明事件循环没有被独占\n');

  // 校验两种算法结果一致 (浮点误差内)
  console.log(`结果校验: sumA=${sumA.toFixed(2)}, sumB=${sumB.toFixed(2)}, 一致=${sumA === sumB}`);

  console.log('\n----------------------------------------');
  console.log('结论:');
  console.log('  · 同步 CPU 密集任务会独占事件循环, 期间所有 IO/定时器/请求都排队等待');
  console.log('  · 用 setImmediate 分片能让出控制权, 代价是总耗时略增');
  console.log('  · 真正的 CPU 密集任务(图像处理/加密/大模型预处理)建议交给 worker_threads 或子进程');

  showMemory('结束');
}

compare();
