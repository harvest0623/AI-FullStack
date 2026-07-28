// chat-room.js - 完整聊天室: 用户加入/离开、广播、私聊、房间概念
// 运行:
//   npm install
//   node chat-room.js
//
// 消息协议(JSON, 统一 {type, data, timestamp} 结构, 必要时加 from/to/roomId):
//
//   客户端 -> 服务端:
//     { type: 'join',   data: { userId, roomId } }            加入房间
//     { type: 'leave',  data: { roomId } }                    离开房间
//     { type: 'chat',   data: { roomId, text } }              房间内发言
//     { type: 'private',data: { toUserId, text } }            私聊
//
//   服务端 -> 客户端:
//     { type: 'system', data: '...', timestamp }              系统提示
//     { type: 'chat',   from, data: { roomId, text }, ts }    房间消息
//     { type: 'private',from, data: { text }, ts }            私聊消息
//     { type: 'error',  data: '...', timestamp }              错误
//     { type: 'presence', data: { roomId, users: [] }, ts }   在线名单变更
//
// 数据结构:
//   userMap:    Map<userId, ws>           —— 全局用户表(私聊用)
//   roomMap:    Map<roomId, Set<userId>>  —— 房间成员(用 userId 而非 ws,
//                                            避免一个用户多端登录时 Set 难维护)
//   ws.user:    { id, name }              —— 在 ws 上挂用户信息, 断开时据此清理
//
// 测试(开 3 个终端):
//   # 终端 A
//   wscat -c ws://localhost:8083
//   > {"type":"join","data":{"userId":"u1","roomId":"room1"}}
//   > {"type":"chat","data":{"roomId":"room1","text":"hi"}}
//   # 终端 B
//   wscat -c ws://localhost:8083
//   > {"type":"join","data":{"userId":"u2","roomId":"room1"}}
//   > {"type":"private","data":{"toUserId":"u1","text":"私聊你好"}}
//   # 终端 C 不加入房间, 收不到 room1 的消息

const { WebSocketServer, WebSocket } = require('ws');

const PORT = 8083;

const wss = new WebSocketServer({ port: PORT });

// ---- 状态: 用户表 + 房间表 ----
const userMap = new Map(); // userId -> ws
const roomMap = new Map(); // roomId -> Set<userId>

// ---- 消息工具 ----
function send(ws, obj) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj));
  }
}

function broadcast(obj) {
  const payload = JSON.stringify(obj);
  wss.clients.forEach((c) => {
    if (c.readyState === WebSocket.OPEN) c.send(payload);
  });
}

// 给房间内所有人发(可选排除某用户)
function broadcastToRoom(roomId, obj, excludeUserId = null) {
  const users = roomMap.get(roomId);
  if (!users) return 0;
  const payload = JSON.stringify(obj);
  let n = 0;
  for (const uid of users) {
    if (uid === excludeUserId) continue;
    const targetWs = userMap.get(uid);
    if (targetWs && targetWs.readyState === WebSocket.OPEN) {
      targetWs.send(payload);
      n++;
    }
  }
  return n;
}

// 推送房间在线名单
function pushPresence(roomId) {
  const users = roomMap.get(roomId);
  if (!users) return;
  broadcastToRoom(roomId, {
    type: 'presence',
    data: { roomId, users: Array.from(users) },
    timestamp: Date.now()
  });
}

// ---- 业务处理 ----
function handleJoin(ws, { userId, roomId }) {
  if (!userId || !roomId) {
    return send(ws, { type: 'error', data: 'join 需要 userId 与 roomId', timestamp: Date.now() });
  }

  // 同一用户重复 join: 先离开旧房间
  if (ws.user) {
    leaveRoom(ws);
  }

  ws.user = { id: userId, roomId };
  userMap.set(userId, ws);

  if (!roomMap.has(roomId)) roomMap.set(roomId, new Set());
  roomMap.get(roomId).add(userId);

  send(ws, {
    type: 'system',
    data: `已加入房间 ${roomId}, 当前房间 ${roomMap.get(roomId).size} 人`,
    timestamp: Date.now()
  });
  broadcastToRoom(roomId, {
    type: 'system',
    data: `${userId} 加入了房间`,
    timestamp: Date.now()
  }, userId);
  pushPresence(roomId);
}

function leaveRoom(ws) {
  if (!ws.user) return;
  const { id: userId, roomId } = ws.user;
  const users = roomMap.get(roomId);
  if (users) {
    users.delete(userId);
    if (users.size === 0) roomMap.delete(roomId);
    else {
      broadcastToRoom(roomId, {
        type: 'system',
        data: `${userId} 离开了房间`,
        timestamp: Date.now()
      });
      pushPresence(roomId);
    }
  }
  userMap.delete(userId);
  ws.user = null;
}

function handleLeave(ws) {
  leaveRoom(ws);
  send(ws, { type: 'system', data: '已离开房间', timestamp: Date.now() });
}

function handleChat(ws, { roomId, text }) {
  if (!ws.user) {
    return send(ws, { type: 'error', data: '请先 join', timestamp: Date.now() });
  }
  // 防止跨房间发消息: 校验调用者确实在该房间
  if (ws.user.roomId !== roomId) {
    return send(ws, { type: 'error', data: '你不在该房间', timestamp: Date.now() });
  }
  const msg = {
    type: 'chat',
    from: ws.user.id,
    data: { roomId, text },
    timestamp: Date.now()
  };
  broadcastToRoom(roomId, msg);
}

function handlePrivate(ws, { toUserId, text }) {
  if (!ws.user) {
    return send(ws, { type: 'error', data: '请先 join', timestamp: Date.now() });
  }
  const target = userMap.get(toUserId);
  if (!target || target.readyState !== WebSocket.OPEN) {
    return send(ws, { type: 'error', data: `用户 ${toUserId} 不在线`, timestamp: Date.now() });
  }
  send(target, {
    type: 'private',
    from: ws.user.id,
    data: { text },
    timestamp: Date.now()
  });
  // 给发送者一份回执(确认已送达)
  send(ws, {
    type: 'system',
    data: `私聊已送达 ${toUserId}`,
    timestamp: Date.now()
  });
}

// ---- 连接生命周期 ----
wss.on('connection', (ws, req) => {
  const ip = req.socket.remoteAddress;
  console.log(`[+] 新连接 ${ip}`);

  ws.on('message', (raw) => {
    let msg;
    try {
      msg = JSON.parse(raw.toString('utf8'));
    } catch {
      return send(ws, { type: 'error', data: '消息必须是合法 JSON', timestamp: Date.now() });
    }

    console.log(`[<] ${ip}`, msg);

    switch (msg.type) {
      case 'join':    handleJoin(ws, msg.data || {}); break;
      case 'leave':   handleLeave(ws); break;
      case 'chat':    handleChat(ws, msg.data || {}); break;
      case 'private': handlePrivate(ws, msg.data || {}); break;
      default:
        send(ws, { type: 'error', data: `未知消息类型: ${msg.type}`, timestamp: Date.now() });
    }
  });

  ws.on('close', () => {
    leaveRoom(ws);
    console.log(`[-] ${ip} 断开`);
  });

  ws.on('error', (err) => console.error('[!]', err.message));

  send(ws, {
    type: 'system',
    data: '欢迎使用 chat-room, 请发送 {type:"join", data:{userId, roomId}} 加入房间',
    timestamp: Date.now()
  });
});

wss.on('listening', () => {
  console.log(`聊天室服务器已启动: ws://localhost:${PORT}`);
  console.log('消息协议示例: {"type":"join","data":{"userId":"u1","roomId":"r1"}}');
});

process.on('SIGINT', () => {
  broadcast({ type: 'system', data: '服务器关闭', timestamp: Date.now() });
  wss.clients.forEach((ws) => ws.close(1001, 'shutdown'));
  wss.close(() => process.exit(0));
});
