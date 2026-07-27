# Day11 - Express 中间件机制

> Express 的中间件机制是整个框架的灵魂。掌握了中间件，你就掌握了 Express 80% 的能力——后续接
入 AI 模型网关、做流式响应、写鉴权拦截、加日志监控，本质都是在"写中间件"。

---

## 一、学习目标

完成本节后，你应当能够：

- [x] 说清"中间件"到底是什么，以及它和 AOP（面向切面）思想的关系
- [x] 解释 `(req, res, next)` 签名的含义，以及 `next()` 如何传递控制权
- [x] 区分应用级 / 路由级 / 错误处理 / 内置 / 第三方 五类中间件
- [x] 独立编写：日志、鉴权、CORS、限流、请求体大小限制、响应耗时统计中间件
- [x] 写出符合规范的四参错误处理中间件，并理解同步/异步错误的差异
- [x] 知道 Express 4 与 Express 5 在 async 错误处理上的关键区别
- [x] 按正确顺序组合多个中间件，构建一个可上生产的后端服务骨架

---

## 二、理论知识

### 2.1 中间件（Middleware）是什么——AOP 思想的体现

**一句话定义**：中间件是处于"请求进来"和"响应出去"之间的一层处理函数，能访问 `req`、`res`，
并决定是把请求"放行"给下一层，还是直接"短路"返回。

如果你写过前端，可以这样类比：

| 前端概念 | Express 中间件 |
| --- | --- |
| Vue/React 的全局守卫 `router.beforeEach` | `app.use((req,res,next)=>...)` |
| Axios 拦截器 `interceptors.request.use` | 请求进入时的中间件 |
| Axios 响应拦截器 `interceptors.response.use` | `res.on('finish')` 回调 |
| Koa 的 `app.use(async (ctx,next)=>{ await next() })` | Express 中间件（但执行模型不同，见 2.3） |

**AOP（Aspect-Oriented Programming，面向切面编程）** 的核心是：把"和主业务逻辑正交"的横切关注点
（cross-cutting concerns）——比如日志、鉴权、限流、监控、错误处理——从业务代码里剥离出来，
集中成一个个可插拔的"切面"。

Express 中间件正是 AOP 在 Web 框架上的落地：

```
请求 → [日志切面] → [鉴权切面] → [限流切面] → [业务路由] → [错误处理切面] → 响应
```

业务路由只关心"做什么"，而"谁能在什么条件下进来、进来要记录什么、出错怎么办"全部交给中间件。
这让你可以像搭积木一样组合能力，新增/移除功能不需要改业务代码。

### 2.2 Express 中间件签名 `(req, res, next)`

每个普通中间件都是这个签名：

```js
function middleware(req, res, next) {
  // req: 请求对象（Node 原生 IncomingRequest 的增强版）
  // res: 响应对象（Node 原生 ServerResponse 的增强版）
  // next: 函数，调用它把控制权交给下一个中间件
}
```

错误处理中间件多一个参数（见第四节）：

```js
function(err, req, res, next) { ... }
```

**关键点**：Express 通过**参数个数**来区分中间件类型——4 个参数的会被注册为错误处理器，3 个参数
的是普通中间件。所以错误处理中间件**即使你不用 `next`，也必须写全 4 个形参**，否则不会被识别。

### 2.3 中间件执行栈模型——洋葱模型的"前半段"

#### Express 的执行模型：线性栈（"半洋葱"）

Express 的中间件本质是一个**线性栈**，请求按注册顺序依次穿过每个中间件，但**只有正向一遍**：

```
请求 →  中间件A (next) →  中间件B (next) → 路由处理器 → 结束
```

如果中间件 A 在 `next()` 之后还写了代码，那段代码会在"响应回流"时执行（因为响应是异步事件）：

```js
app.use((req, res, next) => {
  console.log('A - 前');   // ① 请求进入时
  next();
  console.log('A - 后');   // ② 注意：这里在 next() 同步返回后立刻执行，
                            //    而不是等响应真正发送完！
});
```

⚠️ **这是 Express 和 Koa 最大的区别**。在 Express 里，`next()` 是**同步返回**的，`next()` 后面的
代码会在"下游还没真正处理完"时就执行。所以 Express 很难优雅地写"响应后置处理"（如统一改写
响应体），只能借助 `res.on('finish')` 这类事件钩子。

#### Koa 的洋葱模型：完整双向

Koa 用 `async/await` + `await next()` 实现了真正的洋葱模型——"先进后出"：

```
请求 → A前 → B前 → 路由 → B后 → A后 → 响应
```

```js
app.use(async (ctx, next) => {
  console.log('A - 前');
  await next();          // 真正等下游全部完成
  console.log('A - 后'); // 在响应回流后执行，可改写 ctx.body
});
```

#### 对比总结

| 维度 | Express | Koa |
| --- | --- | --- |
| 控制权传递 | `next()` 同步返回 | `await next()` 异步等待 |
| 执行模型 | 线性栈（单向为主） | 洋葱模型（双向） |
| 后置处理 | 需 `res.on('finish')` 事件 | `await next()` 之后直接写 |
| async 支持 | 4.x 不自动捕获 reject | 原生支持 |
| 心智负担 | 简单直接 | 稍高但更强大 |

> 作为前端转全栈的工程师，理解这个差异非常重要：它解释了为什么 Koa 在"响应统一改写、耗时统计"
> 上更优雅，也解释了为什么 Express 生态更大（更简单、上手更快）。

### 2.4 中间件分类

| 类型 | 注册方式 | 说明 |
| --- | --- | --- |
| **应用级** | `app.use(...)` / `app.get(...)` | 绑定到 app 实例，所有请求都经过 |
| **路由级** | `router.use(...)` / `router.get(...)` | 绑定到 `express.Router()` 实例，仅对该路由生效 |
| **错误处理** | `app.use((err,req,res,next)=>...)` | 4 个参数，捕获 `next(err)` 抛出的错误 |
| **内置** | `express.json()` / `express.static()` / `express.urlencoded()` | Express 自带，4.x 起多数需手动挂载 |
| **第三方** | `morgan` / `cors` / `helmet` 等 | 社区生态，`npm install` 后 `app.use` |

内置中间件速记：

- `express.json()` —— 解析 JSON 请求体
- `express.urlencoded({ extended: true })` —— 解析表单请求体
- `express.static(path)` —— 托管静态文件
- `express.Router()` —— 创建路由模块（不算严格意义的中间件，但常配合使用）

### 2.5 `next()` 的作用与控制权传递

`next()` 是中间件机制的"心脏"。规则只有三条，但极为关键：

1. **不调用 `next()`**：请求会一直挂起（除非你已经用 `res.send()` 结束了响应）。
2. **调用 `next()`**：控制权交给下一个匹配的中间件/路由。
3. **调用 `next(err)`**：跳过后续所有**普通**中间件，直接进入**错误处理**中间件。

```js
app.use((req, res, next) => {
  if (!req.headers['authorization']) {
    return res.status(401).json({ error: '未授权' }); // 短路：直接响应，不再 next
  }
  next(); // 放行
});

app.use((req, res, next) => {
  try {
    doSomething();
    next();
  } catch (e) {
    next(e); // 把错误交给错误处理中间件
  }
});
```

> 注意：短路返回时一定要 `return res.status(...)`，否则 `res` 已发送后还会继续执行 `next()`，
> 触发 "Can't set headers after they are sent" 报错。这是新手最常踩的坑。

### 2.6 中间件加载顺序的重要性

Express 严格按**注册顺序**执行中间件。这意味着：

- ✅ **错误处理中间件必须放最后**：放早了，前面的错误它捕获不到（因为还没注册）。
- ✅ **`express.json()` 必须在业务路由前**：否则 `req.body` 是 `undefined`。
- ✅ **CORS 中间件必须放最前**：否则预检 OPTIONS 请求可能被业务路由拦截。
- ✅ **限流通常在鉴权前**：先挡掉恶意流量，再做昂贵的鉴权计算。

**推荐的生产级顺序**：

```
CORS → 请求体解析 → 日志 → 限流 → 鉴权 → 业务路由 → 404 → 错误处理
```

### 2.7 mount path（挂载路径）

`app.use(path, middleware)` 的第一个参数是挂载路径，只有匹配该前缀的请求才会进入这个中间件。

```js
// 所有请求都经过
app.use(logMiddleware);

// 只有 /api 开头的请求经过
app.use('/api', authMiddleware);

// 只有 /api/admin 开头的请求经过
app.use('/api/admin', requireAdmin);
```

⚠️ **关键细节**：挂载路径会被从 `req.url` 中**剥离**，挂载到 `req.baseUrl` 上。这在路由级中间件
里尤其需要注意：

```js
app.use('/api', (req, res, next) => {
  console.log(req.baseUrl);  // '/api'
  console.log(req.url);      // '/users' （去掉了 /api 前缀）
  next();
});
```

---

## 三、编写中间件

本节对应 `Code/` 下的各个文件，可逐个运行。

### 3.1 自定义日志中间件（含请求耗时）

> 📄 `basic-middleware.js`

```js
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {                       // 响应真正发送完才触发
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms`);
  });
  next();
});
```

**为什么用 `res.on('finish')` 而不是 `next()` 之后的代码？**
因为 Express 的 `next()` 是同步返回的，那时响应还没发出去，`res.statusCode` 可能还没设置。
`finish` 事件在响应数据全部 flush 到底层 socket 后触发，此时读到的状态码和耗时才准确。

### 3.2 鉴权中间件（校验 token）

> 📄 `auth-middleware.js`

```js
function authMiddleware(req, res, next) {
  const token = req.headers['authorization'];
  if (!token) return res.status(401).json({ error: '未提供 token' });
  if (token !== VALID_TOKEN) return res.status(401).json({ error: 'token 无效' });
  req.user = { id: 1, name: '工程师' };   // 把用户信息挂到 req 上，供后续路由复用
  next();
}

app.use('/api', authMiddleware);  // 只保护 /api 下的路由
```

**设计要点**：鉴权通过后，把"解析出的用户"挂到 `req.user` 上，是 Express 的社区约定。后续路由
直接 `req.user` 就能拿到当前用户，无需重复解析 token。

### 3.3 CORS 中间件

> 📄 `cors-middleware.js`

```js
function corsMiddleware(options = {}) {
  const { origin = '*', methods = 'GET,POST,PUT,DELETE,OPTIONS',
          allowedHeaders = 'Content-Type,Authorization', maxAge = 86400 } = options;
  return (req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Methods', methods);
    res.setHeader('Access-Control-Allow-Headers', allowedHeaders);
    res.setHeader('Access-Control-Max-Age', maxAge);
    if (req.method === 'OPTIONS') return res.status(204).end();  // 预检直接返回
    next();
  };
}
```

**预检请求（Preflight）**：浏览器对"非简单请求"（如带自定义头、`PUT`/`DELETE` 方法、`application/json`
内容类型）会先用 `OPTIONS` 方法探测服务器是否允许。中间件必须在 `OPTIONS` 时直接返回，不能进入
业务路由。

### 3.4 请求限流中间件（简易版，基于内存计数）

> 📄 `rate-limit-middleware.js`

```js
function rateLimitMiddleware({ windowMs = 60000, max = 60 } = {}) {
  const store = new Map();   // Map<ip, { count, resetTime }>
  return (req, res, next) => {
    const ip = req.ip;
    const now = Date.now();
    let record = store.get(ip);
    if (!record || now > record.resetTime) {
      record = { count: 0, resetTime: now + windowMs };
      store.set(ip, record);
    }
    record.count++;
    if (record.count > max) {
      return res.status(429).json({ error: '请求过于频繁', retryAfter: ... });
    }
    next();
  };
}
```

**算法说明**：这里用的是**固定窗口计数法**——简单但有个"边界突刺"问题（窗口切换瞬间可放过 2 倍
流量）。生产环境更常用**滑动窗口**或**令牌桶**。单机内存方案在多实例部署下失效，需换 Redis。

### 3.5 请求体大小限制

```js
app.use(express.json({ limit: '10kb' }));           // JSON 请求体最大 10kb
app.use(express.urlencoded({ extended: true, limit: '10kb' }));
```

超限会抛出 `entity.too.large` 错误，交给错误处理中间件转成 `413 Payload Too Large`。这能防止
恶意超大请求体撑爆内存。

### 3.6 响应耗时统计

最准确的写法是结合 `res.on('finish')`（见 3.1）。如果想把耗时写入**响应头**给前端，可以这样：

```js
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    res.setHeader('X-Response-Time', `${Date.now() - start}ms`); // ⚠️ 注意 finish 后改头无效
  });
  // 正确做法：在 finish 之前用 res.on('close') 或提前 setHeader
  next();
});
```

> 实务建议：耗时统计用日志记到服务端即可；若一定要返回给前端，用 `morgan` + 自定义 token 或
> 在 `next()` 前 `res.setHeader`（占位），finish 后再补值会失败（头已发送）。

---

## 四、错误处理中间件

### 4.1 签名与规则

错误处理中间件**必须**有 4 个参数：

```js
app.use((err, req, res, next) => {
  const status = err.status || 500;
  res.status(status).json({ error: err.message });
});
```

四条铁律：

1. **必须 4 个参数**（`err, req, res, next`）——Express 靠参数个数识别它。即使不用 `next` 也得写上。
2. **必须放在所有中间件/路由之后**——否则它捕获不到后续注册的路由抛出的错误。
3. **由 `next(err)` 触发**——任何中间件调用 `next(err)`，控制权就会跳过所有普通中间件，直接交给
   第一个错误处理中间件。
4. **可以有多个错误处理中间件**——按需 `next(err)` 串联，但通常一个就够。

### 4.2 同步错误 vs 异步错误（Express 4 的痛）

```js
// ① 同步抛出：Express 自动捕获，进入错误处理中间件
app.get('/sync', (req, res) => {
  throw new Error('同步错误');  // ✅ 会被捕获
});

// ② 手动 next(err)：可控，推荐
app.get('/manual', (req, res, next) => {
  next(new Error('手动错误'));  // ✅
});

// ③ async 抛出：Express 4 不会捕获！会变成 UnhandledPromiseRejection
app.get('/async-bad', async (req, res) => {
  throw new Error('async 错误');  // ❌ Express 4 抓不到
});
```

**原因**：Express 4 的路由分发是同步的，`async` 函数返回的是 Promise，Express 不会去 `await` 它，
自然也就接不到 reject。这是 Express 4 最大的设计债。

### 4.3 解决方案一：`asyncHandler` 包装器

> 📄 `error-middleware.js`

```js
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);  // reject 转 next(err)
  };
}

app.get('/async-good', asyncHandler(async (req, res) => {
  await db.query();
  throw new Error('async 错误');  // ✅ 被 catch，转给错误处理中间件
}));
```

这是社区最通用的方案，几乎所有 Express 4 项目都自带一个 `asyncHandler`。

### 4.4 解决方案二：`express-async-errors`

```bash
npm install express-async-errors
```

```js
require('express-async-errors');  // 在 app 之前 require，补丁式生效
const express = require('express');
// 之后所有 async 路由的 reject 都会被自动捕获
```

它通过 monkey-patch 修改 Express 内部，让 async 错误自动 `next(err)`。无需每个路由手动包装。

### 4.5 Express 5：原生支持 async 错误

Express 5（目前处于 RC 阶段）**自动捕获 async 路由的 reject**，无需任何包装：

```js
// Express 5
app.get('/async', async (req, res) => {
  throw new Error('async 错误');  // ✅ 自动进入错误处理中间件
});
```

> 学习建议：当前（2025-2026）生产项目仍以 Express 4 为主，但写新项目时建议关注 Express 5 进展。
> 掌握 `asyncHandler` 的原理，迁移到 Express 5 时只需删掉包装即可。

---

## 五、常用第三方中间件速览

| 中间件 | 作用 | 典型用法 |
| --- | --- | --- |
| **morgan** | HTTP 请求日志 | `app.use(morgan('combined'))` |
| **cors** | 跨域处理（功能比手写全） | `app.use(cors({ origin: 'https://a.com' }))` |
| **helmet** | 设置安全响应头（防 XSS、隐藏 Server 等） | `app.use(helmet())` |
| **express-rate-limit** | 限流（生产级，比手写完善） | `app.use(rateLimit({ windowMs, max }))` |
| **compression** | gzip/deflate 压缩响应体 | `app.use(compression())` |
| **cookie-parser** | 解析 Cookie 到 `req.cookies` | `app.use(cookieParser())` |
| **express-session** | Session 管理（基于 Cookie） | `app.use(session({ secret, resave, ... }))` |
| **multer** | `multipart/form-data` 文件上传 | `upload.single('avatar')` 挂到具体路由 |

> 选型建议：手写中间件用来**学原理**；上生产时，安全/限流/CORS 这类"看似简单实则坑深"的，
> 优先用成熟第三方库（它们处理了边界情况、性能、安全细节）。

---

## 六、中间件组合实战模式

### 6.1 鉴权 + 日志 + 错误处理组合

> 📄 `combined-app.js`

完整顺序：

```js
app.use(corsMiddleware(...));         // 1. CORS 最先
app.use(express.json({ limit }));     // 2. 请求体解析
app.use(logMiddleware);               // 3. 日志
app.use(rateLimitMiddleware(...));    // 4. 限流
app.use('/api', authMiddleware);      // 5. 鉴权（按路由分组）
app.get('/api/...', asyncHandler(…)); // 6. 业务路由
app.use(notFound);                    // 7. 404
app.use(errorHandler);                // 8. 错误处理（最后）
```

### 6.2 按路由分组挂载

用 `express.Router()` 把中间件和路由封装成模块，避免 `app` 越来越臃肿：

```js
// routes/admin.js
const router = express.Router();
router.use(authMiddleware);     // 该 router 下所有路由都鉴权
router.use(requireAdmin);       // 再校验管理员
router.get('/dashboard', ...);
module.exports = router;

// app.js
app.use('/admin', require('./routes/admin'));
```

### 6.3 条件中间件

根据请求动态决定是否启用某个中间件：

```js
function conditionalMiddleware(condition, mw) {
  return (req, res, next) => {
    if (condition(req)) return mw(req, res, next);
    next();
  };
}

// 只有 /api 开头且非 /api/public 的请求才鉴权
app.use('/api', conditionalMiddleware(
  (req) => !req.path.startsWith('/public'),
  authMiddleware
));
```

---

## 七、中间件设计原则

1. **单一职责**：一个中间件只做一件事。日志归日志，鉴权归鉴权，不要混在一起——这样能独立复用、
   独立测试、独立开关。

2. **纯函数优先**：尽量让中间件是"输入 → 输出"的纯逻辑，副作用（写文件、改全局变量）降到最低。
   需要副作用时，通过依赖注入（如传入 logger 实例）而非直接 `console.log`。

3. **避免副作用 / 避免泄漏**：
   - 不要在中间件里修改 `req`/`res` 的原生方法签名。
   - 挂载到 `req` 上的自定义字段用命名空间避免冲突（如 `req.__auth_user` 而非 `req.user`，若
     担心和第三方库撞名）。
   - 定时器、监听器记得 `unref()` 或及时清理，避免内存泄漏。

4. **错误处理**：任何可能抛错的逻辑都用 `try/catch` 包住，`catch` 里 `next(err)`。async 路由一定
   套 `asyncHandler`。永远不要让错误"裸奔"成 UnhandledPromiseRejection。

5. **短路要 return**：`res.status(401).json(...)` 后立刻 `return`，防止后续代码继续执行。

6. **可配置**：用工厂函数（`function mw(options){ return (req,res,next)=>... }`）代替硬编码，
   提高复用性。

---

## 八、关键知识点总结

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 中间件 = (req, res, next) => void，AOP 思想在 Web 的落地  │
│ 2. next() 是心脏：放行 / next(err) 跳错误处理 / 不调则挂起    │
│ 3. 错误处理中间件必须 4 个参数，必须放最后                    │
│ 4. Express 4 不捕获 async reject → 用 asyncHandler 或         │
│    express-async-errors；Express 5 原生支持                   │
│ 5. 执行顺序严格按注册顺序：CORS→解析→日志→限流→鉴权→路由→404→错误 │
│ 6. Express 是线性栈(半洋葱)，Koa 是完整洋葱(双向 await next)  │
│ 7. mount path 会从 req.url 剥离到 req.baseUrl                │
│ 8. 短路响应一定要 return res.x()，避免重复响应报错            │
│ 9. 耗时统计用 res.on('finish')，而非 next() 之后的同步代码     │
│ 10. 生产优先用成熟第三方(cors/helmet/rate-limit)，手写为学原理 │
└─────────────────────────────────────────────────────────────┘
```

---

## 九、实战练习

> 在 `Code/` 目录下新建文件完成以下任务，自行用 `curl` 验证。

### 练习 1：实现一个"工作日校验"中间件

写一个中间件 `workdayMiddleware`，仅当当前是周一到周五且时间在 9:00–18:00 时放行，否则返回
`403 { error: '非工作时间，服务暂停' }`。把它挂到 `/api` 路由上测试。

**提示**：用 `new Date().getDay()`（0=周日，6=周六）和 `getHours()`。

### 练习 2：实现一个"请求幂等"中间件

写一个中间件 `idempotencyMiddleware`，根据请求头 `Idempotency-Key` 做幂等：
- 第一次见到该 key：正常处理，并把响应结果缓存到内存。
- 再次见到相同 key：直接返回缓存的结果，不执行下游路由。

**提示**：用 `Map<key, { status, body }>` 缓存；注意只在 `POST/PUT/DELETE` 上启用。

### 练习 3：给 combined-app.js 加上"接口耗时告警"

在现有日志中间件基础上，**当响应耗时超过 500ms 时**，额外打印一条 `[SLOW]` 警告日志。再进阶
一步：把慢请求写入一个 `slow.log` 文件（用 `fs.appendFileSync`）。

**提示**：在 `res.on('finish')` 回调里判断 `duration > 500`。

---

## 十、代码运行说明

```bash
cd "d:\Coding\AI-FullStack\NodeJS\Day11 - Express中间件机制\Code"
npm install          # 安装 express

# 逐个运行（每个文件监听不同端口）
node basic-middleware.js       # 端口 3000
node auth-middleware.js        # 端口 3001
node error-middleware.js       # 端口 3002
node cors-middleware.js        # 端口 3003
node rate-limit-middleware.js  # 端口 3004
node combined-app.js           # 端口 3005（组合应用，推荐先看这个）

# 或用 npm script
npm start                      # 启动 combined-app
```

每个文件启动后会在控制台打印对应的 `curl` 测试命令，复制即可验证。

---

## 目录结构

```
Day11 - Express中间件机制/
├── README.md                      # 本文档
└── Code/
    ├── package.json               # 依赖：express
    ├── basic-middleware.js        # 日志+耗时+next() 传递
    ├── auth-middleware.js         # token 鉴权，保护 /api
    ├── error-middleware.js        # 同步/async 错误 + asyncHandler
    ├── cors-middleware.js         # CORS + OPTIONS 预检
    ├── rate-limit-middleware.js   # 内存限流，429
    └── combined-app.js            # 组合应用（含 curl 测试命令）
```

---

> **下一步预告**：Day12 将进入「Express 路由与项目结构化」，把今天学的中间件组织进可维护的
> 模块化项目，为后续接入 AI 模型 API（OpenAI / 通义千问）打好工程基础。
