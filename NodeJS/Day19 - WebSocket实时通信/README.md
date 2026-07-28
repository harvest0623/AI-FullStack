# Day19 - WebSocket 实时通信

> 作为前端工程师，你已经习惯了 `fetch` / `axios` 这种"一问一答"的 HTTP 模型：客户端发请求、服务端回响应、连接结束。但当你跨入 AI 全栈的领域，会立刻撞上一批"服务端主动推、客户端被动收"或"双向实时"的场景：ChatGPT 那样的逐字流式输出、AI Agent 调用工具时的进度条、多人协同编辑、在线聊天室、向量检索的实时反馈。HTTP 的请求-响应模型在这里力不从心，**WebSocket** 是当前最主流的双向实时通信方案。本篇以你已有的 HTTP 知识为起点，系统讲透 WebSocket 的协议原理、`ws` 库用法、与 Express 的集成、连接管理与鉴权，并落到 AI 全栈的真实业务场景。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 HTTP 的局限：请求-响应单向通信](#21-http-的局限请求-响应单向通信)
  - [2.2 为什么需要实时双向通信](#22-为什么需要实时双向通信)
  - [2.3 实时通信方案对比](#23-实时通信方案对比)
  - [2.4 WebSocket 协议详解](#24-websocket-协议详解)
  - [2.5 WebSocket 与 SSE 的取舍](#25-websocket-与-sse-的取舍)
- [三、ws 库入门](#三ws-库入门)
- [四、与 Express 集成](#四与-express-集成)
- [五、实时通信核心模式](#五实时通信核心模式)
  - [5.1 广播](#51-广播)
  - [5.2 私聊](#52-私聊)
  - [5.3 房间/群组](#53-房间群组)
  - [5.4 消息协议设计](#54-消息协议设计)
- [六、连接管理](#六连接管理)
- [七、鉴权](#七鉴权)
- [八、AI 全栈场景](#八ai-全栈场景)
- [九、关键知识点总结](#九关键知识点总结)
- [十、实战练习](#十实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说清 HTTP 请求-响应模型为什么不适合实时双向通信，能列举至少 4 类必须用实时通信的 AI 全栈场景。
2. 对比轮询 / 长轮询 / SSE / WebSocket / WebRTC 五种方案，从方向、延迟、开销、复杂度、适用场景维度给出选型建议。
3. 描述 WebSocket 的握手流程：客户端发 `Upgrade: websocket` 请求、服务端回 `101 Switching Protocols`、之后在同一 TCP 连接上用帧（frame）双向通信；区分 `ws://` 与 `wss://`。
4. 解释全双工、持久连接、帧、心跳 `ping/pong` 的含义，并说出为什么必须做心跳保活（半开连接、代理超时）。
5. 用 `ws` 库写出最简 WebSocket 服务器：`new WebSocketServer({ port })`、`connection` 事件、`ws.send` / `ws.on('message')` / `close` / `error`、`wss.clients`、`readyState`、`ping/pong`。
6. 让 WebSocket 与 Express 共享同一端口：掌握 `{ server }` 直连与 `{ noServer: true } + handleUpgrade` 两种方式，并知道何时必须用后者。
7. 实现广播、私聊（`Map<userId, ws>`）、房间（`Map<roomId, Set<userId>>`）三种核心模式，设计一份 `{type, data, timestamp}` 的 JSON 消息协议。
8. 做好连接管理：在线用户列表、客户端指数退避重连、心跳超时踢出、最大连接数限制、发送失败消息队列。
9. 在 upgrade 握手阶段校验 token（query 或 header），用 `socket.destroy()` 或 `ws.close(4001)` 拒绝非法连接，并知道浏览器 `new WebSocket` 无法自定义 header 的限制。
10. 把 WebSocket 用到 AI 全栈：流式响应转发、聊天机器人实时回答、Agent 工具调用进度推送、向量检索进度反馈，并能判断 WebSocket 与 SSE 各自更合适的场景。

---

## 二、理论知识讲解

### 2.1 HTTP 的局限：请求-响应单向通信

HTTP 是一个**请求-响应**协议：永远是客户端先开口（发请求），服务端才能回话（返响应），回完这条 TCP 上的"一轮对话"就结束了（HTTP/1.1 默认 `keep-alive` 复用连接，但语义模型仍是"一问一答"）。

这套模型对"客户端要数据"的传统 Web 完美适配，但有三个硬伤：

| 局限 | 表现 | 例子 |
|------|------|------|
| 服务端无法主动推送 | 服务端有新数据时，必须等客户端来问才能给 | 聊天：对方发消息，你这边不知道 |
| 每次请求都要带完整头部 | Header 动辄几百字节~几 KB，频繁通信时开销大 | 实时股价：每秒 10 次请求，大部分字节是 Header |
| 状态零散 | 每次请求要重新建立"上下文"（鉴权、会话） | 协同编辑：每次都要重传文档状态 |

前端工程师最熟悉的"绕过办法"是**轮询**：用 `setInterval` 每隔几秒 `fetch` 一次问"有新消息吗？"。它能用，但延迟高（平均 = 间隔/2）、无效请求多、浪费带宽。WebSocket 就是为解决这些问题而生。

### 2.2 为什么需要实时双向通信

下面四类场景在前端页面里少见，但在 AI 全栈里几乎是日常：

1. **聊天 / IM**：用户发消息、对方消息要即时回推，双向、低延迟（<500ms）。
2. **协同编辑 / 协同画板**：多人同时改一份文档，每次按键都要广播给其他人，要求双向、高频、有序。Figma、腾讯文档、飞书文档都走 WebSocket（或自研协议）。
3. **实时推送 / 通知**：站内信、订单状态变更、监控告警。服务端有事件就推，无需客户端轮询。
4. **AI 流式输出**：大模型生成 token 是逐个产出的，让用户等 30 秒再一次性返回 2000 字，体验灾难；流式逐字返回（打字机效果）是当前 AI 产品的标配。这是前端工程师转 AI 全栈**最常踩**的实时通信场景。

这四类的共性是：要么服务端要主动推，要么客户端要频繁发、服务端要频繁回，要么两者兼有。HTTP 一问一答勉强能做（用 SSE 或流式 HTTP），但双向高频时 WebSocket 更自然。

### 2.3 实时通信方案对比

实现"实时通信"不止 WebSocket 一种。下表是主流方案的横向对比，选型时先看场景再定方案：

| 方案 | 方向 | 延迟 | 开销 | 复杂度 | 适用场景 |
|------|------|------|------|--------|----------|
| **短轮询** (Polling) | 客户端→服务端（拉） | 高（=间隔） | 高（大量空请求） | 极低 | 兼容性要求高、实时性要求低；如旧版邮件刷新 |
| **长轮询** (Long Polling) | 客户端→服务端（拉） | 中低 | 中（保持请求） | 中 | WebSocket 不可用时的降级方案；早期微信网页版 |
| **SSE** (Server-Sent Events) | 服务端→客户端（单向推） | 低 | 低（基于 HTTP 持久连接） | 低 | 服务端单向推送：通知、AI 流式输出、订阅行情 |
| **WebSocket** | 双向（全双工） | 极低 | 低（握手后无 Header） | 中 | 双向高频：聊天、协同、游戏、Agent 进度 |
| **WebRTC** | 双向（P2P） | 极低 | 低（数据直连不经服务端） | 高 | 音视频通话、P2P 文件传输、低延迟数据通道 |

几个选型要点：

- **能 SSE 就别上 WebSocket**。如果只是"服务端推、客户端收"（如 AI 流式输出、通知），SSE 更简单：基于 HTTP、自动重连、浏览器原生 `EventSource` 一行搞定。
- **双向高频才用 WebSocket**。聊天、协同编辑这种客户端也要频繁发消息的，WebSocket 全双工更合适。
- **WebRTC 是另一个世界**。它解决的是浏览器之间直连（P2P）传音视频或大数据，需要信令服务器（往往也用 WebSocket 协助建连）。本篇不展开。
- **轮询是兜底**。WebSocket/SSE 在某些公司网络（代理、防火墙）会被拦截，轮询是最稳的降级方案。

### 2.4 WebSocket 协议详解

WebSocket 协议（RFC 6455）的设计哲学是：**借 HTTP 上车，然后脱掉 HTTP 的壳，变成一条双向裸管道**。

#### ① 基于 HTTP 升级握手

WebSocket 连接的建立是一次"特殊"的 HTTP 请求。客户端发一个带有升级头的 GET 请求：

```http
GET /ws HTTP/1.1
Host: example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

服务端同意升级，回 `101 Switching Protocols`：

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

`Sec-WebSocket-Accept` 是服务端用 `Sec-WebSocket-Key` + 固定 GUID（`258EAFA5-E914-47DA-95CA-C5AB0DC85B11`）做 SHA-1 再 Base64 的结果，用于防跨协议误用。握手成功后，**这条 TCP 连接就不再是 HTTP 了**——双方在它上面收发 WebSocket 帧。

> 这就是为什么 WebSocket 能复用 80/443 端口、能穿过大多数 HTTP 代理：它开头长得像 HTTP，代理放行；握手后代理若支持透传（CONNECT 隧道）就继续当 TCP 转发。

#### ② ws 与 wss 协议

- `ws://`：明文，类似 `http://`，默认端口 80。
- `wss://`：TLS 加密，类似 `https://`，默认端口 443。

生产环境**必须用 `wss://`**。`ws://` 下 token、消息内容全裸传输，且浏览器允许在 `https://` 页面里连 `ws://` 时会触发混合内容拦截（现代浏览器直接拒绝）。

#### ③ 全双工与持久连接

握手后这条连接是**全双工**的：客户端和服务端可**随时**主动发消息，不需要对方先开口。连接持久保持，直到某一方发 `close` 帧或网络中断。这跟 HTTP 的"一问一答就断"形成鲜明对比。

#### ④ 帧 frame

WebSocket 通信的最小单位是**帧**（frame），不是 HTTP 那样的"请求-响应"。常见帧类型：

| opcode | 类型 | 说明 |
|--------|------|------|
| `0x1` | 文本帧 | 负载是 UTF-8 文本（最常用，传 JSON） |
| `0x2` | 二进制帧 | 负载是二进制（传图片、文件、protobuf） |
| `0x8` | 关闭帧 | 主动关闭连接，可带关闭码与原因 |
| `0x9` | ping 帧 | 心跳探测 |
| `0xA` | pong 帧 | 心跳响应（收到 ping 自动回） |

应用代码里 `ws.send(JSON.stringify(...))` 发的是文本帧；`ws.send(Buffer)` 发的是二进制帧。ping/pong 是协议层的，浏览器收到 ping 会**自动**回 pong，无需业务代码。

> 大消息会被拆成多个**分片帧**（fin 位标记是否最后一片），`ws` 库会自动组装，业务层通常感知不到。

#### ⑤ 心跳 ping/pong

为什么必须有心跳？

- **半开连接**：客户端断网/拔网线/路由器重启，TCP FIN 可能发不出去，服务端 OS 层面连接还在，但应用层已经收不到任何数据——"僵尸连接"白白占资源。
- **代理空闲超时**：Nginx、云网关、负载均衡器常有 60s~120s 空闲超时，长时间无流量的连接会被静默断开，业务层无感知。

心跳策略：服务端每 30s 给所有客户端发 `ping`，收到 `pong` 标记存活；下一轮若仍没收到 `pong`，判定为死连接，`terminate()` 立即销毁。`terminate` 与 `close` 的区别见 [六、连接管理](#六连接管理)。

### 2.5 WebSocket 与 SSE 的取舍

前端工程师做 AI 全栈最容易混淆的就是这两个。它们都能"服务端推"，但定位完全不同。

| 维度 | SSE (Server-Sent Events) | WebSocket |
|------|--------------------------|-----------|
| 通信方向 | **单向**（服务端→客户端） | **双向**（全双工） |
| 底层协议 | HTTP（普通长连接响应） | HTTP 升级后切到 WebSocket 协议 |
| 浏览器 API | `EventSource`（极简） | `WebSocket`（稍复杂） |
| 自动重连 | **内置**，断线自动重连 + `Last-Event-ID` 续传 | 无，需自己实现（指数退避） |
| 二进制 | 不支持（只能文本） | 支持 |
| 最大连接数 | 浏览器对同域 HTTP/1.1 限 6 个 | 无此限制 |
| 鉴权 | 走 HTTP header（`Authorization`）方便 | 浏览器无法自定义 header，需 query 或子协议 |
| 典型场景 | 通知、订阅、**AI 流式输出**、消息推送 | 聊天、协同编辑、Agent 进度、游戏 |

**选型口诀**：

- 只推不收 → **SSE**（更简单、自动重连、HTTP 友好）。
- 双向高频 → **WebSocket**（全双工、低开销）。
- AI 流式输出 → **优先 SSE**（OpenAI、Anthropic 官方流式接口就是 SSE；后端把上游 SSE 转发给前端，天然契合）。
- 但如果你的 AI 场景里**客户端也要频繁发**（如语音对话边录边转、协同 + AI 补全），用 WebSocket 一个连接搞定双向更省事。

> 很多 AI 产品（如 ChatGPT 网页版）混用：主聊天用 SSE 流式输出，语音输入用 WebSocket。不必教条。

---

## 三、ws 库入门

Node.js 生态里 WebSocket 服务端事实标准是 [`ws`](https://github.com/websockets/ws) 库——轻量、纯 JS、无原生依赖、性能好。Socket.IO 内部也基于它。本篇所有示例都用 `ws`。

### 3.1 安装与最小服务器

```bash
npm install ws
```

最简服务器（见 `Code/basic-ws.js`）：

```js
const { WebSocketServer } = require('ws');

const wss = new WebSocketServer({ port: 8080 });

wss.on('connection', (ws, req) => {
  const ip = req.socket.remoteAddress;
  console.log(`新连接 ${ip}`);

  ws.send('欢迎'); // 主动发

  ws.on('message', (data, isBinary) => {
    const text = data.toString('utf8');
    ws.send(`[echo] ${text}`); // 回显
  });

  ws.on('close', (code, reason) => {
    console.log(`断开 code=${code}`);
  });

  ws.on('error', (err) => {
    console.error('错误', err.message);
  });
});
```

### 3.2 两种创建方式

| 方式 | 写法 | 适用 |
|------|------|------|
| 独立端口 | `new WebSocketServer({ port: 8080 })` | 纯 WS 服务，无 HTTP 接口 |
| 复用 http server | `new WebSocketServer({ server })` | HTTP 与 WS 共享端口（见第四节） |
| 手动握手 | `new WebSocketServer({ noServer: true })` + `handleUpgrade` | 需在握手前拦截（鉴权、按路径分发） |

### 3.3 核心 API 速查

| API | 说明 |
|-----|------|
| `wss.on('connection', (ws, req) => {})` | 新连接建立，`req` 是底层 HTTP 请求（可读 header / IP） |
| `wss.on('listening', ...)` | 服务器开始监听 |
| `wss.clients` | `Set<WebSocket>`，当前所有活跃连接 |
| `wss.close([cb])` | 关闭服务器 |
| `ws.send(data, [opts], [cb])` | 发消息，`data` 可为 string / Buffer / ArrayBuffer |
| `ws.on('message', (data, isBinary) => {})` | 收消息 |
| `ws.on('close', (code, reason) => {})` | 关闭，`code` 是关闭码，`reason` 是 Buffer |
| `ws.on('error', (err) => {})` | 出错——**务必监听**，否则未捕获错误会崩进程 |
| `ws.readyState` | 状态：`0 CONNECTING` / `1 OPEN` / `2 CLOSING` / `3 CLOSED`，可用 `WebSocket.OPEN` 常量比较 |
| `ws.ping([data])` | 发心跳 ping，对端自动回 pong |
| `ws.on('pong', () => {})` | 收到对端 pong |
| `ws.close([code], [reason])` | 礼貌关闭（发 close 帧，等对方 ack） |
| `ws.terminate()` | 立即销毁底层 socket，不等关闭握手（用于踢死连接） |

> 关闭码常用值：`1000` 正常关闭、`1001` 端点离开、`1006` 异常关闭（无码）、`1011` 服务端内部错误、`4001+` 自定义码（业务用，如鉴权失败）。

### 3.4 浏览器端测试

`ws` 库是 Node 端的，浏览器端用原生 `WebSocket` 全局对象：

```js
const ws = new WebSocket('ws://localhost:8080');
ws.onopen = () => ws.send('hello');
ws.onmessage = (e) => console.log('收到', e.data);
ws.onclose = () => console.log('断开');
ws.onerror = (e) => console.error('错误', e);
```

开发期也可用命令行工具 `wscat` 调试：

```bash
npm i -g wscat
wscat -c ws://localhost:8080
```

---

## 四、与 Express 集成

让 HTTP 接口与 WebSocket 共享同一个端口（同一个 `http.Server`），既能省端口，又能让前端用同一域名访问，便于鉴权与部署。

### 4.1 方式 A：`{ server }` 直连

最简单，`ws` 库自动监听 `http.Server` 的 `upgrade` 事件（见 `Code/express-ws.js`）：

```js
const express = require('express');
const http = require('http');
const { WebSocketServer } = require('ws');

const app = express();
app.get('/api/health', (req, res) => res.json({ status: 'ok' }));

const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/ws' }); // path 限定升级路径

wss.on('connection', (ws, req) => {
  ws.send('hi');
  ws.on('message', (d) => ws.send(`echo ${d}`));
});

server.listen(3000);
```

`path: '/ws'` 让 `ws` 只接管 `/ws` 路径的升级请求，其它路径的 upgrade 被忽略。这样 HTTP 路由 `/api/*` 与 WebSocket `/ws` 互不干扰。

### 4.2 方式 B：`noServer` + `handleUpgrade`

如果需要在**握手前**做点事（鉴权、按 path 分发到不同 wss、记录日志），就要手动接管 upgrade 事件（见 `Code/ws-auth.js` 与 `Code/server.js`）：

```js
const wss = new WebSocketServer({ noServer: true });

server.on('upgrade', (req, socket, head) => {
  // 1. 在这里做鉴权 / 路径分发
  const url = new URL(req.url, `http://${req.headers.host}`);
  if (url.pathname !== '/ws') {
    socket.destroy();
    return;
  }
  const user = verifyToken(url.searchParams.get('token'));
  if (!user) {
    socket.write('HTTP/1.1 401 Unauthorized\r\nConnection: close\r\n\r\n');
    socket.destroy();
    return;
  }
  // 2. 通过校验, 完成握手
  wss.handleUpgrade(req, socket, head, (ws) => {
    // 把 user 作为第 3 个参数透传给 connection 回调
    wss.emit('connection', ws, req, user);
  });
});

wss.on('connection', (ws, req, user) => {
  ws.user = user; // 后续业务可用
});
```

`noServer` 模式下，`ws` 库不自动监听 upgrade，由你在 `server.on('upgrade', ...)` 里决定是否调用 `wss.handleUpgrade`。这是生产环境 WebSocket 服务的标准写法——几乎所有鉴权、限流、多路径分发都在这里做。

### 4.3 路由分发

可以在 upgrade 事件里按 `pathname` 把不同的升级请求交给不同的 `WebSocketServer`：

```js
const chatWss = new WebSocketServer({ noServer: true });
const notifyWss = new WebSocketServer({ noServer: true });

server.on('upgrade', (req, socket, head) => {
  const { pathname } = new URL(req.url, `http://${req.headers.host}`);
  if (pathname === '/chat') chatWss.handleUpgrade(req, socket, head, (ws) => chatWss.emit('connection', ws, req));
  else if (pathname === '/notify') notifyWss.handleUpgrade(req, socket, head, (ws) => notifyWss.emit('connection', ws, req));
  else socket.destroy();
});
```

---

## 五、实时通信核心模式

### 5.1 广播

最基础的模式：一条消息发给所有在线客户端。遍历 `wss.clients`，但**必须先判断 `readyState === WebSocket.OPEN`**，否则对正在关闭的连接 `send` 会抛错（见 `Code/broadcast-demo.js`）：

```js
function broadcast(obj, excludeWs = null) {
  const payload = JSON.stringify(obj);
  for (const client of wss.clients) {
    if (client.readyState === WebSocket.OPEN && client !== excludeWs) {
      client.send(payload);
    }
  }
}
```

广播常用于"系统通知""有人加入/离开"。聊天室里"别人说话我也能看到"也是广播（排除发送者本人）。

### 5.2 私聊

广播发给所有人，私聊发给**特定用户**。需要一个 `Map<userId, ws>` 维护在线用户与连接的映射（见 `Code/chat-room.js`）：

```js
const userMap = new Map(); // userId -> ws

wss.on('connection', (ws, req) => {
  // 鉴权后拿到 userId
  ws.user = { id: userId };
  userMap.set(userId, ws);

  ws.on('message', (raw) => {
    const msg = JSON.parse(raw);
    if (msg.type === 'private') {
      const target = userMap.get(msg.data.toUserId);
      if (target && target.readyState === WebSocket.OPEN) {
        target.send(JSON.stringify({ type: 'private', from: ws.user.id, data: { text: msg.data.text } }));
      }
    }
  });

  ws.on('close', () => {
    userMap.delete(ws.user.id); // 关键: 断开时清理映射
  });
});
```

> 多端登录：同一 userId 可能有多条连接，`Map<userId, ws>` 只能存最后一条。生产环境应改为 `Map<userId, Set<ws>>`，给该用户的所有端都推。

### 5.3 房间/群组

房间是"一对多"的中间形态：消息发给房间内所有成员。用 `Map<roomId, Set<userId>>` 维护（见 `Code/chat-room.js`）：

```js
const roomMap = new Map(); // roomId -> Set<userId>

function joinRoom(userId, roomId) {
  if (!roomMap.has(roomId)) roomMap.set(roomId, new Set());
  roomMap.get(roomId).add(userId);
}

function leaveRoom(userId, roomId) {
  const users = roomMap.get(roomId);
  if (users) {
    users.delete(userId);
    if (users.size === 0) roomMap.delete(roomId); // 空房间清理, 防 Map 无限增长
  }
}

function broadcastToRoom(roomId, obj, excludeUserId = null) {
  const users = roomMap.get(roomId);
  if (!users) return;
  const payload = JSON.stringify(obj);
  for (const uid of users) {
    if (uid === excludeUserId) continue;
    const w = userMap.get(uid);
    if (w && w.readyState === WebSocket.OPEN) w.send(payload);
  }
}
```

**关键设计决策**：房间成员存 `Set<userId>` 而非 `Set<ws>`。原因是同一用户多端登录时，`Set<ws>` 难以维护（哪个 ws 属于哪个用户？断开时怎么删？）；存 userId 后，发送时去 `userMap` 查当前活跃的 ws，更清晰、更稳健。

### 5.4 消息协议设计

WebSocket 传输的是裸字符串/二进制，**协议完全由你定义**。强烈建议用统一的 JSON 信封：

```ts
{
  type: string,      // 消息类型, 决定如何解析 data
  data: any,         // 负载, 结构随 type 变化
  timestamp: number, // 服务端时间戳, 客户端排序/去重用
  from?: string,     // (服务端->客户端) 发送者
}
```

消息类型用枚举约束，避免"字符串满天飞"：

| type | 方向 | data 结构 | 含义 |
|------|------|-----------|------|
| `join` | C→S | `{ roomId }` | 加入房间 |
| `leave` | C→S | `{ roomId }` | 离开房间 |
| `chat` | C→S | `{ roomId, text }` | 房间发言 |
| `private` | C→S | `{ toUserId, text }` | 私聊 |
| `chat` | S→C | `{ roomId, text }` (+`from`) | 房间消息推送 |
| `private` | S→C | `{ text }` (+`from`) | 私聊消息推送 |
| `system` | S→C | `string` | 系统提示（欢迎、加入/离开、错误回执） |
| `presence` | S→C | `{ roomId, users: [] }` | 在线名单变更 |
| `error` | S→C | `string` | 错误（非法消息、不在房间等） |

服务端收到消息先 `JSON.parse`，失败回 `error`；按 `type` switch 分发；未知 `type` 也回 `error`。这套信封在 `Code/chat-room.js` 与 `Code/server.js` 中都有实现。

> 二进制协议（如 protobuf）省带宽、解析快，但可读性差、调试麻烦。除非单消息 > 几 KB 或 QPS 极高，否则 JSON 足够，且与浏览器天然兼容。

---

## 六、连接管理

连接管理是 WebSocket 服务从"能跑"到"能上线"的分水岭。丢一个连接在本地无所谓，在生产环境就是内存泄漏、僵尸连接、用户体验黑洞。

### 6.1 在线用户列表

`wss.clients.size` 给出当前连接数，但业务上更关心"谁在线"。维护 `Map<userId, ws>` 即可，配合 HTTP 接口暴露：

```js
app.get('/api/users', (req, res) => {
  res.json({ count: userMap.size, users: Array.from(userMap.keys()) });
});
```

### 6.2 断线重连（客户端指数退避）

WebSocket **没有自动重连**——断了就断了，浏览器 `onclose` 触发后不会自己重连。客户端必须自己实现，且用**指数退避**避免雪崩（服务端刚恢复就被几万个客户端同时重连打挂）：

```js
let retry = 0;
function connect() {
  const ws = new WebSocket(`ws://host/ws?token=${token}`);
  ws.onopen = () => { retry = 0; console.log('已连接'); };
  ws.onclose = () => {
    retry++;
    const delay = Math.min(1000 * 2 ** retry, 30000); // 1s, 2s, 4s, 8s... 上限 30s
    console.log(`断开, ${delay}ms 后重连`);
    setTimeout(connect, delay);
  };
  ws.onmessage = (e) => { /* 处理消息 */ };
}
connect();
```

退避上限很重要：无上限的指数退避会让离线很久的客户端重连间隔变成天文数字，永远连不回来。

### 6.3 心跳超时踢出

服务端心跳见 `Code/heartbeat.js`。核心逻辑：

```js
const HEARTBEAT_INTERVAL = 30_000;

const timer = setInterval(() => {
  wss.clients.forEach((ws) => {
    if (ws.isAlive === false) {
      ws.terminate(); // 上一轮 ping 没收到 pong -> 死连接, 立即销毁
      return;
    }
    ws.isAlive = false; // 标记, 等pong 置 true
    ws.ping();
  });
}, HEARTBEAT_INTERVAL);

wss.on('connection', (ws) => {
  ws.isAlive = true;
  ws.on('pong', () => { ws.isAlive = true; });
});
```

`terminate()` vs `close()`：

| 方法 | 行为 | 用途 |
|------|------|------|
| `ws.close(code, reason)` | 礼貌关闭：发 close 帧，等对方 ack | 正常关闭、想给对方原因 |
| `ws.terminate()` | 立即销毁底层 socket，不发任何帧 | 死连接、强制踢出 |

死连接用 `close` 没意义——对方已经收不到 close 帧了，连接永远不会真正关闭；必须 `terminate`。

### 6.4 最大连接数限制

防止恶意/异常客户端耗尽资源：

```js
server.on('upgrade', (req, socket, head) => {
  if (wss.clients.size >= MAX_CLIENTS) {
    socket.write('HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\n\r\n');
    socket.destroy();
    return;
  }
  // ... 正常握手
});
```

生产环境还要配合反向代理（Nginx `limit_conn`）和网关层限流。

### 6.5 消息队列（发送失败缓存）

`ws.send` 在连接断开瞬间会抛错或静默失败，重要消息（如订单通知）应缓存待发：

```js
function safeSend(ws, obj) {
  const payload = JSON.stringify(obj);
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(payload, (err) => {
      if (err) {
        // 发送失败, 入队, 等重连后补发
        pendingQueue.push({ userId: ws.user.id, payload });
      }
    });
  } else {
    pendingQueue.push({ userId: ws.user.id, payload });
  }
}

// 客户端重连后, 从队列取出补发
wss.on('connection', (ws, req, user) => {
  flushPending(user.id, ws);
});
```

补发要注意**去重**（客户端可能已经收过部分消息），常用 `timestamp + id` 幂等键。

---

## 七、鉴权

HTTP 接口鉴权用 `Authorization` header 很自然，但浏览器原生 `new WebSocket(url)` **不支持自定义 header**——只能通过两种方式带凭证：

| 方式 | 写法 | 服务端读取 | 优劣 |
|------|------|------------|------|
| URL query | `new WebSocket('ws://h/ws?token=xxx')` | `new URL(req.url).searchParams.get('token')` | 简单；但 token 会进 access log、可能被中间代理记录 |
| 子协议 | `new WebSocket('ws://h/ws', ['bearer.'+token])` | `req.headers['sec-websocket-protocol']` | 走 header 不进 URL；但要正确回选子协议，稍复杂 |
| 自定义 header | 仅非浏览器客户端（`wscat -H`、Node SDK） | `req.headers['authorization']` | 浏览器不可用 |

### 7.1 在 upgrade 阶段校验

鉴权必须在**握手前**做（见 `Code/ws-auth.js`）。一旦 `handleUpgrade` 完成，连接已建立，再踢就只能 `ws.close(4001)`——多走了一步握手。两种拒绝方式：

```js
server.on('upgrade', (req, socket, head) => {
  const user = verifyToken(getToken(req));
  if (!user) {
    // 方式 A: 直接 destroy —— 无 token / 非法请求, 不浪费握手
    socket.write('HTTP/1.1 401 Unauthorized\r\nX-WS-Auth-Error: bad token\r\nConnection: close\r\n\r\n');
    socket.destroy();
    return;
  }
  // 方式 B: 想给客户端明确原因时, 可先 handleUpgrade 再 close(4001, 'unauthorized')
  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit('connection', ws, req, user);
  });
});
```

### 7.2 鉴权后的用户信息透传

`wss.handleUpgrade` 的第 4 个参数是回调，回调里 `wss.emit('connection', ws, req, user)` 可以把 user 作为第 3 个参数传给 `connection` 监听器，后续业务直接用 `ws.user`，无需再查一次 token：

```js
wss.on('connection', (ws, req, user) => {
  ws.user = user; // 挂到 ws 上, 业务全程可用
  // ...
});
```

> 生产环境的 token 应是短期有效的 JWT 或服务端可撤销的 session，**不要用永久 token**。token 泄漏后能被无限复用是 WebSocket 鉴权的高频事故。

---

## 八、AI 全栈场景

这是前端转 AI 全栈最该关注的部分——WebSocket 在 AI 产品里到底用在哪？

### 8.1 大模型流式响应转发

大模型 API（OpenAI、Anthropic、智谱、通义）都支持流式输出，上游格式几乎都是 **SSE**（`text/event-stream`）。后端拿到上游 SSE 后，要转发给前端，有两种选择：

| 方案 | 实现 | 何时选 |
|------|------|--------|
| **SSE 转发** | 后端 `fetch` 上游流式接口，把每个 chunk 通过 `res.write('data: ...\n\n')` 转发给前端 | 前端只收不发；简单；自动重连 |
| **WebSocket 转发** | 后端 `fetch` 上游 SSE，把每个 chunk 通过 `ws.send` 推给前端 | 前端在流式过程中要发消息（如中途取消、追问、切模型） |

SSE 转发的伪代码：

```js
app.post('/api/chat', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  const upstream = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...req.body, stream: true })
  });
  // 把上游 SSE 流管道式转发给客户端
  for await (const chunk of upstream.body) {
    res.write(chunk);
  }
  res.end();
});
```

WebSocket 转发适合"流式过程中客户端要交互"：用户中途喊停、追问、切换模型，一个 WebSocket 连接全程复用，比反复建 HTTP 请求省事。

### 8.2 聊天机器人实时回答

聊天机器人的典型形态：用户发问 → 后端调模型 → 流式返回答案 → 可能还要附带"引用来源""思考过程"。WebSocket 让"问"和"答"走同一条连接，且答案逐字推送：

```js
// 客户端
ws.send(JSON.stringify({ type: 'ask', data: { question: '什么是 RAG?' } }));
ws.on('message', (e) => {
  const m = JSON.parse(e.data);
  if (m.type === 'token') appendToUI(m.data.text);    // 逐字追加
  if (m.type === 'done')  finalizeUI();                // 完成
  if (m.type === 'source') showSources(m.data);        // 引用来源
});
```

### 8.3 AI Agent 工具调用进度推送

AI Agent（如 ReAct、function calling）在执行任务时会调用多个工具：搜索、查数据库、跑代码、调外部 API。每个工具都可能耗时几秒到几十秒，用户盯着空白页面会崩溃。WebSocket 把每一步进度实时推给前端：

```
[用户] 帮我查下北京明天天气并整理成日程
[Agent] → 调用工具 get_weather(beijing)        ← ws 推送 {type:'tool_call', tool:'get_weather'}
[Agent] ← 工具返回: 晴, 28℃                    ← ws 推送 {type:'tool_result', ...}
[Agent] → 调用工具 create_calendar_event(...)  ← ws 推送 {type:'tool_call', tool:'create_calendar_event'}
[Agent] ← 完成                                 ← ws 推送 {type:'done', summary:'...'}
```

每个工具调用的开始/结束/中间日志都推一条消息，前端渲染成"Agent 思考过程"的时间线。这是当前 AI Agent 产品的标配交互。

### 8.4 向量检索进度反馈

RAG 流程里，向量检索（`top-k` 查询）在百万级向量库里可能耗时 1~3 秒，加上后续 rerank、拼 prompt、调模型，总时长 5~10 秒。给用户明确的进度反馈能显著降低"感知等待时间"：

```js
ws.send(JSON.stringify({ type: 'progress', stage: 'retrieving', percent: 30 }));
// ... 检索完成
ws.send(JSON.stringify({ type: 'progress', stage: 'reranking', percent: 50 }));
// ... 拼好 prompt
ws.send(JSON.stringify({ type: 'progress', stage: 'generating', percent: 70 }));
// ... 流式生成
ws.send(JSON.stringify({ type: 'token', data: { text: '...' } }));
```

这类"多阶段、长耗时、需反馈"的任务，WebSocket 的双向持久连接比反复 HTTP 轮询优雅太多。

---

## 九、关键知识点总结

1. **HTTP 是请求-响应单向通信**，服务端无法主动推送，每请求带完整 header，不适合实时双向场景。
2. **实时通信五方案**：短轮询（兼容性兜底）、长轮询（WebSocket 降级）、SSE（单向推，AI 流式首选）、WebSocket（双向高频）、WebRTC（P2P 音视频）。
3. **WebSocket 协议**：借 HTTP `Upgrade: websocket` 握手 → 服务端 `101 Switching Protocols` → 同一 TCP 连接上用帧双向全双工通信；`ws://` 明文、`wss://` 加密，生产必须用 `wss`。
4. **帧类型**：文本帧（JSON）、二进制帧（文件）、关闭帧、ping/pong 心跳帧；浏览器收到 ping 自动回 pong。
5. **心跳保活是必需的**：检测半开连接、防代理空闲超时；服务端定时 ping，无 pong 则 `terminate()` 踢出。`terminate` 立即销毁 vs `close` 礼貌关闭。
6. **ws 库核心**：`WebSocketServer({ port | server | noServer })`、`connection` 事件、`ws.send/on('message')/on('close')/on('error')`、`wss.clients`、`readyState`、`ping/pong`。
7. **与 Express 共享端口**：简单用 `{ server, path }`；需握手前鉴权/分发用 `{ noServer } + server.on('upgrade') + wss.handleUpgrade`。
8. **三种核心模式**：广播（遍历 `wss.clients` 判 OPEN）、私聊（`Map<userId, ws>`）、房间（`Map<roomId, Set<userId>>`，存 userId 不存 ws）。
9. **消息协议**：统一 `{type, data, timestamp}` JSON 信封 + 类型枚举，`type` 决定 `data` 结构，服务端 switch 分发。
10. **连接管理**：在线列表、客户端指数退避重连（上限 30s）、心跳超时踢出、最大连接数限制、发送失败消息队列补发。
11. **鉴权**：浏览器 `new WebSocket` 无法自定义 header，token 走 query 或子协议；在 upgrade 阶段校验，失败用 `socket.destroy()` 拒绝；通过 `handleUpgrade` 回调把 user 透传给 `connection`。
12. **AI 场景选型**：纯流式输出优先 SSE（自动重连、HTTP 友好）；双向交互（聊天、Agent 进度、检索反馈、协同 + AI）用 WebSocket。两者常混用。

---

## 十、实战练习

> 以下练习在 `Code/` 目录基础上扩展，建议独立完成后再对照本篇结论自查。所有练习均可通过 `npm install` 后直接运行验证。

### 练习一：在 `server.js` 基础上实现"打字状态"广播

**目标**：聊天室里当某人正在输入时，房间内其他人能看到"xxx 正在输入..."的实时提示（类似微信/Slack 的 typing indicator）。

**要求**：

1. 新增消息类型 `typing`，客户端发 `{ type: 'typing', data: { roomId } }` 表示"我正在输入"。
2. 服务端收到后，给该房间**除发送者外**的所有人推 `{ type: 'typing', from: userId, timestamp }`。
3. 客户端收到 `typing` 后显示"xxx 正在输入..."，3 秒内没再收到新的 `typing` 就消失（用 `setTimeout` + 覆盖实现）。
4. 思考：为什么不能让客户端每按一个键就发一条 `typing`？应该怎么节流（throttle）？

**考察点**：房间广播（排除发送者）、消息类型扩展、客户端节流。

### 练习二：给聊天室加"消息回执与补发"

**目标**：实现消息送达确认 + 客户端断线重连后补发漏掉的消息。

**要求**：

1. 每条 `chat` 消息服务端附唯一 `id`（`crypto.randomUUID()`），推送给房间成员。
2. 客户端收到后回 `{ type: 'ack', data: { id } }`；服务端记录"已送达"。
3. 服务端为每个用户维护一个"待发送队列"，发送后未收到 ack 的消息保留 30s。
4. 客户端重连后，服务端把该用户未 ack 的消息补发（带 `id`，客户端去重）。
5. 思考：为什么 `ack` 必须在应用层做，而不能依赖 WebSocket 的"发送成功"回调？

**考察点**：消息可靠性、幂等去重、连接管理与重连、应用层 vs 传输层确认。

### 练习三：实现一个"AI 流式问答"最小 Demo

**目标**：用 WebSocket 把"用户提问 → 模型流式回答"打通（模型可用本地 mock 代替真实 API）。

**要求**：

1. 客户端发 `{ type: 'ask', data: { question } }`。
2. 服务端收到后，用 `setInterval` 每 100ms 生成一个"假 token"（如把预设答案按字拆分），推 `{ type: 'token', data: { text } }`，结束推 `{ type: 'done' }`。
3. 客户端逐字追加显示。
4. 新增"中途取消"：客户端发 `{ type: 'cancel' }`，服务端立即停止 token 推送并发 `{ type: 'cancelled' }`。
5. 思考：如果换成真实 OpenAI SSE 接口，服务端如何把上游 SSE chunk "翻译"成自己的 WebSocket `token` 消息？尝试用 `fetch` + `for await...of` 消费上游流并转发。

**考察点**：流式推送、任务取消、上游 SSE 转 WebSocket、长任务连接管理。

---

> 完成本篇后，你已经掌握实时双向通信的核心能力，并能把它用到 AI 流式输出、Agent 进度推送等真实场景。下一篇将进入 **Node.js 与数据库集成**（或消息队列/缓存），把"实时通信 + 数据持久化 + AI 推理"组合成一个可上线的 AI 后端服务。
