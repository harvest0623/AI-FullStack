// Day08 - url 模块演示
// 主题：WHATWG URL 解析、URLSearchParams 操作、fileURLToPath 转 ESM 路径、相对 URL 解析
// 运行：node Code/url-demo.js
//
// 说明：本文件用 .js + CommonJS 风格演示，但 fileURLToPath 演示会构造一个 file: URL 模拟 ESM 场景；
// 真正的 ESM 文件应改成 .mjs 并用 import { fileURLToPath } from 'node:url'。

const { URL, URLSearchParams, fileURLToPath, pathToFileURL } = require('url');
const path = require('path');
const os = require('os');

console.log('========================================');
console.log(' Day08 - url 模块演示');
console.log('========================================\n');

// ---------------------------------------------------------------
// 1. WHATWG URL 解析
// ---------------------------------------------------------------
console.log('--- 1. new URL() 解析完整 URL ---');
const raw = 'https://user:pass@api.example.com:8080/v1/chat?q=gpt-4&top=0.7#section-2';
const u = new URL(raw);

console.log(`  href      : ${u.href}`);
console.log(`  origin    : ${u.origin}`);
console.log(`  protocol  : ${u.protocol}`);
console.log(`  username  : ${u.username}`);
console.log(`  password  : ${u.password}`);
console.log(`  host      : ${u.host}`);
console.log(`  hostname  : ${u.hostname}`);
console.log(`  port      : ${u.port}    ⚠️ 注意是字符串`);
console.log(`  pathname  : ${u.pathname}`);
console.log(`  search    : ${u.search}`);
console.log(`  hash      : ${u.hash}`);

// ---------------------------------------------------------------
// 2. URLSearchParams 操作
// ---------------------------------------------------------------
console.log('\n--- 2. URLSearchParams：增删改查 ---');
const sp = new URLSearchParams('a=1&b=2&a=3');
console.log(`  初始：${sp.toString()}`);
console.log(`  get('a')     = ${sp.get('a')}    ← 只取第一个`);
console.log(`  getAll('a')  = ${JSON.stringify(sp.getAll('a'))}`);
console.log(`  has('b')     = ${sp.has('b')}`);

sp.set('a', '9');                       // 覆盖所有同名
console.log(`  set('a','9') → ${sp.toString()}`);
sp.append('a', '0');                    // 追加
console.log(`  append('a','0') → ${sp.toString()}`);
sp.delete('b');
console.log(`  delete('b') → ${sp.toString()}`);

// 自动 URL 编码（中文与空格）
const sp2 = new URLSearchParams();
sp2.set('q', '中文 测试');
console.log(`  中文编码 → ${sp2.toString()}`);
console.log(`  中文解码 → ${sp2.get('q')}`);

// ---------------------------------------------------------------
// 3. 通过 URL 实例访问 searchParams（绑定关系）
// ---------------------------------------------------------------
console.log('\n--- 3. URL 与 searchParams 双向绑定 ---');
const api = new URL('https://api.example.com/v1/models');
api.searchParams.set('limit', '10');
api.searchParams.set('offset', '20');
console.log(`  最终 URL：${api.href}`);
console.log(`  search  ：${api.search}`);

// ---------------------------------------------------------------
// 4. 相对 URL 解析（new URL(rel, base)）
// ---------------------------------------------------------------
console.log('\n--- 4. 相对 URL 解析 ---');
const base = 'https://api.example.com/v1/chat/completions';
console.log(`  base = ${base}`);
console.log(`  new URL('/v2/x', base)        = ${new URL('/v2/x', base).href}`);
console.log(`  new URL('messages', base)     = ${new URL('messages', base).href}`);
console.log(`  new URL('../users', base)     = ${new URL('../users', base).href}`);
console.log(`  new URL('?foo=1', base)       = ${new URL('?foo=1', base).href}`);
console.log(`  new URL('#hash', base)        = ${new URL('#hash', base).href}`);

// 反面案例：相对 URL 必须给 base，否则抛错
try {
  new URL('relative/path');
} catch (err) {
  console.log(`  ⚠️ new URL('relative/path') 抛错：${err.code}`);
}

// ---------------------------------------------------------------
// 5. fileURLToPath / pathToFileURL：ESM 中的"__dirname"替代方案
// ---------------------------------------------------------------
console.log('\n--- 5. fileURLToPath / pathToFileURL ---');

// 构造当前文件的 file: URL（演示用，真实 ESM 文件里直接用 import.meta.url）
const currentFile = __filename;
const fileUrl = pathToFileURL(currentFile);
console.log(`  本地路径  : ${currentFile}`);
console.log(`  → file URL: ${fileUrl.href}`);

// 反向：file URL → 本地路径
const back = fileURLToPath(fileUrl);
console.log(`  → 转回路径: ${back}`);
console.log(`  往返一致：${back === currentFile}`);

// 模拟 ESM 中拿到 __dirname
const __dirname_ism = path.dirname(fileURLToPath(fileUrl));
console.log(`  模拟 ESM __dirname: ${__dirname_ism}`);

// Windows 盘符特殊处理演示
if (os.platform() === 'win32') {
  const winUrl = pathToFileURL('C:\\Users\\test\\app.mjs');
  console.log(`\n  Windows 路径 → file URL：`);
  console.log(`     C:\\Users\\test\\app.mjs  →  ${winUrl.href}`);
  console.log(`     ↑ 注意盘符前多了一个 /`);
}

// ---------------------------------------------------------------
// 6. 实战：拼装带签名的 API 请求 URL
// ---------------------------------------------------------------
console.log('\n--- 6. 实战：拼装带查询参数的请求 URL ---');

function buildApiURL(baseURL, params) {
  const u = new URL(baseURL);
  const sp = u.searchParams;
  for (const [k, v] of Object.entries(params)) {
    sp.append(k, String(v));
  }
  return u;
}

const req = buildApiURL('https://api.example.com/v1/chat/completions', {
  model: 'gpt-4',
  temperature: 0.7,
  stream: true,
});
console.log(`  最终请求 URL：${req.href}`);
console.log(`  pathname     ：${req.pathname}`);
console.log(`  searchParams：`);
for (const [k, v] of req.searchParams.entries()) {
  console.log(`     ${k} = ${v}`);
}

// ---------------------------------------------------------------
console.log('\n=== 要点回顾 ===');
console.log('  1. 新代码统一用 new URL()，不要再 url.parse()；');
console.log('  2. URLSearchParams 自带 URL 编解码，替代 querystring；');
console.log('  3. URL 与 searchParams 双向绑定，set/delete 会立即反映到 search 字段；');
console.log('  4. 相对 URL 解析必须给 base，否则抛 ERR_INVALID_URL；');
console.log('  5. ESM 中用 fileURLToPath(import.meta.url) 取代 __dirname，Windows 盘符也能正确处理。');
