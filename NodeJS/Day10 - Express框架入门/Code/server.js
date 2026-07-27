// server.js - 启动服务并挂载 users-router 子路由
// 运行: npm start   或   node server.js
// 访问: http://localhost:3000

const express = require('express');
const usersRouter = require('./users-router');

const app = express();

// 解析请求体中间件（必须在挂载路由之前注册，否则路由里拿不到 req.body）
app.use(express.json());                          // 解析 application/json
app.use(express.urlencoded({ extended: true }));  // 解析 application/x-www-form-urlencoded

// 挂载子路由：所有 /api/users 开头的请求交给 usersRouter 处理
app.use('/api/users', usersRouter);

// 根路由：返回接口索引
app.get('/', (req, res) => {
  res.json({
    name: 'Day10 Express CRUD API',
    routes: {
      list: 'GET /api/users',
      detail: 'GET /api/users/:id',
      create: 'POST /api/users',
      update: 'PUT /api/users/:id',
      delete: 'DELETE /api/users/:id'
    }
  });
});

// 404 处理中间件（放在所有路由之后）
app.use((req, res) => {
  res.status(404).json({ error: `路由不存在: ${req.method} ${req.path}` });
});

// 全局错误处理中间件（四参数签名，必须放最后）
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  console.error('[error]', err);
  res.status(500).json({ error: '服务器内部错误' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});

/* ===================== 测试 curl 命令 =====================

# 1. 获取用户列表
curl http://localhost:3000/api/users

# 2. 获取单个用户
curl http://localhost:3000/api/users/1

# 3. 创建用户（POST + JSON body）
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Charlie\",\"email\":\"charlie@example.com\"}"

# 4. 更新用户（PUT）
curl -X PUT http://localhost:3000/api/users/1 \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Alice Updated\"}"

# 5. 删除用户（DELETE）
curl -X DELETE http://localhost:3000/api/users/2

# 6. 测试 404
curl http://localhost:3000/no-such-route

# 7. 测试查询参数（列表过滤示例，本demo未实现过滤，仅演示传参）
curl "http://localhost:3000/api/users?keyword=ali&page=1"

======================================================== */
