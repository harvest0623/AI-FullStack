/**
 * auth-middleware.js
 * 自定义鉴权中间件：从 header 读取 token 校验，保护 /api 路由，失败返回 401
 * 运行: node auth-middleware.js  (端口 3001)
 */

const express = require('express');
const app = express();

// 模拟有效 token（生产环境应从配置中心 / 环境变量读取，并配合 JWT 校验）
const VALID_TOKEN = 'Bearer my-secret-token-2024';

// ============ 鉴权中间件 ============
function authMiddleware(req, res, next) {
  const authHeader = req.headers['authorization'];

  // 1. 未提供 token
  if (!authHeader) {
    return res.status(401).json({ error: '未提供 Authorization token，拒绝访问' });
  }

  // 2. token 无效
  if (authHeader !== VALID_TOKEN) {
    return res.status(401).json({ error: 'token 无效或已过期' });
  }

  // 3. 校验通过：把用户信息挂到 req 上，供后续路由使用
  req.user = { id: 1, name: 'AI全栈工程师', role: 'admin' };
  next();
}

// ============ 公开路由（无需鉴权）============
app.get('/', (req, res) => {
  res.send('公开首页，无需鉴权。访问 /api 需要带 token。');
});

app.get('/login', (req, res) => {
  // 模拟登录返回 token
  res.json({ token: 'my-secret-token-2024', tip: '请使用 Authorization: Bearer <token> 访问受保护接口' });
});

// ============ 受保护路由（挂载鉴权中间件）============
// mount path: /api 下所有路由都会先经过 authMiddleware
app.use('/api', authMiddleware);

app.get('/api/profile', (req, res) => {
  // req.user 由鉴权中间件注入
  res.json({ user: req.user });
});

app.get('/api/orders', (req, res) => {
  res.json({ orders: [{ id: 1, item: 'Express 进阶书籍', price: 99 }] });
});

// ============ 启动 ============
app.listen(3001, () => {
  console.log('auth-middleware 服务启动: http://localhost:3001');
  console.log('\n测试命令:');
  console.log('  # 公开路由');
  console.log('  curl http://localhost:3001/');
  console.log('  curl http://localhost:3001/login');
  console.log('  # 受保护路由 - 无 token（返回 401）');
  console.log('  curl http://localhost:3001/api/profile');
  console.log('  # 受保护路由 - 错误 token（返回 401）');
  console.log('  curl -H "Authorization: Bearer wrong-token" http://localhost:3001/api/profile');
  console.log('  # 受保护路由 - 正确 token（返回 200）');
  console.log('  curl -H "Authorization: Bearer my-secret-token-2024" http://localhost:3001/api/profile');
  console.log('  curl -H "Authorization: Bearer my-secret-token-2024" http://localhost:3001/api/orders');
});
