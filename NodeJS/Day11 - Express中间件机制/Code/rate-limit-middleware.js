/**
 * rate-limit-middleware.js
 * 简易内存限流中间件：每 IP 每分钟 N 次，超限返回 429
 * 运行: node rate-limit-middleware.js  (端口 3004)
 *
 * 实现思路（固定窗口计数法）：
 *   1. 以 IP 为 key，记录每个 IP 在当前时间窗口内的请求次数
 *   2. 超过阈值则拒绝，返回 429 + Retry-After
 *   3. 窗口过期后重置计数
 *
 * 局限：单机内存，多实例部署需改用 Redis 等共享存储
 */

const express = require('express');
const app = express();

// ============ 简易内存限流中间件（工厂函数）============
function rateLimitMiddleware(options = {}) {
  const {
    windowMs = 60 * 1000,   // 时间窗口，默认 1 分钟
    max = 60,                // 窗口内最大请求数
    message = '请求过于频繁，请稍后再试',
    skip = () => false       // 可选：跳过限流的条件函数
  } = options;

  // 内存存储：Map<ip, { count, resetTime }>
  const store = new Map();

  // 定期清理过期记录，防止内存无限增长
  const cleaner = setInterval(() => {
    const now = Date.now();
    for (const [ip, record] of store) {
      if (now > record.resetTime) {
        store.delete(ip);
      }
    }
  }, windowMs);
  cleaner.unref(); // 不阻止进程退出

  return (req, res, next) => {
    // 跳过限流
    if (skip(req)) {
      return next();
    }

    const ip = req.ip || (req.socket && req.socket.remoteAddress) || 'unknown';
    const now = Date.now();

    let record = store.get(ip);
    if (!record || now > record.resetTime) {
      // 新窗口开始
      record = { count: 0, resetTime: now + windowMs };
      store.set(ip, record);
    }

    record.count++;

    // 设置限流信息响应头（标准做法，便于前端感知）
    const remaining = Math.max(0, max - record.count);
    res.setHeader('X-RateLimit-Limit', max);
    res.setHeader('X-RateLimit-Remaining', remaining);
    res.setHeader('X-RateLimit-Reset', record.resetTime);

    if (record.count > max) {
      // 超限：返回 429，并告知客户端重试等待秒数
      const retryAfter = Math.ceil((record.resetTime - now) / 1000);
      res.setHeader('Retry-After', retryAfter);
      return res.status(429).json({
        error: message,
        retryAfter: retryAfter,
        limit: max,
        windowMs: windowMs
      });
    }

    next();
  };
}

// ============ 全局限流：每分钟 10 次 ============
app.use(rateLimitMiddleware({ windowMs: 60 * 1000, max: 10 }));

// ============ 路由 ============
app.get('/', (req, res) => {
  res.json({ message: '请求成功', time: new Date().toISOString() });
});

app.get('/heavy', (req, res) => {
  res.json({ message: '这是个"重"接口，但限流是全局共享的' });
});

// ============ 启动 ============
app.listen(3004, () => {
  console.log('rate-limit-middleware 服务启动: http://localhost:3004');
  console.log('限流配置: 每 IP 每分钟 10 次，超限返回 429');
  console.log('\n测试命令（快速发送 15 次请求，观察第 11 次起返回 429）:');
  console.log('  # PowerShell 写法');
  console.log('  1..15 | ForEach-Object { curl http://localhost:3004/ -UseBasicParsing | Select-Object StatusCode }');
  console.log('  # 观察响应头（含 X-RateLimit-* 信息）');
  console.log('  curl http://localhost:3004/ -i');
});
