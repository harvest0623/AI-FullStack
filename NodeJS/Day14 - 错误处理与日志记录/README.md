# Day14 - 错误处理与日志记录

> 本篇聚焦两个“上线即刚需”的工程能力：**错误处理** 与 **日志记录**。前端出身的工程师习惯于浏览器里 `try/catch` + `console.log`，但 Node.js 服务端跑在远端、无 DevTools、一个未捕获的异常就能让整个进程崩溃、几十个并发请求共享同一个日志输出。本篇将带你建立一套“错误可分类、异常可兜底、日志可追踪”的服务端工程心智，并用 Express + winston + morgan 亲手落地一个可上线的最小方案。这是后续做 AI 接口编排、Agent 后端时排查“为什么大模型调用 500 了”的底气所在。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 错误分类](#21-错误分类)
  - [2.2 同步错误 vs 异步错误](#22-同步错误-vs-异步错误)
  - [2.3 uncaughtException 与 unhandledRejection](#23-uncaughtexception-与-unhandledrejection)
  - [2.4 Express 中的错误传播](#24-express-中的错误传播)
- [三、错误处理最佳实践](#三错误处理最佳实践)
  - [3.1 自定义错误类](#31-自定义错误类)
  - [3.2 错误码设计](#32-错误码设计)
  - [3.3 统一错误响应格式](#33-统一错误响应格式)
  - [3.4 不要吞掉错误](#34-不要吞掉错误)
  - [3.5 错误分层](#35-错误分层)
  - [3.6 区分 4xx 与 5xx](#36-区分-4xx-与-5xx)
  - [3.7 敏感信息脱敏](#37-敏感信息脱敏)
- [四、Express 错误处理中间件详解](#四express-错误处理中间件详解)
- [五、日志基础](#五日志基础)
  - [5.1 为什么 console.log 不够](#51-为什么-consolelog-不够)
  - [5.2 日志级别使用规范](#52-日志级别使用规范)
  - [5.3 结构化日志](#53-结构化日志)
  - [5.4 请求 ID 链路追踪](#54-请求-id-链路追踪)
- [六、winston 详解](#六winston-详解)
- [七、morgan HTTP 请求日志](#七morgan-http-请求日志)
- [八、日志最佳实践](#八日志最佳实践)
- [九、关键知识点总结](#九关键知识点总结)
- [十、实战练习](#十实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说出 Node.js 中常见的错误分类（语法错误、运行时错误、逻辑错误、系统错误）及其特征。
2. 区分同步错误与异步错误（Promise reject、error-first 回调、`error` 事件）的传播方式，并给出对应的捕获手段。
3. 解释 `uncaughtException` 与 `unhandledRejection` 的区别，以及各自的处置策略（记录日志后是否退出进程、Domain 为何已废弃）。
4. 理解 Express 的错误传播链：`next(err)` 如何沿中间件链流转，四参数错误中间件为何必须放在最后。
5. 设计一套自定义错误类体系（继承 `Error`，携带 `statusCode`/`code`/`context`），并实现业务码与 HTTP 状态码的分层。
6. 定义统一的错误响应格式 `{ code, message, details, requestId, timestamp }`，并对 4xx / 5xx 采取不同日志级别。
7. 实现请求 ID 链路追踪：用 uuid 生成贯穿请求全链路的标识，注入到 `req`、响应头与 logger 上下文。
8. 说明 `console.log` 为何不足以支撑生产，掌握日志级别规范与结构化日志（JSON）的价值。
9. 使用 winston 配置 Console + DailyRotateFile 多 transport，按天/按大小轮转，并为不同级别分流。
10. 把 morgan 的 HTTP 请求日志流式接入 winston，形成统一的日志出口；了解 ELK / Loki 等日志聚合方案。

---

## 二、理论知识讲解

### 2.1 错误分类

理解“错误是什么”，才能“对症下药”。Node.js 中的错误大致分四类：

| 类别 | 典型代表 | 何时发生 | 是否可恢复 | 处理建议 |
|------|----------|----------|-----------|----------|
| **语法错误 SyntaxError** | `SyntaxError: Unexpected token` | 代码加载/解析阶段，括号不匹配、写错关键字 | 否（代码根本跑不起来） | 必须改代码；CI 阶段就该被 lint/编译拦截 |
| **运行时错误** | `TypeError` / `RangeError` / `ReferenceError` | 代码执行阶段，如读取 `null` 的属性、数组越界、变量未定义 | 部分可恢复 | `try/catch` 捕获，转为业务错误或修复逻辑 |
| **逻辑错误** | 无异常抛出，但结果不对 | 程序“正常运行”却算错了，如 `if (a = b)` 写成赋值 | 否 | 最难排查；靠测试、断言、日志、Code Review 兜底 |
| **系统错误 SystemError** | `ENOENT` / `ECONNRESET` / `ETIMEDOUT` | 与外部系统交互失败，文件不存在、网络断开、端口占用 | 视情况 | 检查 `err.code` / `err.errno`，重试或降级 |

**几个关键细节：**

- **`SyntaxError`** 在 `require()` 一个模块时会立刻抛出，因为 Node 先要把源码解析成 AST。这类错误不可能靠 `try/catch` 在“同一段代码”里捕获——它发生在解析期。常见做法是把可能出错的 `require` 放进 `try`，或更现实地：用 ESLint / TypeScript 在编码期杜绝。

- **`TypeError`** 是后端最高频的运行时错误：`Cannot read properties of null (reading 'xxx')`。它通常是“上游返回了意料外的数据结构”所致，在 AI 场景里尤为常见（大模型返回的 JSON 结构变了、字段缺失）。防御手段：入口处做 schema 校验，而不是到处写 `?.`。

- **`RangeError`** 典型是递归太深（栈溢出）或传了非法的数组长度。

- **`SystemError`** 是 Node 对底层 libuv 错误的封装，特征是带有 `code`（字符串如 `'ENOENT'`）和 `errno`（数值常量）属性。判断系统错误靠 `err.code`，**不要**靠 `err.message`（文案可能随版本变化）：

  ```js
  fs.readFile('/no/such/file', (err) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // 文件不存在：可降级处理
      } else if (err.code === 'EACCES') {
        // 权限不足
      }
    }
  });
  ```

> 前端经验对照：浏览器里 `undefined is not a function` 顶多让某个按钮失效；在 Node 里一个未捕获的 `TypeError` 会让**整个进程崩溃**，所有正在处理的并发请求一起遭殃。这是服务端错误处理必须更严谨的根本原因。

### 2.2 同步错误 vs 异步错误

Node.js 的错误传播方式与代码“同步还是异步”强相关，这是前端工程师最容易踩坑的地方。

#### 同步错误

同步代码中 `throw` 出的错误，可以被同作用域的 `try/catch` 立即捕获：

```js
try {
  throw new Error('同步抛出');
} catch (err) {
  console.log(err.message); // 能捕获
}
```

#### 异步错误的三种形态

异步代码的 `throw` 不会冒泡到外层 `try/catch`，因为 `try/catch` 早已执行完毕：

```js
try {
  setTimeout(() => {
    throw new Error('异步抛出'); // ❌ 外层 catch 捕获不到
  }, 0);
} catch (err) {
  console.log('永远到不了这里');
}
```

异步错误有三种主流传播方式，处置手段各不相同：

| 方式 | 形态 | 捕获手段 |
|------|------|----------|
| **Promise reject** | `Promise.reject(err)` 或 `async` 函数里 `throw` | `.catch()` 或 `try/await/catch` |
| **error-first 回调** | `callback(err, data)`，`err` 为第一个参数 | 检查 `if (err)` 分支处理 |
| **`error` 事件** | `EventEmitter` 的 `error` 事件（如 stream、http） | 监听 `'error'` 事件，否则会抛出并崩溃 |

**① Promise reject：**

```js
// async/await 写法（推荐）
async function getUser(id) {
  try {
    const res = await fetch(`/api/users/${id}`);
    return await res.json();
  } catch (err) {
    // 这里能捕获 fetch 抛出的网络错误或 reject
    throw new AppError('获取用户失败', { cause: err });
  }
}
```

**② error-first 回调（Node 传统风格）：**

```js
fs.readFile(path, 'utf8', (err, data) => {
  if (err) {
    // 必须显式检查 err，不能假设成功
    return callback(err);
  }
  callback(null, data);
});
```

> 规则：**回调的第一个参数永远是 `err`**。这是 Node 早期为统一异步错误传播约定的规范，称为 error-first callback。现代代码优先用 Promise，但读老代码、用核心模块时仍会大量遇到。

**③ `error` 事件（极易被忽略的崩溃源）：**

`EventEmitter` 在触发 `error` 事件时，若**没有**监听器，Node 会直接抛出并终止进程：

```js
const stream = fs.createReadStream('不存在的文件');
// 没有监听 'error' → 进程崩溃：Error: ENOENT
stream.on('error', (err) => {
  console.error('流读取失败', err);
});
```

> 这是“明明 `try/catch` 都写了还是崩了”的常见原因。**凡是 `EventEmitter` / Stream / `http`，都要记得 `.on('error', ...)`。**

### 2.3 uncaughtException 与 unhandledRejection

当错误“逃逸”出了所有用户代码的捕获范围，就会触发进程级事件。两者是 Node 服务端兜底的最后一道防线：

| 事件 | 触发条件 | 含义 | 推荐策略 |
|------|----------|------|----------|
| `uncaughtException` | **同步**异常未被任何 `try/catch` 捕获 | 进程状态已不可靠（可能正在处理中间状态、资源泄漏） | 记录日志后**退出进程**（`process.exit(1)`），交给 PM2 / Docker / k8s 重启 |
| `unhandledRejection` | Promise 被 reject 但没有 `.catch()` | 通常是漏写了错误处理 | 记录日志；新版本 Node 倾向于也退出进程，避免静默失败 |

**为什么 `uncaughtException` 后要退出进程？**

进程在抛出未捕获异常的那一刻，可能正处于“改了一半的状态”：文件写到一半、数据库事务未提交、缓存半更新。继续运行下去行为不可预测。Node 官方文档明确建议：**`uncaughtException` 只应作为“优雅退出前的日志记录点”，不要当成兜底继续服务**。正确的可靠性来源是“进程管理器自动重启”，而不是“进程不死”。

```js
process.on('uncaughtException', (err) => {
  logger.error('uncaughtException', { stack: err.stack });
  process.exit(1); // 退出，让 PM2/k8s 拉起新进程
});

process.on('unhandledRejection', (reason) => {
  logger.error('unhandledRejection', {
    reason: reason && reason.stack ? reason.stack : String(reason)
  });
  // 生产环境同样建议退出，避免漏处理的 rejection 静默累积
});
```

**关于 Domain：** 早期 Node 提供过 `domain` 模块试图统一同步/异步错误捕获，但它设计上有根本缺陷（无法可靠地关联异步上下文），**已被废弃**，新项目不要使用。现代方案是用 `AsyncLocalStorage`（Node 13+）做请求上下文隔离，配合本篇的请求 ID 链路追踪。

### 2.4 Express 中的错误传播

Express 提供了一套机制让错误沿中间件链“跳转”，这就是 `next(err)`：

- 中间件/路由处理函数中调用 `next(err)`（`err` 为非空，通常是个 Error 对象），Express 会**跳过**后续所有普通中间件，直接把请求交给**第一个**四参数错误处理中间件。
- 普通中间件签名是 `(req, res, next)`（3 参数），错误中间件签名是 `(err, req, res, next)`（4 参数）。Express **靠参数个数识别**错误中间件，所以哪怕 `next` 没用到也**不能省略**，否则会被当成普通中间件，永远收不到错误。
- 同步抛出的错误（`throw err`）在路由 handler 内会被 Express 自动捕获并转交错误中间件；但 **async 函数内抛出的 rejection 不会被自动捕获**（Express 4），需要 `try/catch + next(err)` 或异步包装器。

```
请求 → 中间件A → 中间件B → 路由handler(throw/next(err))
                                        ↓ 跳过后续普通中间件
                                   错误中间件(4参数) → 响应
```

错误中间件必须**最后注册**，否则它之后注册的普通路由将永远无法匹配（错误中间件一旦“接住”错误就终结了请求链）。

---

## 三、错误处理最佳实践

### 3.1 自定义错误类

直接抛 `new Error('...')` 会在错误中间件里丢失“这是什么类型的错误”“该回什么状态码”的信息。最佳实践是建立一套**自定义错误类体系**，把元信息固化在错误对象上。

设计要点（见 `Code/custom-errors.js`）：

1. **基类 `AppError` 继承 `Error`**，额外携带 `statusCode`、`code`、`context`、`isOperational`。
2. **子类按语义命名**：`NotFoundError`（404）、`ValidationError`（400）、`UnauthorizedError`（401）、`ForbiddenError`（403），构造时自动设置对应的 `statusCode` 与 `code`。
3. **`Error.captureStackTrace`** 让堆栈指向抛出处而非基类构造器，排查更准。
4. **`isOperational`** 区分“操作型错误”（用户输错密码、资源不存在，可预期）与“程序 bug”（`TypeError`、空指针，不可预期）。操作型错误记 warn 即可，程序 bug 应记 error 并告警。

```js
class AppError extends Error {
  constructor(message, options = {}) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = options.statusCode || 500;
    this.code = options.code || 'INTERNAL_ERROR';
    this.context = options.context || {};
    this.isOperational = options.isOperational !== false;
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

// 业务代码只抛语义错误，不拼状态码
throw new ValidationError('name 不能为空', { context: { field: 'name' } });
```

### 3.2 错误码设计

新手常把“HTTP 状态码”当成唯一的错误标识，但这不够——一个 `400` 可能是“邮箱格式错”也可能是“余额不足”，程序无法精确分支。推荐**业务码与 HTTP 状态码分层**：

- **HTTP 状态码**：面向传输层与客户端协议，回答“这次请求在协议层面成功了吗”。`4xx` 客户端问题、`5xx` 服务端问题、`2xx` 成功。
- **业务码（code）**：面向业务语义，字符串形式，便于程序判断与国际化。如 `USER_NOT_FOUND`、`EMAIL_INVALID`、`BALANCE_INSUFFICIENT`。

两者关系：一个业务码通常映射到固定的 HTTP 状态码，但同一个 HTTP 状态码可对应多个业务码。

```json
// 同样是 400, 但业务码不同, 前端可据此做不同提示
{ "code": "EMAIL_INVALID",      "message": "邮箱格式不正确", "statusCode": 400 }
{ "code": "PASSWORD_TOO_WEAK",  "message": "密码强度不足",   "statusCode": 400 }
```

命名建议：业务码用**大写蛇形**（`SCREAMING_SNAKE_CASE`），按模块前缀分组（`USER_*`、`ORDER_*`、`AI_*`），集中在一份枚举/常量表里维护，避免散落字符串。

### 3.3 统一错误响应格式

所有错误应走**同一个出口**，返回结构一致，前端只需写一套解析逻辑：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "email 格式不正确",
  "details": { "field": "email", "value": "a" },
  "requestId": "9b1f...",
  "timestamp": "2026-07-24T10:30:00.000Z"
}
```

字段含义：

| 字段 | 用途 |
|------|------|
| `code` | 业务错误码，供程序分支判断 |
| `message` | 人类可读的提示，可直接展示给用户（注意不要泄露内部实现） |
| `details` | 额外上下文（如哪个字段出错），可选 |
| `requestId` | 请求 ID，用户上报问题时据此在日志里一查到底 |
| `timestamp` | ISO 时间戳，便于对账 |

> 成功响应也应遵循统一格式（如 `{ code: 'OK', data, requestId }`），与错误格式对齐，前端逻辑更清爽。本篇聚焦错误侧，成功格式可参考 Day10。

### 3.4 不要吞掉错误

“吞掉错误”指捕获了错误却不做任何处理，或只 `console.log` 后继续：

```js
// ❌ 反模式：吞掉错误
try {
  await doSomething();
} catch (err) {
  // 什么都没做，问题被掩盖
}

// ❌ 反模式：只 console.log，不传播也不处理
try {
  await doSomething();
} catch (err) {
  console.log(err); // 生产环境看不到，且不阻断错误流程
}
```

正确做法三选一（视场景）：

1. **处理并恢复**：确可降级（如缓存读失败就回源），处理后继续。
2. **包装并上抛**：转换为业务错误向上传播，附上 cause 保留原始信息。
3. **记录并传播**：记日志后 `throw` / `next(err)`，让上层统一处理。

```js
// ✅ 包装上抛，保留原始 cause
try {
  await callLLM(prompt);
} catch (err) {
  throw new AppError('大模型调用失败', {
    statusCode: 502,
    code: 'LLM_CALL_FAILED',
    cause: err
  });
}
```

### 3.5 错误分层

职责清晰的分层能让错误处理有条不紊：

| 层 | 职责 | 错误处理方式 |
|----|------|-------------|
| **控制器层（Controller / 路由 handler）** | 解析 `req`、调用 service、组装 `res` | `try/catch + next(err)`，或用 `asyncHandler` 包装；不写业务规则 |
| **服务层（Service）** | 业务逻辑编排 | 校验失败/资源不存在时**抛出**自定义错误，不关心 HTTP |
| **数据层（Model / DAO）** | 数据访问 | 抛底层错误或返回 `null`，由 service 判断是否转业务错误 |
| **中间件层** | 横切关注点 | 统一错误中间件兜底所有 `next(err)`，输出统一响应 |

要点：**业务层只抛语义错误，不关心 HTTP 状态码；中间件层负责把错误对象翻译成 HTTP 响应**。这样 service 可被非 HTTP 场景（定时任务、消息队列）复用。

### 3.6 区分 4xx 与 5xx

这是 HTTP 语义的基础，但常被混用：

- **4xx 客户端错误**：请求本身有问题（参数错、未鉴权、资源不存在）。服务端没问题，不该告警。日志记 `warn`。
- **5xx 服务端错误**：服务端出了问题（代码 bug、依赖挂了、超时）。需要开发和告警介入。日志记 `error`，含完整堆栈。

区分的实际价值：**告警阈值**。若把 4xx 也按 error 记录并告警，会被大量“用户填错表单”的噪声淹没，真正的故障反而被掩盖。本篇 `error-middleware.js` 正是按 `statusCode >= 500` 切分日志级别。

### 3.7 敏感信息脱敏

错误响应与日志都可能成为信息泄露通道：

- **响应体**：生产环境**绝不返回堆栈**、SQL、内部路径、第三方密钥。堆栈只在开发环境返回，便于调试。
- **日志**：不要记录用户密码、token、身份证、银行卡全号。需要时做掩码（如 `138****1234`）。
- **`message`**：面向用户的提示不要泄露实现细节。例如登录失败统一回“账号或密码错误”，而不是“用户名不存在”——后者可被用来枚举账号。

```js
// 错误中间件中的脱敏
const body = { code, message, details, requestId, timestamp };
if (process.env.NODE_ENV !== 'production') {
  body.stack = err.stack; // 仅开发环境
}
res.status(statusCode).json(body);
```

---

## 四、Express 错误处理中间件详解

### 4.1 四参数签名

错误处理中间件必须声明四个参数 `(err, req, res, next)`，Express 通过参数个数识别它。**哪怕 `next` 没用到也不能省略**——省略后参数个数变成 3，会被当成普通中间件，永远收不到错误：

```js
// ✅ 错误中间件（4 参数）
app.use((err, req, res, next) => {
  res.status(err.statusCode || 500).json({ code: err.code, message: err.message });
});

// ❌ 少写 next → 这是普通中间件，收不到 err
app.use((err, req, res) => { /* 永远不会执行 */ });
```

### 4.2 async 错误包装器 asyncHandler

Express 4 不会自动捕获 async handler 内的 rejection。每个 async 路由都写 `try/catch` 很啰嗦，用包装器统一处理（见 `Code/async-handler.js`）：

```js
function asyncHandler(fn) {
  return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

// 用法：内部 throw 或 await reject 都会自动转 next(err)
router.get('/ai/ask', asyncHandler(async (req, res) => {
  const result = await callLLM(req.body.prompt); // 可能 reject
  res.json({ result });
}));
```

> Express 5 对 async 更友好，会自动转发 rejection，届时包装器可省。在 4.x 中这是事实标准。

### 4.3 404 处理中间件

404 不是“错误”，而是“没有匹配的路由”。实现方式是注册一个**放在所有业务路由之后**的普通中间件，构造错误并 `next(err)`，让统一错误中间件输出一致的 404 响应：

```js
// 必须在所有 app.get/post... 之后
app.use((req, res, next) => {
  const err = new Error(`未找到路由: ${req.method} ${req.originalUrl}`);
  err.statusCode = 404;
  err.code = 'NOT_FOUND';
  next(err);
});
```

### 4.4 错误中间件放在最后

注册顺序决定执行顺序。错误中间件必须**最后注册**，确保它能兜住所有路由与 404 转发来的错误：

```js
app.use(express.json());
app.use(requestId);
app.use(morgan(...));
// ...所有业务路由...
app.use(notFoundHandler);   // 404
app.use(errorHandler);      // 统一错误处理，最后
```

---

## 五、日志基础

### 5.1 为什么 console.log 不够

前端用 `console.log` 调试没问题，但服务端生产环境它有四大硬伤：

| 不足 | 说明 |
|------|------|
| **无级别** | `console.log/error/warn` 区分粗糙，无法按级别过滤（如“只看 error”） |
| **无结构** | 输出是自由文本，难以被日志系统解析、检索、聚合 |
| **无持久化** | 默认只写到 stdout/stderr，进程重启即丢失，无法回溯 |
| **无轮转** | 即便重定向到文件，也会无限增长，撑爆磁盘 |

生产级日志需要：**级别分明 + 结构化 + 持久化到文件 + 自动轮转 + 可被聚合系统采集**。这正是 winston 等专业库存在的理由。

### 5.2 日志级别使用规范

业界通用的级别（从低到高）：

| 级别 | 用途 | 举例 |
|------|------|------|
| `debug` | 详细诊断信息，仅开发/排查时开 | “收到请求体: {...}”、“进入函数 X，参数=...” |
| `info` | 关键业务节点、正常运行轨迹 | “用户登录成功”、“请求完成 status=200” |
| `warn` | 可预期的异常，需关注但不告警 | “参数校验失败 400”、“缓存未命中，回源” |
| `error` | 非预期错误，需排查 | “数据库连接失败”、“下游服务超时 500” |
| `fatal` | 致命错误，进程无法继续 | “配置加载失败，启动终止” |

规范：

- **生产环境关 `debug`**：避免日志量爆炸与潜在的信息泄露。
- **`info` 别滥用**：每条 info 都在被采集、占存储。只记有价值的节点。
- **`error` 要有上下文**：光记 `error: undefined` 毫无意义，要带请求、参数、堆栈。

### 5.3 结构化日志

用 **JSON 格式**而非自由文本，让日志可被机器解析、检索、聚合：

```json
{
  "timestamp": "2026-07-24 10:30:00.123",
  "level": "error",
  "message": "大模型调用失败",
  "requestId": "9b1f-...",
  "userId": 42,
  "prompt": "你好",
  "model": "gpt-4",
  "durationMs": 5000,
  "stack": "Error: timeout\n    at ..."
}
```

必备字段：`timestamp`、`level`、`message`，再按需加 `requestId`、`userId`、业务上下文。winston 的 `json()` format 会自动把 info 对象序列化成 JSON。

### 5.4 请求 ID 链路追踪

一个请求可能经过日志、鉴权、多个服务调用，没有标识就串不起来。**请求 ID（requestId）** 是给每个请求分配一个唯一 ID，贯穿整个处理链路：

1. 入口处生成（优先复用上游透传的 `X-Request-Id`，否则用 uuid 生成）。
2. 挂到 `req` 上，注入到响应头 `X-Request-Id`。
3. 注入到 logger 上下文，该请求所有日志都自动带上同一 `requestId`。
4. 调用下游服务时，把 `requestId` 放进请求头透传，串联整条调用链。

用户报错时提供 `requestId`，运维在日志系统里一搜即可定位该请求的全部轨迹。本篇 `request-id.js` 用 `logger.child({ requestId })` 实现上下文注入。

---

## 六、winston 详解

[winston](https://github.com/winstonjs/winston) 是 Node.js 生态最主流的日志库，核心概念：**logger**（日志器）、**transport**（输出目标）、**format**（格式化）、**level**（级别）。

### 6.1 transports（输出目标）

一个 logger 可同时挂多个 transport，每条日志会广播到所有匹配级别的 transport：

| Transport | 用途 |
|-----------|------|
| `transports.Console` | 输出到控制台，开发调试用 |
| `transports.File` | 输出到固定文件，简单场景 |
| `DailyRotateFile` | 按天/按大小轮转的文件，生产主力 |
| `transports.Http` | 通过 HTTP 发送到远端日志服务 |

```js
const logger = createLogger({
  transports: [
    new transports.Console({ level: 'debug' }),
    new transports.File({ filename: 'app.log', level: 'info' })
  ]
});
```

### 6.2 format（格式化）

format 是一个组合管道，常用：

- `timestamp`：注入时间戳。
- `json`：序列化为 JSON（生产文件日志首选）。
- `printf`：自定义模板（控制台可读性首选）。
- `colorize`：控制台彩色输出。
- `errors({ stack: true })`：自动把 Error 的 `stack` 提取出来（默认 `stack` 不会被序列化）。

用 `combine` 串联：

```js
const { combine, timestamp, json, errors } = format;
const fileFormat = combine(timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }), errors({ stack: true }), json());
```

> `errors({ stack: true })` 很关键：winston 默认对 Error 对象只记录 `message`，加上它才能在日志里看到完整堆栈。

### 6.3 级别配置

- `level`（logger 级别）：低于该级别的日志直接丢弃，不进入 transport。
- 每个 transport 还可单独设 `level`，实现“不同 transport 记不同级别”。

本篇 `logger.js` 的设计：

```js
const logger = createLogger({
  level: isProd ? 'info' : 'debug',   // 全局：生产 info，开发 debug
  transports: [
    errorRotateTransport,  // level: 'error'  → 只收 error 及以上
    appRotateTransport     // level: 'info'   → 收 info 及以上
  ]
});
```

效果：`error` 级日志同时写进 `error-*.log` 和 `app-*.log`；`info/warn` 只写进 `app-*.log`。排查故障时优先看 `error-*.log`，量小干净。

### 6.4 DailyRotateFile 轮转

`winston-daily-rotate-file` 提供按时间和大小双维度轮转，避免单文件无限增长：

```js
new DailyRotateFile({
  dirname: './logs',
  filename: 'app-%DATE%.log',     // %DATE% 会被日期替换
  datePattern: 'YYYY-MM-DD',      // 按天切割
  maxSize: '20m',                 // 单文件超 20MB 也切割
  maxFiles: '14d',                // 保留 14 天，超期自动删除
  level: 'info'
});
```

- `maxFiles` 支持 `'14d'`（天数）或 `'100'`（文件数）。
- 老文件到期自动清理，磁盘可控。
- 按天切割的文件天然适合按日期归档与检索。

### 6.5 多 transport 不同级别

把“全量日志”与“错误日志”分流到不同文件，是生产实践标配：

| 文件 | level | 用途 |
|------|-------|------|
| `app-YYYY-MM-DD.log` | `info` | 全量运行轨迹，量大 |
| `error-YYYY-MM-DD.log` | `error` | 仅错误，量小，优先排查/告警 |
| `exceptions-YYYY-MM-DD.log` | — | winston 的 `exceptionHandlers` 专门收 `uncaughtException` |

本篇 `logger.js` 即采用此三段式分流。

---

## 七、morgan HTTP 请求日志

[morgan](https://github.com/expressjs/morgan) 是 Express 生态最常用的 HTTP 请求日志中间件，记录每个请求的方法、路径、状态码、耗时等。

### 7.1 内置格式

| 格式 | 内容 | 适用 |
|------|------|------|
| `combined` | Apache 标准 combined 日志（含 IP、UA、referer） | 生产 |
| `common` | Apache 标准 common 日志（较简洁） | 通用 |
| `dev` | 彩色、按状态码着色、开发友好 | 开发 |
| `tiny` | 极简：方法 url 状态 耗时 长度 | 简易 |

```js
app.use(morgan('dev'));         // 开发
app.use(morgan('combined'));    // 生产
```

### 7.2 自定义 token

可用 `morgan.token(name, fn)` 定义新字段，再用自定义格式串引用：

```js
morgan.token('requestId', (req) => req.id || '-');
const fmt = ':method :url :status :response-time ms - :requestId';
app.use(morgan(fmt));
```

### 7.3 流到 winston

morgan 默认输出到 `process.stdout`。要让它进入 winston 体系（统一持久化、统一级别），通过 `stream` 选项把输出重定向：

```js
const morganStream = {
  write: (line) => logger.info(line.trim(), { source: 'morgan' })
};
app.use(morgan(morganFormat, { stream: morganStream }));
```

> `stream.write` 接收的 `line` 末尾带换行，需 `trim()`。这样 morgan 的请求日志与业务日志走同一个 winston，文件里混排但可按 `source: 'morgan'` 区分。

---

## 八、日志最佳实践

1. **不记录敏感信息**：密码、token、API key、身份证、银行卡一律不记。需要时掩码（`138****1234`）。审计日志单独存储并加权限。
2. **生产环境关 `debug`**：通过环境变量控制 `level`，避免日志量爆炸与信息泄露。
3. **错误日志含完整上下文**：一条 error 日志应能让你“不看代码也大致明白发生了什么”——带上 requestId、请求方法与路径、关键参数、堆栈、`isOperational`。
4. **请求 ID 全链路贯穿**：入口生成，日志带上，调用下游时透传到请求头。这是分布式排查的基础。
5. **结构化优先**：文件日志用 JSON，便于机器处理；控制台可用 printf 做人眼可读。
6. **轮转与保留**：按天+按大小轮转，设保留期，避免磁盘被撑爆。
7. **日志聚合**：单机日志文件难以应对多实例。生产环境通常把日志采集到集中式系统检索：
   - **ELK**（Elasticsearch + Logstash + Kibana）：经典栈，功能全、资源占用高。
   - **Loki + Grafana**：轻量、像 Prometheus 一样只索引标签，性价比高，云原生流行。
   - **云厂商日志服务**（如阿里云 SLS、AWS CloudWatch）：托管免运维。
   采集方式：winston 写文件 → Filebeat / Promtail 采集 → 集中存储 → Kibana / Grafana 查询。

> AI 场景特别提醒：记录大模型调用时，prompt 和 completion 可能很长且含敏感内容。建议记录摘要（token 数、耗时、模型名、是否成功），完整内容按需存到对象存储并加权限，而非全量进日志。

---

## 九、关键知识点总结

1. **错误四分类**：语法错误（解析期，改代码）、运行时错误（`TypeError`/`RangeError`，`try/catch`）、逻辑错误（结果错，靠测试）、系统错误（`ENOENT` 等，看 `err.code`）。
2. **异步错误三形态**：Promise reject（`.catch`/`try-await`）、error-first 回调（检查首参）、`error` 事件（必须 `.on('error')`，否则崩溃）。外层 `try/catch` 捕获不到异步 `throw`。
3. **进程级兜底**：`uncaughtException` 记录后退出进程交给重启；`unhandledRejection` 记录（建议也退出）；`domain` 已废弃，用 `AsyncLocalStorage` 替代。
4. **Express 错误传播**：`next(err)` 跳到第一个四参数错误中间件；错误中间件靠参数个数识别，`next` 不能省；放最后；async 错误需 `asyncHandler` 包装（4.x）。
5. **自定义错误类**：继承 `Error`，携带 `statusCode`/`code`/`context`/`isOperational`，业务层只抛语义错误。
6. **业务码与 HTTP 状态码分层**：状态码面向协议，业务码面向语义；统一响应 `{ code, message, details, requestId, timestamp }`。
7. **4xx vs 5xx**：4xx 客户端问题记 warn 不告警，5xx 服务端问题记 error 含堆栈并告警。
8. **脱敏**：生产环境不返回堆栈；日志不记密码/token；面向用户的 message 不泄露实现细节。
9. **console.log 不够**：无级别、无结构、无持久化、无轮转；生产用 winston：transports（Console/File/DailyRotateFile/HTTP）+ format（timestamp/json/printf/colorize/errors）+ 分级别分流。
10. **请求 ID 链路追踪**：uuid 生成，挂 `req`、写响应头、注入 `logger.child`，贯穿全链路；morgan 通过 `stream` 接入 winston 统一出口；日志最终聚合到 ELK/Loki。

---

## 十、实战练习

> 以下练习在 `Code/` 目录基础上扩展，建议独立完成后再对照本篇结论自查。

### 练习一：扩展自定义错误类与错误码表

**目标**：丰富错误体系，建立可维护的错误码表。

**要求**：

1. 在 `custom-errors.js` 中新增 `ConflictError`（409，如重复注册）、`RateLimitError`（429，限流）。
2. 新建一个 `error-codes.js`，把所有业务码集中成常量对象（如 `ERROR_CODES = { USER_NOT_FOUND: 'USER_NOT_FOUND', ... }`），并在自定义错误类里引用常量而非裸字符串。
3. 思考：把错误码集中成常量对象，相比散落字符串，有哪些工程收益？

**考察点**：错误类设计、错误码集中管理、避免魔法字符串。

### 练习二：给 AI 接口加上完整的错误处理与上下文日志

**目标**：模拟一个真实的大模型调用接口，把本篇所有能力串起来。

**要求**：

1. 新增路由 `POST /api/ai/chat`，body 为 `{ prompt }`。
2. 在 service 层用 `setTimeout` 模拟大模型调用，随机 30% 概率 reject（模拟超时/限流/内容审核失败三种不同错误，分别抛 504/429/400）。
3. 用 `asyncHandler` 包装路由，service 层抛自定义错误（如 `AppError` 的子类），控制器层不做 try/catch。
4. 错误中间件已能统一处理；确认 5xx 进 `error-*.log` 且含堆栈，4xx 只进 `app-*.log`。
5. 每条日志都带 `requestId`、`prompt`（截断前 50 字符）、`model`、`durationMs`。
6. 给出 curl 测试命令并验证日志输出。

**考察点**：错误分层（service 抛 / controller 透传 / 中间件兜底）、`asyncHandler`、上下文日志、4xx/5xx 分流。这是后续 AI 接口编排的高频范式。

### 练习三：实现敏感信息脱敏中间件

**目标**：防止敏感数据进日志。

**要求**：

1. 写一个 `sanitize(obj)` 工具函数，递归遍历对象，把 `password`、`token`、`authorization`、`apiKey` 等 key 的值替换为 `'***'`。
2. 在 `request-id.js` 的 access 日志里，对 `req.body` 先 `sanitize` 再记录。
3. 测试：`POST /api/users` 带 `{"name":"a","password":"123456"}`，确认日志里 password 显示为 `***`，但控制器收到的 `req.body.password` 仍是原文（脱敏只影响日志，不影响业务）。
4. 进阶：思考如何在 `logger` 层面统一做脱敏（提示：winston 的自定义 format），而非每个调用点手动 `sanitize`。

**考察点**：日志安全、深拷贝/递归遍历、关注点分离（脱敏不应破坏业务数据）。

---

> 完成本篇后，你已具备让一个 Node.js 服务“出错不崩、有迹可循”的工程能力。下一篇将在此基础上引入**进程管理与优雅停机、配置与环境变量管理、健康检查与就绪探针**等上线相关主题，把“能跑”的服务推向“可运维”的服务。
