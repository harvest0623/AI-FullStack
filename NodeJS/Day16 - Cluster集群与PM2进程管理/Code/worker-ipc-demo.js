// worker-ipc-demo.js - 主进程与多个 worker 通信、分发任务示例
// 运行:
//   node worker-ipc-demo.js
//
// 本 demo 演示 cluster + IPC 的双向通信能力:
//   - master fork 多个 worker
//   - master 把一批任务通过 IPC 分发给 worker(轮询 / 空闲优先)
//   - worker 计算完通过 IPC 回传结果
//   - master 收集所有结果后汇总, 通知 worker 退出
//
// 这是"任务队列 + 多进程消费"的雏形, 适用于:
//   - 批量 AI 推理任务分发给多个 worker 并行
//   - 大文件分块处理
//   - CPU 密集计算切片并行(对比单进程串行的加速比)
//
// 注意: 真实生产任务队列通常用 Redis / RabbitMQ / Kafka,
//       本 demo 用 IPC 仅用于学习 cluster 通信机制。

const cluster = require('cluster');
const os = require('os');

const WORKER_COUNT = Math.min(2, os.cpus().length); // 用 2 个 worker 演示即可

// ---------------------------------------------------------------
// 主进程
// ---------------------------------------------------------------
if (cluster.isPrimary) {
  console.log('=== cluster + IPC 任务分发演示 ===\n');
  console.log(`[master] 启动, pid=${process.pid}, 将 fork ${WORKER_COUNT} 个 worker\n`);

  const workers = [];
  // 待分发的任务列表(模拟一批 AI 推理任务, 这里用 fib 代替)
  const tasks = [
    { id: 1, type: 'fib', n: 35 },
    { id: 2, type: 'fib', n: 36 },
    { id: 3, type: 'fib', n: 37 },
    { id: 4, type: 'fib', n: 38 },
    { id: 5, type: 'fib', n: 35 },
    { id: 6, type: 'fib', n: 36 }
  ];

  const results = [];
  let dispatched = 0;
  const startTime = Date.now();

  // 每个 worker 维护一个"是否空闲"状态, 用于空闲优先分发
  const workerState = new Map();

  // fork worker 并初始化状态
  for (let i = 0; i < WORKER_COUNT; i++) {
    const worker = cluster.fork();
    workers.push(worker);
    workerState.set(worker.id, { idle: true, pendingTask: null });
  }

  cluster.on('online', (worker) => {
    console.log(`[master] worker ${worker.id} (pid=${worker.process.pid}) 上线`);
    // worker 上线后尝试分发任务
    dispatchNext();
  });

  // ---------------------------------------------------------------
  // 收到 worker 的消息(任务结果 / 心跳等)
  // ---------------------------------------------------------------
  cluster.on('message', (worker, msg) => {
    if (msg.type === 'result') {
      // worker 回传的任务结果
      results.push(msg);
      console.log(`[master] 收到任务 ${msg.taskId} 结果: fib(${msg.input})=${msg.result}, 耗时 ${msg.elapsed}ms (worker ${worker.id})`);

      // 标记该 worker 空闲, 继续分发下一个任务
      const state = workerState.get(worker.id);
      if (state) state.idle = true;

      // 所有任务都完成?
      if (results.length === tasks.length) {
        finishAll();
      } else {
        dispatchNext();
      }
    }
  });

  // ---------------------------------------------------------------
  // 分发逻辑: 轮询找一个空闲 worker, 派发下一个未分发的任务
  // 策略: 空闲优先(谁闲给谁), 而非严格 round-robin
  // ---------------------------------------------------------------
  function dispatchNext() {
    while (dispatched < tasks.length) {
      // 找一个空闲 worker
      const idleWorker = workers.find((w) => {
        const s = workerState.get(w.id);
        return s && s.idle && !w.isDead();
      });
      if (!idleWorker) break; // 没有空闲 worker, 等回信

      const task = tasks[dispatched++];
      const state = workerState.get(idleWorker.id);
      state.idle = false;
      state.pendingTask = task;

      console.log(`[master] 派发任务 ${task.id} (fib ${task.n}) 给 worker ${idleWorker.id}`);
      idleWorker.send({ type: 'task', payload: task });
    }
  }

  // ---------------------------------------------------------------
  // 所有任务完成: 汇总并通知 worker 退出
  // ---------------------------------------------------------------
  function finishAll() {
    const elapsed = Date.now() - startTime;
    console.log('\n[master] === 所有任务完成 ===');
    console.log(`[master] 总任务数: ${tasks.length}`);
    console.log(`[master] worker 数: ${WORKER_COUNT}`);
    console.log(`[master] 并行总耗时: ${elapsed}ms`);
    console.log('[master] 结果汇总:');
    results
      .sort((a, b) => a.taskId - b.taskId)
      .forEach((r) => {
        console.log(`   任务 ${r.taskId}: fib(${r.input}) = ${r.result} (${r.elapsed}ms, worker ${r.workerId})`);
      });

    // 对比: 单进程串行跑的总耗时(估算)
    const serialTotal = results.reduce((sum, r) => sum + r.elapsed, 0);
    console.log(`\n[master] 单进程串行估算耗时: ${serialTotal}ms`);
    console.log(`[master] 加速比: ${(serialTotal / elapsed).toFixed(2)}x`);

    // 通知所有 worker 退出
    console.log('\n[master] 通知 worker 退出...');
    workers.forEach((w) => w.send({ type: 'shutdown' }));
  }

  // worker 崩溃处理(本 demo 不重点演示, 但保留兜底)
  cluster.on('exit', (worker, code) => {
    console.log(`[master] worker ${worker.id} 退出 code=${code}`);
  });

} else {
  // ---------------------------------------------------------------
  // worker 进程: 接收任务、计算、回传结果
  // ---------------------------------------------------------------
  const workerId = cluster.worker.id;
  const pid = process.pid;
  console.log(`[worker ${workerId}] 启动, pid=${pid}, 等待任务`);

  process.on('message', (msg) => {
    if (msg.type === 'task') {
      const task = msg.payload;
      const start = Date.now();

      // 执行计算(模拟 CPU 密集任务, 如模型推理)
      let result;
      if (task.type === 'fib') {
        result = fibonacci(task.n);
      }

      const elapsed = Date.now() - start;
      // 回传结果给 master
      process.send({
        type: 'result',
        taskId: task.id,
        input: task.n,
        result,
        elapsed,
        workerId
      });
    }

    if (msg.type === 'shutdown') {
      console.log(`[worker ${workerId}] 收到 shutdown, 退出`);
      process.exit(0);
    }
  });

  // CPU 密集计算: 递归斐波那契
  function fibonacci(n) {
    if (n < 2) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
  }
}

// ---------------------------------------------------------------
// 关键结论
// ---------------------------------------------------------------
/*
  cluster + IPC 通信要点:
    1. master 与每个 worker 间有一条 IPC 管道(来自 child_process.fork)
    2. master 用 worker.send(msg) 发消息, 用 cluster.on('message') 收消息
       worker  用 process.send(msg) 发消息, 用 process.on('message') 收消息
    3. 消息走 JSON 序列化, 无法传函数 / 循环引用 / Class 实例
    4. 适合"任务分发"模式: master 做调度, worker 做计算, 结果回传统一汇总

  适用场景:
    - 批量 AI 推理任务并行(多个 worker 各跑一份模型)
    - 大文件分块处理(每个 worker 处理一块)
    - CPU 密集计算切片(fib / 图像处理 / 张量运算)

  vs 直接用 child_process.fork:
    - cluster 的 worker 自带共享端口能力(适合 HTTP 服务)
    - 但 IPC 通信机制是一样的, 都是 send / on('message')
    - 不需要共享端口的纯任务分发, 用 child_process.fork 也可, 更轻量

  vs 真实任务队列(Redis / RabbitMQ):
    - IPC 只能在同一台机器的父子进程间通信, 跨机器不行
    - 生产环境多机部署要用 Redis 等中间件做任务队列
    - 本 demo 仅用于学习 cluster 的 IPC 机制

  vs worker_threads:
    - cluster 是多进程, 隔离强, 启动开销大
    - worker_threads 是多线程, 可共享 SharedArrayBuffer, 启动开销小
    - 纯 Node 内 CPU 密集 -> worker_threads
    - 需要进程隔离 / 调外部程序 -> cluster 或 child_process
*/
