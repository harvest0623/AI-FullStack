// users-router.js - 用户子路由（使用 express.Router 实现模块化）
// 该模块导出一个 Router 实例，由 server.js 挂载到 /api/users

const express = require('express');
const router = express.Router();

// 内存数据源（不连数据库，重启即丢失）
let users = [
  { id: 1, name: 'Alice', email: 'alice@example.com' },
  { id: 2, name: 'Bob', email: 'bob@example.com' }
];

let nextId = 3;

// 路由级中间件：打印每个用户请求的来源（演示 Router 内也可挂中间件）
router.use((req, res, next) => {
  console.log(`[users-router] ${req.method} ${req.originalUrl}`);
  next();
});

// GET /api/users - 获取用户列表
router.get('/', (req, res) => {
  res.json({ data: users, total: users.length });
});

// GET /api/users/:id - 获取单个用户（:id 为路由参数）
router.get('/:id', (req, res) => {
  const id = Number(req.params.id);
  const user = users.find((u) => u.id === id);
  if (!user) {
    return res.status(404).json({ error: `用户 ${id} 不存在` });
  }
  res.json({ data: user });
});

// POST /api/users - 创建用户（依赖 express.json() 解析 req.body）
router.post('/', (req, res) => {
  const { name, email } = req.body || {};
  if (!name || !email) {
    return res.status(400).json({ error: 'name 和 email 为必填项' });
  }
  const user = { id: nextId++, name, email };
  users.push(user);
  res.status(201).json({ data: user });
});

// PUT /api/users/:id - 全量更新用户
router.put('/:id', (req, res) => {
  const id = Number(req.params.id);
  const idx = users.findIndex((u) => u.id === id);
  if (idx === -1) {
    return res.status(404).json({ error: `用户 ${id} 不存在` });
  }
  const { name, email } = req.body || {};
  users[idx] = {
    ...users[idx],
    name: name ?? users[idx].name,
    email: email ?? users[idx].email
  };
  res.json({ data: users[idx] });
});

// DELETE /api/users/:id - 删除用户
router.delete('/:id', (req, res) => {
  const id = Number(req.params.id);
  const idx = users.findIndex((u) => u.id === id);
  if (idx === -1) {
    return res.status(404).json({ error: `用户 ${id} 不存在` });
  }
  const [removed] = users.splice(idx, 1);
  res.json({ data: removed });
});

module.exports = router;
