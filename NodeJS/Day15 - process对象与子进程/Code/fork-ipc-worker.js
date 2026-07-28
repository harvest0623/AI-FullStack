// fork-ipc-worker.js - 子进程入口，配合 fork-ipc.js 使用
// 由父进程通过 fork() 启动，自动拥有 IPC 通道

// 子进程收到父进程消息
process.on('message', async (msg) => {
  // console.log('[子] 收到消息:', JSON.stringify(msg));

  if (msg.type === 'task') {
    const { id, payload } = msg;
    let result;

    if (payload.type === 'fib') {
      // CPU 密集任务：递归斐波那契
      result = await runHeavy('fib', payload.n);
    } else if (payload.type === 'echo') {
      result = payload.msg;
    } else {
      result = { error: 'unknown type' };
    }

    // 把结果回传给父进程
    process.send({ type: 'result', id, result });
    return;
  }

  if (msg.type === 'shutdown') {
    // console.log('[子] 收到 shutdown，主动退出');
    process.exit(0);
  }
});

process.on('disconnect', () => {
  // 父进程主动 disconnect 时触发
  // console.log('[子] IPC 通道被父进程关闭，子进程将自然退出');
});

// ---------------------------------------------------------------
// CPU 密集计算：用 fibonacci 模拟"模型推理"
// ---------------------------------------------------------------
function fibonacci(n) {
  if (n < 2) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

async function runHeavy(kind, n) {
  // 用 setImmediate 让出一次事件循环，便于接收 shutdown 等消息
  await new Promise((r) => setImmediate(r));
  if (kind === 'fib') return fibonacci(n);
  return null;
}

// 启动提示（会打到父进程的终端）
// console.log('[子] worker 已启动 pid=', process.pid);
