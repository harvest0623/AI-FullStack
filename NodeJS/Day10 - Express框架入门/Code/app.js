// app.js - 最简 Express 应用
// 运行: node app.js   或   npm run app
// 访问: http://localhost:3000

const express = require('express');

// 应用对象 app：Express 的核心，既是中间件容器，也是路由容器
const app = express();

// 启用 JSON 请求体解析中间件（解析 application/json）
app.use(express.json());

// 根路由：返回 JSON
app.get('/', (req, res) => {
  res.json({
    name: 'Day10 Express Demo',
    version: '1.0.0',
    description: '最简 Express 应用示例',
    endpoints: ['GET /', 'GET /health'],
    time: new Date().toISOString()
  });
});

// 健康检查路由
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', uptime: process.uptime() });
});

// 启动服务，监听端口
const PORT = 3000;
app.listen(PORT, () => {
  console.log(`App running at http://localhost:${PORT}`);
});
