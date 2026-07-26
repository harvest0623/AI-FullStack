'use strict';

/**
 * Day05 - Promise 基础演示
 * 主题：手动创建 Promise、三种状态、状态不可逆、then 链、catch/finally
 * 运行：node promise-basic.js
 */

console.log('=== 1. Promise 三种状态：pending → fulfilled / rejected ===\n');

// 1.1 pending → fulfilled
const p1 = new Promise((resolve, reject) => {
  console.log('[p1] 执行器是【同步】执行的，此刻状态为 pending');
  setTimeout(() => {
    resolve('p1 成功的结果');
    // 状态已变为 fulfilled，下面两行都会被静默忽略（验证不可逆）
    reject(new Error('p1 想反悔为失败'));
    resolve('p1 想改第二次值');
  }, 100);
});

p1.then(
  value => console.log('[p1] then 成功回调：', value),
  reason => console.log('[p1] then 失败回调：', reason.message)
);

// 1.2 pending → rejected
const p2 = new Promise((resolve, reject) => {
  setTimeout(() => reject(new Error('p2 主动失败')), 100);
});

p2.then(
  () => console.log('[p2] 不会走到这里'),
  reason => console.log('[p2] then 失败回调：', reason.message)
);

console.log('\n=== 2. 状态不可逆验证 ===\n');
// resolve 之后再 reject / 再 resolve，都不会生效
const p3 = new Promise(resolve => {
  resolve('第一次值');                    // 生效
  resolve('第二次值');                    // 忽略
  // reject 在已 fulfilled 后调用也会被忽略
  Promise.resolve().then(() => { /* 模拟异步 */ });
});
p3.then(v => console.log('[p3] 最终值永远是：', v)); // "第一次值"

console.log('\n=== 3. then 链式调用原理（then 返回新 Promise）===\n');
// 演示：返回普通值 → 新 Promise fulfilled；返回 Promise → adopt 其状态
const p4 = new Promise(resolve => resolve(1));
const p5 = p4.then(v => v + 1);
console.log('[链] p4 === p5 ?', p4 === p5, '（说明 then 返回的是新 Promise）');

p4
  .then(v => {
    console.log('[链] 第一步收到：', v);
    return v + 1;                         // 返回普通值
  })
  .then(v => {
    console.log('[链] 第二步收到：', v);
    return new Promise(resolve =>         // 返回 Promise，会被 adopt
      setTimeout(() => resolve(v * 10), 100)
    );
  })
  .then(v => {
    console.log('[链] 第三步收到：', v);  // 等待内部 Promise resolve 后才执行
  });

console.log('\n=== 4. catch 与 finally、错误冒泡 ===\n');
// 错误会沿链向下冒泡，直到遇到 catch
new Promise((_, reject) => reject(new Error('链首抛错')))
  .then(() => console.log('（跳过）第一环成功回调'))
  .then(() => console.log('（跳过）第二环成功回调'))
  .catch(err => {
    console.log('[catch] 捕获到错误：', err.message);
    return '兜底值';                      // catch 返回值会让链恢复为 fulfilled
  })
  .finally(() => console.log('[finally] 无论成败都会执行，且不改变传递的值'))
  .then(v => console.log('[链恢复] 最终值：', v));

console.log('\n=== 5. throw 也会让 Promise 变为 rejected ===\n');
new Promise(resolve => resolve('start'))
  .then(v => {
    throw new Error(`处理 ${v} 时炸了`);  // then 回调里 throw → 新 Promise rejected
  })
  .catch(err => console.log('[catch] 捕获 throw：', err.message));

console.log('\n（以上异步任务将在约 200ms 内陆续输出）\n');
