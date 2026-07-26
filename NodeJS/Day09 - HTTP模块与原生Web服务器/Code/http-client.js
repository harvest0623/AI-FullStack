/**
 * Day09 - HTTP 模块与原生 Web 服务器
 * 文件：http-client.js
 * 主题：用 http.get / https.get 主动发起请求
 *
 * 演示：
 *   1. 用 https.get 请求公共 API（注意 HTTPS 要切到 https 模块）
 *   2. 响应也是 IncomingMessage（Readable 流），用 data/end 拼接
 *   3. 超时控制：req.setTimeout + req.destroy
 *   4. 错误事件：DNS 失败 / 连接拒绝 / 超时
 *   5. HTTP 4xx/5xx 不会自动触发 error 事件，需自己看 statusCode
 *
 * 运行：
 *   node Code/http-client.js
 */

'use strict';

const https = require('https');

const API_URL = 'https://jsonplaceholder.typicode.com/users/1';
const TIMEOUT_MS = 3000;

/**
 * 封装一个"带超时与统一错误处理"的 GET JSON 函数
 * 返回 Promise，便于用 async/await 调用
 */
function getJSON(url, timeoutMs = 8000) {
  return new Promise((resolve, reject) => {
    // http/https 都用同一个 API：.get(url, callback)
    const req = https.get(url, (res) => {
      // HTTP 状态码非 2xx：不算成功，但要自己判断（不会自动触发 error）
      const { statusCode } = res;
      if (statusCode < 200 || statusCode >= 300) {
        // 消费掉响应体，否则 socket 不会被释放
        res.resume();
        reject(new Error(`HTTP ${statusCode}`));
        return;
      }

      // 响应也是 Readable 流：data/end 事件收集 chunk
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        try {
          const text = Buffer.concat(chunks).toString('utf8');
          resolve(JSON.parse(text));
        } catch (err) {
          reject(new Error(`JSON 解析失败: ${err.message}`));
        }
      });
      res.on('error', reject);
    });

    // 超时控制：setTimeout 触发后必须手动 destroy，
    // 否则 socket 还会挂着，请求并不会真的中止
    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error(`请求超时（${timeoutMs}ms）`));
    });

    // 网络层错误（DNS、连接拒绝、destroy 抛出的错误）都走这里
    req.on('error', (err) => reject(err));
  });
}

async function main() {
  console.log('=== 1. 正常请求 ===');
  try {
    const user = await getJSON(API_URL, TIMEOUT_MS);
    console.log('  用户名：', user.name);
    console.log('  邮箱：', user.email);
    console.log('  公司：', user.company.name);
  } catch (err) {
    console.error('  失败：', err.message);
  }

  console.log('\n=== 2. 404 演示：接口不存在 ===');
  try {
    await getJSON('https://jsonplaceholder.typicode.com/users/999999', TIMEOUT_MS);
  } catch (err) {
    // 期望：HTTP 404（我们自己 reject 的，不是网络层错误）
    console.log('  按预期捕获：', err.message);
  }

  console.log('\n=== 3. 超时演示（超时设为 1ms）===');
  try {
    await getJSON(API_URL, 1);
  } catch (err) {
    // 期望：超时被 destroy，触发 error 事件
    console.log('  按预期捕获：', err.message);
  }

  console.log('\n=== 4. DNS 错误演示（域名不存在）===');
  try {
    await getJSON('https://this-domain-does-not-exist-xxxx.com', 3000);
  } catch (err) {
    // 期望：getaddrinfo ENOTFOUND
    console.log('  按预期捕获：', err.message);
  }

  console.log('\n=== 全部完成 ===');
  console.log('要点回顾：');
  console.log('  1. http/https 模块：URL 是 https:// 必须用 https 模块');
  console.log('  2. 响应是 Readable 流，用 data/end 拼 Buffer');
  console.log('  3. setTimeout 触发后必须手动 req.destroy，否则 socket 不会断');
  console.log('  4. HTTP 4xx/5xx 不会自动触发 error 事件，需自己看 statusCode');
  console.log('  5. 网络层错误（DNS、超时、连接拒绝）走 req.on("error")');
}

main();
