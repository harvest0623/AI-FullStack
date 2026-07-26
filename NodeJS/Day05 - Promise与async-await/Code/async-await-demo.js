'use strict';

/**
 * Day05 - async/await 串行请求演示
 * 主题：async 函数返回值、await 暂停语义、try/catch、串行编排
 * 运行：node async-await-demo.js
 */

// 模拟异步接口：根据 id 获取用户，可选失败
function fetchUser(id, { fail = false, delay = 100 } = {}) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (fail) return reject(new Error(`用户 ${id} 不存在`));
      resolve({ id, name: `用户${id}`, delay });
    }, delay);
  });
}

// 模拟根据用户 id 获取其订单
function fetchOrders(userId, delay = 100) {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve([
        { orderId: `${userId}-1`, amount: 100 },
        { orderId: `${userId}-2`, amount: 200 },
      ]);
    }, delay);
  });
}

// ---------------------------------------------------------------
// 1. async 函数永远返回 Promise
// ---------------------------------------------------------------
async function returnDemo() {
  return 42; // 等价于 return Promise.resolve(42)
}
returnDemo().then(v => console.log('[返回值] async 函数 return 42 →', v));

async function throwDemo() {
  throw new Error('async 内 throw 变成 rejected');
}
throwDemo().catch(e => console.log('[返回值] async 内 throw →', e.message));

// ---------------------------------------------------------------
// 2. await 暂停语义：只暂停当前函数，不阻塞主线程
// ---------------------------------------------------------------
async function pauseDemo() {
  console.log('[暂停] 1. 函数开始（同步）');
  await fetchUser(1, { delay: 50 }); // 让出控制权，事件循环去忙别的
  console.log('[暂停] 3. 恢复执行（约 50ms 后）');
}
console.log('[暂停] 0. 调用 pauseDemo 前');
pauseDemo();
console.log('[暂停] 2. 调用后（主线程同步代码继续往下走）');

// ---------------------------------------------------------------
// 3. try/catch 捕获 await 错误
// ---------------------------------------------------------------
async function tryCatchDemo() {
  try {
    const user = await fetchUser(999, { fail: true });
    console.log('  不会执行到这里', user);
  } catch (err) {
    console.log('[try/catch] 捕获到：', err.message);
    return null; // 兜底返回，调用方拿到 null 而非 rejection
  }
}
tryCatchDemo().then(v => console.log('[try/catch] 最终值：', v));

// ---------------------------------------------------------------
// 4. 串行流程：先拿用户，再拿订单（存在依赖，只能串行）
// ---------------------------------------------------------------
async function serialFlow() {
  console.log('\n--- 串行流程开始 ---');
  const t0 = Date.now();

  const user = await fetchUser(1, { delay: 100 });
  console.log(`  拿到用户：${user.name}（耗时 ${Date.now() - t0}ms）`);

  const orders = await fetchOrders(user.id, 150); // 依赖 user.id
  console.log(`  拿到订单：${JSON.stringify(orders)}（累计 ${Date.now() - t0}ms）`);

  return { user, orders };
}
serialFlow().then(data =>
  console.log(`  串行完成：${data.user.name}，订单数 ${data.orders.length}`)
);

// ---------------------------------------------------------------
// 5. 串行循环：依次处理多个用户（for...of + await）
// ---------------------------------------------------------------
async function processUsers(ids) {
  const results = [];
  for (const id of ids) {
    const user = await fetchUser(id, { delay: 80 }); // 一个接一个
    results.push(user.name);
  }
  return results;
}
processUsers([1, 2, 3]).then(names =>
  console.log('[串行循环] 依次处理结果：', names)
);

// ---------------------------------------------------------------
// 6. 对比：错误的 forEach + await 反模式（不会等待）
// ---------------------------------------------------------------
async function wrongForEach() {
  const ids = [1, 2, 3];
  console.log('\n[反模式] forEach 内 await 不会等待：');
  // forEach 不会等待 async 回调，下面三行几乎同时触发，且无法保证顺序
  ids.forEach(async id => {
    const user = await fetchUser(id, { delay: 50 });
    console.log(`  forEach 拿到：${user.name}（顺序可能乱）`);
  });
  console.log('  forEach 已返回（任务还没完成就打印了这行）');
}
wrongForEach();

console.log('\n（以上为异步任务，将在约 300ms 内陆续输出）\n');
