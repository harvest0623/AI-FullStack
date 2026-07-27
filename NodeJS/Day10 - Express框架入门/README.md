# Day10 - Express 框架入门

> 本篇聚焦 Node.js 生态中最经典的 Web 框架——**Express**。你将告别 Day09 中“手搓原生 `http` 模块”的繁琐，理解框架为解决了什么问题而来，掌握路由、中间件、请求/响应对象等核心机制，并亲手跑通一个模块化的 CRUD 接口。Express 是后续学习鉴权、文件上传、AI 接口编排等高级主题的地基。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 Express 是什么](#21-express-是什么)
  - [2.2 为什么需要框架：原生 http 模块的痛点](#22-为什么需要框架原生-http-模块的痛点)
  - [2.3 Express 核心特性](#23-express-核心特性)
  - [2.4 Express 应用对象 app](#24-express-应用对象-app)
  - [2.5 Express 的极简哲学与生态](#25-express-的极简哲学与生态)
  - [2.6 Express 4 vs Express 5 现状](#26-express-4-vs-express-5-现状)
  - [2.7 与 Koa / Fastify / NestJS 的定位对比](#27-与-koa--fastify--nestjs-的定位对比)
- [三、快速上手](#三快速上手)
  - [3.1 安装](#31-安装)
  - [3.2 Hello World](#32-hello-world)
  - [3.3 监听端口](#33-监听端口)
  - [3.4 路由基本写法](#34-路由基本写法)
  - [3.5 路由路径匹配](#35-路由路径匹配)
  - [3.6 路由参数 :id](#36-路由参数-id)
  - [3.7 查询参数 req.query](#37-查询参数-reqquery)
  - [3.8 请求体 req.body](#38-请求体-reqbody)
  - [3.9 req.params / req.body / req.query 区别](#39-reqparams--reqbody--reqquery-区别)
- [四、应用与路由结构](#四应用与路由结构)
  - [4.1 app.use 挂载中间件](#41-appuse-挂载中间件)
  - [4.2 express.Router 子路由](#42-expressrouter-子路由)
  - [4.3 路由模块化拆分](#43-路由模块化拆分)
- [五、常用内置中间件](#五常用内置中间件)
- [六、请求与响应对象](#六请求与响应对象)
  - [6.1 req 常用属性与方法](#61-req-常用属性与方法)
  - [6.2 res 常用方法](#62-res-常用方法)
  - [6.3 链式调用](#63-链式调用)
- [七、项目结构建议](#七项目结构建议)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 准确说明 Express 相对于原生 `http` 模块解决了哪些工程痛点。
2. 解释中间件的“洋葱式”执行模型，能写出带 `next()` 的自定义中间件。
3. 区分 `req.params`、`req.query`、`req.body` 三种请求数据的来源与使用场景。
4. 使用 `app.get/post/put/delete` 定义 RESTful 风格的接口。
5. 使用 `express.Router` 将路由按业务模块拆分，并通过 `app.use` 挂载。
6. 掌握 `express.json()`、`express.urlencoded()`、`express.static()` 等内置中间件的用途。
7. 熟练使用 `res.json()`、`res.status()`、`res.redirect()`、`res.cookie()` 等响应方法，并理解链式调用。
8. 设计一个 routes / controllers / middlewares / models 分层的 Express 项目结构。
9. 了解 Express 4 与 Express 5 的差异，以及它与 Koa、Fastify、NestJS 的定位关系，为后续技术选型铺垫。

---

## 二、理论知识讲解

### 2.1 Express 是什么

**Express** 是 Node.js 平台上最流行、最轻量的 Web 应用框架，由 TJ Holowaychuk 于 2010 年发布。它构建在 Node 原生 `http` 模块之上，提供了一套极简而强大的 API，用于构建 Web 应用、RESTful API、静态文件服务、服务端渲染等。

一句话概括它的定位：

> Express 是一个**路由与中间件**框架——它本身几乎不包含业务功能，所有能力都通过“中间件”组合而来。

它的核心由三件事组成：

1. **接收 HTTP 请求**（委托给底层 `http` 模块）。
2. **按注册顺序匹配路由**，找到对应的处理函数。
3. **沿中间件链流转请求**，每个中间件可读取/修改 `req`、`res`，并决定是否交给下一个中间件。

```js
const express = require('express');
const app = express();

app.get('/', (req, res) => res.send('Hello Express'));

app.listen(3000);
```

短短几行就跑起一个 HTTP 服务，这是原生 `http` 模块做不到的简洁。

### 2.2 为什么需要框架：原生 http 模块的痛点

在 Day09 中，我们用原生 `http` 模块写过类似这样的代码：

```js
const http = require('http');
const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/users') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify([{ id: 1, name: 'Alice' }]));
  } else if (req.method === 'POST' && req.url === '/users') {
    let body = '';
    req.on('data', (chunk) => (body += chunk));
    req.on('end', () => {
      const data = JSON.parse(body);
      res.writeHead(201, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(data));
    });
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});
server.listen(3000);
```

随着接口数量增长，原生写法会暴露出明显痛点：

| 痛点 | 原生 http 模块的表现 | Express 的解法 |
|------|----------------------|-----------------|
| **路由匹配繁琐** | 手写 `if (method === 'X' && url === 'Y')`，扩展性差 | `app.get('/users/:id', ...)` 声明式路由，支持路径模式与正则 |
| **路径参数解析** | 自己 `split('/')` 切字符串，易错 | `:id` 自动注入 `req.params.id` |
| **请求体解析** | 监听 `data`/`end` 事件手动拼接，还要处理编码与异常 | `express.json()` 一行解决 |
| **查询参数** | 手动 `new URL(req.url).searchParams` | 自动注入 `req.query` |
| **响应简化** | `writeHead` + `end`，JSON 要手动序列化与设头 | `res.json()` 自动序列化并设 `Content-Type` |
| **中间件/切面** | 无统一机制，日志、鉴权、错误处理散落各处 | 统一的中间件链，按需插拔 |
| **错误处理** | 同步抛错会导致进程崩溃，需大量 `try/catch` | 四参数错误处理中间件集中兜底 |
| **模块化** | 路由堆在一个 `createServer` 回调里，难以拆分 | `express.Router` 按模块拆分 |

简言之：原生 `http` 模块是“零件”，Express 是“组装好的底盘”——它不替你造发动机，但让你能专注业务，而不是反复造轮子。

### 2.3 Express 核心特性

Express 的能力可归纳为四大支柱：

#### ① 路由（Routing）

根据 **HTTP 方法 + URL 路径** 把请求分发给对应的处理函数。

```js
app.get('/users', getUsers);
app.post('/users', createUser);
app.put('/users/:id', updateUser);
app.delete('/users/:id', deleteUser);
```

#### ② 中间件（Middleware）

中间件是“处理请求的函数队列”，每个函数签名为 `(req, res, next) => {}`。Express 请求生命周期就是一串中间件依次执行：

```
请求 ──► 日志 ──► 鉴权 ──► 解析body ──► 路由处理 ──► 错误处理 ──► 响应
```

中间件可以：

- 执行任意代码（日志、统计、埋点）。
- 修改 `req`、`res` 对象（如注入 `req.user`）。
- 终结请求-响应循环（如鉴权失败直接 `res.status(401).end()`）。
- 调用 `next()` 把控制权交给下一个中间件。

```js
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);
  next(); // 不调用 next，请求会挂起
});
```

#### ③ 模板引擎（Template Engine）

Express 可结合 Pug、EJS、Handlebars 等模板引擎做服务端渲染（SSR）：

```js
app.set('view engine', 'ejs');
app.get('/profile', (req, res) => {
  res.render('profile', { name: 'Alice' }); // 渲染 views/profile.ejs
});
```

> 现代 AI 全栈项目多以“前后端分离”为主，SSR 用得较少，本篇不深入，了解即可。

#### ④ 静态文件服务（Static Files）

`express.static` 可直接把某个目录作为静态资源对外提供：

```js
app.use(express.static('public'));
// public/index.html → http://localhost:3000/index.html
```

### 2.4 Express 应用对象 app

`const app = express()` 创建的 `app` 是整个应用的“总指挥”，它同时承担两类角色：

| 角色 | 作用 | 典型 API |
|------|------|----------|
| **中间件容器** | 注册全局中间件，对所有请求生效 | `app.use(fn)`、`app.use('/api', fn)` |
| **路由容器** | 定义顶层路由 | `app.get/post/put/delete(path, fn)` |
| **配置容器** | 存储应用级设置 | `app.set('key', value)`、`app.get('key')` |
| **服务启动器** | 监听端口启动 HTTP 服务 | `app.listen(port, callback)` |

`app` 本质上也是一个“大中间件”，因此它可以被挂载到另一个应用上（子应用模式），也可以被 `express.Router` 复用相同 API 风格。

### 2.5 Express 的极简哲学与生态

Express 遵循 **“小核心 + 大生态”** 的 Unix 哲学：

- **核心极小**：Express 自身只提供路由、中间件机制、几个内置中间件，连 session、CSRF、文件上传都不内置。
- **生态丰富**：几乎所有功能都有对应的 `npm` 中间件，按需安装：

| 需求 | 常用中间件 |
|------|-----------|
| Cookie 解析 | `cookie-parser` |
| Session | `express-session` |
| 文件上传 | `multer` |
| 跨域 | `cors` |
| 日志 | `morgan` |
| 安全加固 | `helmet` |
| 压缩 | `compression` |
| 参数校验 | `express-validator` / `zod` |
| 登录鉴权 | `passport` / `jsonwebtoken` |

这种“框架不替你做决定”的风格，让 Express 既能写一个 10 行的脚本，也能撑起大型项目。代价是：当项目变大时，架构和规范需要团队自行约定。

### 2.6 Express 4 vs Express 5 现状

Express 5 在 2024 年正式发布（GA），但截至 2026 年，**Express 4 仍是生产环境的主流**，原因是大量中间件与教程都基于 4.x。

| 维度 | Express 4.x | Express 5.x |
|------|-------------|-------------|
| 发布状态 | 长期稳定，生态最完整 | 已 GA，生态逐步跟进 |
| Node 版本 | Node 0.10+ | Node 18+ |
| 路由引擎 | 自实现，基于 path-to-regexp 0.x | 基于 path-to-regexp 8.x，语法更严谨 |
| 异步错误 | 同步抛错自动捕获；异步需手动 `next(err)` | 对 Promise/async 更友好，支持自动转发 rejection |
| 移除的 API | — | 移除 `app.del`、`res.json(status)`、`res.send(status)`、`req.param()` 等历史包袱 |
| 路由路径 | 支持部分模糊写法 | 更严格，`:name` 不再匹配 `/`，正则语法统一 |
| 推荐场景 | 现有项目、教程学习 | 新项目评估、追求现代化 |

> 本篇示例统一使用 **Express 4**（`express@^4.21.2`），因为它与绝大多数现有教程、中间件兼容，学习曲线最平缓。学完后迁移到 5 主要注意上述 breaking changes，整体心智模型一致。

### 2.7 与 Koa / Fastify / NestJS 的定位对比

Node.js 框架生态中，Express 并非唯一选择。提前了解它们的定位差异，有助于后续技术选型：

| 框架 | 定位 | 与 Express 的关系 | 特点 | 适合场景 |
|------|------|-------------------|------|----------|
| **Express** | 极简 Web 框架 | — | 回调风格、生态最丰富、心智最简单 | 入门、中小型 API、快速原型 |
| **Koa** | 极简 Web 框架 | Express 原班团队“下一代” | `async/await` 原生、洋葱模型更纯粹、不内置中间件 | 追求异步优雅、自定义程度高 |
| **Fastify** | 高性能 Web 框架 | 另起炉灶 | 性能极高、内置 JSON Schema 校验、插件体系严谨 | 高吞吐 API、对性能敏感 |
| **NestJS** | 企业级应用框架 | 可基于 Express/Fastify 作底层 | 强 OOP、装饰器、依赖注入、自带工程规范（类似 Spring） | 大型后端、团队协作、微服务 |

一个常见的认知坐标：

```
   极简/自由  ◄────────────────────────►  重量/规范
   Express ── Koa ── Fastify ──────────── NestJS
```

- **学习顺序建议**：先 Express（理解路由与中间件本质）→ 按需深入 Koa/Fastify（性能与异步）→ NestJS（企业架构）。
- 对 AI 全栈工程师而言，Express 足以承载大多数 AI 接口编排、Agent 后端、内部工具；当项目复杂到需要 DI、模块化时再上 NestJS。

---

## 三、快速上手

> 本节代码对应 `Code/` 目录下的示例文件，进入该目录执行 `npm install` 后即可运行。

### 3.1 安装

```bash
# 初始化项目（已有 package.json 可跳过）
npm init -y

# 安装 Express
npm install express
```

`package.json` 关键字段：

```json
{
  "dependencies": {
    "express": "^4.21.2"
  }
}
```

### 3.2 Hello World

最小的 Express 应用（对应 `app.js`）：

```js
const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.json({ message: 'Hello Express' });
});

app.listen(3000, () => {
  console.log('Server running at http://localhost:3000');
});
```

运行与访问：

```bash
node app.js
# 浏览器或 curl 访问 http://localhost:3000
```

### 3.3 监听端口

`app.listen(port, callback)` 内部调用 `http.createServer(app).listen(...)`，返回一个 `http.Server` 实例。

```js
const PORT = process.env.PORT || 3000; // 支持环境变量覆盖
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
```

> 生产环境通常不直接用 `app.listen`，而是交给 PM2、Docker 或 nginx 反向代理管理进程。

### 3.4 路由基本写法

Express 提供 `app.METHOD(path, handler)` 形式定义路由，METHOD 为小写 HTTP 方法：

```js
app.get('/users', (req, res) => { /* 查询列表 */ });
app.post('/users', (req, res) => { /* 创建 */ });
app.put('/users/:id', (req, res) => { /* 全量更新 */ });
app.patch('/users/:id', (req, res) => { /* 部分更新 */ });
app.delete('/users/:id', (req, res) => { /* 删除 */ });

// app.all 匹配所有方法；app.use 也可作为通配中间件
app.all('/health', (req, res) => res.json({ status: 'ok' }));
```

一个路由可挂多个处理函数（链式中间件）：

```js
app.get(
  '/orders/:id',
  authenticate,    // 鉴权
  loadOrder,       // 加载资源
  sendOrder        // 响应
);
```

### 3.5 路由路径匹配

Express 路径支持三种写法：

| 写法 | 示例 | 匹配 |
|------|------|------|
| **字符串** | `app.get('/users', ...)` | 精确匹配 `/users` |
| **字符串模式** | `app.get('/users/:id', ...)` | `/users/123`、`/users/abc` |
| **正则表达式** | `app.get(/^\/users\/\d+$/, ...)` | 仅匹配数字 id，如 `/users/123` |

字符串模式中的特殊字符：

```js
app.get('/ab?cd', handler);      // 匹配 /acd 或 /abcd（? 表示前一个字符可选）
app.get('/ab+cd', handler);      // 匹配 /abcd、/abbcd、/abbbcd（+ 至少一次）
app.get('/ab*cd', handler);      // 匹配 /abcd、/abXcd、/abXYZcd（* 任意）
app.get('/ab(cd)?e', handler);   // 匹配 /abe 或 /abcde（括号分组可选）
```

### 3.6 路由参数 :id

以冒号开头的路径段是**命名参数**，自动收集到 `req.params`：

```js
// GET /users/42
app.get('/users/:id', (req, res) => {
  console.log(req.params.id); // '42'
  res.json({ id: req.params.id });
});
```

多参数与通配：

```js
app.get('/posts/:postId/comments/:commentId', (req, res) => {
  // GET /posts/1/comments/5
  const { postId, commentId } = req.params;
});

app.get('/files/*', (req, res) => {
  // GET /files/a/b/c.txt
  console.log(req.params[0]); // 'a/b/c.txt'
});
```

### 3.7 查询参数 req.query

URL 中 `?` 之后的键值对自动解析到 `req.query`，无需任何中间件：

```js
// GET /users?keyword=ali&page=1&limit=20
app.get('/users', (req, res) => {
  const { keyword, page, limit } = req.query;
  // keyword='ali', page='1', limit='20'（均为字符串）
  res.json({ keyword, page: Number(page), limit: Number(limit) });
});
```

> 注意：`req.query` 的值默认都是字符串，需要数字时手动转换。Express 5 起，解析行为受 `query parser` 设置控制。

### 3.8 请求体 req.body

`req.body` **默认是 `undefined`**，必须先注册对应的解析中间件才能拿到：

```js
app.use(express.json());                          // 解析 application/json
app.use(express.urlencoded({ extended: true }));  // 解析表单 application/x-www-form-urlencoded

app.post('/users', (req, res) => {
  const { name, email } = req.body; // 现在能拿到
  res.status(201).json({ name, email });
});
```

| 请求体类型 | Content-Type | 所需中间件 |
|-----------|--------------|-----------|
| JSON | `application/json` | `express.json()` |
| 表单 | `application/x-www-form-urlencoded` | `express.urlencoded()` |
| 原始 Buffer | `application/octet-stream` | `express.raw()` |
| 纯文本 | `text/plain` | `express.text()` |
| multipart 文件上传 | `multipart/form-data` | 第三方 `multer` |

### 3.9 req.params / req.body / req.query 区别

三者是最常用的请求入口，务必分清：

| 属性 | 数据来源 | 出现位置 | 是否需要中间件 | 典型用途 |
|------|---------|----------|---------------|----------|
| `req.params` | URL 路径中的命名段 | `/users/:id` → `/users/42` | 否（路由自带） | 资源标识，如 `id`、`slug` |
| `req.query` | URL 问号后的键值对 | `/search?q=express&page=2` | 否（自动解析） | 过滤、分页、搜索条件 |
| `req.body` | 请求体（payload） | POST/PUT/PATCH 的 body | **是**（需 `express.json()` 等） | 创建/更新资源的数据 |

记忆口诀：

- **params 定“是谁”**（Which resource）。
- **query 定“怎么筛”**（How to filter）。
- **body 定“改什么”**（What to write）。

举例对照：

```bash
# 更新 id=42 的用户，name 放 body，返回时带 ?fields=email 查询参数
curl -X PUT http://localhost:3000/users/42?fields=email \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice"}'

# 路由内：
// app.put('/users/:id', (req, res) => {
//   req.params.id      // '42'      ← 路径参数
//   req.query.fields   // 'email'   ← 查询参数
//   req.body.name      // 'Alice'   ← 请求体
// });
```

---

## 四、应用与路由结构

### 4.1 app.use 挂载中间件

`app.use` 是注册中间件的通用方式，支持多种重载：

```js
// 1) 全局中间件：对所有路径、所有方法生效
app.use((req, res, next) => {
  console.log(req.method, req.url);
  next();
});

// 2) 路径前缀中间件：只对 /api/* 生效
app.use('/api', (req, res, next) => {
  req.startTime = Date.now();
  next();
});

// 3) 挂载子应用 / 子路由
app.use('/api/users', usersRouter);

// 4) 错误处理中间件（四参数，放最后）
app.use((err, req, res, next) => {
  res.status(500).json({ error: err.message });
});
```

`app.use` 与 `app.METHOD` 的区别：

| 项 | `app.use` | `app.get/post/...` |
|----|-----------|--------------------|
| 匹配方式 | 前缀匹配（`/api` 匹配 `/api`、`/api/x`） | 精确匹配（`/api` 只匹配 `/api`） |
| HTTP 方法 | 所有方法 | 指定方法 |
| 典型用途 | 挂中间件、挂子路由 | 定义业务路由 |

### 4.2 express.Router 子路由

`express.Router` 是一个“迷你应用”，拥有与 `app` 几乎相同的 API（`use/get/post/...`），但不会自动监听端口。它专门用于**把一组路由打包成模块**。

```js
// users-router.js
const express = require('express');
const router = express.Router();

router.get('/', (req, res) => { /* 列表 */ });
router.get('/:id', (req, res) => { /* 详情 */ });
router.post('/', (req, res) => { /* 创建 */ });

module.exports = router;
```

```js
// server.js
const usersRouter = require('./users-router');
app.use('/api/users', usersRouter); // 挂载，自动拼前缀
```

效果：`router.get('/')` 实际响应 `GET /api/users`，`router.get('/:id')` 响应 `GET /api/users/:id`。

### 4.3 路由模块化拆分

随着接口增多，把所有路由堆在 `server.js` 会失控。推荐按资源/业务模块拆分：

```
routes/
  index.js          // 聚合所有子路由
  users.js          // 用户相关
  posts.js          // 文章相关
  auth.js           // 鉴权相关
```

聚合文件示例：

```js
// routes/index.js
const express = require('express');
const router = express.Router();

router.use('/users', require('./users'));
router.use('/posts', require('./posts'));
router.use('/auth', require('./auth'));

module.exports = router;
```

```js
// app.js
app.use('/api', require('./routes')); // 统一加 /api 前缀
```

这样最终 URL 形如 `/api/users`、`/api/posts`，结构清晰、易于维护。本篇 `users-router.js` + `server.js` 即此模式的最小可运行版本。

---

## 五、常用内置中间件

Express 4.x 起将多数中间件从核心拆出独立包，但保留了最常用的几个内置：

| 中间件 | 作用 | 典型用法 |
|--------|------|----------|
| `express.json()` | 解析 JSON 请求体 → `req.body` | `app.use(express.json())` |
| `express.urlencoded({ extended })` | 解析 URL 编码表单 → `req.body` | `extended:true` 用 qs 库支持嵌套 |
| `express.static(root, options)` | 提供静态文件服务 | `app.use(express.static('public'))` |
| `express.raw(options)` | 将请求体解析为 Buffer | 用于二进制数据 |
| `express.text(options)` | 将请求体解析为字符串 | 用于 `text/plain` |
| `express.Router()` | 创建可挂载的子路由 | 见 4.2 |

使用示例：

```js
// JSON 与表单
app.use(express.json({ limit: '1mb' }));           // 限制大小，防止超大 body
app.use(express.urlencoded({ extended: true }));    // true 支持 a[b]=1 嵌套

// 静态文件
app.use('/assets', express.static('public', {
  maxAge: '1d',          // 浏览器缓存 1 天
  etag: true,
  lastModified: true
}));

// 原始 Buffer / 纯文本
app.use('/webhook', express.raw({ type: '*/*' }));
app.use('/echo', express.text({ type: 'text/plain' }));
```

> 已被拆出但常见的历史中间件：`body-parser`（功能已并入 `express.json/urlencoded`）、`cookie-parser`、`morgan`、`serve-favicon` 等，需单独安装。

---

## 六、请求与响应对象

Express 对原生 `http.IncomingMessage` 和 `http.ServerResponse` 做了封装与增强，得到 `req` 和 `res`。

### 6.1 req 常用属性与方法

| 属性/方法 | 说明 | 示例 |
|----------|------|------|
| `req.method` | HTTP 方法 | `'GET'`、`'POST'` |
| `req.url` / `req.originalUrl` | 请求 URL（`originalUrl` 保留原始） | `'/api/users/1?a=1'` |
| `req.path` | 不含查询串的路径 | `'/api/users/1'` |
| `req.params` | 路由命名参数 | `{ id: '1' }` |
| `req.query` | 查询参数对象 | `{ a: '1' }` |
| `req.body` | 请求体（需中间件解析） | `{ name: 'Alice' }` |
| `req.headers` | 请求头对象（小写键） | `{ 'content-type': '...' }` |
| `req.get(field)` | 读取某个请求头（别名 `req.header`） | `req.get('user-agent')` |
| `req.cookies` | Cookie 对象（需 `cookie-parser`） | `{ token: 'xxx' }` |
| `req.ip` | 客户端 IP | `'127.0.0.1'` |
| `req.hostname` | 主机名 | `'localhost'` |
| `req.protocol` | 协议 | `'http'` / `'https'` |

### 6.2 res 常用方法

| 方法 | 说明 | 示例 |
|------|------|------|
| `res.send(body)` | 发送响应（自动判断类型） | `res.send('hi')` / `res.send({a:1})` |
| `res.json(obj)` | 发送 JSON（自动序列化 + 设头） | `res.json({ ok: true })` |
| `res.status(code)` | 设置状态码（返回 res，可链式） | `res.status(201)` |
| `res.set(field, value)` | 设置响应头（别名 `res.header`） | `res.set('X-Custom', '1')` |
| `res.get(field)` | 读取响应头 | `res.get('Content-Type')` |
| `res.redirect([code], url)` | 重定向 | `res.redirect(302, '/login')` |
| `res.cookie(name, value, opts)` | 设置 Cookie | `res.cookie('token', 'xxx', { httpOnly: true })` |
| `res.clearCookie(name)` | 清除 Cookie | `res.clearCookie('token')` |
| `res.render(view, locals)` | 渲染模板 | `res.render('profile', { name })` |
| `res.end()` | 结束响应（不写 body） | `res.status(204).end()` |
| `res.type(type)` | 设置 Content-Type | `res.type('json')` |

### 6.3 链式调用

多数 `res` 方法返回 `res` 本身，可链式书写：

```js
res
  .status(201)
  .set('Location', `/users/${newUser.id}`)
  .set('X-RateLimit-Remaining', '99')
  .json({ data: newUser });
```

```js
res
  .status(401)
  .set('WWW-Authenticate', 'Bearer')
  .end();
```

> 关键规则：一个请求只能**终结一次**。`send` / `json` / `end` / `redirect` 都是终结方法，调用后不要再调用其它终结方法。

---

## 七、项目结构建议

中大型 Express 项目推荐按职责分层，避免单文件膨胀：

```
project-root/
├── src/
│   ├── app.js                 # 创建 app，注册全局中间件（不监听端口）
│   ├── server.js              # 监听端口，启动入口
│   ├── config/                # 配置（环境变量、常量）
│   │   └── index.js
│   ├── routes/                # 路由层：只定义路径与处理器映射
│   │   ├── index.js
│   │   ├── user.routes.js
│   │   └── post.routes.js
│   ├── controllers/           # 控制器层：处理请求/响应编排
│   │   ├── user.controller.js
│   │   └── post.controller.js
│   ├── middlewares/           # 自定义中间件
│   │   ├── auth.js
│   │   ├── logger.js
│   │   └── error-handler.js
│   ├── models/                # 数据层（Mongoose / Sequelize / 自封装）
│   │   ├── user.model.js
│   │   └── post.model.js
│   ├── services/              # 业务逻辑层（可选，进一步解耦）
│   │   └── user.service.js
│   └── utils/                 # 工具函数
│       └── response.js
├── public/                    # 静态资源
├── tests/                     # 测试
├── .env                       # 环境变量
└── package.json
```

分层职责：

| 层 | 职责 | 不该做的事 |
|----|------|-----------|
| routes | 声明路径、HTTP 方法、绑定控制器 | 不写业务逻辑 |
| controllers | 解析 `req`、调用 service、组装 `res` | 不直接操作数据库 |
| services | 业务规则编排 | 不关心 HTTP |
| models | 数据访问与校验 | 不含 HTTP 逻辑 |
| middlewares | 横切关注点（日志、鉴权、错误） | 不含业务规则 |

> 本篇的 `users-router.js` 为教学简洁起见，把路由与处理逻辑写在一起。真实项目中应拆成 `routes/user.routes.js` + `controllers/user.controller.js`。

---

## 八、关键知识点总结

1. **Express = 路由 + 中间件**。它不内置业务功能，一切能力靠中间件组合。
2. **中间件签名** `(req, res, next) => {}`，必须调用 `next()` 才会继续；四参数版本 `(err, req, res, next) => {}` 是错误处理中间件，需放最后。
3. **app.use 前缀匹配，app.METHOD 精确匹配**。挂子路由用 `app.use('/prefix', router)`。
4. **req.params（路径）、req.query（查询串）、req.body（请求体）** 是三大请求入口，`req.body` 默认 `undefined`，必须先注册解析中间件。
5. **express.Router** 是路由模块化的核心工具，让大型项目可按业务拆分。
6. **内置中间件**：`express.json()`、`express.urlencoded()`、`express.static()`、`express.raw()`、`express.text()`。
7. **res 终结方法只能调一次**：`send` / `json` / `end` / `redirect` / `render`。`status`、`set`、`cookie` 可链式。
8. **Express 4 是当前主流**，5 已 GA 但生态仍在跟进；学习用 4，新项目可评估 5。
9. **生态定位**：Express 极简通用 → Koa 异步优雅 → Fastify 高性能 → NestJS 企业架构。
10. **分层结构**：routes / controllers / services / models / middlewares 各司其职，是中大型项目的工程基础。

---

## 九、实战练习

> 以下练习在 `Code/` 目录基础上扩展，建议独立完成后再对照本篇结论自查。

### 练习一：实现一个文章（Posts）CRUD 模块

**目标**：模仿 `users-router.js`，新增一个 `posts-router.js` 并挂载到 `/api/posts`。

**要求**：

1. 数据结构：`{ id, title, content, author, createdAt }`。
2. 实现 `GET /api/posts`（列表）、`GET /api/posts/:id`（详情）、`POST /api/posts`（创建）、`PUT /api/posts/:id`（更新）、`DELETE /api/posts/:id`（删除）。
3. 创建时自动填充 `createdAt`；列表支持 `?limit=N` 查询参数限制返回数量。
4. 在 `server.js` 中 `app.use('/api/posts', postsRouter)` 挂载，并补充对应 curl 测试命令。

**考察点**：`express.Router` 模块化、`req.params`、`req.body`、`req.query` 综合运用。

### 练习二：写一个简易鉴权中间件

**目标**：实现一个基于请求头的“伪鉴权”中间件。

**要求**：

1. 新建 `middlewares/auth.js`，导出一个中间件函数。
2. 读取请求头 `x-api-key`，若不等于 `process.env.API_KEY`（默认 `'secret123'`）则返回 `401 { error: '未授权' }`。
3. 把它挂载到 `/api/posts` 前缀上，使文章接口需要鉴权；但 `/api/users` 与 `/health` 不需要。
4. 思考：为什么中间件注册顺序很重要？

**考察点**：自定义中间件、`req.get`、`app.use(path, middleware)` 的前缀作用域。

### 练习三：扩展日志中间件并接入错误处理

**目标**：在 `middleware-demo.js` 思路基础上，做一个更工程化的日志与错误处理方案。

**要求**：

1. 自定义 `logger` 中间件，记录：时间、方法、路径、状态码、耗时、客户端 IP，输出成一行 JSON（便于后续被日志系统采集）。
2. 自定义 `errorHandler` 错误处理中间件，捕获同步错误与 `next(err)` 转发的错误，统一返回 `{ error: message, code: status }`，并打印错误堆栈到终端。
3. 写一个异步路由 `GET /api/ai/ask`，内部用 `setTimeout` 模拟调用大模型，随机有 20% 概率抛错，用 `try/catch + next(err)` 把错误交给错误处理中间件。
4. 验证：成功时返回 200 JSON；失败时返回 500 且日志中能看到错误堆栈。

**考察点**：中间件洋葱模型、错误处理中间件四参数签名、异步错误转发的正确姿势（这是后续 AI 接口编排的高频场景）。

---

> 完成本篇后，你已具备用 Express 搭建 RESTful API 的基本能力。下一篇将在此基础上引入**异步错误处理、文件上传（multer）、CORS、与数据库集成**等工程化主题，逐步向一个可上线的 AI 后端靠拢。
