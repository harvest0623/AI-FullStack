# Day09 - HTTP 模块与原生 Web 服务器

> 本篇聚焦 Node.js 的 `http` 内置模块。你将用零依赖、纯原生的方式手写一个能解析路由、能读 POST 请求体、能流式返回大文件的 Web 服务器，并理解 HTTP 协议在 Node 中的完整映射。这一切看起来"繁琐"，但它正是 Express、Koa、Fastify 乃至 Next.js Server 的底层地基——理解了它，框架对你将不再是黑盒。下一篇 Day10 会引出 Express，看它如何把这些样板代码压缩成几行。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 HTTP 协议基础回顾](#21-http-协议基础回顾)
  - [2.2 Node.js http 模块架构](#22-nodejs-http-模块架构)
  - [2.3 createServer 与回调参数（req / res）](#23-createserver-与回调参数req--res)
  - [2.4 IncomingMessage（req）常用属性](#24-incomingmessagereq-常用属性)
  - [2.5 ServerResponse（res）常用方法](#25-serverresponseres-常用方法)
  - [2.6 监听端口 listen](#26-监听端口-listen)
  - [2.7 IPv4 vs IPv6](#27-ipv4-vs-ipv6)
- [三、路由实现](#三路由实现)
- [四、请求体解析](#四请求体解析)
- [五、响应：JSON / HTML / 文件 / 流式 / CORS](#五响应json--html--文件--流式--cors)
- [六、http 客户端：request / get / fetch](#六http-客户端request--get--fetch)
- [七、为什么原生够用但开发效率低（引出 Express）](#七为什么原生够用但开发效率低引出-express)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 用 `http.createServer` 在 30 秒内启动一个可被浏览器/curl 访问的 HTTP 服务，并说明 `req`/`res` 的本质类型。
2. 准确说出 GET / POST / PUT / DELETE / PATCH 的语义差异，以及它们在"幂等性""安全""是否有请求体"上的区别。
3. 解释 1xx ~ 5xx 五类状态码的语义，并能在业务代码中合理选择 200 / 201 / 204 / 301 / 304 / 400 / 401 / 403 / 404 / 409 / 422 / 500。
4. 读懂 `Content-Type` 常见取值（`application/json`、`text/html`、`x-www-form-urlencoded`、`multipart/form-data`），并知道请求体应当如何对应解析。
5. 用 `new URL(req.url, base)` 解析 pathname 与 query，写出一个对象映射式路由分发器，并正确处理 404。
6. 解释 `req` 是 `Readable` 流，用 `data` / `end` 事件手动拼接 Buffer，处理 JSON 与表单请求体，规避"未等 end 就响应"的常见坑。
7. 区分 `res.writeHead` / `res.setHeader` / `res.statusCode`，知道响应头必须先于响应体写入。
8. 用 `fs.createReadStream` + `pipe` 流式返回大文件，并理解"边读边写"如何避免内存爆炸。
9. 用 `http.get` / `http.request` 主动发起请求，处理响应流、超时与错误，并能与 Node 18+ 原生 `fetch` 对比取舍。
10. 说清 CORS 预检 `OPTIONS` 的工作机制，手写一套基本的 CORS 响应头。

---

## 二、理论知识讲解

### 2.1 HTTP 协议基础回顾

HTTP 是一种**无状态、基于请求-响应模型、文本协议**的应用层协议。客户端发一个 `Request`，服务端回一个 `Response`，一次交互就结束了。无状态意味着服务端默认不记得"上一次请求"是谁——Cookie / Session / JWT 都是为了给"无状态"补上"状态感"。

一个完整的 HTTP 请求长这样：

```http
POST /api/users HTTP/1.1
Host: localhost:3000
Content-Type: application/json
Content-Length: 36

{"name":"Alice","email":"a@b.com"}
```

一个完整的 HTTP 响应长这样：

```http
HTTP/1.1 201 Created
Content-Type: application/json
Content-Length: 21

{"id":1,"ok":true}
```

两者结构完全对称：**起始行 → Headers（多个） → 空行 → Body**。空行是协议约定的分隔符，丢失空行会导致解析失败。

#### 2.1.1 请求方法（HTTP Methods）

| 方法 | 语义 | 安全 | 幂等 | 有请求体 | 典型用途 |
|------|------|------|------|----------|----------|
| `GET` | 获取资源 | ✅ | ✅ | 一般无（语义上不应改状态） | 拉列表、查详情 |
| `POST` | 创建资源 / 提交动作 | ❌ | ❌ | ✅ | 新建用户、提交表单、调用 LLM |
| `PUT` | 用请求体**整体替换**指定 URL 的资源 | ❌ | ✅ | ✅ | 全量更新用户资料 |
| `PATCH` | **部分修改**资源 | ❌ | 不保证 | ✅ | 只改邮箱字段 |
| `DELETE` | 删除资源 | ❌ | ✅ | 可有可无 | 删除一条记录 |
| `HEAD` | 同 GET 但只返回响应头 | ✅ | ✅ | 无 | 探测资源是否存在、看 Content-Length |
| `OPTIONS` | 询问服务器支持哪些方法 | ✅ | ✅ | 无 | **CORS 预检** |

> 🔑 **安全（Safe）**：不会改变服务端状态。<br>
> 🔑 **幂等（Idempotent）**：执行 N 次和执行 1 次的**最终状态**相同。`POST` 不幂等是因为多次提交会创建多条记录；`PUT` 幂等是因为同样的"全量替换"做多少遍结果都一样。

#### 2.1.2 状态码（Status Code）

5 类，首数字代表类别：

| 类别 | 含义 | 典型例子 |
|------|------|----------|
| **1xx** | 信息性，请求已收到，继续处理 | `100 Continue`、`101 Switching Protocols`（升级到 WebSocket） |
| **2xx** | 成功 | `200 OK`、`201 Created`、`204 No Content`（成功但无响应体，常用于 DELETE） |
| **3xx** | 重定向 | `301 Moved Permanently`、`302 Found`、`304 Not Modified`（协商缓存命中） |
| **4xx** | 客户端错误 | `400 Bad Request`、`401 Unauthorized`（未认证）、`403 Forbidden`（无权限）、`404 Not Found`、`409 Conflict`、`422 Unprocessable Entity`（语义错误）、`429 Too Many Requests` |
| **5xx** | 服务端错误 | `500 Internal Server Error`、`502 Bad Gateway`、`503 Service Unavailable`、`504 Gateway Timeout` |

> ⚠️ **常见误用**：把所有错误都返回 `500`。正确做法是——参数缺失/格式错用 `400` 或 `422`，没登录用 `401`，登录了但没权限用 `403`，资源不存在用 `404`，重复创建用 `409`，限流用 `429`，只有"代码炸了/数据库挂了"才用 `500`。

#### 2.1.3 请求头 / 响应头

HTTP 头是大小写不敏感的键值对，Node 会统一转成小写。常见请求头：

| Header | 作用 |
|--------|------|
| `Host` | 目标主机（HTTP/1.1 必需，用于虚拟主机路由） |
| `User-Agent` | 客户端标识 |
| `Accept` | 客户端能接收的 MIME 类型 |
| `Accept-Encoding` | 支持的压缩方式（gzip/br） |
| `Content-Type` | 请求体的 MIME 类型 |
| `Content-Length` | 请求体字节数 |
| `Authorization` | 凭证（`Bearer xxx`、`Basic xxx`） |
| `Cookie` | 携带的 Cookie |
| `Origin` / `Referer` | 来源（CORS / 防盗链） |

常见响应头：

| Header | 作用 |
|--------|------|
| `Content-Type` | 响应体 MIME 类型 |
| `Content-Length` | 响应体字节数 |
| `Cache-Control` | 缓存策略（`max-age`、`no-cache`、`no-store`） |
| `Set-Cookie` | 写入 Cookie（可多个） |
| `Location` | 重定向目标（配合 3xx） |
| `Access-Control-Allow-Origin` | CORS 允许的来源 |

#### 2.1.4 Content-Type 与请求体格式

`Content-Type` 决定请求/响应体如何被解析，是前后端最容易踩坑的地方：

| Content-Type | 体格式 | 解析方式 |
|--------------|--------|----------|
| `application/json` | `{"k":"v"}` | `JSON.parse` |
| `application/x-www-form-urlencoded` | `a=1&b=2` | `URLSearchParams` 或 `querystring` |
| `multipart/form-data; boundary=---xxx` | 多段二进制 | 需 `busboy` / `multer`，原生手写很复杂 |
| `text/plain` | 纯文本 | 直接当字符串 |
| `text/html` | HTML | 浏览器直接渲染 |
| `application/octet-stream` | 任意二进制 | 当 Buffer 处理 |

> 💡 **AI 场景联想**：调用 OpenAI / 通义千问 API，请求体永远是 `application/json`，但响应可能是普通 JSON，也可能是 `text/event-stream`（SSE 流式输出 token）。识别 `Content-Type` 后选择不同解析策略，是大模型 SDK 的核心代码。

### 2.2 Node.js http 模块架构

`http` 是 Node 的内置模块，**无需 npm install**，`require('http')` 即可使用。它在底层基于 `net` 模块（TCP）和 `stream` 模块实现，核心角色有四个：

```
┌────────────────────────────────────────────────────────┐
│  http.createServer(requestListener)                    │
│      └─► 返回 http.Server（继承自 net.Server）          │
│                                                          │
│  每来一个 HTTP 请求，调用 requestListener(req, res)：    │
│                                                          │
│    req  ─► http.IncomingMessage                         │
│           （Readable 流 + 请求行/头解析结果）            │
│                                                          │
│    res  ─► http.ServerResponse                          │
│           （Writable 流 + 写响应头/体的方法）            │
│                                                          │
│  客户端方向：                                            │
│    http.request(options) / http.get(url)                 │
│      └─► 返回 http.ClientRequest（Writable，写请求体）   │
│          response 事件回调收到 http.IncomingMessage      │
└────────────────────────────────────────────────────────┘
```

要点：

1. **`http.Server`** 本质是一个 TCP 服务器，监听端口后接收连接。
2. **`IncomingMessage`** 既是请求对象的容器，也是 `Readable` 流——请求体内容要靠"读流"来拿。
3. **`ServerResponse`** 既是响应对象的写入口，也是 `Writable` 流——响应体既可以 `res.write()` 多次写，也可以 `fs.createReadStream().pipe(res)` 让文件直接灌进去。
4. **服务端方向**和**客户端方向**复用同一对 `IncomingMessage` / 流概念，所以会一边写代码后，反过来用 `http.get` 也几乎零学习成本。

### 2.3 createServer 与回调参数（req / res）

```js
const http = require('http');

const server = http.createServer((req, res) => {
  // req: http.IncomingMessage —— 读请求
  // res: http.ServerResponse —— 写响应
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Hello HTTP');
});

server.listen(3000, () => console.log('listening on http://localhost:3000'));
```

`createServer` 接收一个回调，称为 **request handler**。这个回调是"每来一个请求就被同步调用一次"的——注意是**同步**注册逻辑，**异步**处理流。

如果不传 listener，也可以用 `server.on('request', (req, res) => {...})` 显式注册，效果一样。后者更适合需要同时监听 `connection` / `checkContinue` / `clientError` 等多事件的场景。

> ⚠️ **必须 `res.end()`**：不调用 `end`，客户端会一直等响应直到超时。这是新手最常忘的一步。`end` 之后不能再 `write`，否则抛 `ERR_STREAM_WRITE_AFTER_END`。

### 2.4 IncomingMessage（req）常用属性

| 属性 / 方法 | 含义 | 示例值 |
|-------------|------|--------|
| `req.method` | 请求方法（大写字符串） | `'GET'` / `'POST'` |
| `req.url` | 原始路径（含 query，不含 host） | `'/api/users?page=2&limit=10'` |
| `req.httpVersion` | HTTP 版本 | `'1.1'` / `'2.0'` |
| `req.headers` | 请求头对象（**小写键**） | `{ 'content-type': 'application/json', host: 'localhost:3000' }` |
| `req.socket.remoteAddress` | 客户端 IP | `'::ffff:127.0.0.1'` |
| `req` 作为流 | 监听 `'data'` / `'end'` 拿请求体 | 见第四节 |

> 🔑 `req.url` 只包含路径与 query，**不含 `http://host`**。要拿完整的 URL 需要拼 `req.headers.host` 或用 `new URL(req.url, `http://${req.headers.host}`)` 构造。

### 2.5 ServerResponse（res）常用方法

| 方法 / 属性 | 作用 | 备注 |
|-------------|------|------|
| `res.statusCode = 201` | 设置状态码 | 简单场景赋值即可 |
| `res.statusMessage = 'Created'` | 设置状态描述 | 通常省略，使用默认 |
| `res.setHeader(name, value)` | 单独设置一个响应头 | 可多次调用，**在 writeHead 之前**调 |
| `res.writeHead(statusCode, headers)` | 一次性写状态码 + 多个响应头 | 调用后即视为响应头已发出 |
| `res.write(chunk)` | 写一段响应体 | `chunk` 可为 `string` 或 `Buffer` |
| `res.end([chunk])` | 结束响应，可顺带写最后一段 | **必调**，否则请求挂起 |
| `res.getHeader(name)` / `res.removeHeader(name)` | 读/删响应头 | writeHead 前可用 |
| `res.flushHeaders()` | 强制立即把响应头发出去 | 一般不用 |
| `res` 作为 `Writable` 流 | 可被 `pipe` 进来 | 见文件响应 |

**writeHead vs setHeader 的区别**：

```js
// 写法 A：分步
res.statusCode = 201;
res.setHeader('Content-Type', 'application/json');
res.setHeader('X-Custom', 'abc');
res.end('...');

// 写法 B：一次性
res.writeHead(201, {
  'Content-Type': 'application/json',
  'X-Custom': 'abc',
});
res.end('...');
```

两者等价，但 **`writeHead` 一旦调用就锁定响应头**，之后 `setHeader` 不再生效；`setHeader` 则允许在 `write` 之前随时改。

> ⚠️ **响应头必须在 `write` / `end` 之前设置**。一旦开始写响应体，HTTP 协议上响应头已发出，再设就无效了。

### 2.6 监听端口 listen

`server.listen` 有几个常见重载：

```js
server.listen(3000);                                   // 端口，任意 IP
server.listen(3000, '127.0.0.1');                      // 端口 + IPv4
server.listen(3000, '0.0.0.0');                        // 监听所有 IPv4
server.listen(3000, '::');                             // 监听所有 IPv6（含 IPv4 映射）
server.listen(3000, () => console.log('ready'));        // 第三参为 listening 回调
server.listen('/tmp/node.sock');                       // 监听 Unix Socket
```

常见端口坑：

- **`EADDRINUSE`**：端口被占用，开发时常因上次进程没退干净，用 `lsof -i :3000` / `netstat -ano | findstr :3000` 查占用。
- **端口 < 1024**：Linux/macOS 需 root 权限，生产建议用反向代理（Nginx）把 80 转 3000。
- **不传 host**：默认监听所有网卡（`::`），开发期建议显式 `'127.0.0.1'`，避免暴露到外网。

### 2.7 IPv4 vs IPv6

| 名称 | 格式 | 回环地址 | 全部网卡 |
|------|------|----------|----------|
| IPv4 | 32 位，`192.168.1.1` | `127.0.0.1` | `0.0.0.0` |
| IPv6 | 128 位，`2001:db8::1` | `::1` | `::` |

Node 的 `net.Server` 在双栈系统上**默认监听 `::`**，会同时接受 IPv4 和 IPv6 连接（IPv4 连接以 `::ffff:IPv4` 形式呈现）。这就是为什么有时 `req.socket.remoteAddress` 看起来像 `::ffff:127.0.0.1`——它是 IPv6 套接字上的 IPv4 映射地址。

如果你只想监听 IPv4，就显式传 `'0.0.0.0'` 或 `'127.0.0.1'`。

---

## 三、路由实现

### 3.1 解析 url：pathname 与 query

`req.url` 是原始字符串，得自己解析。**强烈推荐用 WHATWG `URL`**（Node 10+ 全局可用），不要再用老的 `url.parse`（已废弃）：

```js
const http = require('http');

http.createServer((req, res) => {
  // 注意：req.url 不含 host，所以必须给一个 base
  const base = `http://${req.headers.host}`;
  const parsed = new URL(req.url, base);

  console.log(parsed.pathname);   // '/api/users'
  console.log(parsed.search);     // '?page=2&limit=10'
  console.log(parsed.searchParams.get('page'));   // '2'

  res.end('ok');
}).listen(3000);
```

`URL` 对象上常用的字段：

- `pathname`：路径部分，不含 query（`/api/users`）
- `search`：含 `?` 的 query 串（`?page=2`）
- `searchParams`：`URLSearchParams` 实例，有 `.get(name)` / `.has(name)` / `.getAll(name)` / `.entries()` 等方法
- `hostname` / `port` / `protocol`：从 base 解析得到，通常用不到

### 3.2 手动路由分发

最朴素的方式是 `if/else`：

```js
const { method, pathname } = parseRequest(req);

if (pathname === '/' && method === 'GET') {
  res.end('home');
} else if (pathname === '/api/users' && method === 'GET') {
  res.end(JSON.stringify([{ id: 1 }]));
} else {
  res.writeHead(404);
  res.end('Not Found');
}
```

路由一多就难看，更工程化的写法是**对象映射**：

```js
const routes = {
  'GET /': () => 'home',
  'GET /api/users': () => JSON.stringify([{ id: 1 }]),
  'POST /api/users': (body) => JSON.stringify({ ok: true, body }),
};

const handler = routes[`${method} ${pathname}`];
if (handler) {
  res.end(handler());
} else {
  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('404 Not Found');
}
```

这种写法的好处是路由表集中、易扩展，缺点是不支持路径参数（如 `/api/users/:id`）——要支持参数化路由就得引入"路由树"或正则匹配，这正是 Express / Koa Router 帮你做的事。

### 3.3 404 与 405

找不到路径返回 `404 Not Found`；路径存在但方法不允许（比如某路由只接受 `GET`，却收到了 `POST`），应返回 `405 Method Not Allowed`，并附 `Allow` 响应头列出允许的方法。生产实践中很多人把 405 也当 404 处理，但严格按规范区分能帮前端更快定位问题。

参考 `Code/router-server.js`，它实现了：对象映射路由、query 参数读取、统一 404 处理。

---

## 四、请求体解析

### 4.1 req 是 Readable 流

这是和前端 `fetch` 最大的认知差异。在前端，`body` 是一个 `ReadableStream` 对象；在 Node，`req` **本身**就是一个 `Readable` 流。请求体的字节并不会一次性到齐，而是分块（chunk）随着 TCP 报文陆续到达。

```js
http.createServer((req, res) => {
  if (req.method === 'POST') {
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));   // 每来一块就推入数组
    req.on('end', () => {
      const body = Buffer.concat(chunks).toString('utf8');
      res.end(`收到：${body}`);
    });
    req.on('error', err => {
      res.writeHead(400);
      res.end('bad request');
    });
  }
});
```

### 4.2 拼接 Buffer 的正确姿势

`chunk` 是 `Buffer`，**不要用字符串拼接**（`+= chunk` 在 UTF-8 多字节字符被拆开时会乱码）。正确做法：

```js
const chunks = [];
req.on('data', c => chunks.push(c));
req.on('end', () => {
  const buf = Buffer.concat(chunks);    // 一次性合并
  const text = buf.toString('utf8');
});
```

或用 `URLSearchParams` 直接处理表单：

```js
const text = buf.toString('utf8');
const params = new URLSearchParams(text);
params.get('name');
```

### 4.3 解析 JSON

```js
req.on('end', () => {
  const text = Buffer.concat(chunks).toString('utf8');
  try {
    const data = JSON.parse(text);
    res.end(JSON.stringify({ ok: true, received: data }));
  } catch (e) {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'invalid json' }));
  }
});
```

### 4.4 边界情况与坑

| 坑 | 表现 | 解法 |
|----|------|------|
| **没等 `end` 就响应** | 拿到 body 为空或部分丢失 | 所有处理逻辑都放在 `end` 回调里 |
| **不监听 `data` 事件** | 请求体不会被消费，客户端可能挂住 | 即使不关心 body，也建议 `req.on('data', ()=>{})` + `req.on('end', ...)` 走完 |
| **大文件上传撑爆内存** | 1GB 上传全进 `chunks` 数组 | 用流式处理或 multer，提前限制 `Content-Length` |
| **没有大小上限** | 被恶意大包打 OOM | 累计长度超过阈值就 `res.writeHead(413)` 中断 |
| **Content-Type 不对还硬解析** | `JSON.parse('a=1&b=2')` 抛异常 | 先判 `Content-Type` 再选解析器 |
| **没有 try/catch** | JSON 解析失败直接让进程崩 | 解析必加 `try/catch` |

完整封装见 `Code/json-api-server.js`，它把"收集 + 解析 + 大小限制 + 错误兜底"打包成了 `readBody(req)` 工具函数。

---

## 五、响应：JSON / HTML / 文件 / 流式 / CORS

### 5.1 返回 JSON

```js
res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
res.end(JSON.stringify({ ok: true, data: [1, 2, 3] }));
```

> ⚠️ 必须 `JSON.stringify`，`res.end` 接收的是 `string` 或 `Buffer`，传对象会 `[object Object]`。

### 5.2 返回 HTML

```js
res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
res.end('<h1>你好，世界</h1>');
```

`charset=utf-8` 不能省，否则中文会乱码。

### 5.3 文件响应与流式返回

小文件可以一次性 `fs.readFile` 然后 `end`：

```js
fs.readFile(path, (err, data) => {
  if (err) { res.writeHead(404); res.end('not found'); return; }
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(data);
});
```

但**大文件**这样做会让整个文件进内存，100 个并发请求就把 Node 撑爆。正确做法是用 `fs.createReadStream` + `pipe`：

```js
const stream = fs.createReadStream(path);
stream.on('open', () => {
  res.writeHead(200, { 'Content-Type': mime });
  stream.pipe(res);              // 边读边写到 res
});
stream.on('error', () => {
  res.writeHead(404);
  res.end('not found');
});
```

`pipe` 内部按"上游 push → 下游 drain"的节奏控制背压（backpressure），不会一次性塞满内存。

### 5.4 Content-Type 判断

按扩展名映射 MIME 类型，原生用 `path.extname` + 一张表：

```js
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.gif':  'image/gif',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.txt':  'text/plain; charset=utf-8',
};
const mime = MIME[path.extname(p).toLowerCase()] || 'application/octet-stream';
```

生产环境建议直接用 `mime-types` 这个 npm 包，覆盖更全。完整实现见 `Code/static-file-server.js`。

### 5.5 CORS 与 OPTIONS 预检

**CORS（Cross-Origin Resource Sharing）** 是浏览器的同源策略机制。当前端 `fetch('http://localhost:3000/api')` 跨源时，浏览器会检查响应头里是否带 `Access-Control-Allow-Origin` 没带就拒绝把响应交给 JS。

#### 简单请求 vs 预检请求

- **简单请求**：方法为 `GET` / `HEAD` / `POST`，且请求头仅限几个"安全"字段（`Accept`、`Accept-Language`、`Content-Language`、`Content-Type` 仅限 `text/plain` / `multipart/form-data` / `application/x-www-form-urlencoded`）。浏览器直接发请求，只看响应头。
- **预检请求**：只要不符合"简单"条件（典型是 `Content-Type: application/json`、自定义头 `Authorization`、`PUT` / `DELETE` 方法），浏览器会**先发一个 `OPTIONS` 请求**问服务器"我能不能这么发"，服务器同意后才发真正的请求。

#### 手写 CORS 响应头

```js
function setCors(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '86400');

  // 预检请求直接 204 返回，不再走业务逻辑
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return true;
  }
  return false;
}

http.createServer((req, res) => {
  if (setCors(req, res)) return;    // OPTIONS 已被处理
  // ... 业务路由
});
```

要点：

1. **`Access-Control-Allow-Origin`**：可以是 `*`（任意来源）或具体 origin（如 `http://localhost:5173`）。带 Cookie 时不能用 `*`，必须指定具体 origin 并同时设 `Access-Control-Allow-Credentials: true`。
2. **`Access-Control-Allow-Methods`**：允许的方法。
3. **`Access-Control-Allow-Headers`**：允许的请求头。
4. **`Access-Control-Max-Age`**：预检结果缓存时间，可减少 OPTIONS 请求。
5. **`OPTIONS` 预检**：响应 `204 No Content`（无响应体）即可，业务逻辑跳过。

> ⚠️ CORS 是浏览器行为，不是服务端拦截。`curl` / Postman 不受 CORS 限制——所以"接口用 curl 测没问题、浏览器报 CORS 错"是经典现象，本质就是缺响应头。

参考 `Code/json-api-server.js` 的完整 CORS 实现。

---

## 六、http 客户端：request / get / fetch

`http` 模块不仅是服务端，也能当客户端发请求。

### 6.1 http.get（最常用）

`http.get` 是 `http.request` 的简化版，固定 `GET` 方法，无需手动 `req.end()`：

```js
http.get('http://jsonplaceholder.typicode.com/users/1', (res) => {
  const { statusCode } = res;
  const chunks = [];
  res.on('data', c => chunks.push(c));
  res.on('end', () => {
    const text = Buffer.concat(chunks).toString('utf8');
    try {
      const data = JSON.parse(text);
      console.log(statusCode, data);
    } catch (e) {
      console.error('JSON 解析失败');
    }
  });
}).on('error', err => {
  console.error('请求错误：', err.message);
});
```

响应 `res` 也是 `IncomingMessage`（Readable 流），处理方式和服务端读 `req` 完全一样。

### 6.2 http.request（支持所有方法）

```js
const data = JSON.stringify({ name: 'Alice' });
const req = http.request({
  hostname: 'localhost',
  port: 3000,
  path: '/api/users',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(data),   // 必填，否则对方可能读不全
  },
}, (res) => {
  // 处理响应，同 get
});

req.on('error', err => console.error(err));
req.write(data);    // 写请求体
req.end();          // 必须 end，否则请求不发出去
```

### 6.3 错误与超时

`http.get` / `http.request` 返回 `ClientRequest` 对象，常见事件：

| 事件 | 触发场景 |
|------|----------|
| `'error'` | DNS 解析失败、连接被拒、TCP 错误等 |
| `'timeout'` | `req.setTimeout(ms)` 设置的超时到点了 |
| `'response'` | 收到响应头（一般用回调代替） |

**超时控制**（注意 `setTimeout` 之后必须手动 `req.destroy()`，否则 socket 还会挂着）：

```js
const req = http.get(url, callback);
req.setTimeout(3000, () => {
  req.destroy(new Error('timeout'));  // 触发 error 事件
});
req.on('error', err => console.error(err.message));
```

> ⚠️ **`http.get` 不会因 HTTP 4xx/5xx 自动触发 error 事件**——只要 TCP 通了、收到响应头，就算"成功"。判断业务是否成功必须自己看 `statusCode`。

### 6.4 与原生 fetch（Node 18+）对比

Node 18+ 内置了 WHATWG `fetch`，API 与浏览器一致：

```js
const res = await fetch('https://jsonplaceholder.typicode.com/users/1');
const data = await res.json();
```

| 对比项 | `http.get` | 原生 `fetch` |
|--------|-----------|---------------|
| API 风格 | 事件 / 回调 | Promise / async |
| 代码量 | 多（手动拼 Buffer、超时） | 少 |
| 流式响应 | 原生支持 `res` 是流 | 需 `res.body.getReader()`（Web Streams） |
| 流式请求体 | 原生支持 `req.write` | 支持，传 `ReadableStream` |
| 超时控制 | `req.setTimeout` + `destroy` | `AbortController` |
| 取消请求 | `req.destroy()` | `AbortController` |
| HTTPS | 要切到 `https` 模块 | 自动（URL 协议决定） |
| 自定义底层（如 Agent） | 强，能精细控制 socket | 相对受限 |
| 适合场景 | 需要底层控制、长连接、自建代理 | 业务侧普通 HTTP 调用 |

实践建议：

- **业务代码默认用 `fetch`**（Node 18+），心智成本最低。
- 需要细粒度控制（自定义 Agent、连接池、HTTP/2 推送）才回到 `http` 模块。
- 真正生产场景可以考虑 `undici`（Node 自家高性能 HTTP 客户端，fetch 底层就是它）或 `axios`。

对比实现见 `Code/http-client.js` 与 `Code/fetch-client.mjs`。

---

## 七、为什么原生够用但开发效率低（引出 Express）

到目前为止，你已经能用原生 `http` 模块做出一个"全功能"服务器了：路由、参数、请求体、CORS、文件、流式响应，应有尽有。**功能上完全够用**——很多生产服务跑的就是裸 `http`。

但你会发现每写一个新接口都要重复一套样板：

```js
// 每个接口的开头都是这些
const parsedUrl = new URL(req.url, `http://${req.headers.host}`);
const pathname = parsedUrl.pathname;
const method = req.method;

// 收请求体
const chunks = [];
req.on('data', c => chunks.push(c));
req.on('end', () => {
  const body = JSON.parse(Buffer.concat(chunks).toString());
  // ... 业务
});

// 响应前要写 JSON 头
res.writeHead(200, { 'Content-Type': 'application/json' });
res.end(JSON.stringify(result));
```

而且这些场景原生模块都**没现成方案**：

| 痛点 | 原生要做的事 | 框架已封装 |
|------|---------------|-----------|
| 路径参数 `/users/:id` | 自己写正则或拆段 | `req.params.id` |
| 路由分组 | 自己拼前缀 | `Router` 子路由 |
| 请求体解析 | 自己监听流 + 判 Content-Type | `app.use(express.json())` |
| 统一错误处理 | 每个 try 都得自己 catch | 错误中间件 |
| 中间件链 | 自己手写"洋葱模型" | `app.use` |
| 静态文件 | 自己实现 mime + 流 | `express.static('public')` |
| 模板渲染 | 自己拼字符串 | `res.render('index', data)` |
| Cookie / Session | 自己解析 | `cookie-parser` |
| 安全头 | 自己设 | `helmet` |

**Express**（下一篇 Day10 的主角）把这些重复劳动压缩成了几行：

```js
const express = require('express');
const app = express();
app.use(express.json());                    // 自动解析 JSON 请求体

app.get('/api/users/:id', (req, res) => {
  res.json({ id: req.params.id });          // 自动设 Content-Type + JSON.stringify
});

app.listen(3000);
```

理解原生 `http` 的最大价值在于：

1. **看懂框架源码**——Express 的 `req` / `res` 正是对 `IncomingMessage` / `ServerResponse` 的扩展。
2. **遇到框架 bug 时不慌**——能下钻到底层事件流定位问题。
3. **知道性能瓶颈在哪**——框架只是封装，真正的 I/O 还是 `http` 模块那套。

下一篇我们就来学 Express，把今天手写的所有样板代码"折叠"起来。

---

## 八、关键知识点总结

1. **HTTP 协议**：请求/响应结构对称（起始行 → Headers → 空行 → Body），无状态。
2. **方法语义**：GET 查、POST 增、PUT 全量改、PATCH 部分改、DELETE 删。安全/幂等是判断 RESTful 设计的尺子。
3. **状态码 5 类**：1xx 信息、2xx 成功、3xx 重定向、4xx 客户端错、5xx 服务端错。
4. **Content-Type 决定解析方式**：JSON / 表单 / multipart 三种主流格式，要按头分流。
5. **Node http 模块四角色**：`http.Server` / `IncomingMessage`（Readable）/ `ServerResponse`（Writable）/ `ClientRequest`。
6. **req 是流**：必须用 `data` + `end` 拿请求体，**所有处理逻辑要放在 `end` 回调里**。
7. **拼 Buffer 用 `Buffer.concat`**，不要字符串拼接，避免多字节字符拆分乱码。
8. **响应头必须先于响应体**：`writeHead` 一旦调用即锁定，之后 `setHeader` 无效。
9. **必须 `res.end()`**：不调用请求会挂起；调用后不能再 `write`。
10. **大文件用 `createReadStream` + `pipe`**，依靠背压避免内存爆炸。
11. **`new URL(req.url, base)` 解析 pathname 和 query**，`searchParams.get` 取参数。
12. **路由分发**：对象映射比 if/else 更工程化，但不支持路径参数（这是框架的入口）。
13. **CORS 是浏览器行为**：响应头加 `Access-Control-Allow-*`；预检 `OPTIONS` 直接 `204`。
14. **`http.get` / `http.request` 不因 4xx/5xx 报错**，要自己看 `statusCode`。
15. **超时控制**：`req.setTimeout(ms, () => req.destroy(err))`，destroy 才会真正断开。
16. **Node 18+ 原生 `fetch`**：业务代码优先用，更简洁；底层控制才回到 `http`。
17. **IPv4 vs IPv6**：默认监听 `::` 双栈，IPv4 以 `::ffff:` 前缀呈现；只想 IPv4 显式传 `'0.0.0.0'`。
18. **原生够用但啰嗦**：路径参数、中间件、统一错误处理都要自己造轮子——这就是 Express 存在的意义。

---

## 九、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：最简服务器 + curl 验证（对应 `hello-server.js`）

1. 用 `http.createServer` 启动一个监听 `3000` 端口的服务器，无论什么请求都返回 `Hello HTTP`。
2. 启动后用 `curl http://localhost:3000` 验证。
3. 进阶：让根路径 `/` 返回 `Hello`，其他路径返回 `Bye`。

**测试命令**：

```bash
node Code/hello-server.js
# 另开终端
curl http://localhost:3000
curl http://localhost:3000/anything
```

### 练习 2：路由分发 + query 解析（对应 `router-server.js`）

实现一个服务器，满足：

| 路径 | 方法 | 行为 |
|------|------|------|
| `/` | GET | 返回 `"首页"` |
| `/api/users` | GET | 读取 query 参数 `page`（默认 1）和 `limit`（默认 10），返回 `{ page, limit }` |
| `/api/time` | GET | 返回当前 ISO 时间 |
| 其他 | * | 返回 `404` |

要求用对象映射方式实现，所有响应都是 JSON，并设置正确的 `Content-Type`。

**测试命令**：

```bash
node Code/router-server.js
curl http://localhost:3001/
curl "http://localhost:3001/api/users?page=2&limit=20"
curl http://localhost:3001/api/time
curl -i http://localhost:3001/nope   # 看 404 状态码
```

### 练习 3：JSON API + CORS + POST 请求体（对应 `json-api-server.js`）

实现一个服务器（端口 3002），具备：

1. `GET /api/ping` 返回 `{ ok: true, time: <now> }`。
2. `POST /api/echo` 接收 JSON 请求体 `{ message: "..." }`，返回 `{ received: "..." }`。
3. 请求体非 JSON 或字段缺失时返回 `400` + `{ error: "..." }`。
4. 全局加 CORS 头，正确处理 `OPTIONS` 预检。
5. 限制请求体大小为 1MB，超出返回 `413`。

**测试命令**：

```bash
node Code/json-api-server.js

# 简单 GET
curl http://localhost:3002/api/ping

# 预检 OPTIONS
curl -X OPTIONS http://localhost:3002/api/echo \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" -i

# POST JSON
curl -X POST http://localhost:3002/api/echo \
  -H "Content-Type: application/json" \
  -d '{"message":"hi from curl"}'

# 故意发坏 JSON
curl -X POST http://localhost:3002/api/echo \
  -H "Content-Type: application/json" \
  -d 'not-a-json'
```

### 练习 4：HTTP 客户端对比（对应 `http-client.js` 与 `fetch-client.mjs`）

1. 用 `http.get` 请求 `https://jsonplaceholder.typicode.com/users/1`（注意要切到 `https` 模块），打印用户名和邮箱；设置 3 秒超时，超时则报错退出。
2. 用原生 `fetch` 实现完全相同的功能，对比代码量与可读性。
3. 把超时改成 1ms，验证错误能被捕获。

**运行命令**：

```bash
node Code/http-client.js
node Code/fetch-client.mjs
```

### 练习 5：静态文件服务器（对应 `static-file-server.js`）

实现一个静态文件服务器（端口 3004），根目录指向同目录的 `public` 文件夹（如果没有，自己建一个并放点 `index.html`、`a.txt`）：

1. 按扩展名映射 `Content-Type`，至少覆盖 `.html / .css / .js / .json / .png / .txt`。
2. 文件不存在返回 `404`。
3. 用 `fs.createReadStream` + `pipe` 流式返回，能服务大文件。
4. 防路径穿越：`GET /../../etc/passwd` 不能读到上层文件。

**测试命令**：

```bash
node Code/static-file-server.js
curl http://localhost:3004/index.html
curl -i http://localhost:3004/not-exist.txt
```

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/hello-server.js` | 最简 HTTP 服务器，返回纯文本 |
| `Code/router-server.js` | 手动路由分发，query 参数解析，404 处理 |
| `Code/json-api-server.js` | GET/POST、JSON 请求体解析、CORS、OPTIONS 预检 |
| `Code/http-client.js` | `http.get` 请求公共 API，超时与错误处理 |
| `Code/fetch-client.mjs` | 原生 `fetch`（Node 18+）等价实现，与 `http` 模块对比 |
| `Code/static-file-server.js` | 文件服务，MIME 判断，`createReadStream` 流式返回，404，防路径穿越 |

运行方式（Node 18+）：

```bash
# 服务器类（启动后可用 curl 测试，注释里有具体命令）
node Code/hello-server.js
node Code/router-server.js
node Code/json-api-server.js
node Code/static-file-server.js

# 客户端类
node Code/http-client.js
node Code/fetch-client.mjs
```

---

> 📚 **延伸阅读**
> - Node.js 官方文档：[HTTP](https://nodejs.org/api/http.html)
> - MDN：[HTTP 概述](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Overview)
> - MDN：[CORS](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)
> - RFC 7230 ~ 7235：HTTP/1.1 协议规范
> - Node.js 官方文档：[fetch（实验性稳定）](https://nodejs.org/api/globals.html#fetch)
> - undici：[Node 高性能 HTTP 客户端](https://github.com/nodejs/undici)
