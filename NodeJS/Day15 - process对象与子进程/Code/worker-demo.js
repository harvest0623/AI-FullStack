// worker-demo.js - 用 worker_threads 跑 CPU 密集计算，对比主线程阻塞 vs worker 不阻塞
// 运行:
//   node worker-demo.js

const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

// ---------------------------------------------------------------
// 计算函数：递归斐波那契，CPU 密集
// ---------------------------------------------------------------
function fibonacci(n) {
  if (n < 2) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

const N = 42; // 大约 1-2 秒计算量，足以观察到阻塞

// ---------------------------------------------------------------
// Worker 线程入口：收到 workerData 后计算，把结果 postMessage 给主线程
// ---------------------------------------------------------------
if (!isMainThread) {
  // 这里是 worker 线程执行的代码
  const n = workerData.n;
  const start = Date.now();
  const result = fibonacci(n);
  const elapsed = Date.now() - start;
  parentPort.postMessage({ n, result, elapsed });
  return; // 防止继续往下执行主线程逻辑
}

// ---------------------------------------------------------------
// 以下只在主线程执行
// ---------------------------------------------------------------
console.log('=== worker_threads 演示: CPU 密集任务 ===');
console.log('计算 fibonacci(' + N + ')，主线程 vs worker 线程对比\n');

// ---------------------------------------------------------------
// 场景 1：直接在主线程跑 → 期间事件循环被阻塞
// 主线程跑同步计算时，setTimeout/HTTP 请求等异步任务全部"卡住"
// ---------------------------------------------------------------
function runInMainThread() {
  console.log('--- 1. 在主线程同步计算 ---');
  const start = Date.now();

  // 启动一个 100ms 间隔的"心跳"计时器，用来观察事件循环是否被卡
  const heartbeat = setInterval(() => {
    console.log(`  [心跳] ${Date.now() - start}ms`);
  }, 100);

  const result = fibonacci(N); // 这一行会阻塞主线程 1-2 秒
  const elapsed = Date.now() - start;

  clearInterval(heartbeat);
  console.log(`  结果: fib(${N}) = ${result}`);
  console.log(`  耗时: ${elapsed}ms`);
  console.log(`  ↑ 注意：心跳计时器在计算期间一次都没触发——事件循环被阻塞！\n`);
}

// ---------------------------------------------------------------
// 场景 2：放到 worker 线程跑 → 主线程不阻塞，心跳正常
// ---------------------------------------------------------------
function runInWorker() {
  console.log('--- 2. 在 worker 线程计算 ---');
  return new Promise((resolve) => {
    const start = Date.now();

    // 主线程继续跑心跳，用来证明没被阻塞
    const heartbeat = setInterval(() => {
      console.log(`  [心跳] ${Date.now() - start}ms`);
    }, 100);

    // 启动 worker，传入 workerData
    const worker = new Worker(__filename, {
      workerData: { n: N }
    });

    worker.on('message', (msg) => {
      clearInterval(heartbeat);
      console.log(`  结果: fib(${msg.n}) = ${msg.result}`);
      console.log(`  worker 计算耗时: ${msg.elapsed}ms`);
      console.log(`  主线程总等待: ${Date.now() - start}ms`);
      console.log(`  ↑ 心跳正常触发——主线程没有被阻塞！\n`);
      resolve();
    });

    worker.on('error', (err) => {
      clearInterval(heartbeat);
      console.error('  worker 出错:', err);
      resolve();
    });

    worker.on('exit', (code) => {
      // console.log('  worker 退出码:', code);
    });
  });
}

// ---------------------------------------------------------------
// 场景 3：Promise + worker 封装，便于 await
// ---------------------------------------------------------------
function runWorker(n) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(__filename, { workerData: { n } });
    worker.on('message', resolve);
    worker.on('error', reject);
    worker.on('exit', (code) => {
      if (code !== 0) reject(new Error(`worker 异常退出 code=${code}`));
    });
  });
}

async function demoAwait() {
  console.log('--- 3. Promise + worker，可 await ---');
  const result = await runWorker(30);
  console.log(`  fib(30) = ${result.result}, 耗时 ${result.elapsed}ms\n`);
}

// ---------------------------------------------------------------
// 场景 4：并行跑多个 worker（多核加速）
// ---------------------------------------------------------------
async function demoParallel() {
  console.log('--- 4. 并行跑多个 worker ---');
  const tasks = [38, 38, 38, 38]; // 4 个相同任务
  const start = Date.now();

  const results = await Promise.all(tasks.map((n) => runWorker(n)));
  const elapsed = Date.now() - start;

  results.forEach((r, i) => {
    console.log(`  任务 ${i + 1}: fib(${r.n}) = ${r.result}, 单任务耗时 ${r.elapsed}ms`);
  });
  console.log(`  并行总耗时: ${elapsed}ms`);
  console.log(`  ↑ 4 个任务并行，总耗时接近单任务耗时，而非 4 倍\n`);
}

// ---------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------
(async () => {
  // 1. 主线程阻塞演示
  runInMainThread();

  // 2. worker 不阻塞演示
  await runInWorker();

  // 3. Promise 封装
  await demoAwait();

  // 4. 并行加速
  await demoParallel();

  console.log('=== 关键结论 ===');
  console.log('1. 主线程跑 CPU 密集任务会阻塞事件循环 → HTTP/定时器全部卡住');
  console.log('2. worker_threads 让计算在独立线程跑，主线程继续响应 I/O');
  console.log('3. 多核机器上多个 worker 可真并行，CPU 密集任务可显著加速');
  console.log('4. worker_threads 适合"纯 Node 内的 CPU 密集"');
  console.log('   调用 Python/ffmpeg 等外部程序仍用 child_process');
  console.log('5. AI 场景: 模型推理多交给 Python/CUDA，Node 层用 child_process 编排;');
  console.log('   预处理(图像解码、张量运算)等纯 JS 计算可用 worker_threads');
  process.exit(0);
})();
