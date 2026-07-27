/**
 * basic-middleware.js
 * 演示 app.use 挂载日志中间件、记录请求耗时、next() 控制权传递
 * 运行: node basic-middleware.js  (端口 3000)
 */

const express = require('express');
const app = express();

// ============ 第一层中间件：日志 + 耗时统计 ============
app.use((req, res, next) => {
  const start = Date.now();
  // 监听响应结束事件，此时再读取耗时才是真实响应耗时
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(
      `[日志] ${new Date().toISOString()} ${req.method} ${req.originalUrl} -> ${res.statusCode} (${duration}ms)`
    );
  });
  // 必须调用 next()，否则请求会一直挂起
  next();
});

// ============ 第二层中间件：演示 next() 传递 ============
app.use((req, res, next) => {
  console.log('  -> 第二层中间件执行（在路由前）');
  next();
  console.log('  <- 第二层中间件回调（路由处理后回流）');
});

// ============ 路由 ============
app.get('/', (req, res) => {
  res.send('Hello, Day11 中间件机制！访问 /api 看看 JSON 响应。');
});

app.get('/api', (req, res) => {
  res.json({ message: 'API 响应', time: Date.now() });
});

// ============ 启动 ============
app.listen(3000, () => {
  console.log('basic-middleware 服务启动: http://localhost:3000');
  console.log('测试命令:');
  console.log('  curl http://localhost:3000/');
  console.log('  curl http://localhost:3000/api');
});
