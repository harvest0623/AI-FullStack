// ws-auth.js - 在 upgrade 握手阶段校验 token, 拒绝非法连接
// 运行:
//   npm install
//   node ws-auth.js
//
// 核心思路:
//   浏览器原生 new WebSocket(url) 不支持自定义 header, 只能通过两种方式带凭证:
//     1) URL query 参数: ws://host/path?token=xxx —— 简单但 token 会进 access log
//     2) 协议子协议: new WebSocket(url, ['bearer.' + token]) —— 把 token 放到
//        Sec-WebSocket-Protocol 头, 服务端 req.headers['sec-websocket-protocol'] 可读
//   非浏览器客户端(wscat/Node SDK)可直接加 header (如 Authorization)
//
//   在 HTTP -> WS 升级握手时(Upgrade 请求), 服务端有两种拒绝方式:
//     A) socket.destroy() —— 直接销毁底层 socket, 客户端收到 ECONNRESET, 连接失败
//        适合"完全不合法"的请求(没带 token / token 解析失败)
//     B) 先 handleUpgrade 建立连接, 然后立即 ws.close(4001, 'unauthorized') 带码关闭
//        适合"想给客户端一个明确拒绝原因"的场景
//   本演示用 A 方式: 无 token 直接 destroy; token 无效则建立连接后 close(4001)
//
// 测试:
//   # 1) 无 token —— 应被拒绝
//   wscat -c ws://localhost:8084
//   # 2) 有效 token (本演示中 'secret-token' 与 'admin-token' 视为有效)
//   wscat -c "ws://localhost:8084?token=secret-token"
//   > hello
//   # 3) 无效 token —— 建连后被 close
//   wscat -c "ws://localhost:8084?token=wrong"

const http = require('http');
const { WebSocketServer, WebSocket } = require('ws');

const PORT = 8084;

// 演示用 token 校验函数(真实项目应查 JWT/数据库/Redis)
function verifyToken(token) {
  if (!token) return { ok: false, reason: 'missing token' };
  // 模拟: 'secret-token' -> 普通用户, 'admin-token' -> 管理员
  if (token === 'secret-token') return { ok: true, user: { id: 'u1', role: 'user' } };
  if (token === 'admin-token') return { ok: true, user: { id: 'admin', role: 'admin' } };
  return { ok: false, reason: 'invalid token' };
}

// 创建独立的 http server, 自己处理 upgrade 事件
const server = http.createServer((req, res) => {
  // 普通 HTTP 请求(非 upgrade)走这里
  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('WebSocket 鉴权演示。请用 ws 客户端连接 ws://localhost:' + PORT + '?token=xxx');
});

// noServer 模式: wss 不自己监听, 由我们手动在 upgrade 事件中分发
const wss = new WebSocketServer({ noServer: true });

server.on('upgrade', (req, socket, head) => {
  // 解析 URL, 取 query 中的 token
  const url = new URL(req.url, `http://${req.headers.host}`);
  const token = url.searchParams.get('token');

  // 也支持从 header 读 (非浏览器客户端可用)
  // const auth = req.headers['authorization'];
  // const tokenFromHeader = auth ? auth.replace(/^Bearer\s+/i, '') : null;

  const result = verifyToken(token);
  if (!result.ok) {
    // 拒绝方式 A: 直接 destroy socket
    // 写一个 HTTP 401 响应再 destroy, 让客户端能看到原因
    socket.write(
      'HTTP/1.1 401 Unauthorized\r\n' +
      'Content-Type: text/plain; charset=utf-8\r\n' +
      `X-WS-Auth-Error: ${result.reason}\r\n` +
      'Connection: close\r\n' +
      '\r\n' +
      `WebSocket 鉴权失败: ${result.reason}\n`
    );
    socket.destroy();
    console.log(`[拒绝] ${req.socket.remoteAddress} - ${result.reason}`);
    return;
  }

  // 通过校验: 完成 WebSocket 握手
  // wss.handleUpgrade 会把 req/socket 升级为 ws, 并触发 wss 'connection' 事件
  // 第二个参数(result.user)会作为 'connection' 回调的第三个参数透传
  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit('connection', ws, req, result.user);
  });
});

wss.on('connection', (ws, req, user) => {
  const ip = req.socket.remoteAddress;
  console.log(`[+] ${ip} 已认证 user=${JSON.stringify(user)}`);

  // 把用户信息挂到 ws 上, 后续消息处理可用
  ws.user = user;

  ws.send(JSON.stringify({
    type: 'system',
    data: `认证成功, 你是 ${user.id} (${user.role})`,
    timestamp: Date.now()
  }));

  ws.on('message', (data) => {
    const text = data.toString('utf8');
    console.log(`[<] ${user.id}: ${text}`);
    ws.send(JSON.stringify({
      type: 'chat',
      from: 'server',
      data: `(${user.id}) 你说: ${text}`,
      timestamp: Date.now()
    }));
  });

  ws.on('close', (code) => {
    console.log(`[-] ${ip} (${user.id}) 断开 code=${code}`);
  });

  ws.on('error', (err) => console.error('[!]', err.message));
});

server.listen(PORT, () => {
  console.log(`鉴权演示服务器已启动: ws://localhost:${PORT}`);
  console.log('  有效 token: secret-token (普通用户) / admin-token (管理员)');
  console.log('  测试: wscat -c "ws://localhost:' + PORT + '?token=secret-token"');
  console.log('  无 token: wscat -c ws://localhost:' + PORT + '  (会被拒绝)');
});

process.on('SIGINT', () => {
  wss.clients.forEach((ws) => ws.close(1001, 'shutdown'));
  wss.close();
  server.close(() => process.exit(0));
});
