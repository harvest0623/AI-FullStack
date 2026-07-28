// express-ws.js - Express + ws 共享同一端口
// 运行:
//   npm install
//   node express-ws.js
//
// 演示:
//   HTTP 接口: GET /api/health, GET /api/clients
//   WebSocket: ws://localhost:3000/ws
//
// 两种共享端口的方式:
//   方式 A (本文件): WebSocketServer({ server }) — ws 库自动监听 http server 的 upgrade 事件
//   方式 B (见 ws-auth.js / server.js): WebSocketServer({ noServer: true })
//                  + 手动 server.on('upgrade', ...) + wss.handleUpgrade(...)
//                  ——这种方式可在握手阶段拦截做鉴权、按 path 分发, 更灵活
//
// 浏览器测试:
//   const ws = new WebSocket('ws://localhost:3000/ws');
//   ws.onmessage = e => console.log(e.data);
//   ws.onopen = () => ws.send('hello express+ws');

const express = require('express');
const http = require('http');
const { WebSocketServer } = require('ws');

const app = express();
const PORT = 3000;

// ---- HTTP 路由 ----
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', time: Date.now() });
});

app.get('/api/clients', (req, res) => {
  // wss.clients 是 Set<WebSocket>, 可查看当前在线连接
  const list = [];
  wss.clients.forEach((ws) => {
    list.push({
      readyState: ws.readyState, // 0 CONNECTING, 1 OPEN, 2 CLOSING, 3 CLOSED
      ip: ws._socket ? ws._socket.remoteAddress : null
    });
  });
  res.json({ count: wss.clients.size, clients: list });
});

// ---- 创建 http server 并让 express 与 ws 共享它 ----
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/ws' });
// path 选项限定只接受该路径的 upgrade 请求, 其它路径的 upgrade 会被 ws 忽略
// 没有 path 则默认接受任意路径

wss.on('connection', (ws, req) => {
  const ip = req.socket.remoteAddress;
  console.log(`[ws+] ${ip} 已连接`);

  ws.send(JSON.stringify({
    type: 'system',
    data: '连接成功, 这是 express + ws 共享端口的演示',
    timestamp: Date.now()
  }));

  ws.on('message', (data) => {
    const msg = data.toString('utf8');
    console.log(`[ws<] ${ip}: ${msg}`);
    ws.send(`[server] 你说的是: ${msg}`);
  });

  ws.on('close', () => console.log(`[ws-] ${ip} 断开`));
});

server.listen(PORT, () => {
  console.log(`HTTP+WS 服务器已启动: http://localhost:${PORT}`);
  console.log(`  HTTP:  GET http://localhost:${PORT}/api/health`);
  console.log(`  HTTP:  GET http://localhost:${PORT}/api/clients`);
  console.log(`  WS:    ws://localhost:${PORT}/ws`);
});

process.on('SIGINT', () => {
  console.log('\n关闭...');
  wss.clients.forEach((ws) => ws.close(1001, 'shutdown'));
  wss.close();
  server.close(() => process.exit(0));
});
