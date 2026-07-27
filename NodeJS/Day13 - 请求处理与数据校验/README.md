# Day13 - 请求处理与数据校验

> 本篇聚焦 Express 应用中最容易被前端转型工程师低估、却直接决定接口健壮性的两个主题：**请求处理的完整链路**与**入参数据校验**。你将理解一次 HTTP 请求从进入 Express 到返回响应的内部流转过程，掌握 `express.json` / `urlencoded` / `multer` 等解析中间件背后的原理，并学会使用 **Joi** 与 **express-validator** 两套主流校验方案。最终你将拥有一个“分层校验 + 统一错误响应”的可复用骨架，为后续鉴权、AI 接口编排打下基础。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解：请求处理完整链路](#二理论知识讲解请求处理完整链路)
  - [2.1 一次请求的生命周期](#21-一次请求的生命周期)
  - [2.2 请求体解析中间件原理](#22-请求体解析中间件原理)
  - [2.3 文件上传 multipart/form-data 与 multer](#23-文件上传-multipartform-data-与-multer)
  - [2.4 参数来源全景图](#24-参数来源全景图)
  - [2.5 参数类型转换的坑](#25-参数类型转换的坑)
- [三、为什么需要校验](#三为什么需要校验)
- [四、校验库对比](#四校验库对比)
- [五、Joi 详解](#五joi-详解)
- [六、express-validator 详解](#六express-validator-详解)
- [七、校验最佳实践](#七校验最佳实践)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 完整描述一次 HTTP 请求在 Express 内部的流转链路：路由匹配 → 中间件 → 参数解析 → 业务逻辑 → 响应。
2. 说明 `express.json()`、`express.urlencoded()`、`express.raw()`、`express.text()` 各自解析的 `Content-Type` 与适用场景，并理解其 `limit`、`type` 等配置项。
3. 理解 `multipart/form-data` 的结构，使用 multer 完成单文件/多文件上传，并对文件大小与类型做白名单限制。
4. 区分 `req.params`、`req.query`、`req.body`、`req.headers`、`req.cookies` 五种参数来源，并理解 query 全为字符串带来的类型陷阱。
5. 准确阐述“为什么后端必须做入参校验”的五个理由（前端不可信、防注入、数据完整性、统一错误信息、早失败原则）。
6. 在 Joi、express-validator、Zod、Yup、class-validator 之间根据 API 风格、TS 支持、生态与框架集成度做出合理选型。
7. 使用 Joi 定义 schema（含 `object`/`string`/`number`/`array`/`boolean`/`date`），并掌握 `required`/`optional`/`min`/`max`/`email`/`regex`/`valid` 等规则，配置 `stripUnknown`、`default`、`abortEarly`、自定义错误信息。
8. 使用 express-validator 的 `checkSchema` 与 `body/query/param` 链式 API，通过 `validationResult` 收集错误，编写自定义校验器与 sanitize 输入。
9. 设计分层校验架构：参数校验放中间件层、业务校验放 service 层，并通过统一错误响应中间件把 Joi / express-validator / multer 三类错误归一化输出。

---

## 二、理论知识讲解：请求处理完整链路

### 2.1 一次请求的生命周期

Express 本质上是一个“路由 + 中间件”框架。当请求到达时，它并不是直接跳到某个 handler，而是沿着一条预先注册的“管道”逐层处理。理解这条管道，是写出可维护 API 的前提。

完整链路分为五个阶段：

```
客户端请求
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. 路由匹配：app/router 按注册顺序匹配 method + path          │
│    （未命中 → 默认 404）                                       │
├─────────────────────────────────────────────────────────────┤
│ 2. 中间件链：app.use / 路由级 middleware 依次执行              │
│    ├─ 全局中间件：日志、CORS、helmet、bodyParser              │
│    ├─ 校验中间件：Joi / express-validator                     │
│    └─ 业务前置：鉴权、限流、上下文构建                          │
├─────────────────────────────────────────────────────────────┤
│ 3. 参数解析：req.params / req.query / req.body / req.headers │
│    由解析中间件在到达 handler 前挂载到 req 上                   │
├─────────────────────────────────────────────────────────────┤
│ 4. 业务逻辑：controller 调 service 调 model，返回数据           │
├─────────────────────────────────────────────────────────────┤
│ 5. 响应：res.json() / res.send()，经过错误中间件兜底           │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
客户端响应
```

几个关键认知：

- **中间件按注册顺序执行**，`next()` 决定是否进入下一个。一旦某个中间件不调用 `next()` 且不结束响应，请求就会“悬空”。
- **路由匹配在前，中间件执行在后**：Express 先确定命中哪条路由，再把该路由前的中间件链组装执行。`app.use` 挂在全局，`router.use` 挂在子路由。
- **参数解析本身也是中间件**：`express.json()` 之所以能让 `req.body` 有值，是因为它在请求体流式到达时完成了读取与反序列化，并把结果挂到 `req.body`。
- **错误中间件必须四参数**：`(err, req, res, next)`，且要放在所有路由之后，否则无法捕获同步/异步抛出的错误。

> 对前端工程师而言，可以把这条链路类比为：路由匹配 = Vue Router 路由守卫，中间件 = 全局 beforeEach，参数解析 = props 解析，业务逻辑 = 组件 setup，响应 = 渲染输出。

### 2.2 请求体解析中间件原理

Express 把请求体解析能力完全外置成中间件（4.x 内置但需显式挂载），其核心思想是：

1. 监听 `req`（一个 `IncomingMessage` 可读流）的 `data` 事件，把分块到达的 Buffer 累积起来。
2. 在 `end` 事件触发时，依据 `Content-Type` 选择对应的解析器把 Buffer 转成 JS 对象。
3. 把结果挂到 `req.body`，调用 `next()` 交给后续中间件。

#### 四个内置解析器

| 中间件 | 解析的 Content-Type | 用途 | 默认产物 |
|--------|---------------------|------|----------|
| `express.json()` | `application/json` | RESTful API 主力 | JS 对象 |
| `express.urlencoded({ extended: true })` | `application/x-www-form-urlencoded` | 传统表单提交 | 键值对象 |
| `express.raw()` | `application/octet-stream` | 二进制原始 Buffer | Buffer |
| `express.text()` | `text/plain` | 纯文本 | 字符串 |

```js
app.use(express.json({ limit: '1mb' }));            // 限制体积，防内存耗尽
app.use(express.urlencoded({ extended: true, limit: '1mb' }));
app.use(express.text({ type: 'text/plain' }));
app.use(express.raw({ type: 'application/octet-stream', limit: '5mb' }));
```

#### `express.json` 工作细节

- 仅当请求头 `Content-Type: application/json`（或匹配 `type` 选项的正则）时才解析，否则跳过，`req.body` 为 `undefined`。
- `reviver` 选项：传入 JSON.parse 的 reviver，可对特定字段做转换。
- `strict` 默认 `true`：只接受顶层数组或对象，拒绝裸字符串/数字，防止单值注入。
- `limit`：控制请求体大小（如 `'100kb'`），超过直接 413，避免恶意大请求体打满内存。

> `urlencoded` 的 `extended: true` 使用 `qs` 库，支持嵌套对象（`a[b][c]=1` → `{a:{b:{c:1}}}`）；`extended: false` 使用内置 `querystring`，只支持扁平键值。新项目默认 `true`。

#### `raw` / `text` 限制

- 它们解析后挂到 `req.body` 的是 **Buffer 或字符串**，不是对象，因此校验时需要先自行处理。
- 通常只针对特定路由启用（如 webhook 原始签名校验、文件代理），不要全局挂载，否则会与 `express.json` 抢解析权——Express 只允许一个解析器处理同一请求。

### 2.3 文件上传 multipart/form-data 与 multer

#### 为什么需要专门处理

`express.json` 只能处理 `application/json`，无法处理 `multipart/form-data`。后者是 RFC 2388 定义的“多部分表单”格式，一个请求体里可以同时包含普通字段和文件二进制，每部分用 `boundary` 分隔：

```
POST /upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryABC

------WebKitFormBoundaryABC
Content-Disposition: form-data; name="title"

我的头像
------WebKitFormBoundaryABC
Content-Disposition: form-data; name="avatar"; filename="me.png"
Content-Type: image/png

<二进制数据>
------WebKitFormBoundaryABC--
```

Express 官方推荐的解析库是 **multer**。

#### multer 的两种存储策略

| 策略 | API | 适用场景 |
|------|-----|----------|
| 内存存储 | `multer.memoryStorage()` | 小文件，需进一步处理（压缩、上传到 OSS）后不留盘 |
| 磁盘存储 | `multer.diskStorage({ destination, filename })` | 大文件直落磁盘，省内存 |

```js
const multer = require('multer');

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, 'uploads/'),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `${Date.now()}-${Math.random().toString(36).slice(2)}${ext}`);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
  fileFilter: (req, file, cb) => {
    const allowed = ['image/png', 'image/jpeg', 'image/webp'];
    cb(allowed.includes(file.mimetype) ? null : new Error('仅允许 png/jpeg/webp'), allowed.includes(file.mimetype));
  },
});

// 单文件：upload.single('avatar') → req.file
// 多文件同字段：upload.array('photos', 9) → req.files[]
// 多文件不同字段：upload.fields([{ name: 'avatar', maxCount: 1 }, { name: 'gallery', maxCount: 9 }])
// 纯文本字段：upload.none() → 只解析字段到 req.body，不接受文件
```

> multer 解析完成后，普通字段会挂到 `req.body`，文件挂到 `req.file`（单）或 `req.files`（多）。因此** multer 必须在校验中间件之前挂载**，否则校验时拿不到 `req.body` 和文件。

#### 安全要点

- `fileFilter` 一定要校验 `mimetype`，但不能只信 mimetype——攻击者可伪造请求头，生产环境应结合**文件魔数（magic number）**或扩展名白名单。
- `limits.fileSize` 必设，否则单个超大文件就能耗尽内存/磁盘。
- 上传目录不要放在静态资源目录下直接对外暴露，防止上传可执行脚本被访问触发 RCE。

### 2.4 参数来源全景图

| 来源 | 访问方式 | 典型示例 | 解析中间件 |
|------|----------|----------|------------|
| 路径参数 | `req.params` | `/users/:id` → `req.params.id` | Express 路由本身 |
| 查询参数 | `req.query` | `/search?q=node&page=2` | Express 内置 querystring |
| 请求体 | `req.body` | POST JSON | `express.json` / `urlencoded` / `raw` / multer |
| 请求头 | `req.headers` | `Authorization: Bearer xxx` | Express 内置 |
| Cookie | `req.cookies` / `req.signedCookies` | 会话令牌 | 需 `cookie-parser` |

记忆口诀：**params 走路径、query 走问号、body 走请求体、headers 走请求头、cookies 走签名小饼干**。

### 2.5 参数类型转换的坑

最容易踩的两个坑都来自 **query 全是字符串**：

1. `/api/user?age=18` 中 `req.query.age` 是字符串 `"18"`，不是数字。`typeof req.query.age === 'number'` 永远 false。
2. `/api/user?active=true` 中 `req.query.active` 是字符串 `"true"`，`if (req.query.active)` 在 `active=false` 时仍为真（非空字符串）。

解决方案：

- 在校验层做显式类型转换：Joi 用 `Joi.number()` 会自动 cast，express-validator 用 `toInt()` / `toBoolean()`。
- 切勿在业务代码里直接用 `==` 做隐式比较，应通过校验层保证类型已规范。

---

## 三、为什么需要校验

很多前端工程师转型时认为“我已经在表单里做了校验，后端再做一遍是重复劳动”。这是危险的想法。后端校验不可省略，理由如下：

| 理由 | 说明 |
|------|------|
| **前端校验不可信** | 浏览器只是“友好的用户提示”，绕过前端（curl、Postman、抓包改包）可直接打到后端。后端是数据进入系统的最后一道闸门。 |
| **防止注入攻击** | NoSQL 注入（`{$gt: ""}` 越权）、SQL 注入、原型链污染（`__proto__`）、XSS（存库的 `<script>`）都依赖对入参形状与字符的控制。校验 schema 限定字段白名单 = 直接挡掉未知字段。 |
| **保证数据完整性** | 数据库默认值、唯一约束、外键只能在写入时兜底；在入口处校验可避免“半截脏数据”流入下游 service、消息队列、AI 推理管线。 |
| **统一错误信息** | 让前端拿到结构化、可国际化的错误（`{ field, message, code }`），而不是各组件各报各的，提升联调效率。 |
| **早失败原则（Fail Fast）** | 在中间件层就拒绝非法请求，避免无效请求进入昂贵的业务流程（数据库查询、第三方调用、模型推理），节约服务器资源与成本。 |

> 对 AI 全栈场景尤其关键：一次 LLM 调用可能花费数秒与真实费用，入参不合法就调用大模型是直接的资源浪费。校验必须前置到调用模型之前。

---

## 四、校验库对比

主流 JS/TS 校验库可粗分两类：**schema 优先**（声明式定义结构，与框架解耦）和 **middleware 优先**（专为 Express 链路设计）。

| 库 | API 风格 | TS 支持 | 与 Express 集成 | 错误格式 | 生态 | 适用场景 |
|----|----------|---------|-----------------|----------|------|----------|
| **Joi** | Schema 优先，链式 + 对象 | 良好（可推断） | 需手写中间件包装 | `ValidationError.details[]` | 极广，hapi 生态核心 | 框架无关的纯校验，可复用到 CLI/前端 |
| **express-validator** | middleware-chain，`checkSchema` 或 `body().isEmail()` | 良好 | 原生，一行挂载 | `validationResult.array()` | Express 生态最大 | 纯 Express 项目，追求最少样板 |
| **Zod** | Schema 优先，TS 原生 | 顶级（类型即 schema） | 需手写中间件，但有 `zod-express-middleware` | `ZodError.issues[]` | 上升最快，NestJS/Next/tRPC 都用 | TS 项目、跨端共享类型、AI 接口 |
| **Yup** | Schema 优先，类似 Joi | 良好 | 需手写中间件 | `ValidationError.errors[]` | 较广，常用于前端表单 | 前后端同构校验 |
| **class-validator** | 装饰器 + class，基于 validator.js | 优秀 | 通过 NestJS pipe | `ValidationError[]` | NestJS 标配 | NestJS 项目，DTO 模式 |

选型建议（针对本课程路线）：

- **Day13 阶段**：用 Joi 理解“schema 是独立资产”，用 express-validator 理解“中间件式校验”。
- **后续 TS / NestJS 阶段**：迁移到 Zod（前端共享类型）或 class-validator（DTO 装饰器）。本篇对比表中已为这两个方向铺垫。
- **AI 接口编排**：Zod 与 Joi 都适合校验 LLM 输入（结构化 prompt 参数），可复用到 Edge / Serverless。

---

## 五、Joi 详解

Joi 的核心理念是：**schema 是一等公民**。你先声明期望的数据形状，再对任意输入做校验/转换，不绑定任何 Web 框架。

### 5.1 定义 schema

```js
const Joi = require('joi');

const schema = Joi.object({
  username: Joi.string().alphanum().min(3).max(30).required(),
  email: Joi.string().email().required(),
  password: Joi.string().pattern(/^[A-Za-z0-9!@#$%^&*]{8,32}$/).required(),
  age: Joi.number().integer().min(0).max(150),
  role: Joi.string().valid('admin', 'editor', 'viewer').default('viewer'),
  tags: Joi.array().items(Joi.string().max(20)).max(10),
  active: Joi.boolean().default(true),
  birthday: Joi.date().less('now'),
  address: Joi.object({
    city: Joi.string(),
    zip: Joi.string().pattern(/^\d{6}$/),
  }),
});
```

常用类型构造器：`Joi.string()`、`Joi.number()`、`Joi.boolean()`、`Joi.array()`、`Joi.object()`、`Joi.date()`、`Joi.alternatives()`（多类型择一）。

### 5.2 校验规则速查

| 规则 | 作用 | 示例 |
|------|------|------|
| `required()` | 必填 | `Joi.string().required()` |
| `optional()` | 可选（默认即是） | `Joi.string().optional()` |
| `min(n)` / `max(n)` | 长度/数值上下界 | `Joi.string().min(6)`、`Joi.number().max(100)` |
| `length(n)` | 精确长度 | `Joi.string().length(11)` |
| `email()` | 邮箱格式 | `Joi.string().email()` |
| `pattern(re)` / `regex(re)` | 正则 | `Joi.string().pattern(/^1\d{10}$/)` |
| `valid(...vals)` / `equal(...)` | 枚举白名单 | `Joi.string().valid('a','b')` |
| `invalid(...vals)` | 枚举黑名单 | `Joi.number().invalid(0)` |
| `alphanum()` | 仅字母数字 | `Joi.string().alphanum()` |
| `integer()` | 整数 | `Joi.number().integer()` |
| `uri()` | URL 格式 | `Joi.string().uri()` |
| `less(v)` / `greater(v)` | 严格小于/大于 | `Joi.date().less('now')` |

### 5.3 校验与转换

Joi 在校验时可以做“清洗”，返回**校验通过后的值**（而不是原值），这是它与简单 if 校验的关键区别：

```js
const schema = Joi.object({
  name: Joi.string().trim().default('匿名'),
  age: Joi.number(),
}).options({
  stripUnknown: true,   // 丢弃 schema 未声明的字段，防注入与脏数据
  abortEarly: false,    // 收集所有错误而不是遇首个就停
  convert: true,        // 自动类型转换（默认开启）
  allowUnknown: false,  // 未知字段报错（与 stripUnknown 二选一）
});

const { value, error } = schema.validate({ name: '  Tom  ', age: '20', extra: 'x' });
// value => { name: 'Tom', age: 20 }  ← 已 trim、已 cast、extra 被剥离
```

- `stripUnknown`：删掉 schema 没有的字段，是防原型链污染 / 注入的关键开关。
- `default`：缺失时填默认值。
- `convert`：默认 `true`，`Joi.number()` 会把字符串 `"20"` 转成 `20`，这对解决“query 全是字符串”非常实用。
- `abortEarly: false`：默认 Joi 遇到第一个错误就停，调试与友好提示时建议关闭，一次性返回所有错误。

### 5.4 错误信息定制

```js
const schema = Joi.object({
  password: Joi.string().min(8).required().messages({
    'string.empty': '密码不能为空',
    'string.min': '密码至少 {#limit} 位',
    'any.required': '缺少必填字段 {#label}',
  }),
});
```

`{#limit}`、`{#label}`、`{#value}` 是 Joi 模板变量。也可以全局设置语言：

```js
const schema = Joi.object({ /*...*/ }).prefs({
  errors: { label: 'key', wrap: { label: false } },
  messages: {
    'string.empty': '{#label} 不可为空',
    'string.min': '{#label} 长度不少于 {#limit}',
  },
});
```

### 5.5 包装成 Express 中间件（校验 query / body / params）

Joi 本身不认识 Express，需要一个小包装。常见做法是写一个工厂函数，按来源分别校验：

```js
function validate(schema, source = 'body') {
  return (req, res, next) => {
    const data = req[source]; // 'body' | 'query' | 'params'
    const { value, error } = schema.validate(data, { abortEarly: false, stripUnknown: true });
    if (error) {
      // 抛给统一错误中间件处理
      return next({ type: 'JOI_ERROR', error });
    }
    req[source] = value; // 用清洗后的值覆盖原值，下游拿到的就是规范数据
    next();
  };
}

// 使用
router.post('/register', validate(registerSchema, 'body'), controller.register);
router.get('/search', validate(searchSchema, 'query'), controller.search);
router.put('/users/:id', validate(idSchema, 'params'), validate(updateSchema, 'body'), controller.update);
```

> 把校验后的 `value` 回写到 `req[source]`，下游 controller 永远拿到的是“干净数据”，无需重复校验。

---

## 六、express-validator 详解

express-validator 的设计哲学与 Joi 相反：**它就是为 Express 而生**。校验本身就是一个中间件，错误收集在 `req` 上，由下一个中间件统一读取。

### 6.1 链式 API

```js
const { body, query, param, validationResult } = require('express-validator');

router.post(
  '/login',
  [
    body('email').isEmail().withMessage('邮箱格式不正确'),
    body('password').isLength({ min: 8 }).withMessage('密码至少 8 位'),
  ],
  (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(422).json({ errors: errors.array() });
    }
    // 业务逻辑
  }
);
```

- `body(field)` / `query(field)` / `param(field)` / `header(field)` / `cookie(field)`：选择校验源。
- 每个调用返回一个链式 builder，`.isEmail()`、`.isLength()`、`.isInt()` 等都是链式方法。
- `.withMessage()` 紧跟在校验器后，给该规则绑定错误信息。
- `validationResult(req)` 汇总所有校验器的结果，`.isEmpty()` / `.array()` / `.mapped()`。

### 6.2 checkSchema（声明式写法）

链式 API 在字段多时较啰嗦，`checkSchema` 提供对象式声明，更接近 Joi 的可读性：

```js
const { checkSchema, validationResult } = require('express-validator');

const articleSchema = checkSchema({
  title: {
    in: ['body'],
    notEmpty: { errorMessage: '标题不可为空' },
    isLength: { options: { min: 2, max: 100 }, errorMessage: '标题 2-100 字' },
    trim: true,
  },
  content: {
    in: ['body'],
    notEmpty: { errorMessage: '内容不可为空' },
    isLength: { options: { min: 10 }, errorMessage: '内容至少 10 字' },
  },
  tags: {
    in: ['body'],
    isArray: { errorMessage: 'tags 必须是数组' },
    custom: {
      options: (value) => Array.isArray(value) && value.length >= 1 && value.length <= 5,
      errorMessage: 'tags 至少 1 个、最多 5 个',
    },
  },
});
```

`in` 字段决定该规则应用于哪些来源（`body` / `query` / `params` / `headers` / `cookies`），是 express-validator 灵活性的核心。

### 6.3 自定义校验器

`custom` 允许写任意逻辑（含异步查库），返回 `true/false` 或 `Promise`，抛错则失败：

```js
body('username').custom(async (value) => {
  const user = await User.findOne({ username: value });
  if (user) throw new Error('用户名已被占用');
  return true;
}),
```

### 6.4 sanitize 输入

校验之外，express-validator 还能在请求进入业务前“清洗”字段：去空格、转大小写、转类型、HTML 转义。链式方法：

```js
body('email').normalizeEmail(),           // 规范化邮箱
body('username').trim().toLowerCase(),    // 去空格 + 小写
query('page').default(1).toInt(),         // 默认值 + 转数字
query('active').toBoolean(),              // 字符串转布尔
body('bio').escape(),                     // HTML 转义，防 XSS
```

> Sanitization 与校验一样会原地修改 `req.body` / `req.query`，下游拿到的就是清洗后的值。

### 6.5 收集错误的标准写法

```js
function handleValidationErrors(req, res, next) {
  const errors = validationResult(req);
  if (errors.isEmpty()) return next();
  next({ type: 'EXPRESS_VALIDATOR_ERROR', errors: errors.array() });
}
```

把这一步抽成统一中间件，挂在校验链之后，可避免每个 controller 都写一遍 `if (!errors.isEmpty())`。

---

## 七、校验最佳实践

### 7.1 分层校验

| 层次 | 职责 | 工具 |
|------|------|------|
| 中间件层 | 参数存在性、格式、类型、长度、枚举值（与业务无关的“形状”校验） | Joi / express-validator |
| Service 层 | 业务规则：邮箱是否已注册、余额是否充足、是否有权限 | 手写判断 + 抛业务错误 |
| 数据层 | 数据库唯一约束、外键、非空兜底 | 数据库 schema |

原则：**能在中间件层挡掉的，绝不放进 service**；**业务规则不放进中间件层**，避免中间件膨胀、与 model 耦合。

### 7.2 统一错误响应

无论错误来自 Joi、express-validator、multer 还是 service，最终对外都应是同一种结构：

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数校验失败",
    "details": [
      { "field": "email", "message": "邮箱格式不正确" }
    ]
  }
}
```

实现方式见 `unified-error.js`：用一个四参数错误中间件，根据 `err.type` 分支格式化。

### 7.3 敏感字段过滤

- 用 `stripUnknown` / schema 白名单确保**未知字段直接丢弃**，防原型链污染（`__proto__`、`constructor`）与字段注入。
- 永远不要把用户传入的字段直接展开到数据库查询：`User.create({ ...req.body })` 是反模式，应显式取 `const { name, email } = req.body`。
- 响应里过滤密码、token、内部字段，使用 `toJSON()` 或序列化白名单。

### 7.4 类型转换

- query 全是字符串：在校验层用 `toInt` / `Joi.number()` 显式 cast。
- 不要依赖 `==` 隐式转换，统一在 schema 层处理后，业务层用 `===`。
- 布尔值用 `toBoolean` 或 Joi `Joi.boolean().truthy('true').falsy('false')`。

### 7.5 安全额外清单

- 对字符串字段做 `escape()` 或在输出时转义，防存储型 XSS。
- 对 URL 字段用 `isURL({ protocols: ['https'] })` 限制协议，防 SSRF。
- 对数组字段一定校验长度上限，防超长数组导致后续循环 / AI 调用成本失控。

---

## 八、关键知识点总结

1. **请求链路五阶段**：路由匹配 → 中间件 → 参数解析 → 业务逻辑 → 响应。校验属于中间件阶段，参数解析必须在它之前完成。
2. **四个内置解析器**：`express.json` / `urlencoded` / `raw` / `text`，分别对应不同 `Content-Type`，只能有一个生效，受 `limit` 约束。
3. **文件上传**：`multipart/form-data` 必须 multer 处理；`upload.single/array/fields/none` 决定接受方式；`limits` + `fileFilter` 是安全底线。
4. **五种参数来源**：`params`（路径）/ `query`（查询）/ `body`（请求体）/ `headers`（请求头）/ `cookies`（需 cookie-parser）。
5. **query 全是字符串**：在校验层做显式类型转换，绝不依赖隐式 `==`。
6. **后端必须校验的五个理由**：前端不可信、防注入、数据完整性、统一错误信息、早失败原则。
7. **Joi = schema 优先**：`validate` 返回 `{value, error}`，`stripUnknown` / `abortEarly` / `convert` / `messages` 是四大常用选项。
8. **express-validator = middleware 优先**：`checkSchema` 声明式 + `validationResult` 收集 + `custom` 自定义 + sanitize 清洗。
9. **分层校验**：形状校验在中间件层，业务校验在 service 层，数据库层做最终兜底。
10. **统一错误响应**：用四参数错误中间件把 Joi / express-validator / multer 三类错误归一为同一 JSON 结构，前端联调成本骤降。
11. **选型路线**：Day13 用 Joi + express-validator 打基础 → TS 阶段上 Zod → NestJS 阶段用 class-validator，三者思想一致，迁移成本低。
12. **AI 场景延伸**：校验应在调用 LLM 之前完成，避免无效请求消耗真实费用与时间。

---

## 九、实战练习

> 以下练习建议在本目录 `Code/` 下新建文件完成，复用 `unified-error.js` 的统一错误中间件。

### 练习 1：用户注册接口（Joi）

实现 `POST /api/register`，使用 Joi 校验以下规则，失败时返回统一错误结构：

- `username`：3-20 位字母数字，必填
- `email`：合法邮箱，必填
- `password`：8-32 位，必须包含字母和数字（用 `pattern`），必填
- `age`：18-100 的整数，可选
- `role`：枚举 `user` / `vip`，默认 `user`

**自测用例**：

- 成功：`{ "username": "alice", "email": "a@b.com", "password": "abc12345" }` → 200
- 失败（密码弱）：`{ "username": "alice", "email": "a@b.com", "password": "123" }` → 422，含字段级错误
- 失败（未知字段）：传入 `__proto__` 字段，应被 `stripUnknown` 丢弃

### 练习 2：文章创建接口（express-validator）

实现 `POST /api/articles`，使用 `checkSchema` 校验：

- `title`：2-100 字，trim 后非空
- `content`：至少 10 字
- `tags`：数组，1-5 个元素，每个元素 1-20 字（用 `custom` 校验数组长度）
- `cover`（可选）：合法 URL 且仅 https

**自测用例**：

- 成功：含 3 个标签 → 200
- 失败：tags 为空数组 → 422，错误信息提示“tags 至少 1 个、最多 5 个”
- 失败：cover 用 `http://` → 422

### 练习 3：带文件上传的接口（multer + 校验组合）

实现 `POST /api/avatar`，接收 `avatar` 单文件（png/jpeg/webp，≤2MB）+ `caption` 文本字段，要求：

1. multer 在前，解析后 `req.file` / `req.body.caption` 可用
2. express-validator 在后，校验 `caption` 非空且 ≤ 50 字
3. 文件大小/类型错误经统一错误中间件格式化输出
4. 成功返回 `{ url, caption }`

**思考题**：如果用户上传了合法 mimetype 但内容是改名的 .exe，仅靠 multer 能否拦住？应如何加固？（提示：文件魔数 / 重新编码）

---

> 完成练习后，对照 `Code/server.js` 的注释 curl 命令验证。下一 Day 将在统一错误响应之上引入鉴权（JWT）与会话管理。
