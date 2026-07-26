/**
 * Day09 - HTTP 模块与原生 Web 服务器
 * 文件：hello-server.js
 * 主题：最简 HTTP 服务器
 *
 * 演示：
 *   1. http.createServer 创建服务器
 *   2. request handler 回调的 req / res 参数
 *   3. res.writeHead / res.end 的最小用法
 *   4. server.listen 启动监听
 *
 * 运行：
 *   node Code/hello-server.js
 *
 * 测试（另开终端）：
 *   curl http://localhost:3000
 *   curl http://localhost:3000/anything
 *   curl -i http://localhost:3000         # 看完整响应头
 */

'use strict';

const http = require('http');

// createServer 接收一个回调，每来一个请求就同步调用一次
//   req:  http.IncomingMessage —— 读请求（Readable 流 + 请求行/头）
//   res:  http.ServerResponse —— 写响应（Writable 流 + 响应方法）
const server = http.createServer((req, res) => {
  // 1. 打印一下收到了什么（学习期调试用，生产别打太多日志）
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);

  // 2. 写响应：状态码 + 响应头（一次性写）
  //    Content-Type 决定客户端如何解析响应体
  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });

  // 3. 结束响应并写入响应体
  //    不调用 end 会让客户端一直挂起到超时——这是新手最常忘的一步
  res.end('Hello HTTP\n');
});

// 监听 3000 端口；回调在 listening 事件触发时执行
const PORT = 3000;
server.listen(PORT, () => {
  console.log(`服务器已启动：http://localhost:${PORT}`);
  console.log('按 Ctrl+C 停止');
});

// 处理进程级错误，避免悄悄崩溃
process.on('uncaughtException', (err) => {
  console.error('未捕获异常：', err);
});
