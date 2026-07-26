'use strict';

/**
 * Day05 - Promise 合并器（Combinators）对比
 * 主题：Promise.all / allSettled / race / any 的行为差异
 * 运行：node promise-combinators.js
 */

// 模拟 API：success 决定成功/失败，delay 决定延迟，value 决定成功值
function mockApi(name, { success = true, delay = 0, value = '' } = {}) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (success) {
        resolve(value || `${name}:OK`);
      } else {
        reject(new Error(`${name}:FAIL`));
      }
    }, delay);
  });
}

// 四个任务工厂：A、B 成功（不同延迟），C 失败，D 成功但最慢
const taskA = () => mockApi('A', { success: true, delay: 100, value: 'A-100ms' });
const taskB = () => mockApi('B', { success: true, delay: 200, value: 'B-200ms' });
const taskC = () => mockApi('C', { success: false, delay: 150 });
const taskD = () => mockApi('D', { success: true, delay: 300, value: 'D-300ms' });

(async () => {
  console.log('=== 1. Promise.all（全成才成，一败即败）===\n');

  // 1.1 全部成功
  try {
    const results = await Promise.all([taskA(), taskB(), taskD()]);
    console.log('  全部成功，结果（按原顺序）：', results);
  } catch (err) {
    console.log('  有失败：', err.message);
  }

  // 1.2 混入失败的 C
  try {
    await Promise.all([taskA(), taskC(), taskD()]);
  } catch (err) {
    console.log('  混入 C 后整体 reject：', err.message);
    console.log('  （注意：A、D 仍会跑完，只是结果被忽略——Promise 不可取消）');
  }

  console.log('\n=== 2. Promise.allSettled（永不失败，逐个汇报）===\n');
  const settled = await Promise.allSettled([taskA(), taskC(), taskD()]);
  settled.forEach((r, i) => {
    if (r.status === 'fulfilled') {
      console.log(`  [${i}] fulfilled →`, r.value);
    } else {
      console.log(`  [${i}] rejected  →`, r.reason.message);
    }
  });
  console.log('  结论：allSettled 永远 fulfilled，适合日志收集/批量上报。');

  console.log('\n=== 3. Promise.race（第一个敲定说了算，成败皆可）===\n');
  // 3.1 第一个敲定的是 A（100ms 成功）
  const raceWinner = await Promise.race([taskA(), taskB(), taskD()]);
  console.log('  race 结果（最快者）：', raceWinner);

  // 3.2 若第一个是失败？让 C（150ms 失败）跑赢 D（300ms 成功）
  try {
    await Promise.race([taskC(), taskD()]);
  } catch (err) {
    console.log('  race 第一个是失败时整体 reject：', err.message);
  }
  console.log('  结论：race 常用于超时控制与多源竞速。');

  console.log('\n=== 4. Promise.any（一成就成，全败才败 AggregateError）===\n');
  // 4.1 三个任务里只要有一个成功即可，取第一个成功
  const anyWinner = await Promise.any([taskC(), taskA(), taskD()]);
  console.log('  any 结果（第一个成功）：', anyWinner);

  // 4.2 全部失败时抛 AggregateError
  try {
    await Promise.any([taskC(), taskC(), taskC()]);
  } catch (err) {
    console.log('  any 全部失败 →', err.name, '（AggregateError）');
    console.log('  errors 数组长度：', err.errors.length);
    err.errors.forEach((e, i) => console.log(`    [${i}]`, e.message));
  }
  console.log('  结论：any 适合多镜像源抢答，容错性比 race 强。');

  console.log('\n=== 结论速查表 ===');
  console.log('  all        : 全成才成，一败即败（必须全成功的拼装场景）');
  console.log('  allSettled  : 永不失败，逐个汇报（日志/批量收集）');
  console.log('  race        : 第一个说了算，成败皆可（超时/竞速）');
  console.log('  any         : 一成就成，全败才败（多源抢答容错）');
})();
