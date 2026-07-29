/**
 * compression-demo.js - Express + compression 中间件压缩对比
 * ------------------------------------------------------------
 * 运行:
 *   cd Code
 *   npm install
 *   node compression-demo.js
 *
 * 测试:
 *   # 未压缩端点 (返回原始大 JSON)
 *   curl http://localhost:3001/raw -i --compressed -o /dev/null -w "size=%{size_download} time=%{time_total}\n"
 *
 *   # 压缩端点 (gzip)
 *   curl http://localhost:3001/gz -i --compressed -o /dev/null -w "size=%{size_download} time=%{time_total}\n"
 *
 *   # 查看 gzip 响应头
 *   curl http://localhost:3001/gz -I --compressed
 *
 * 演示要点:
 *   - 同一份大 JSON, 未压缩 ~XX KB, gzip 后通常只剩 5%-15%
 *   - 客户端必须带 Accept-Encoding: gzip, 否则中间件不压缩
 *   - 压缩消耗少量 CPU 换取显著的网络带宽, 对弱网/移动端收益巨大
 * ------------------------------------------------------------
 */

'use strict';

const express = require('express');
const compression = require('compression');
const { performance } = require('perf_hooks');

const app = express();
const PORT = 3001;

// 造一份大 JSON: 模拟一个返回 2000 条记录的列表接口
function buildBigPayload() {
  const list = [];
  for (let i = 0; i < 2000; i++) {
    list.push({
      id: i,
      name: `用户_${i}`,
      email: `user${i}@example.com`,
      avatar: `https://cdn.example.com/avatars/${i}.png`,
      bio: '这是一段重复的个人简介, 用来让 gzip 压缩率更明显, 因为重复文本压缩比极高。'.repeat(3),
      createdAt: new Date().toISOString()
    });
  }
  return { total: list.length, page: 1, data: list };
}

const PAYLOAD = buildBigPayload();
const PAYLOAD_JSON = JSON.stringify(PAYLOAD);
const RAW_BYTES = Buffer.byteLength(PAYLOAD_JSON);

// ---- /raw: 不挂 compression, 原样返回 ----
app.get('/raw', (req, res) => {
  const t0 = performance.now();
  res.set('Content-Type', 'application/json; charset=utf-8');
  res.send(PAYLOAD_JSON);
  const dt = performance.now() - t0;
  console.log(`[raw] 响应字节数=${RAW_BYTES}, 序列化+发送耗时=${dt.toFixed(2)}ms`);
});

// ---- /gz: 挂 compression, 自动 gzip ----
// 只对 /gz 及其子路径生效, 演示"按需挂载"
app.use('/gz', compression());
app.get('/gz', (req, res) => {
  const t0 = performance.now();
  res.set('Content-Type', 'application/json; charset=utf-8');
  res.send(PAYLOAD_JSON);
  const dt = performance.now() - t0;
  console.log(`[gz]  响应字节数=${RAW_BYTES}(压缩后由中间件处理), 序列化+发送耗时=${dt.toFixed(2)}ms`);
});

// ---- 启动 ----
app.listen(PORT, () => {
  console.log(`compression-demo 启动: http://localhost:${PORT}`);
  console.log(`原始 JSON 体积: ${(RAW_BYTES / 1024).toFixed(1)} KB\n`);
  console.log('对比命令 (PowerShell 可用 curl.exe):');
  console.log('  curl http://localhost:' + PORT + '/raw -o nul -w "raw  size=%{size_download} bytes\n"');
  console.log('  curl http://localhost:' + PORT + '/gz  -o nul -w "gzip size=%{size_download} bytes\n" --compressed');
  console.log('  curl http://localhost:' + PORT + '/gz -I --compressed   (查看 Content-Encoding: gzip)\n');
  console.log('提示: --compressed 让 curl 声明 Accept-Encoding: gzip, 否则中间件不会压缩\n');
});
