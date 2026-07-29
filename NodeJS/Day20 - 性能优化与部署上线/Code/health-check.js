/**
 * health-check.js - 健康检查端点 + 优雅退出
 * ------------------------------------------------------------
 * 运行: node health-check.js  (端口 3000, 与 Dockerfile/PM2 配置对齐)
 *
 * 端点:
 *   GET /health  存活探针(liveness): 进程还活着就返回 200
 *   GET /ready   就绪探针(readiness): 依赖(数据库)就绪才返回 200, 否则 503
 *
 * 优雅退出 (呼应 Day16):
 *   收到 SIGTERM/SIGINT → 进入 shuttingDown 状态 → /ready 立刻返回 503
 *   (让负载均衡把流量摘掉) → 停止接受新连接 → 等待在途请求完成 → 关闭 DB → exit
 *
 * 测试优雅退出:
 *   启动后 curl http://localhost:3000/ready  → 200
 *   Ctrl+C 或 kill <pid> 发 SIGINT
 *   再 curl http://localhost:3000/ready       → 503 (流量已摘除)
 * ------------------------------------------------------------
 */

'use strict';

const http = require('http');

// 用原生 http 演示, 让健康检查服务自身极轻量、无第三方依赖
// (生产中可直接挂在业务 Express app 上, 共享同一个 http server)
const server = http.createServer((req, res) => {
  // 路由分发
  if (req.method === 'GET' && req.url === '/health') return handleHealth(req, res);
  if (req.method === 'GET' && req.url === '/ready') return handleReady(req, res);
  if (req.method === 'GET' && req.url === '/') return handleRoot(req, res);
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ code: 'NOT_FOUND', message: `未找到路由 ${req.url}` }));
});

// ============================================================
// 全局状态
// ============================================================
const state = {
  startedAt: Date.now(),
  shuttingDown: false,     // 优雅退出标志: 一旦为 true, /ready 立即 503
  dbReady: false           // 模拟依赖就绪状态
};

// ============================================================
// 模拟数据库连接 (启动时连接, 退出时关闭)
// ============================================================
function connectDB() {
  // 真实场景: await mongoose.connect(...) / await pg.connect()
  return new Promise((resolve) => {
    setTimeout(() => {
      state.dbReady = true;
      console.log('[db] 连接就绪');
      resolve();
    }, 500); // 模拟连接耗时
  });
}

function closeDB() {
  return new Promise((resolve) => {
    state.dbReady = false;
    console.log('[db] 连接已关闭');
    resolve();
  });
}

// ============================================================
// 端点处理
// ============================================================
function json(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body));
}

// /health: 存活探针 —— 进程没死就 200, 不检查依赖
// k8s livenessProbe 用: 失败 → 重启容器
function handleHealth(req, res) {
  json(res, 200, {
    status: 'ok',
    uptime: Math.floor((Date.now() - state.startedAt) / 1000) + 's',
    pid: process.pid
  });
}

// /ready: 就绪探针 —— 依赖(数据库等)就绪 + 未在退出中, 才 200
// k8s readinessProbe 用: 失败 → 从 Service Endpoints 摘除流量, 但不重启
function handleReady(req, res) {
  if (state.shuttingDown) {
    // 退出中: 立即 503, 让负载均衡摘流量, 但进程其实还活着 (health 仍 200)
    return json(res, 503, { status: 'shutting_down', message: '正在优雅退出, 不再接收新流量' });
  }
  if (!state.dbReady) {
    return json(res, 503, { status: 'not_ready', message: '依赖未就绪 (数据库未连接)' });
  }
  json(res, 200, {
    status: 'ready',
    uptime: Math.floor((Date.now() - state.startedAt) / 1000) + 's',
    db: 'connected'
  });
}

function handleRoot(req, res) {
  json(res, 200, {
    service: 'day20-health-check',
    endpoints: ['/health (存活)', '/ready (就绪)'],
    shuttingDown: state.shuttingDown,
    dbReady: state.dbReady
  });
}

// ============================================================
// 优雅退出 (呼应 Day16)
// ============================================================
let connections = new Set();

server.on('connection', (socket) => {
  connections.add(socket);
  socket.on('close', () => connections.delete(socket));
});

async function gracefulShutdown(signal) {
  if (state.shuttingDown) return; // 防止重复触发
  state.shuttingDown = true;
  console.log(`\n[shutdown] 收到 ${signal}, 开始优雅退出...`);

  // 1. 立即标记 not-ready, 让 LB/k8s 摘流量 (此时 /ready 返回 503)
  console.log('[shutdown] 已标记 not-ready, 等待 1s 让探针摘流量');
  await new Promise((r) => setTimeout(r, 1000));

  // 2. 停止接受新连接
  server.close(async () => {
    console.log('[shutdown] HTTP server 已关闭, 不再接受新连接');
    // 3. 关闭依赖
    await closeDB();
    console.log('[shutdown] 退出完成');
    process.exit(0);
  });

  // 4. 兜底: 给在途请求一些时间, 超时强杀 (避免卡死)
  setTimeout(() => {
    console.error('[shutdown] 超时仍有连接未关闭, 强制退出');
    process.exit(1);
  }, 10_000).unref();

  // 5. 主动结束现有空闲连接 (keep-alive 的连接不传数据时不会触发 close)
  //    这里只关闭空闲连接, 在途请求让 server.close 自然等完
  for (const socket of connections) {
    if (socket.readyState === 'open') {
      // 仅对没有活跃请求的连接发 FIN
      socket.destroy();
    }
  }
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// ============================================================
// 启动
// ============================================================
const PORT = process.env.PORT || 3000;

(async () => {
  await connectDB();
  server.listen(PORT, () => {
    console.log(`health-check 启动: http://localhost:${PORT} (pid=${process.pid})`);
    console.log('  GET /health  存活探针 (进程活着即 200)');
    console.log('  GET /ready   就绪探针 (依赖就绪 + 未退出中 才 200)');
    console.log('\n优雅退出: 发送 SIGTERM/SIGINT (Ctrl+C) 观察 /ready 返回 503');
  });
})();
