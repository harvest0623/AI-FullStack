// process-demo.js - 演示 process 对象的核心属性、环境变量与信号处理
// 运行:
//   node process-demo.js
//   NODE_ENV=production node process-demo.js        (Linux/macOS 或 git bash)
//   cross-env NODE_ENV=production node process-demo.js   (跨平台推荐)
//   node process-demo.js --name=alice --age=18       (演示 argv)

console.log('=== 1. process 核心属性 ===');
console.log('process.version        :', process.version);
console.log('process.versions.node  :', process.versions.node);
console.log('process.platform       :', process.platform);   // win32 / linux / darwin
console.log('process.arch           :', process.arch);       // x64 / arm64
console.log('process.pid            :', process.pid);
console.log('process.ppid           :', process.ppid);
console.log('process.title          :', process.title);
console.log('process.cwd()          :', process.cwd());
console.log('process.uptime()       :', process.uptime(), 's');

console.log('\n=== 2. process.argv 命令行参数 ===');
// argv[0] = node 可执行文件路径
// argv[1] = 当前脚本路径
// argv[2..] = 自定义参数
console.log('argv:', process.argv);

// 简易参数解析：把 --name=alice 解析成 { name: 'alice' }
const args = process.argv.slice(2).reduce((acc, cur) => {
  const m = cur.match(/^--([^=]+)=(.*)$/);
  if (m) acc[m[1]] = m[2];
  return acc;
}, {});
console.log('解析后的参数:', args);

console.log('\n=== 3. process.env 环境变量 ===');
console.log('NODE_ENV :', process.env.NODE_ENV || '(未设置, 视为 development)');
console.log('PORT     :', process.env.PORT || '(未设置, 默认 3000)');
console.log('PATH 是否存在 :', 'PATH' in process.env);

// 演示为什么用 ?? 而非 ||：当 PORT=0 时 || 会误判
process.env.PORT_DEMO = '0';
console.log('用 || :', process.env.PORT_DEMO || 3000);   // 3000 ❌
console.log('用 ?? :', process.env.PORT_DEMO ?? 3000);   // '0'   ✅

console.log('\n=== 4. 内存与 CPU 使用情况 ===');
const mem = process.memoryUsage();
console.log('memoryUsage:');
console.log('  rss           :', (mem.rss / 1024 / 1024).toFixed(2), 'MB');
console.log('  heapTotal     :', (mem.heapTotal / 1024 / 1024).toFixed(2), 'MB');
console.log('  heapUsed      :', (mem.heapUsed / 1024 / 1024).toFixed(2), 'MB');
console.log('  external      :', (mem.external / 1024 / 1024).toFixed(2), 'MB');
console.log('  arrayBuffers  :', (mem.arrayBuffers / 1024 / 1024).toFixed(2), 'MB');

// cpuUsage 返回 { user, system }，单位微秒
const start = process.cpuUsage();
// 跑一段计算消耗点 CPU
let sum = 0;
for (let i = 0; i < 1e6; i++) sum += Math.sqrt(i);
const end = process.cpuUsage(start);
console.log('cpuUsage(本次计算):');
console.log('  user   :', end.user, 'μs');
console.log('  system :', end.system, 'μs');

console.log('\n=== 5. 标准流演示 ===');
// console.log 默认写到 process.stdout
process.stdout.write('用 process.stdout.write 写一行(不带换行)\n');
// console.error 默认写到 process.stderr
console.error('这条日志走 stderr（重定向时与 stdout 分离）');

console.log('\n=== 6. 退出与事件演示 ===');
// beforeExit: 事件循环空了，可以安排新异步任务
process.on('beforeExit', (code) => {
  console.log('[beforeExit] 事件循环为空，code =', code);
});
// exit: 进程即将真正退出，只能做同步清理
process.on('exit', (code) => {
  console.log('[exit] 进程退出，code =', code, '（此处不能安排异步任务）');
});

console.log('\n=== 7. 信号处理（SIGINT 优雅退出演示）===');
let shuttingDown = false;

async function gracefulShutdown(signal) {
  if (shuttingDown) {
    // 第二次 Ctrl+C：用户不耐烦，强退
    console.log('\n收到第二次信号，立即强制退出');
    process.exit(130);
    return;
  }
  shuttingDown = true;
  console.log(`\n收到 ${signal}，开始清理资源...`);
  // 模拟清理：关闭连接、flush 日志、终止子进程等
  await new Promise((r) => setTimeout(r, 500));
  console.log('清理完成，优雅退出');
  process.exit(0);
}

// Ctrl+C 在所有平台都可靠
process.on('SIGINT', () => gracefulShutdown('SIGINT'));
// SIGTERM: Linux 容器停止时发送；Windows 上行为弱化但保留监听
if (process.platform !== 'win32') {
  process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
}

console.log('程序运行中。按 Ctrl+C 触发 SIGINT 优雅退出演示。');
console.log('或等待 3 秒自动结束（演示 beforeExit / exit 事件）...');

// 3 秒后自动让事件循环变空，触发 beforeExit
setTimeout(() => {
  console.log('\n[定时器] 3 秒到，没有其他任务了，即将退出。');
}, 3000);

// 如果想立即测试 SIGINT，可以注释掉上面的 setTimeout，让程序一直挂着等信号
