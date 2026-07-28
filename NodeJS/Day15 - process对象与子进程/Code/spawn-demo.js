// spawn-demo.js - 用 spawn 执行系统命令，流式读取 stdout/stderr，对比 stdio 选项
// 运行:
//   node spawn-demo.js
//   node spawn-demo.js inherit     (演示 stdio: 'inherit')
//   node spawn-demo.js ignore      (演示 stdio: 'ignore')

const { spawn } = require('child_process');

const isWin = process.platform === 'win32';

// 跨平台列目录命令
//   Windows: cmd /c dir       (dir 是 cmd 内建，需通过 cmd 调用)
//   Linux/macOS: ls -la
const LIST_CMD = isWin ? 'cmd' : 'ls';
const LIST_ARGS = isWin ? ['/c', 'dir'] : ['-la'];

console.log('当前平台:', process.platform, '| 命令:', LIST_CMD, LIST_ARGS.join(' '));

// ---------------------------------------------------------------
// 示例 1：默认 stdio: 'pipe'，子进程的 stdout/stderr 是 Readable 流
// ---------------------------------------------------------------
function demoPipe() {
  console.log('\n=== 1. stdio: pipe（默认，流式读取）===');

  const child = spawn(LIST_CMD, LIST_ARGS);

  // child.stdout 是 Readable 流，逐块触发 'data' 事件
  // 适合输出可能很大、需要边读边处理的场景（如 ffmpeg 转码日志）
  let stdoutChunks = '';
  child.stdout.on('data', (chunk) => {
    stdoutChunks += chunk.toString();
    // 也可以边收边处理：解析进度条、提取关键日志等
  });

  child.stderr.on('data', (chunk) => {
    process.stderr.write(`[stderr] ${chunk}`);
  });

  child.on('error', (err) => {
    // 子进程无法启动（如命令不存在）时触发
    console.error('启动失败:', err.message);
  });

  // 'close' 事件：所有 stdio 流都已关闭（比 'exit' 更适合做收尾）
  child.on('close', (code, signal) => {
    console.log(`子进程退出 code=${code} signal=${signal || '(无)'}`);
    console.log('收集到的 stdout 前 200 字符:');
    console.log(stdoutChunks.slice(0, 200));
  });

  // 'exit' 事件：子进程本身已退出，但 stdio 可能还没读完
  child.on('exit', (code, signal) => {
    // 注意：拿 stdout 应该用 'close' 而不是 'exit'
  });
}

// ---------------------------------------------------------------
// 示例 2：stdio: 'inherit'，子进程直接复用父进程的终端
// ---------------------------------------------------------------
function demoInherit() {
  console.log('\n=== 2. stdio: inherit（子进程输出直达终端）===');

  const child = spawn(LIST_CMD, LIST_ARGS, {
    stdio: 'inherit' // stdin/stdout/stderr 都直接连到父进程
    // 此时 child.stdout / child.stderr 是 null，不能再 on('data')
  });

  child.on('close', (code) => {
    console.log(`(inherit 模式) 子进程退出 code=${code}`);
  });
}

// ---------------------------------------------------------------
// 示例 3：stdio: 'ignore'，丢弃所有输出
// ---------------------------------------------------------------
function demoIgnore() {
  console.log('\n=== 3. stdio: ignore（丢弃输出，相当于重定向到 /dev/null）===');

  const child = spawn(LIST_CMD, LIST_ARGS, {
    stdio: 'ignore',
    windowsHide: true // Windows 隐藏子进程窗口
  });

  child.on('close', (code) => {
    console.log(`(ignore 模式) 子进程退出 code=${code}，stdout 被丢弃`);
  });
}

// ---------------------------------------------------------------
// 示例 4：node --version，演示成功流式输出
// ---------------------------------------------------------------
function demoNodeVersion() {
  console.log('\n=== 4. 用 spawn 跑 node --version ===');
  const child = spawn(process.execPath, ['--version']);

  child.stdout.on('data', (chunk) => {
    console.log('node 版本:', chunk.toString().trim());
  });
  child.stderr.on('data', (chunk) => {
    console.error('stderr:', chunk.toString());
  });
  child.on('close', (code) => {
    console.log(`退出 code=${code}`);
  });
}

// ---------------------------------------------------------------
// 示例 5：用 Promise + spawn 封装，便于 await
// ---------------------------------------------------------------
function runSpawn(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'], ...opts });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (c) => (stdout += c));
    child.stderr.on('data', (c) => (stderr += c));
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) resolve({ code, stdout, stderr });
      else reject(new Error(`子进程退出码 ${code}: ${stderr || stdout}`));
    });
  });
}

async function demoPromise() {
  console.log('\n=== 5. Promise + spawn，便于 async/await 调用 ===');
  try {
    const { stdout } = await runSpawn(process.execPath, ['-e', 'console.log(1+1)']);
    console.log('子进程计算 1+1 =', stdout.trim());
  } catch (e) {
    console.error('失败:', e.message);
  }
}

// 根据命令行参数选择演示
const mode = process.argv[2];
(async () => {
  demoPipe();
  demoNodeVersion();
  if (mode === 'inherit') {
    demoInherit();
  } else if (mode === 'ignore') {
    demoIgnore();
  } else {
    console.log('\n(可加参数 inherit / ignore 查看其他 stdio 模式)');
  }
  await demoPromise();
})();
