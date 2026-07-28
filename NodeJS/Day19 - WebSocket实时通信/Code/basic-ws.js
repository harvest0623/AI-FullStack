// basic-ws.js - 最简 WebSocket 服务器
// 运行:
//   npm install
//   node basic-ws.js
//
// 行为: 任何客户端发来的消息都会被原样回显(加前缀 [echo])
//       新连接 / 断开 / 错误都会打印日志
//
// 浏览器测试代码(打开 Chrome DevTools Console, 在该页所在源下执行):
// ----------------------------------------------------------------------
//   // 注意: 受同源策略限制较松, ws 可跨域; 但页面需为 https 才能连 wss
//   const ws = new WebSocket('ws://localhost:8080');
//
//   ws.onopen = () => {
//     console.log('已连接');
//     ws.send('hello from browser');
//   };
//   ws.onmessage = (ev) => console.log('收到:', ev.data);
//   ws.onerror = (ev) => console.error('错误', ev);
//   ws.onclose = () => console.log('已断开');
//
//   // 继续在 console 里手动发消息:
//   ws.send(JSON.stringify({ type: 'ping', ts: Date.now() }));
// ----------------------------------------------------------------------
//
// 命令行测试(推荐安装 wscat):
//   npm i -g wscat
//   wscat -c ws://localhost:8080
//   > 你好
//   < [echo] 你好

const { WebSocketServer } = require('ws');

const PORT = 8080;

// 方式一: 直接传 port, ws 库内部自建 http server
// 方式二: 传 server 复用已有 http 服务(见 express-ws.js)
const wss = new WebSocketServer({ port: PORT });

wss.on('connection', (ws, req) => {
  // req 是底层 http.IncomingMessage, 可读 headers / socket.remoteAddress
  const ip = req.socket.remoteAddress;
  console.log(`[+] 新连接 来自 ${ip}`);

  // ws.send 发送消息: 字符串 / Buffer / ArrayBuffer, 第二参可选 {binary, fin}
  ws.send(JSON.stringify({
    type: 'system',
    data: '欢迎连接 basic-ws, 你发什么我就回什么',
    timestamp: Date.now()
  }));

  // 收到客户端消息
  ws.on('message', (data, isBinary) => {
    // data 是 Buffer, isBinary 标识是否为二进制帧
    const text = isBinary ? `<binary ${data.length} bytes>` : data.toString('utf8');
    console.log(`[<] 收到: ${text}`);

    // 回显
    ws.send(`[echo] ${text}`);
  });

  ws.on('close', (code, reason) => {
    // code: 关闭码(1000 正常关闭, 1001 端点离开, 1006 异常关闭无码, 1011 服务端内部错误...)
    // reason: 关闭原因 Buffer
    const reasonText = reason ? reason.toString('utf8') : '';
    console.log(`[-] 断开 code=${code} reason=${reasonText || '(无)'}`);
  });

  ws.on('error', (err) => {
    // 注意: 监听 error 否则未捕获会抛出导致进程崩溃
    console.error('[!] 连接错误:', err.message);
  });
});

wss.on('listening', () => {
  console.log(`WebSocket 服务器已启动: ws://localhost:${PORT}`);
  console.log('浏览器测试: 打开 Chrome DevTools Console 执行注释中的代码');
  console.log(`命令行测试: wscat -c ws://localhost:${PORT}`);
});

wss.on('error', (err) => {
  console.error('服务器错误:', err);
});

// 优雅退出
process.on('SIGINT', () => {
  console.log('\n关闭服务器...');
  // 关闭所有客户端连接(发送 1001 going away)
  wss.clients.forEach((ws) => ws.close(1001, 'server shutting down'));
  wss.close(() => process.exit(0));
});
