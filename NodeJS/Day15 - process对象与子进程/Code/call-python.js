// call-python.js - 用 spawn 调用外部脚本，流式收集输出，含错误处理与超时
// 运行:
//   node call-python.js
//
// 默认调用的是 node 本身（确保跨平台可演示）。
// 真实场景只需把 CMD / ARGS 替换为:
//   python infer.py <imagePath>     (AI 推理)
//   ffmpeg -i in.mp4 out.mp4         (视频转码)
//   node puppeteer-shot.js <url>     (无头浏览器截图)

const { spawn } = require('child_process');

// ---------------------------------------------------------------
// 真实场景示例（注释保留，按需切换）:
//   const CMD = 'python';
//   const ARGS = ['infer.py', imagePath];
//
//   const CMD = 'ffmpeg';
//   const ARGS = ['-i', 'in.mp4', '-vcodec', 'libx264', 'out.mp4'];
//
//   const CMD = process.execPath; // node 可执行文件
//   const ARGS = ['puppeteer-shot.js', url];
// ---------------------------------------------------------------

// 为了让本文件"开箱即跑"，这里用 node -e 执行一段 JS 模拟外部脚本
const CMD = process.execPath;
const ARGS = ['-e', `
  // 模拟一个会逐步产生输出的"推理脚本"
  process.stdout.write('loading model...\\n');
  setTimeout(() => process.stdout.write('model ready\\n'), 200);
  setTimeout(() => process.stdout.write('inference: 0.92\\n'), 500);
  setTimeout(() => {
    // 模拟偶尔会输出 stderr 日志
    process.stderr.write('[warn] low confidence on sample 3\\n');
    process.stdout.write(JSON.stringify({ label: 'cat', score: 0.92 }) + '\\n');
    process.exit(0);
  }, 800);
`];

/**
 * 用 spawn 调用外部命令，流式收集 stdout/stderr，支持超时
 * @param {string} cmd  可执行文件
 * @param {string[]} args  参数数组(避免命令注入)
 * @param {object} opts  { timeout, cwd, env }
 * @returns {Promise<{code:number, stdout:string, stderr:string}>}
 */
function runExternal(cmd, args, opts = {}) {
  const { timeout = 5000, cwd, env } = opts;

  return new Promise((resolve, reject) => {
    // spawn 不走 shell，args 作为 argv 单独传，避免注入
    const child = spawn(cmd, args, {
      cwd,
      env: env || process.env,
      stdio: ['ignore', 'pipe', 'pipe'], // stdin 不需要
      windowsHide: true
    });

    let stdout = '';
    let stderr = '';
    let timer = null;
    let killed = false;

    // 流式收集：输出可能很大时，可改为边收边处理（如解析进度条）
    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
      // 也可以边输出边解析，例如:
      //   chunk.toString().split('\n').forEach(line => parseProgress(line))
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    // 超时处理: 到点发送 SIGTERM，再等几秒不退则 SIGKILL
    if (timeout > 0) {
      timer = setTimeout(() => {
        killed = true;
        console.warn(`[call-python] 超时 ${timeout}ms，发送 SIGTERM`);
        child.kill('SIGTERM');
        // 给 1 秒优雅退出时间，否则强杀
        setTimeout(() => {
          if (!child.killed) {
            console.warn('[call-python] SIGTERM 后仍未退出，发送 SIGKILL');
            child.kill('SIGKILL');
          }
        }, 1000);
      }, timeout);
    }

    const cleanup = () => {
      if (timer) clearTimeout(timer);
    };

    // 'error' 事件: 子进程无法启动（如命令不存在）
    child.on('error', (err) => {
      cleanup();
      reject(new Error(`启动失败: ${err.message}`));
    });

    // 'close' 事件: 所有 stdio 流关闭后再触发，比 'exit' 更可靠
    child.on('close', (code, signal) => {
      cleanup();
      if (killed) {
        reject(new Error(`子进程因超时被终止 signal=${signal}`));
        return;
      }
      if (code === 0) {
        resolve({ code, stdout, stderr });
      } else {
        // 非零退出码视为失败
        reject(new Error(`子进程退出码 ${code}${signal ? ` signal=${signal}` : ''}\nstderr: ${stderr}`));
      }
    });
  });
}

// ---------------------------------------------------------------
// 主流程：调用外部脚本并解析结果
// ---------------------------------------------------------------
async function main() {
  console.log('=== 调用外部脚本（spawn 流式收集 + 超时控制）===');
  console.log('CMD :', CMD);
  console.log('ARGS:', ARGS);
  console.log('');

  try {
    const { code, stdout, stderr } = await runExternal(CMD, ARGS, {
      timeout: 5000 // 5 秒超时
    });

    console.log('--- stdout (原始) ---');
    console.log(stdout.trim());
    if (stderr.trim()) {
      console.log('--- stderr ---');
      console.log(stderr.trim());
    }

    // 解析最后一行 JSON 作为推理结果
    const lines = stdout.trim().split('\n');
    const lastLine = lines[lines.length - 1];
    try {
      const result = JSON.parse(lastLine);
      console.log('\n=== 解析得到的结构化结果 ===');
      console.log('label:', result.label);
      console.log('score:', result.score);
    } catch (e) {
      console.log('\n最后一行不是 JSON:', lastLine);
    }

    console.log(`\n退出码: ${code}`);
  } catch (err) {
    console.error('调用失败:', err.message);
    process.exit(1);
  }
}

main();

// ---------------------------------------------------------------
// 并行调用示例：Promise.all 包多个 spawn
// ---------------------------------------------------------------
/*
  const images = ['a.jpg', 'b.jpg', 'c.jpg'];
  const results = await Promise.all(
    images.map(img => runExternal('python', ['infer.py', img], { timeout: 30000 }))
  );

  // 注意: 并发数过多会撑爆 CPU/内存，建议用 p-limit 等库控制并发
  //   const pLimit = require('p-limit');
  //   const limit = pLimit(4); // 最多 4 个并发
  //   const results = await Promise.all(
  //     images.map(img => limit(() => runExternal('python', ['infer.py', img])))
  //   );
*/
