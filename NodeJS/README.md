# Node.js 全栈学习指南

> 一本 Node.js 系统化学习手册

> 共 20 天，覆盖从运行时基础到生产部署的完整知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是 AI 全栈学习系列的**第一站**。Node.js 既是前端工程师最自然的后端切入点，也是 AI 应用后端服务（BFF、模型推理包装、RAG 后端、向量数据预处理）的核心载体。

**学习目标**：完成本板块后，你应能独立设计并实现一个包含路由、中间件、数据库、认证、实时通信、日志、部署的 Node.js 生产级后端服务，为后续接入 AI 能力（大模型调用、向量数据库、Agent 后端）打下坚实基础。

**设计原则**：
- 知识点梳理为主，不包含大型完整项目
- 每天均为独立知识单元，含理论 + 代码示例 + 实战练习
- 紧扣 AI 全栈视角，多处铺垫 AI 应用场景
- 所有代码可在 Node 18+ 直接运行，已实测通过

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| JavaScript 基础 | 熟练 | ES6+ 语法、闭包、原型链、异步概念 |
| 前端工程经验 | 有 | 了解 npm、webpack/vite、HTTP 基础 |
| 命令行操作 | 基础 | 能用终端执行命令、配置环境变量 |
| 操作系统概念 | 基础 | 进程、文件系统、网络端口 |
| 数据库概念 | 了解 | 知道 SQL 与 NoSQL 的区别即可 |

**环境准备**：
- Node.js 18 LTS 或更高（推荐用 nvm 管理版本）
- VS Code（含 Node.js 调试插件）
- Git
- 可选：本地 MySQL 8+、MongoDB 6+（Day17 需要，也可用 Docker）

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Node.js 全栈学习路线（20天）                  │
└─────────────────────────────────────────────────────────────────┘

阶段一：基础与环境（Day01-Day03）
┌──────────────┬──────────────┬──────────────┐
│  Day01 初识  │  Day02 模块  │  Day03 npm   │
│  Node.js     │  系统        │  包管理      │
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       ▼              ▼              ▼
阶段二：异步编程（Day04-Day05）
┌──────────────────────┬──────────────────────┐
│  Day04 回调与事件循环  │  Day05 Promise/async  │
└──────────┬───────────┴──────────┬───────────┘
           │                      │
           ▼                      ▼
阶段三：核心模块（Day06-Day08）
┌──────────────┬──────────────┬──────────────┐
│  Day06 Buffer│  Day07 fs    │  Day08 Path  │
│  与 Stream   │  文件系统    │  与 OS 等    │
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       ▼              ▼              ▼
阶段四：Web 开发（Day09-Day13）
┌────────────┬────────────┬────────────┬────────────┬────────────┐
│ Day09 HTTP │ Day10      │ Day11       │ Day12      │ Day13      │
│ 模块       │ Express    │ 中间件      │ RESTful    │ 数据校验   │
└─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┘
      │            │            │            │            │
      ▼            ▼            ▼            ▼            ▼
阶段五：工程化（Day14-Day16）
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  Day14 错误处理与日志  │  Day15 process 与子进程│  Day16 Cluster 与 PM2 │
└──────────┬───────────┴──────────┬───────────┴──────────┬───────────┘
           │                      │                      │
           ▼                      ▼                      ▼
阶段六：数据与安全（Day17-Day19）
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  Day17 数据库集成     │  Day18 JWT 身份认证   │  Day19 WebSocket     │
└──────────┬───────────┴──────────┬───────────┴──────────┬───────────┘
           │                      │                      │
           ▼                      ▼                      ▼
阶段七：生产部署（Day20）
┌──────────────────────────────────────────────────────┐
│  Day20 性能优化与部署上线                              │
│  （压缩/缓存/Docker/Nginx/健康检查/PM2）              │
└──────────────────────────────────────────────────────┘
```

---

## 每日内容详表

### 阶段一：基础与环境

#### Day01 - 初识Node.js与运行环境
- **核心**：Node.js 本质、V8 引擎与 libuv、与浏览器 JS 的差异、事件驱动与非阻塞 I/O
- **代码**：`hello.js` / `system-info.js` / `args-demo.js`
- **AI 视角**：BFF、数据预处理、模型服务包装、RAG 后端

#### Day02 - 模块系统(CommonJS与ES Modules)
- **核心**：require 解析机制、Module._cache、exports vs module.exports、ESM 静态特性、互操作、循环依赖
- **代码**：`math-commonjs.js` / `circle-area.mjs` / `dynamic-import.js` 等
- **重点**：`"type": "module"`、`.mjs/.cjs` 扩展名

#### Day03 - npm包管理与package.json
- **核心**：package.json 字段、SemVer（^ vs ~）、package-lock.json、npx、npm scripts 钩子、npm audit
- **代码**：`package.json` / `math-util.js` / `.npmrc` / `use-npx-demo.js`
- **重点**：pre/post 钩子、cross-env、scope 包

---

### 阶段二：异步编程

#### Day04 - 异步编程(回调与事件循环)
- **核心**：错误优先回调、回调地狱、Event Loop 六阶段、微任务 vs 宏任务、process.nextTick 优先级、EventEmitter
- **代码**：`callback-demo.js` / `callback-hell.js` / `event-loop-order.js` / `eventemitter-demo.js` / `timer-vs-immediate.js`
- **重点**：setTimeout(0) vs setImmediate 的执行顺序差异

#### Day05 - Promise与async-await
- **核心**：Promise 三态、链式调用、all/allSettled/race/any、async/await 语法糖本质、顶层 await
- **代码**：`promise-basic.js` / `promise-combinators.js` / `async-await-demo.js` / `parallel-vs-serial.js` / `fetch-data.mjs`
- **重点**：串行 vs 并发性能差异、forEach+await 反模式

---

### 阶段三：核心模块

#### Day06 - Buffer与Stream流
- **核心**：Buffer 与 Uint8Array、编码转换、四种流类型、背压、pipe vs pipeline、自定义流、Web Streams
- **代码**：`buffer-basic.js` / `readable-stream.js` / `transform-stream.js` / `pipeline-demo.js` / `backpressure-demo.js`
- **AI 视角**：大模型流式输出、文件上传分块

#### Day07 - 文件系统fs模块
- **核心**：三种 API 风格（同步/回调/Promise）、读写删改、stat、watch、目录操作、原子写入
- **代码**：`sync-vs-async.js` / `file-ops.js` / `dir-ops.js` / `stream-copy.js` / `jsonl-reader.js`
- **AI 视角**：读取 jsonl 训练数据、保存模型与向量

#### Day08 - Path与OS等核心模块
- **核心**：path.join vs resolve、os 模块（CPU/内存/网络）、WHATWG URL、util.promisify、crypto（哈希/HMAC/AES）
- **代码**：`path-demo.js` / `os-demo.js` / `url-demo.js` / `util-demo.js` / `crypto-demo.js`
- **AI 视角**：根据 CPU 核数设并发、API key 加密

---

### 阶段四：Web 开发

#### Day09 - HTTP模块与原生Web服务器
- **核心**：createServer、req/res、手动路由、请求体解析、http 客户端、原生 fetch
- **代码**：`hello-server.js` / `router-server.js` / `json-api-server.js` / `http-client.js` / `fetch-client.mjs` / `static-file-server.js`
- **重点**：为引出 Express 做铺垫

#### Day10 - Express框架入门
- **核心**：Express 哲学、路由方法、路径匹配、路由参数、express.Router、内置中间件、req/res 对象
- **代码**：`app.js` / `users-router.js` / `server.js` / `middleware-demo.js` / `static-demo.js`
- **依赖**：express

#### Day11 - Express中间件机制
- **核心**：中间件签名、执行栈模型、next() 控制权、应用级/路由级/错误处理中间件、asyncHandler、第三方中间件速览
- **代码**：`basic-middleware.js` / `auth-middleware.js` / `error-middleware.js` / `cors-middleware.js` / `rate-limit-middleware.js` / `combined-app.js`
- **依赖**：express

#### Day12 - RESTful API设计与实现
- **核心**：REST 原则、HTTP 方法语义、幂等性、状态码、URI 设计规范、统一响应格式、版本化
- **代码**：`response-helper.js` / `articles-router.js` / `server.js` / `async-handler.js` / `pagination-demo.js`
- **依赖**：express

#### Day13 - 请求处理与数据校验
- **核心**：请求处理链路、参数来源、Joi、express-validator、multer 文件上传、统一错误响应
- **代码**：`joi-validation.js` / `express-validator-demo.js` / `multer-upload.js` / `unified-error.js` / `server.js`
- **依赖**：express, joi, express-validator, multer

---

### 阶段五：工程化

#### Day14 - 错误处理与日志记录
- **核心**：错误分类、自定义错误类、错误中间件、winston 日志、DailyRotateFile、请求 ID 链路追踪、morgan
- **代码**：`custom-errors.js` / `error-middleware.js` / `async-handler.js` / `logger.js` / `request-id.js` / `app.js`
- **依赖**：express, morgan, winston, winston-daily-rotate-file, uuid

#### Day15 - process对象与子进程
- **核心**：process 对象、环境变量、信号处理、child_process 四方法（spawn/exec/execFile/fork）、worker_threads
- **代码**：`process-demo.js` / `spawn-demo.js` / `exec-demo.js` / `fork-ipc.js` / `call-python.js` / `worker-demo.js`
- **AI 视角**：spawn 调用 Python 推理脚本、worker 跑 CPU 密集计算

#### Day16 - Cluster集群与PM2进程管理
- **核心**：cluster 模块、master/worker、零停机重启、PM2 命令、ecosystem.config.js、优雅退出、容器化取舍
- **代码**：`cluster-http.js` / `graceful-shutdown.js` / `zero-downtime-reload.js` / `ecosystem.config.js` / `pm2-commands.md` / `worker-ipc-demo.js`

---

### 阶段六：数据与安全

#### Day17 - 数据库集成(MySQL与MongoDB)
- **核心**：MySQL vs MongoDB 对比、连接池、mysql2 Promise 风格、事务、mongoose 三层架构、DAO/Repository 模式
- **代码**：`mysql-pool.js` / `mysql-transaction.js` / `mongoose-model.js` / `mongoose-crud.js` / `repository-pattern.js` / `server.js`
- **依赖**：express, mysql2, mongoose
- **AI 视角**：存储对话历史、向量元数据、知识库

#### Day18 - JWT身份认证
- **核心**：Session vs JWT、JWT 结构与算法、签发与校验、bcrypt 密码哈希、access + refresh token 机制、黑名单
- **代码**：`password-hash.js` / `jwt-sign-verify.js` / `auth-middleware.js` / `user-store.js` / `refresh-token.js` / `server.js`
- **依赖**：express, jsonwebtoken, bcryptjs

#### Day19 - WebSocket实时通信
- **核心**：实时通信方案对比、WebSocket 协议、ws 库、Express 集成、广播/私聊/房间、心跳、鉴权
- **代码**：`basic-ws.js` / `express-ws.js` / `chat-room.js` / `broadcast-demo.js` / `heartbeat.js` / `ws-auth.js` / `server.js`
- **依赖**：express, ws
- **AI 视角**：大模型流式响应转发、Agent 工具调用进度推送

---

### 阶段七：生产部署

#### Day20 - 性能优化与部署上线
- **核心**：性能测量、CPU/内存/网络/数据库优化、安全加固、Docker 多阶段构建、Nginx 反向代理、PM2 生产配置、健康检查
- **代码**：`performance-measure.js` / `caching-demo.js` / `compression-demo.js` / `security-checklist.js` / `health-check.js` / `Dockerfile` / `nginx.conf` / `ecosystem.config.js`
- **依赖**：express, helmet, compression, express-rate-limit

---

## 目录结构

```
NodeJS/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - 初识Node.js与运行环境/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天代码示例
│       ├── hello.js
│       ├── system-info.js
│       └── args-demo.js
├── Day02 - 模块系统(CommonJS与ES Modules)/
│   ├── README.md
│   └── Code/
│       └── ...
├── Day03 - npm包管理与package.json/
│   ├── README.md
│   └── Code/
│       └── ...
├── ...（Day04-Day19 同构）...
└── Day20 - 性能优化与部署上线/
    ├── README.md
    └── Code/
        ├── Dockerfile
        ├── nginx.conf
        ├── ecosystem.config.js
        └── ...
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内
- 需要依赖的天数在 `Code/` 下有 `package.json`
- Day15、Day16 额外含子进程入口文件（fork 必需）

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 6-8 小时 | 约 3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 6-8 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2-3 月 |

### 学习方法论

1. **先读后写**：每天先通读 README，理解概念后再动手跑代码
2. **动手验证**：每个代码文件都要亲自运行，观察输出是否符合预期
3. **改写实验**：在示例基础上做修改，验证你的理解是否正确
4. **完成实战**：每天 README 末尾的实战练习是巩固知识的关键
5. **做笔记**：建议用 Markdown 记录每天的关键收获与疑问

### 阶段性检查点

完成每个阶段后，应能回答以下问题：

- **阶段一完成后**：能否解释 Node.js 为什么单线程却能处理高并发？
- **阶段二完成后**：能否画出 Event Loop 完整执行流程？
- **阶段三完成后**：能否用 Stream 实现一个大文件的转换与拷贝？
- **阶段四完成后**：能否独立设计一个 RESTful API 并用 Express 实现？
- **阶段五完成后**：能否为应用加上结构化日志与请求链路追踪？
- **阶段六完成后**：能否实现一个带 JWT 认证与实时通信的完整后端？
- **阶段七完成后**：能否把应用 Docker 化并用 Nginx 反向代理上线？

---

## 如何运行代码

### 内置模块示例（Day01-Day09、Day15、Day16）

```bash
cd "Day01 - 初识Node.js与运行环境/Code"
node hello.js
node system-info.js
node args-demo.js 10 20 30
```

### 需要安装依赖的示例（Day10-Day14、Day17-Day20）

```bash
cd "Day10 - Express框架入门/Code"
npm install
node server.js
# 按注释中的 curl 命令测试
```

### 需要外部服务（Day17、可选 Day18）

```bash
# Day17 需要 MySQL 与 MongoDB，可用 Docker 快速启动
docker run -d --name mysql -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 mysql:8
docker run -d --name mongo -p 27017:27017 mongo:6

# 然后进入 Code 目录
cd "Day17 - 数据库集成(MySQL与MongoDB)/Code"
npm install
node server.js
```

### 调试技巧

```bash
# 用 --inspect 启用 Chrome DevTools 调试
node --inspect server.js

# 用 nodemon 热重载（需全局安装）
npm install -g nodemon
nodemon server.js
```

### Windows 用户注意

- PowerShell 中 `curl` 是 `Invoke-WebRequest` 的别名，建议用 `curl.exe` 或在 Git Bash 中运行
- 环境变量设置用 `cross-env` 或 `$env:NODE_ENV="production"`
- 路径分隔符为 `\`，但 Node.js 的 `path` 模块会自动处理

---

## 知识点速查

### Node.js 核心概念速查表

| 概念 | 一句话解释 | 对应天数 |
|------|----------|---------|
| Event Loop | Node.js 异步调度核心，分 6 个阶段循环执行 | Day04 |
| 模块缓存 | require 首次加载后缓存，再次 require 返回同一对象 | Day02 |
| 错误优先回调 | `(err, data) => {}` 约定，err 非 null 表示出错 | Day04 |
| 微任务优先级 | nextTick > Promise > setTimeout/setImmediate | Day04 |
| 背压 | 写入速度慢于读取时，流通过返回 false 暂停读取 | Day06 |
| 中间件 | Express 中处理请求的函数链，通过 next() 传递 | Day11 |
| 幂等性 | 同一请求重复执行结果相同（PUT/DELETE 幂等，POST 不幂等） | Day12 |
| 连接池 | 预创建一批数据库连接复用，避免频繁建连开销 | Day17 |
| JWT 无状态 | 服务端不存储会话，靠签名校验 token 真伪 | Day18 |
| 优雅退出 | 收到信号后停止接新请求、处理完在途、关连接、退出 | Day16、Day20 |

### 常用命令速查

```bash
# Node 运行
node file.js                    # 运行脚本
node --inspect file.js          # 启用调试
node -e "console.log(1+1)"      # 执行一行代码

# npm
npm install                     # 安装依赖
npm install <pkg> --save        # 安装生产依赖
npm install <pkg> --save-dev   # 安装开发依赖
npm run <script>                # 运行 scripts
npm audit                        # 安全审计
npx <cmd>                        # 一次性执行命令

# PM2
pm2 start ecosystem.config.js   # 启动集群
pm2 list                         # 查看进程
pm2 logs                         # 查看日志
pm2 reload <app>                 # 零停机重载
pm2 monit                        # 监控面板

# 调试与性能
node --inspect                   # Chrome DevTools 调试
node --prof                       # CPU 性能分析
clinic doctor                     # clinic.js 性能诊断
```

### Express 常用中间件速查

| 中间件 | 作用 | 来源 |
|--------|------|------|
| express.json() | 解析 JSON 请求体 | 内置 |
| express.urlencoded() | 解析表单请求体 | 内置 |
| express.static() | 静态文件服务 | 内置 |
| morgan | HTTP 请求日志 | 第三方 |
| helmet | 安全响应头 | 第三方 |
| cors | 跨域处理 | 第三方 |
| compression | gzip 压缩 | 第三方 |
| express-rate-limit | 请求限流 | 第三方 |
| multer | 文件上传 | 第三方 |
| cookie-parser | Cookie 解析 | 第三方 |

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **TypeScript** | Day02 的 ESM、Day13 的 Zod、Day17 的 mongoose 都受益于 TS 类型系统 |
| **NestJS** | 基于 Express（Day10-14）的进阶框架，依赖注入、装饰器、模块化 |
| **MySQL** | 深化 Day17 的数据库知识，索引优化、事务隔离级别、慢查询 |
| **Redis** | 配合 Day20 的缓存策略，会话存储、限流、消息队列 |
| **Linux** | Day20 的部署、Nginx、进程管理需要 Linux 基础 |
| **Docker** | Day20 的 Dockerfile 实战化，多服务编排、镜像优化 |
| **Python** | Day15 的 spawn 调用 Python 推理脚本的真实场景 |
| **LLM / RAG / Agent** | 本板块的 Web 服务、数据库、WebSocket 是 AI 后端的承载层 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [Node.js 官方文档](https://nodejs.org/zh-cn/docs/) - 最权威的 API 参考
- [Node.js 最佳实践](https://github.com/goldbergyoni/nodebestpractices) - 社区维护的最佳实践集合
- [Express 官方文档](https://expressjs.com/) - Express 框架权威指南
- [MDN Web Docs](https://developer.mozilla.org/zh-CN/) - JavaScript 与 Web API 参考

---

## 贡献与反馈

本学习手册为原创内容，参考 GitHub 优质仓库的文档风格但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，早日成为 AI 全栈工程师！**
