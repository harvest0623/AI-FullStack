// heartbeat.js - 服务端 ping/pong 心跳保活 + 超时踢出
// 运行:
//   npm install
//   node heartbeat.js
//
// 为什么需要心跳?
//   - TCP 连接断开(如客户端断网/拔网线/路由器重启)时, 对端可能收不到 FIN,
//     连接在 OS 层面"半开", 应用层毫无感知 -> "僵尸连接"占资源
//   - 中间代理(Nginx/云网关)常有空闲超时(默认 60s~120s), 无流量会主动断开
//   - 主动发心跳既保活, 又能及时检测死连接
//
// ping/pong 机制(ws 协议层):
//   - ws.ping() 发送一个 protocol-level ping 帧(不是应用层消息)
//   - 对端(浏览器/其它 ws 客户端)收到 ping 会自动回 pong(无需应用代码)
//   - 服务端监听 'pong' 事件收到对端响应, 据此判断连接是否健康
//   - 也可反向: 客户端发 ping, 服务端自动回 pong
//
// 策略:
//   1) 每隔 HEARTBEAT_INTERVAL(30s) 给所有客户端发 ping
//   2) 标记每条连接为 "alive=false", 收到 pong 时置 true
//   3) 下一次心跳时, 若仍 alive=false, 说明上次 ping 没收到 pong -> 视为死连接, terminate()
//   4) terminate() 立即销毁底层 socket(不等关闭握手), 用于踢死连接
//      ws.close() 是"礼貌关闭"(发 close 帧等对方 ack), 死连接用 close 无意义
//
// 测试:
//   wscat -c ws://localhost:8082
//   连上后人为"拔网线"(如直接关掉终端而不发 disconnect), 等约 60s 后服务端应踢出

const { WebSocketServer, WebSocket } = require('ws');

const PORT = 8082;
const HEARTBEAT_INTERVAL = 30_000; // 30s 发一次 ping

const wss = new WebSocketServer({ port: PORT });

// 给每条连接附加一个 isAlive 标志
// 注意: 不能直接在 ws 对象上加任意属性? 实际可以, ws 对象是普通对象, 自定义属性可挂载
function attachHeartbeat(ws) {
  ws.isAlive = true;

  ws.on('pong', () => {
    ws.isAlive = true;
    console.log(`[pong] ${ws._socket.remoteAddress}`);
  });

  ws.on('close', () => {
    ws.isAlive = false;
  });
}

const heartbeatTimer = setInterval(() => {
  wss.clients.forEach((ws) => {
    if (ws.isAlive === false) {
      // 上一次 ping 后一直没收到 pong, 判定为死连接
      console.log(`[terminate] 僵尸连接被踢出: ${ws._socket.remoteAddress}`);
      // terminate() vs close():
      //   terminate() 立即销毁 socket, 不发 close 帧
      //   close() 发 close 帧等对方 ack, 对死连接无意义
      ws.terminate();
      return;
    }

    ws.isAlive = false;
    // 发 ping, 期待对方自动回 pong
    // 第二参可选: 掩码/二进制标识; ping 帧最多 125 字节, 可带点数据
    ws.ping();
  });
}, HEARTBEAT_INTERVAL);

// 心跳清理: wss.close 时也要清 timer
wss.on('close', () => {
  clearInterval(heartbeatTimer);
});

wss.on('connection', (ws, req) => {
  const ip = req.socket.remoteAddress;
  console.log(`[+] 新连接 ${ip}`);
  attachHeartbeat(ws);

  ws.send(JSON.stringify({
    type: 'system',
    data: '已连接, 心跳间隔 30s, 无响应将被踢出',
    timestamp: Date.now()
  }));

  ws.on('message', (data) => {
    console.log(`[<] ${ip}: ${data.toString('utf8')}`);
    ws.send(`[echo] ${data.toString('utf8')}`);
  });

  ws.on('close', (code) => {
    console.log(`[-] ${ip} 断开 code=${code}`);
  });

  ws.on('error', (err) => console.error('[!]', err.message));
});

wss.on('listening', () => {
  console.log(`心跳演示服务器已启动: ws://localhost:${PORT}`);
  console.log('心跳间隔:', HEARTBEAT_INTERVAL / 1000, 's');
  console.log('模拟死连接: 用 wscat 连上后强制关闭终端, ~60s 后服务端会踢出');
});

process.on('SIGINT', () => {
  clearInterval(heartbeatTimer);
  wss.clients.forEach((ws) => ws.terminate());
  wss.close(() => process.exit(0));
});
