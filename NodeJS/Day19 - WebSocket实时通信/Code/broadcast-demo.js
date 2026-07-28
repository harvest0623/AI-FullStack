// broadcast-demo.js - 演示广播、wss.clients 遍历、连接状态判断
// 运行:
//   npm install
//   node broadcast-demo.js
//
// 行为:
//   1) 任意客户端发来的消息会广播给所有"当前在线且处于 OPEN 状态"的客户端
//   2) 服务端每 10 秒主动推送一次"系统广播"(演示服务端主动 push)
//   3) 控制台实时打印当前在线人数
//
// 测试: 开多个终端窗口执行 wscat -c ws://localhost:8081
//   在任一窗口输入文字, 其它窗口应同步收到
//
// wss.clients 关键点:
//   - 是 Set<WebSocket>, 仅包含当前 wss 实例下的活跃连接
//   - 客户端断开后会被自动从 Set 中移除
//   - 遍历广播时必须先判断 ws.readyState === ws.OPEN, 否则对 CLOSING/CLOSED 状态的 ws.send 会抛错

// ws 模块导出的 WebSocket 类上有 OPEN/CLOSING/CLOSED/CONNECTING 常量
// 实例对象也能通过 ws.OPEN 访问这些静态常量(值=1)
const { WebSocketServer, WebSocket } = require('ws');

const PORT = 8081;
const wss = new WebSocketServer({ port: PORT });

// 封装一个安全广播函数: 跳过非 OPEN 连接, 可排除发送者
function broadcast(message, excludeWs = null) {
  const payload = typeof message === 'string' ? message : JSON.stringify(message);
  let sent = 0;
  for (const client of wss.clients) {
    // ws.readyState 取值:
    //   0 CONNECTING  1 OPEN  2 CLOSING  3 CLOSED
    //   用 WebSocket.OPEN 常量(=1) 比魔法数字更可读
    if (client.readyState === WebSocket.OPEN && client !== excludeWs) {
      client.send(payload);
      sent++;
    }
  }
  return sent;
}

wss.on('connection', (ws, req) => {
  const ip = req.socket.remoteAddress;
  console.log(`[+] ${ip} 上线, 当前在线 ${wss.clients.size}`);

  // 给新成员发欢迎
  ws.send(JSON.stringify({
    type: 'system',
    data: `欢迎, 当前共 ${wss.clients.size} 人在线`,
    timestamp: Date.now()
  }));

  // 广播"有人加入"
  broadcast({
    type: 'system',
    data: `新人加入(${ip}), 在线 ${wss.clients.size}`,
    timestamp: Date.now()
  }, ws);

  ws.on('message', (data) => {
    const text = data.toString('utf8');
    console.log(`[<] ${ip}: ${text}`);

    // 广播给除自己以外的所有人(模拟聊天室"别人说话我也能看到")
    const ok = broadcast({
      type: 'chat',
      from: ip,
      data: text,
      timestamp: Date.now()
    }, ws);

    // 给发送者回执
    ws.send(JSON.stringify({
      type: 'system',
      data: `已广播给 ${ok} 人`,
      timestamp: Date.now()
    }));
  });

  ws.on('close', () => {
    console.log(`[-] ${ip} 下线, 当前在线 ${wss.clients.size}`);
    broadcast({
      type: 'system',
      data: `有人离开(${ip}), 在线 ${wss.clients.size}`,
      timestamp: Date.now()
    });
  });

  ws.on('error', (err) => console.error('[!]', err.message));
});

// 服务端定时主动 push(模拟后端有新事件时推送)
const timer = setInterval(() => {
  if (wss.clients.size === 0) return;
  const n = broadcast({
    type: 'system',
    data: `[定时广播 ${new Date().toLocaleTimeString()}] 在线 ${wss.clients.size} 人`,
    timestamp: Date.now()
  });
  console.log(`[广播] 推送至 ${n} 个客户端`);
}, 10_000);

wss.on('listening', () => {
  console.log(`广播演示服务器已启动: ws://localhost:${PORT}`);
  console.log(`多开几个终端: wscat -c ws://localhost:${PORT}`);
});

process.on('SIGINT', () => {
  clearInterval(timer);
  broadcast({ type: 'system', data: '服务器即将关闭', timestamp: Date.now() });
  wss.clients.forEach((ws) => ws.close(1001, 'shutdown'));
  wss.close(() => process.exit(0));
});
