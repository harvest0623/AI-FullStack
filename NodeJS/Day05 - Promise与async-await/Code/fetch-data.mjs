// Day05 - 原生 fetch + 超时控制演示
// 主题：Node 18+ 内置 fetch、async/await 处理 JSON、错误处理、Promise.race 超时、AbortController 取消、顶层 await
// 运行：node fetch-data.mjs
//
// 说明：本文件为 .mjs（ESM），可直接使用顶层 await；
// 若改成 .cjs 或在 CommonJS 项目里，顶层 await 会报 SyntaxError，需用 (async () => {...})() 包裹。

// 顶层 await（仅 ESM 支持）：在模块顶层直接 await
const API_BASE = 'https://jsonplaceholder.typicode.com';
console.log('--- 启动：已通过顶层 await 加载配置 ---');
console.log(`API_BASE = ${API_BASE}\n`);

// ---------------------------------------------------------------
// 工具函数：给任意 Promise 加超时（Promise.race + setTimeout）
// 同时通过 AbortController 真正取消底层 fetch 请求
// ---------------------------------------------------------------
function withTimeout(promise, ms, controller) {
  const timeout = new Promise((_, reject) => {
    const id = setTimeout(() => {
      // 触发 abort，让正在进行的 fetch 中止（fetch 原生支持 signal）
      if (controller) controller.abort();
      reject(new Error(`请求超时（${ms}ms）`));
    }, ms);
    // 主 Promise 敲定后清掉定时器，避免无谓的定时器挂载
    promise.finally(() => clearTimeout(id));
  });
  // race：谁先敲定用谁的结果；超时 Promise 先 reject 则整体 reject
  return Promise.race([promise, timeout]);
}

// ---------------------------------------------------------------
// 封装：带超时与统一错误处理的 fetch JSON
// ---------------------------------------------------------------
async function fetchJSON(url, { timeout = 8000 } = {}) {
  const controller = new AbortController();
  const request = fetch(url, { signal: controller.signal }).then(res => {
    // HTTP 状态码非 2xx 视为失败（fetch 不会自动 reject 4xx/5xx）
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    return res.json();
  });
  return withTimeout(request, timeout, controller);
}

// ---------------------------------------------------------------
// 1. 正常请求单个资源
// ---------------------------------------------------------------
try {
  console.log('--- 1. 请求用户信息（超时 8s）---');
  const user = await fetchJSON(`${API_BASE}/users/1`);
  console.log('  用户名：', user.name);
  console.log('  邮箱：', user.email);
} catch (err) {
  console.error('  请求失败：', err.message);
}

// ---------------------------------------------------------------
// 2. 并发请求多个资源（Promise.all）
// ---------------------------------------------------------------
try {
  console.log('\n--- 2. 并发请求 3 篇帖子 ---');
  const ids = [1, 2, 3];
  const posts = await Promise.all(
    ids.map(id => fetchJSON(`${API_BASE}/posts/${id}`))
  );
  posts.forEach(p => console.log(`  帖子 ${p.id}: ${p.title}`));
} catch (err) {
  console.error('  并发请求失败：', err.message);
}

// ---------------------------------------------------------------
// 3. 超时演示：故意设置极短超时（1ms），观察 try/catch 捕获
// ---------------------------------------------------------------
try {
  console.log('\n--- 3. 超时演示（超时设为 1ms）---');
  await fetchJSON(`${API_BASE}/users/1`, { timeout: 1 });
} catch (err) {
  console.error('  按预期捕获到：', err.message);
}

// ---------------------------------------------------------------
// 4. HTTP 错误状态码演示（404）
// ---------------------------------------------------------------
try {
  console.log('\n--- 4. 404 错误演示 ---');
  await fetchJSON(`${API_BASE}/users/does-not-exist`);
} catch (err) {
  console.error('  按预期捕获到：', err.message);
}

// ---------------------------------------------------------------
// 5. allSettled 容错批量请求（部分失败不影响整体）
// ---------------------------------------------------------------
console.log('\n--- 5. allSettled 批量请求（含一个故意失败的）---');
const batchResults = await Promise.allSettled([
  fetchJSON(`${API_BASE}/posts/1`),
  fetchJSON(`${API_BASE}/posts/does-not-exist`), // 404
  fetchJSON(`${API_BASE}/posts/2`),
]);
batchResults.forEach((r, i) => {
  if (r.status === 'fulfilled') {
    console.log(`  [${i}] 成功：帖子 ${r.value.id}`);
  } else {
    console.log(`  [${i}] 失败：${r.reason.message}`);
  }
});

console.log('\n=== 全部完成 ===');
console.log('要点回顾：');
console.log('  1. Node 18+ 内置 fetch，无需 npm install node-fetch');
console.log('  2. Promise.race + setTimeout 实现超时控制；');
console.log('  3. AbortController 可真正取消 fetch（普通自定义 Promise 无法取消，race 落败任务仍会跑完）；');
console.log('  4. fetch 不会因 4xx/5xx 自动 reject，需手动检查 res.ok；');
console.log('  5. 顶层 await 仅 ESM 支持，CommonJS 需用 IIFE 包裹。');
