'use strict';

/**
 * Day07 - 三种 fs API 风格对比
 * 主题：同步 / 回调 / Promise(fs/promises) 读取同一文件，演示推荐用 fs/promises
 * 运行：node sync-vs-async.js
 *
 * 要点：
 *   1. xxxSync：阻塞主线程，仅限启动期/脚本工具
 *   2. 回调式：错误优先，旧代码常见
 *   3. fs/promises：配合 async/await，新项目首选
 */

const fs = require('fs');
const fsp = require('fs/promises');
const path = require('path');

// ---------------------------------------------------------------
// 准备测试文件：用 __dirname 拼接绝对路径，避免依赖 process.cwd()
// ---------------------------------------------------------------
const sampleFile = path.join(__dirname, 'sample.txt');
const missingFile = path.join(__dirname, 'definitely-not-exist-' + Date.now() + '.txt');

fs.writeFileSync(
  sampleFile,
  [
    'Hello, fs module!',
    '面向从前端转向 AI 全栈的工程师',
    '这一行用来演示三种 API 风格读取同一个文件。',
    ''
  ].join('\n'),
  'utf8'
);

console.log('测试文件路径:', sampleFile);
console.log('process.cwd():', process.cwd());
console.log('__dirname    :', __dirname);
console.log('-----------------------------------\n');

// ---------------------------------------------------------------
// ① 同步：readFileSync —— 阻塞，简单直接
// 适用：进程启动期加载配置、CLI 工具
// 禁忌：HTTP 请求处理函数内绝对不要用
// ---------------------------------------------------------------
function readSync() {
  console.log('[1] 同步 readFileSync');
  try {
    const data = fs.readFileSync(sampleFile, 'utf8');
    console.log('  读取成功，前 20 字符:', JSON.stringify(data.slice(0, 20)));
  } catch (err) {
    // 同步 API 用 try/catch 捕获
    console.error('  同步读取出错:', err.code, '-', err.message);
  }

  // 故意读不存在的文件，观察错误形态
  try {
    fs.readFileSync(missingFile, 'utf8');
  } catch (err) {
    console.log('  读不存在文件 -> err.code:', err.code); // ENOENT
  }
  console.log('');
}

// ---------------------------------------------------------------
// ② 回调式：readFile —— 错误优先回调 (err, data)
// 适用：旧代码维护；新代码不再推荐
// ---------------------------------------------------------------
function readCallback() {
  console.log('[2] 回调式 readFile');
  fs.readFile(sampleFile, 'utf8', (err, data) => {
    // 回调约定：第一个参数永远是 err，需要每层手动判断
    if (err) {
      console.error('  回调读取出错:', err.code, '-', err.message);
      return;
    }
    console.log('  读取成功，前 20 字符:', JSON.stringify(data.slice(0, 20)));
  });

  // 故意读不存在的文件
  fs.readFile(missingFile, 'utf8', (err, data) => {
    if (err) {
      console.log('  读不存在文件 -> err.code:', err.code); // ENOENT
    }
  });

  // 注意：回调是异步的，下面这行会先于回调打印
  console.log('  (回调已发起，等待 I/O 完成...)');
  console.log('');
}

// ---------------------------------------------------------------
// ③ Promise：fs/promises —— 配合 async/await
// 适用：新项目首选，可与 Promise.all 组合做并发
// ---------------------------------------------------------------
async function readPromise() {
  console.log('[3] Promise fs/promises');
  try {
    const data = await fsp.readFile(sampleFile, 'utf8');
    console.log('  读取成功，前 20 字符:', JSON.stringify(data.slice(0, 20)));
  } catch (err) {
    // 与同步一样用 try/catch，但不会阻塞主线程
    console.error('  Promise 读取出错:', err.code, '-', err.message);
  }

  // 故意读不存在的文件
  try {
    await fsp.readFile(missingFile, 'utf8');
  } catch (err) {
    console.log('  读不存在文件 -> err.code:', err.code); // ENOENT
  }
  console.log('');
}

// ---------------------------------------------------------------
// ④ 进阶对比：用 Promise.all 并发读取多个文件
// 这是 fs/promises 配合 async/await 的真正威力
// ---------------------------------------------------------------
async function readMultipleConcurrent() {
  console.log('[4] Promise.all 并发读取多个文件');
  const files = ['sample.txt', 'sample.txt', 'sample.txt'].map(name =>
    path.join(__dirname, name)
  );

  const t0 = Date.now();
  // 三个 readFile 同时发起，等最慢的那个
  const contents = await Promise.all(
    files.map(f => fsp.readFile(f, 'utf8'))
  );
  const cost = Date.now() - t0;
  console.log(`  并发读了 ${contents.length} 个文件，耗时 ${cost}ms`);
  console.log('');
}

// ---------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------
(async () => {
  readSync();        // 同步立即执行
  readCallback();    // 回调式异步发起
  await readPromise();
  await readMultipleConcurrent();

  // 清理测试文件
  try {
    await fsp.unlink(sampleFile);
    console.log('已清理测试文件 sample.txt');
  } catch (err) {
    /* 忽略 */
  }

  console.log('\n=== 结论 ===');
  console.log('1. 同步 xxxSync 阻塞主线程，仅用于启动脚本/CLI 工具；');
  console.log('   HTTP 处理函数内一律禁用。');
  console.log('2. 回调式是历史包袱，新代码不要再用。');
  console.log('3. fs/promises 配合 async/await 是新项目首选：');
  console.log('   - 不阻塞、可读性好、try/catch 统一错误处理；');
  console.log('   - 能与 Promise.all 等合并器组合做并发批量 I/O。');
})();
