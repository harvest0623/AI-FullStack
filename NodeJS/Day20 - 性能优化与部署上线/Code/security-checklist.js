/**
 * security-checklist.js - 生产环境安全配置示例
 * ------------------------------------------------------------
 * 运行:
 *   cd Code
 *   npm install
 *   node security-checklist.js   (端口 3002)
 *
 * 测试:
 *   # 安全响应头 (helmet 设置了一组: X-Content-Type-Options, X-Frame-Options 等)
 *   curl http://localhost:3002/ -i
 *
 *   # CORS 预检: 只允许白名单来源
 *   curl http://localhost:3002/ -H "Origin: https://evil.com" -i   (无 Access-Control-Allow-Origin)
 *   curl http://localhost:3002/ -H "Origin: https://app.example.com" -i (有)
 *
 *   # 限流: 快速连发 6 次, 第 6 次返回 429
 *   1..6 | ForEach-Object { curl http://localhost:3002/ -UseBasicParsing | Select StatusCode }
 *
 *   # 请求体过大被拒 (>10kb)
 *   curl -X POST http://localhost:3002/echo -H "Content-Type: application/json" -d "{\"x\":\"$(python -c "print('a'*20000)")\"}"
 *
 *   # 非法 JSON 解析错误被兜底为 400 (而非默认的裸 500 堆栈)
 *   curl -X POST http://localhost:3002/echo -H "Content-Type: application/json" -d "{bad json"
 * ------------------------------------------------------------
 */

'use strict';

const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const app = express();
const PORT = 3002;
const isProd = process.env.NODE_ENV === 'production';

// ============================================================
// 1. Helmet: 一键设置一组安全响应头
//    - X-Content-Type-Options: nosniff  防 MIME 嗅探
//    - X-Frame-Options: SAMEORIGIN      防点击劫持(不被 iframe 嵌套)
//    - Strict-Transport-Security        强制 HTTPS (HSTS)
//    - Content-Security-Policy          限制资源加载来源 (按需调严)
// ============================================================
app.use(helmet());

// ============================================================
// 2. CORS 严格白名单: 只放行指定来源, 杜绝 "*"
//    生产务必显式列出前端域名, 切勿用 origin: '*' 配合 credentials
// ============================================================
const ALLOWED_ORIGINS = [
  'https://app.example.com',
  'https://admin.example.com'
  // 本地开发可临时加入 'http://localhost:5173'
];

app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (origin && ALLOWED_ORIGINS.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Vary', 'Origin'); // 缓存正确性: 同一 URL 不同 Origin 返回不同头
    res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
    res.setHeader('Access-Control-Allow-Credentials', 'true'); // 允许带 Cookie
    res.setHeader('Access-Control-Max-Age', '600'); // 预检结果缓存 10 分钟
  }
  // 预检请求直接 204 结束, 不进入业务路由
  if (req.method === 'OPTIONS') return res.status(204).end();
  next();
});

// ============================================================
// 3. 请求体大小限制: 防止超大 payload 撑爆内存 (默认 100kb 偏大, 按业务收紧)
//    同时兜底 JSON 解析错误, 避免裸抛 SyntaxError 暴露堆栈
// ============================================================
app.use((req, res, next) => {
  express.json({
    limit: '10kb',                       // 限制请求体, 防大 payload 攻击
    strict: true                         // 只接受 {} / [] 顶层结构
  })(req, res, (err) => {
    if (err) {
      // 解析失败统一转 400, 不暴露内部错误细节
      return res.status(400).json({
        code: 'INVALID_JSON',
        message: '请求体不是合法的 JSON'
      });
    }
    next();
  });
});

// ============================================================
// 4. 限流: 防 brute force / 爬虫/ CC 攻击
//    express-rate-limit 默认内存计数, 多实例需换 Redis store
// ============================================================
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,       // 1 分钟窗口
  max: 5,                    // 每 IP 每分钟 5 次 (演示用, 生产按 QPS 估)
  standardHeaders: true,     // 返回 RateLimit-* 标准头
  legacyHeaders: false,      // 关闭旧的 X-RateLimit-* 头
  message: {
    code: 'RATE_LIMITED',
    message: '请求过于频繁, 请稍后重试'
  }
});
app.use(apiLimiter);

// 更严格的限流: 登录类接口单独加配 (防撞库)
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 分钟
  max: 10,                   // 每 IP 15 分钟最多 10 次登录尝试
  standardHeaders: true,
  legacyHeaders: false,
  message: { code: 'TOO_MANY_LOGIN', message: '登录尝试过多, 请 15 分钟后再试' }
});

// ============================================================
// 5. 请求超时: 慢请求及时中断, 释放连接 (防 Slowloris 慢速攻击)
// ============================================================
app.use((req, res, next) => {
  // 10s 内必须完成; 超时则 408
  req.setTimeout(10_000, () => {
    if (!res.headersSent) {
      res.status(408).json({ code: 'REQUEST_TIMEOUT', message: '请求超时' });
    }
  });
  next();
});

// ============================================================
// 路由
// ============================================================
app.get('/', (req, res) => {
  res.json({
    code: 'OK',
    message: '安全配置已生效',
    security: ['helmet 头', 'CORS 白名单', '限流 5次/分', 'body 10kb 限制', '10s 超时']
  });
});

app.post('/login', loginLimiter, (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ code: 'BAD_REQUEST', message: '缺少账号或密码' });
  }
  // 演示: 永远返回失败, 配合 loginLimiter 观察限流
  res.status(401).json({ code: 'AUTH_FAILED', message: '账号或密码错误' });
});

app.post('/echo', (req, res) => {
  res.json({ code: 'OK', received: req.body });
});

// ============================================================
// 统一错误兜底: 不向客户端泄露堆栈
// ============================================================
app.use((err, req, res, next) => {
  console.error('[未捕获错误]', err.message);
  res.status(500).json({
    code: 'INTERNAL_ERROR',
    message: '服务器内部错误',
    ...(isProd ? {} : { stack: err.stack }) // 仅开发环境返回堆栈
  });
});

app.listen(PORT, () => {
  console.log(`security-checklist 启动: http://localhost:${PORT}`);
  console.log('已启用: helmet / CORS 白名单 / 限流 / body 限制 / 超时 / 错误兜底');
});
