// middleware-demo.js - 自定义日志中间件演示
// 运行: npm run middleware   或   node middleware-demo.js
// 访问: http://localhost:3001

const express = require('express');
const app = express();

// 自定义日志中间件：记录 method / url / 状态码 / 耗时
// 中间件签名：(req, res, next) => { ... next(); }
app.use((req, res, next) => {
  const start = Date.now();

  // res.on('finish') 在响应发送完成后触发，此时可拿到最终状态码
  res.on('finish', () => {
    const duration = Date.now() - start;
    const time = new Date().toISOString();
    console.log(`[${time}] ${req.method} ${req.originalUrl} -> ${res.statusCode} (${duration}ms)`);
  });

  // 必须调用 next()，否则请求会一直挂起
  next();
});

// 一个“慢”路由，用于观察耗时差异
app.get('/slow', (req, res) => {
  setTimeout(() => res.send('Slow response (200ms later)'), 200);
});

// 一个普通路由
app.get('/', (req, res) => {
  res.send('Home - 查看终端日志输出');
});

// 返回请求信息的路由（演示 req 常用属性）
app.get('/api/info', (req, res) => {
  res.json({
    method: req.method,
    url: req.originalUrl,
    ip: req.ip,
    userAgent: req.get('user-agent'),
    headers: req.headers
  });
});

// 故意抛错，测试日志中间件能否记录到 500
app.get('/error', (req, res) => {
  throw new Error('手动触发的错误');
});

// 错误处理中间件
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  console.error('[error]', err.message);
  res.status(500).json({ error: err.message });
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`Middleware demo running at http://localhost:${PORT}`);
  console.log('尝试依次访问以下地址，观察终端日志:');
  console.log('  http://localhost:3001/');
  console.log('  http://localhost:3001/slow');
  console.log('  http://localhost:3001/api/info');
  console.log('  http://localhost:3001/error');
});
