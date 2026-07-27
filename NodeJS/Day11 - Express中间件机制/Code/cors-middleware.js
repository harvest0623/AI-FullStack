/**
 * cors-middleware.js
 * 自定义 CORS 中间件：处理预检 OPTIONS 请求、设置允许头
 * 运行: node cors-middleware.js  (端口 3003)
 *
 * CORS 核心响应头：
 *   Access-Control-Allow-Origin      允许的源
 *   Access-Control-Allow-Methods     允许的方法
 *   Access-Control-Allow-Headers     允许的请求头
 *   Access-Control-Max-Age           预检结果缓存时间（秒）
 *   Access-Control-Allow-Credentials 是否允许携带 Cookie
 *
 * 预检请求（Preflight）：
 *   浏览器在发送"非简单请求"前，会先用 OPTIONS 方法探测服务器是否允许
 */

const express = require('express');
const app = express();

// ============ 自定义 CORS 中间件（工厂函数，支持配置）============
function corsMiddleware(options = {}) {
  const {
    origin = '*',
    methods = 'GET,POST,PUT,DELETE,OPTIONS',
    allowedHeaders = 'Content-Type,Authorization',
    exposedHeaders = '',
    credentials = false,
    maxAge = 86400
  } = options;

  return (req, res, next) => {
    // 1. 设置允许的源
    // 注意：origin 与 credentials=true 不能同时为 '*'，需动态回填请求源
    res.setHeader('Access-Control-Allow-Origin', origin);

    // 2. 允许的方法
    res.setHeader('Access-Control-Allow-Methods', methods);

    // 3. 允许的请求头
    res.setHeader('Access-Control-Allow-Headers', allowedHeaders);

    // 4. 允许前端读取的响应头
    if (exposedHeaders) {
      res.setHeader('Access-Control-Expose-Headers', exposedHeaders);
    }

    // 5. 预检结果缓存时间
    res.setHeader('Access-Control-Max-Age', maxAge);

    // 6. 是否允许携带凭证（Cookie 等）
    if (credentials) {
      res.setHeader('Access-Control-Allow-Credentials', 'true');
    }

    // 7. 处理预检请求：直接返回 204，不进入后续路由
    if (req.method === 'OPTIONS') {
      return res.status(204).end();
    }

    next();
  };
}

// 挂载 CORS 中间件（必须在路由之前）
app.use(corsMiddleware({
  origin: 'http://localhost:8080',
  methods: 'GET,POST,PUT,DELETE,OPTIONS',
  allowedHeaders: 'Content-Type,Authorization,X-Custom-Header',
  exposedHeaders: 'X-Request-Id',
  maxAge: 600
}));

// ============ 路由 ============
app.get('/api/data', (req, res) => {
  res.setHeader('X-Request-Id', 'req-' + Date.now());
  res.json({ message: 'CORS 已配置，跨域可访问', time: Date.now() });
});

app.post('/api/data', (req, res) => {
  res.json({ message: 'POST 请求成功，跨域通过' });
});

app.get('/api/public', (req, res) => {
  res.json({ message: '公开数据' });
});

// ============ 启动 ============
app.listen(3003, () => {
  console.log('cors-middleware 服务启动: http://localhost:3003');
  console.log('\n测试命令:');
  console.log('  # 普通跨域请求');
  console.log('  curl http://localhost:3003/api/data -i');
  console.log('  # 预检请求（OPTIONS，模拟浏览器跨域前探测）');
  console.log('  curl -X OPTIONS \\');
  console.log('    -H "Origin: http://localhost:8080" \\');
  console.log('    -H "Access-Control-Request-Method: POST" \\');
  console.log('    -H "Access-Control-Request-Headers: Content-Type,Authorization" \\');
  console.log('    http://localhost:3003/api/data -i');
  console.log('  # 带 Origin 的 POST');
  console.log('  curl -X POST -H "Origin: http://localhost:8080" -H "Content-Type: application/json" \\');
  console.log('    -d \'{"a":1}\' http://localhost:3003/api/data -i');
});
