// graceful-shutdown.js - 优雅退出演示
// 运行:
//   node graceful-shutdown.js
//
// 测试优雅退出:
//   # 终端 1: 启动服务
//   node graceful-shutdown.js
//
//   # 终端 2: 发起一个耗时 2 秒的请求(模拟在途请求)
//   curl http://localhost:3000/slow
//   # 立即在终端 3 执行:
//   #   Linux/Mac:  kill -TERM <pid>     或 kill -INT <pid>
//   #   Windows:    taskkill /PID <pid>  或 直接在终端 1 按 Ctrl+C
//   # 观察: 终端 2 的 curl 仍能拿到正常响应(在途请求被保护),
//   #       服务端日志会打印各阶段: 收到信号 -> 停新连接 -> 等在途 -> 关资源 -> 退出
//
//   # 对比: 用 kill -9 (SIGKILL, 无法捕获) 直接强杀,
//   #       终端 2 的 curl 立即断连, 在途请求被丢弃
//
// 健康检查配合:
//   curl http://localhost:3000/health
//   退出过程中该端点会返回 503, 让负载均衡器摘掉流量

const http = require('http');

const PORT = 3000;
const SHUTDOWN_TIMEOUT = 8000; // 优雅退出超时, 超过则强杀(应小于上游 K8s/Docker 的宽限期)

// ---------------------------------------------------------------
// 模拟一个"数据库连接"对象, 演示关闭资源
// ---------------------------------------------------------------
const fakeDatabase = {
  connected: true,
  async close() {
    if (!this.connected) return;
    console.log('[shutdown] 正在关闭数据库连接...');
    await new Promise((r) => setTimeout(r, 300)); // 模拟关闭耗时
    this.connected = false;
    console.log('[shutdown] 数据库连接已关闭');
  }
};

let shuttingDown = false;       // 是否正在退出(防重复触发 + 健康检查返回 503)
let inFlightRequests = 0;       // 当前在途请求数(用于观察)

// ---------------------------------------------------------------
// 创建 HTTP 服务
// ---------------------------------------------------------------
const server = http.createServer((req, res) => {
  // 优雅退出期间, 健康检查返回 503, 让 LB 摘流量
  if (req.url === '/health') {
    if (shuttingDown) {
      res.writeHead(503, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ status: 'shutting down' }));
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ status: 'ok', inFlight: inFlightRequests }));
  }

  // 优雅退出期间可拒绝新业务请求(也可选择继续处理, 看 LB 是否已摘流量)
  if (shuttingDown) {
    res.writeHead(503, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ error: 'server is shutting down' }));
  }

  // /slow 端点: 模拟耗时 2 秒的请求, 用于测试在途请求保护
  if (req.url === '/slow') {
    inFlightRequests++;
    console.log(`[request] /slow 开始, 在途=${inFlightRequests}`);
    setTimeout(() => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, msg: '耗时请求完成' }));
      inFlightRequests--;
      console.log(`[request] /slow 完成, 在途=${inFlightRequests}`);
    }, 2000);
    return;
  }

  // 普通快速请求
  inFlightRequests++;
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ ok: true, pid: process.pid, inFlight: inFlightRequests }));
  inFlightRequests--;
});

server.listen(PORT, () => {
  console.log(`[server] 启动, pid=${process.pid}, 监听 http://localhost:${PORT}`);
  console.log('[server] 试试:');
  console.log('  curl http://localhost:3000/slow   (耗时 2s 的请求)');
  console.log('  curl http://localhost:3000/health (健康检查)');
  console.log(`[server] 然后按 Ctrl+C 或 kill -TERM ${process.pid} 观察优雅退出`);
  console.log('------------------------------------------------');
});

// ---------------------------------------------------------------
// 优雅退出主流程
// 收到 SIGTERM(K8s/Docker 停容器、kill 默认) 或 SIGINT(Ctrl+C) 后执行
// ---------------------------------------------------------------
async function gracefulShutdown(signal) {
  // 防止重复触发(用户连按两次 Ctrl+C, 或 SIGTERM + SIGINT 同时到)
  if (shuttingDown) {
    console.log('[shutdown] 已在退出流程中, 忽略重复信号');
    return;
  }
  shuttingDown = true;

  console.log('\n================================================');
  console.log(`[shutdown] 1. 收到 ${signal} 信号, 开始优雅退出`);
  console.log(`[shutdown]    当前在途请求数: ${inFlightRequests}`);
  console.log('================================================');

  // ---- 步骤 2: 停止接受新连接 ----
  // server.close() 让 server 不再接受新连接, 但已建立的连接会继续处理
  // 它返回一个 Promise(Node 18+), resolve 时表示所有连接都已关闭
  console.log('[shutdown] 2. 调用 server.close(), 停止接受新连接');
  const closePromise = new Promise((resolve) => {
    server.close(() => {
      console.log('[shutdown]    所有连接已关闭, server.close 完成');
      resolve();
    });
  });

  // ---- 步骤 3: 设置超时强杀 ----
  // 若在途请求一直不结束(死循环 / 下游无响应), 不能无限等
  // 超时后强制退出。注意: 退出超时要小于上游(K8s 30s / Docker 10s)的宽限期
  const forceExitTimer = setTimeout(() => {
    console.error(`[shutdown] !! 超时 ${SHUTDOWN_TIMEOUT}ms 仍未退出, 强制 process.exit(1)`);
    process.exit(1);
  }, SHUTDOWN_TIMEOUT);
  forceExitTimer.unref(); // unref: 这个定时器本身不阻止进程退出

  // 等在途请求处理完(server.close resolve)
  await closePromise;

  // ---- 步骤 4: 关闭外部资源(数据库、Redis、消息队列等) ----
  console.log('[shutdown] 3. 关闭外部资源(数据库/Redis/MQ)');
  await fakeDatabase.close();

  // ---- 步骤 5: flush 日志 ----
  // 真实场景: logger.end() 后等 'finish' 事件, 确保日志写盘
  console.log('[shutdown] 4. flush 日志(本 demo 用 console 立即输出)');

  // ---- 步骤 6: 正常退出 ----
  console.log('[shutdown] 5. 优雅退出完成, process.exit(0)');
  clearTimeout(forceExitTimer);
  process.exit(0);
}

// ---------------------------------------------------------------
// 注册信号处理
// SIGTERM: K8s 停 Pod / Docker stop / kill <pid> 默认信号
// SIGINT:  终端 Ctrl+C
// 两者都触发优雅退出
// ---------------------------------------------------------------
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// ---------------------------------------------------------------
// 兜底: 未捕获异常也走优雅退出(避免直接崩丢在途请求)
// 这是 Day14/Day15 知识的延伸应用
// ---------------------------------------------------------------
process.on('uncaughtException', (err) => {
  console.error('[shutdown] 未捕获异常, 触发优雅退出:', err);
  gracefulShutdown('uncaughtException');
});

// ---------------------------------------------------------------
// 关键结论
// ---------------------------------------------------------------
/*
  优雅退出标准流程:
    1. 收到信号(SIGTERM/SIGINT) -> 标记 shuttingDown
    2. 健康检查返回 503, 让 LB 摘流量
    3. server.close() 停止接受新连接, 但继续处理在途请求
    4. 设置超时强杀(防在途请求卡死), 超时要小于上游宽限期
    5. 关闭数据库/Redis/MQ 等外部资源
    6. flush 日志
    7. process.exit(0)

  关键原则:
    - shuttingDown 标志防重复触发
    - server.close 只停新连接, 不中断在途请求
    - 退出超时 < 上游超时(K8s 30s / Docker 10s)
    - 先摘流量(健康检查 503)再 server.close, 避免 LB 还在转发

  对比 SIGKILL(kill -9):
    - 无法捕获, 在途请求立即丢失, 资源不释放, 数据可能不一致
    - 这就是为什么要用 SIGTERM + 优雅退出, 而非直接 kill -9
*/
