// server.js - 整合应用: Express HTTP + WebSocket(鉴权 + 心跳 + 聊天室)
// 运行:
//   npm install
//   npm start          # 或 node server.js
//
// 集成能力一览:
//   1. Express 提供 HTTP 接口: /api/login(换取 token), /api/health, /api/rooms, /api/users
//   2. WebSocket 与 HTTP 共享同一端口(3000), 使用 noServer + handleUpgrade 手动分发
//   3. upgrade 握手阶段校验 token(query 参数), 非法连接直接 socket.destroy
//   4. 心跳保活: 30s 一次 ping, 两次无 pong 则 terminate 踢出
//   5. 聊天室业务: join / leave / chat / private / rooms, 用 Map 管理 userMap 与 roomMap
//   6. 最大连接数限制(MAX_CLIENTS), 超出拒绝建连
//   7. 优雅退出: SIGINT/SIGTERM 时广播通知 + 关闭所有连接 + 关闭 http server
//
// ============================== 测试 ==============================
//
// ① 先登录拿 token(HTTP):
//   curl http://localhost:3000/api/login -X POST -H "Content-Type: application/json" \
//        -d '{"userId":"alice"}'
//   -> {"token":"alice-token","user":{"id":"alice","role":"user"}}
//
// ② wscat 连接(带 token):
//   # 终端 A
//   wscat -c "ws://localhost:3000/ws?token=alice-token"
//   > {"type":"join","data":{"roomId":"room1"}}
//   > {"type":"chat","data":{"roomId":"room1","text":"大家好"}}
//
//   # 终端 B(另一个用户)
//   curl http://localhost:3000/api/login -X POST -H "Content-Type: application/json" -d '{"userId":"bob"}'
//   wscat -c "ws://localhost:3000/ws?token=bob-token"
//   > {"type":"join","data":{"roomId":"room1"}}
//   > {"type":"private","data":{"toUserId":"alice","text":"私聊"}}
//
// ③ 浏览器端 JS 测试片段(在 DevTools Console 执行):
// ------------------------------------------------------------------
//   // 1. 拿 token
//   const r = await fetch('/api/login', {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ userId: 'browser-user' })
//   });
//   const { token } = await r.json();
//
//   // 2. 建 WebSocket
//   const ws = new WebSocket(`ws://${location.host}/ws?token=${token}`);
//   ws.onopen  = () => { console.log('已连接'); ws.send(JSON.stringify({ type: 'join', data: { roomId: 'room1' } })); };
//   ws.onmessage = (e) => console.log('<<', JSON.parse(e.data));
//   ws.onclose = (e) => console.log('断开', e.code, e.reason);
//   ws.onerror = console.error;
//
//   // 3. 发消息
//   ws.send(JSON.stringify({ type: 'chat', data: { roomId: 'room1', text: '来自浏览器' } }));
//
//   // 4. 模拟断线重连(指数退避)
//   let retry = 0;
//   function connect() {
//     const ws2 = new WebSocket(`ws://${location.host}/ws?token=${token}`);
//     ws2.onclose = () => {
//       retry++;
//       const delay = Math.min(1000 * 2 ** retry, 30000); // 1s,2s,4s...上限 30s
//       console.log(`断开, ${delay}ms 后重连`);
//       setTimeout(connect, delay);
//     };
//   }
// ------------------------------------------------------------------
//
// ④ 查看状态:
//   curl http://localhost:3000/api/health
//   curl http://localhost:3000/api/rooms
//   curl http://localhost:3000/api/users

const express = require('express');
const http = require('http');
const crypto = require('crypto');
const { WebSocketServer, WebSocket } = require('ws');

const PORT = process.env.PORT || 3000;
const HEARTBEAT_INTERVAL = 30_000;
const MAX_CLIENTS = 1000; // 最大连接数, 防止资源耗尽

// ---- 演示用 token 仓库(真实项目应存 Redis/JWT) ----
// userId -> { token, user }
const tokenStore = new Map();
function issueToken(userId) {
  const token = `${userId}-${crypto.randomBytes(4).toString('hex')}`;
  const user = { id: userId, role: 'user' };
  tokenStore.set(token, user);
  return { token, user };
}
function verifyToken(token) {
  if (!token) return null;
  return tokenStore.get(token) || null;
}

// ---- 业务状态 ----
const userMap = new Map(); // userId -> ws
const roomMap = new Map(); // roomId -> Set<userId>

// ---- Express 应用 ----
const app = express();
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    clients: wss.clients.size,
    rooms: roomMap.size,
    timestamp: Date.now()
  });
});

app.post('/api/login', (req, res) => {
  const { userId } = req.body || {};
  if (!userId || typeof userId !== 'string') {
    return res.status(400).json({ error: '需要 userId' });
  }
  const { token, user } = issueToken(userId);
  res.json({ token, user });
});

app.get('/api/rooms', (req, res) => {
  const rooms = {};
  for (const [roomId, users] of roomMap) {
    rooms[roomId] = Array.from(users);
  }
  res.json({ rooms });
});

app.get('/api/users', (req, res) => {
  res.json({ count: userMap.size, users: Array.from(userMap.keys()) });
});

// ---- http server + noServer 模式 ws ----
const server = http.createServer(app);
const wss = new WebSocketServer({ noServer: true });

// 在 upgrade 握手阶段校验 token
server.on('upgrade', (req, socket, head) => {
  // 最大连接数限制
  if (wss.clients.size >= MAX_CLIENTS) {
    socket.write('HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\n\r\n');
    socket.destroy();
    console.log('[拒绝] 连接数已达上限', MAX_CLIENTS);
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);
  // 只接受 /ws 路径
  if (url.pathname !== '/ws') {
    socket.write('HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n');
    socket.destroy();
    return;
  }

  const token = url.searchParams.get('token');
  const user = verifyToken(token);
  if (!user) {
    socket.write(
      'HTTP/1.1 401 Unauthorized\r\n' +
      'X-WS-Auth-Error: invalid or missing token\r\n' +
      'Connection: close\r\n\r\n'
    );
    socket.destroy();
    console.log(`[拒绝] ${req.socket.remoteAddress} 鉴权失败`);
    return;
  }

  // 通过校验, 完成 ws 握手, 把 user 作为第 3 个参数透传给 connection 事件
  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit('connection', ws, req, user);
  });
});

// ---- 心跳 ----
const heartbeatTimer = setInterval(() => {
  wss.clients.forEach((ws) => {
    if (ws.isAlive === false) {
      console.log(`[terminate] 僵尸连接 user=${ws.user && ws.user.id}`);
      ws.terminate();
      return;
    }
    ws.isAlive = false;
    ws.ping();
  });
}, HEARTBEAT_INTERVAL);

function attachHeartbeat(ws) {
  ws.isAlive = true;
  ws.on('pong', () => { ws.isAlive = true; });
}

// ---- 消息工具 ----
function send(ws, obj) {
  if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

function broadcastToRoom(roomId, obj, excludeUserId = null) {
  const users = roomMap.get(roomId);
  if (!users) return 0;
  const payload = JSON.stringify(obj);
  let n = 0;
  for (const uid of users) {
    if (uid === excludeUserId) continue;
    const w = userMap.get(uid);
    if (w && w.readyState === WebSocket.OPEN) { w.send(payload); n++; }
  }
  return n;
}

function pushPresence(roomId) {
  const users = roomMap.get(roomId);
  if (!users) return;
  broadcastToRoom(roomId, {
    type: 'presence',
    data: { roomId, users: Array.from(users) },
    timestamp: Date.now()
  });
}

// ---- 聊天室业务 ----
function leaveRoom(ws) {
  if (!ws.user || !ws.user.roomId) return;
  const { id, roomId } = ws.user;
  const users = roomMap.get(roomId);
  if (users) {
    users.delete(id);
    if (users.size === 0) roomMap.delete(roomId);
    else {
      broadcastToRoom(roomId, { type: 'system', data: `${id} 离开了房间`, timestamp: Date.now() });
      pushPresence(roomId);
    }
  }
  if (userMap.get(id) === ws) userMap.delete(id); // 防止多端登录互相覆盖
  ws.user.roomId = null;
}

function handleJoin(ws, { roomId }) {
  if (!roomId) return send(ws, { type: 'error', data: 'join 需要 roomId', timestamp: Date.now() });
  if (ws.user.roomId) leaveRoom(ws);
  ws.user.roomId = roomId;
  userMap.set(ws.user.id, ws);
  if (!roomMap.has(roomId)) roomMap.set(roomId, new Set());
  roomMap.get(roomId).add(ws.user.id);
  send(ws, { type: 'system', data: `已加入 ${roomId}, 共 ${roomMap.get(roomId).size} 人`, timestamp: Date.now() });
  broadcastToRoom(roomId, { type: 'system', data: `${ws.user.id} 加入了房间`, timestamp: Date.now() }, ws.user.id);
  pushPresence(roomId);
}

function handleChat(ws, { roomId, text }) {
  if (!ws.user.roomId) return send(ws, { type: 'error', data: '请先 join', timestamp: Date.now() });
  if (ws.user.roomId !== roomId) return send(ws, { type: 'error', data: '你不在该房间', timestamp: Date.now() });
  broadcastToRoom(roomId, {
    type: 'chat', from: ws.user.id, data: { roomId, text }, timestamp: Date.now()
  });
}

function handlePrivate(ws, { toUserId, text }) {
  const target = userMap.get(toUserId);
  if (!target || target.readyState !== WebSocket.OPEN) {
    return send(ws, { type: 'error', data: `${toUserId} 不在线`, timestamp: Date.now() });
  }
  send(target, { type: 'private', from: ws.user.id, data: { text }, timestamp: Date.now() });
  send(ws, { type: 'system', data: `已送达 ${toUserId}`, timestamp: Date.now() });
}

function handleRooms(ws) {
  const rooms = {};
  for (const [rid, users] of roomMap) rooms[rid] = users.size;
  send(ws, { type: 'rooms', data: rooms, timestamp: Date.now() });
}

// ---- 连接生命周期 ----
wss.on('connection', (ws, req, user) => {
  const ip = req.socket.remoteAddress;
  ws.user = { ...user, roomId: null };
  attachHeartbeat(ws);

  console.log(`[+] ${ip} user=${user.id} 在线=${wss.clients.size}`);

  send(ws, {
    type: 'system',
    data: `认证成功 ${user.id}, 可发送 {type:"join", data:{roomId:"room1"}}`,
    timestamp: Date.now()
  });

  ws.on('message', (raw) => {
    let msg;
    try { msg = JSON.parse(raw.toString('utf8')); }
    catch { return send(ws, { type: 'error', data: '需要合法 JSON', timestamp: Date.now() }); }

    switch (msg.type) {
      case 'join':    handleJoin(ws, msg.data || {}); break;
      case 'leave':   leaveRoom(ws); send(ws, { type: 'system', data: '已离开房间', timestamp: Date.now() }); break;
      case 'chat':    handleChat(ws, msg.data || {}); break;
      case 'private': handlePrivate(ws, msg.data || {}); break;
      case 'rooms':   handleRooms(ws); break;
      default: send(ws, { type: 'error', data: `未知类型 ${msg.type}`, timestamp: Date.now() });
    }
  });

  ws.on('close', (code) => {
    leaveRoom(ws);
    console.log(`[-] ${ip} (${user.id}) 断开 code=${code} 剩余在线=${wss.clients.size}`);
  });

  ws.on('error', (err) => console.error('[!]', err.message));
});

// ---- 启动与退出 ----
server.listen(PORT, () => {
  console.log(`服务器已启动: http://localhost:${PORT}`);
  console.log(`  POST /api/login   { userId } -> 拿 token`);
  console.log(`  GET  /api/health`);
  console.log(`  GET  /api/rooms`);
  console.log(`  GET  /api/users`);
  console.log(`  WS   ws://localhost:${PORT}/ws?token=xxx`);
  console.log(`  心跳间隔 ${HEARTBEAT_INTERVAL / 1000}s, 最大连接 ${MAX_CLIENTS}`);
});

// 优雅退出
let shuttingDown = false;
function shutdown(signal) {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log(`\n收到 ${signal}, 关闭中...`);
  clearInterval(heartbeatTimer);
  wss.clients.forEach((ws) => {
    try { ws.close(1001, 'server shutting down'); } catch {}
  });
  wss.close();
  server.close(() => {
    console.log('已关闭');
    process.exit(0);
  });
  // 兜底: 5s 后强制退出
  setTimeout(() => process.exit(1), 5000).unref();
}
process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
