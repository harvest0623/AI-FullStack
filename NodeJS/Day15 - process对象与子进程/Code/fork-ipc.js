// fork-ipc.js - 父进程 fork 子进程，通过 send/on('message') 双向通信
// 运行:
//   node fork-ipc.js
//
// 本文件既是父进程入口，也作为子进程被 fork
// 通过判断 process.env.CHILD_ROLE 区分父子角色

const { fork } = require('child_process');
const path = require('path');

// ---------------------------------------------------------------
// 子进程角色：fork-ipc-worker.js（运行时由本文件 fork 出来）
// 为了演示方便，我们用一个独立的 worker 文件
// 实际项目中 worker 通常是独立的 .js
// ---------------------------------------------------------------
const WORKER_FILE = path.join(__dirname, 'fork-ipc-worker.js');

// ---------------------------------------------------------------
// 父进程逻辑：分发任务、收集结果
// ---------------------------------------------------------------
function runParent() {
  console.log('=== 父进程: 启动子进程并分发任务 ===\n');

  const child = fork(WORKER_FILE, [], {
    // silent: true 表示子进程 stdin/stdout/stderr 走管道（不继承父进程）
    // 这里保持 false 让子进程的 console 直接打到当前终端，便于观察
    silent: false
  });

  const tasks = [
    { id: 1, type: 'fib', n: 30 },
    { id: 2, type: 'fib', n: 35 },
    { id: 3, type: 'echo', msg: 'hello from child' },
    { id: 4, type: 'fib', n: 38 }
  ];

  let pending = tasks.length;
  const results = [];
  const startTime = Date.now();

  // 监听子进程消息
  child.on('message', (msg) => {
    if (msg.type === 'result') {
      results.push(msg);
      console.log(`[父] 收到任务 ${msg.id} 结果:`, msg.result);

      if (--pending === 0) {
        const elapsed = Date.now() - startTime;
        console.log(`\n[父] 所有任务完成，总耗时 ${elapsed}ms`);
        console.log('[父] 结果汇总:', results);
        // 通知子进程退出
        child.send({ type: 'shutdown' });
      }
    }
  });

  // 子进程退出
  child.on('exit', (code, signal) => {
    console.log(`[父] 子进程退出 code=${code} signal=${signal || '(无)'}`);
  });

  // IPC 通道关闭
  child.on('disconnect', () => {
    console.log('[父] IPC 通道已断开');
  });

  // 子进程出错
  child.on('error', (err) => {
    console.error('[父] 子进程错误:', err);
  });

  // 依次发送任务（也可一次性 send，子进程会排队处理）
  console.log('[父] 分发任务:', tasks);
  tasks.forEach((t) => child.send({ type: 'task', payload: t }));
}

// ---------------------------------------------------------------
// 通过环境变量区分父子角色
// ---------------------------------------------------------------
if (process.env.IS_FORK_CHILD === '1') {
  // 这条分支需要 fork-ipc-worker.js 文件来承载
  // 我们这里用单独的 worker 文件实现，因此本文件被 fork 时不会走到这里
  // 保留这段注释说明父子同文件模式的判断方式
  console.log('[子] (本文件不作为 worker，请查看 fork-ipc-worker.js)');
} else {
  runParent();
}

// ---------------------------------------------------------------
// 双向通信机制说明
// ---------------------------------------------------------------
/*
  IPC 通信能力对照:
  ┌─────────────────┬─────────────────────────────────┐
  │ 方向            │ API                              │
  ├─────────────────┼─────────────────────────────────┤
  │ 父 → 子         │ child.send(msg)                  │
  │ 子 → 父         │ process.send(msg)                │
  │ 父收子消息      │ child.on('message', cb)          │
  │ 子收父消息      │ process.on('message', cb)        │
  │ 父断 IPC        │ child.disconnect()               │
  │ 子断 IPC        │ process.disconnect()             │
  │ 父杀子进程      │ child.kill(signal)               │
  │ 子自杀          │ process.exit(code)               │
  └─────────────────┴─────────────────────────────────┘

  注意:
  1. IPC 消息走 JSON 序列化，无法传递函数、循环引用、Class 实例
  2. child.disconnect() 只断通信，不杀进程；子进程若无其他任务会自然退出
  3. 子进程崩了不会自动重启，需要父进程监听 'exit' 自行重启(类似 PM2 cluster)
  4. 大数据通信建议用文件或 SharedArrayBuffer，不要走 IPC JSON
*/
