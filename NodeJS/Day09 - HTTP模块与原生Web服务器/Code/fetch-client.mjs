/**
 * Day09 - HTTP 模块与原生 Web 服务器
 * 文件：fetch-client.mjs
 * 主题：用 Node 18+ 原生 fetch 实现与 http-client.js 相同的功能，对比写法
 *
 * 对比要点：
 *   - http.get：回调/事件风格，手动拼 Buffer、手动 setTimeout+destroy
 *   - fetch：Promise 风格，async/await 直读，超时用 AbortController
 *
 * 运行：
 *   node Code/fetch-client.mjs
 *
 * 注意：本文件是 .mjs（ESM），可直接使用顶层 await。
 * 若改成 .cjs 或在 CommonJS 项目里，顶层 await 会报 SyntaxError，
 * 需要用 (async () => {...})() 包裹。
 */

const API_URL = 'https://jsonplaceholder.typicode.com/users/1';

// ---------------------------------------------------------------
// 工具：给任意 fetch 加超时
// - AbortController 是真正能取消 fetch 的机制
// - 取消后 fetch 会 reject 一个 AbortError
// ---------------------------------------------------------------
async function fetchJSON(url, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, { signal: controller.signal });

    // fetch 不会因 4xx/5xx 自动 reject，需手动检查 res.ok
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    // res.json() 是 Promise，内部会自动按 Content-Type 解析
    return await res.json();
  } finally {
    // 主请求完成（无论成败）后清掉定时器，避免悬挂
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------
// 主流程：顶层 await（仅 ESM 支持）
// ---------------------------------------------------------------
console.log('=== 1. 正常请求 ===');
try {
  const user = await fetchJSON(API_URL, 3000);
  console.log('  用户名：', user.name);
  console.log('  邮箱：', user.email);
  console.log('  公司：', user.company.name);
} catch (err) {
  console.error('  失败：', err.message);
}

console.log('\n=== 2. 404 演示：接口不存在 ===');
try {
  await fetchJSON('https://jsonplaceholder.typicode.com/users/999999', 3000);
} catch (err) {
  console.log('  按预期捕获：', err.message);
}

console.log('\n=== 3. 超时演示（超时设为 1ms）===');
try {
  await fetchJSON(API_URL, 1);
} catch (err) {
  // fetch 被 abort 时 err.name === 'AbortError'，message 是 'This operation was aborted'
  console.log('  按预期捕获：', err.name, '-', err.message);
}

console.log('\n=== 4. DNS 错误演示（域名不存在）===');
try {
  await fetchJSON('https://this-domain-does-not-exist-xxxx.com', 3000);
} catch (err) {
  // fetch 在 DNS 失败时会 reject 一个 TypeError，cause 里有 getaddrinfo ENOTFOUND
  console.log('  按预期捕获：', err.name, '-', err.message);
  if (err.cause) console.log('    cause:', err.cause.code || err.cause.message);
}

console.log('\n=== 全部完成 ===');
console.log('要点回顾：');
console.log('  1. Node 18+ 全局可用 fetch，API 与浏览器一致');
console.log('  2. res.ok 判断 2xx；4xx/5xx 不会自动 reject');
console.log('  3. res.json() / res.text() / res.blob() 都是 Promise');
console.log('  4. 超时用 AbortController，fetch 真正会被取消');
console.log('  5. DNS 等网络层错误 reject 一个 TypeError，细节在 err.cause');
console.log('  6. 与 http.get 相比：代码量减半，可读性显著提升');

console.log('\n--- 与 http-client.js 的代码量对比 ---');
console.log('  http.get  版本：约 60 行（含拼 Buffer / setTimeout / destroy / 错误分支）');
console.log('  fetch     版本：约 20 行（fetch + res.ok + res.json + AbortController）');
console.log('  生产建议：业务代码默认用 fetch；需要底层控制才回到 http 模块');
