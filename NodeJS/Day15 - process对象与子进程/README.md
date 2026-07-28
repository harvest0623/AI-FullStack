# Day15 - process 对象与子进程

> 本篇聚焦 Node.js 运行时的两个底层基石——**`process` 全局对象**与**`child_process` / `worker_threads` 模块**。`process` 让你掌控进程自身的信息、环境、标准流与退出行为；`child_process` 让 Node 能够“跳出单线程”去调用外部命令（如 Python 推理脚本、ffmpeg、puppeteer）并与其通信；`worker_threads` 则提供真正的多线程能力，为后续在 Node 中编排 CPU 密集的 AI 预处理与推理任务铺垫。掌握本篇之后，你将不再受困于“主线程被一段同步计算卡住”的窘境，并能初步具备编排多语言/多进程 AI 流水线的能力。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 process 对象核心属性](#21-process-对象核心属性)
  - [2.2 环境变量管理](#22-环境变量管理)
  - [2.3 标准流](#23-标准流)
  - [2.4 进程退出与事件](#24-进程退出与事件)
  - [2.5 信号处理](#25-信号处理)
  - [2.6 process.nextTick 优先级回顾](#26-processnexttick-优先级回顾)
- [三、子进程 child_process 模块](#三子进程-child_process-模块)
  - [3.1 四种方法对比](#31-四种方法对比)
  - [3.2 spawn：流式执行](#32-spawn流式执行)
  - [3.3 exec：缓冲执行](#33-exec缓冲执行)
  - [3.4 execFile：不启动 shell](#34-execfile不启动-shell)
  - [3.5 fork：Node 子进程与 IPC](#35-forknode-子进程与-ipc)
  - [3.6 stdio 选项详解](#36-stdio-选项详解)
  - [3.7 子进程常用选项](#37-子进程常用选项)
- [四、父子进程通信](#四父子进程通信)
- [五、实用场景](#五实用场景)
- [六、安全注意事项](#六安全注意事项)
- [七、worker_threads 模块速览](#七worker_threads-模块速览)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说出 `process.env`、`process.argv`、`process.pid`、`process.cwd`、`process.memoryUsage` 等核心属性的含义与典型用途。
2. 解释为什么生产环境必须用环境变量管理配置，而非硬编码；能用 `dotenv` 加载 `.env`，用 `cross-env` 跨平台设置 `NODE_ENV`。
3. 区分 `process.stdin/stdout/stderr` 三条标准流，知道它们与 `console` 的关系。
4. 准确说明 `process.exit(code)`、`exit` 事件、`beforeExit` 事件三者的差异，并理解“优雅退出”的含义。
5. 用 `process.on('SIGINT')` 处理 Ctrl+C，实现“收到信号后清理资源再退出”的优雅关闭模式。
6. 对比 `exec` / `execFile` / `spawn` / `fork` 四种创建子进程方法的差异，能根据场景选择正确的方法。
7. 用 `spawn` 流式读取子进程的 `stdout` / `stderr`，理解 `stdio` 各选项（`pipe` / `inherit` / `ignore` / `null`）的行为。
8. 用 `fork` 建立父子进程的 IPC 通道，通过 `send` / `on('message')` 双向通信，并知道何时 `disconnect`。
9. 识别命令注入风险，知道为什么“拼接用户输入到 `exec`”是危险动作，能改用 `execFile` / `spawn` + 参数数组规避。
10. 了解 `worker_threads` 与 `child_process` 的本质差异与适用场景，为后续 AI 推理优化铺垫。

---

## 二、理论知识讲解

### 2.1 process 对象核心属性

`process` 是 Node.js 的全局对象（无需 `require`），代表**当前 Node 进程本身**。它同时是 `EventEmitter` 的实例，可监听 `exit`、`SIGINT` 等事件。

下表汇总最常用的属性：

| 属性 | 类型 | 说明 | 典型用途 |
|------|------|------|----------|
| `process.env` | object | 环境变量键值对（启动时从 OS 继承） | 读取 `NODE_ENV`、`PORT`、密钥 |
| `process.argv` | string[] | 命令行参数数组，前两项是 `node` 路径与脚本路径 | 解析自定义 CLI 参数 |
| `process.arch` | string | CPU 架构，如 `'x64'`、`'arm64'` | 加载原生模块时判断 |
| `process.platform` | string | 操作系统平台，如 `'win32'`、`'linux'`、`'darwin'` | 跨平台兼容分支 |
| `process.versions` | object | Node 与各依赖（V8、OpenSSL、zlib…）版本 | 兼容性诊断、上报 |
| `process.pid` | number | 当前进程 ID | 写日志、`kill` 自身、PM2 识别 |
| `process.ppid` | number | 父进程 ID | 调试进程关系 |
| `process.title` | string | 进程名（`ps` 中显示的标题） | 生产环境标识不同 worker |
| `process.cwd()` | method | 当前工作目录 | 解析相对路径 |
| `process.uptime()` | method | 进程运行秒数 | 健康检查、监控 |
| `process.memoryUsage()` | method | 内存占用快照（`rss`/`heapTotal`/`heapUsed`/`external`/`arrayBuffers`） | 内存泄漏排查 |
| `process.cpuUsage([prev])` | method | CPU 时间（`user`/`system`，微秒） | 性能测量 |
| `process.version` | string | Node 版本字符串，如 `v20.11.0` | 启动日志 |

> 重点记忆：`argv[0]` 是 node 可执行文件路径，`argv[1]` 是入口脚本路径，**自定义参数从 `argv[2]` 开始**。这就是为什么很多 CLI 工具从 `process.argv.slice(2)` 起解析。

`memoryUsage()` 返回值含义：

| 字段 | 含义 |
|------|------|
| `rss` | Resident Set Size，常驻物理内存（含 C++ 对象、Buffer） |
| `heapTotal` | V8 已申请的堆大小 |
| `heapUsed` | V8 实际使用的堆大小 |
| `external` | V8 管理、但由 C++ 分配的内存（如 Buffer 内容） |
| `arrayBuffers` | 专属于 `ArrayBuffer` / `SharedArrayBuffer` 的内存 |

AI 场景下，加载模型权重常用 `Buffer` 或 `Float32Array`，会让 `external` / `arrayBuffers` 暴涨——这是排查“进程内存爆了但 `heapUsed` 看起来正常”的关键线索。

### 2.2 环境变量管理

#### ① 读取环境变量

`process.env` 是一个对象，所有键都是字符串（OS 不区分类型），未设置时为 `undefined`：

```js
const port = process.env.PORT || 3000;
const nodeEnv = process.env.NODE_ENV || 'development';
const apiKey = process.env.OPENAI_API_KEY;
```

> 注意：`process.env.PORT = 0` 这样的“假值”也会被 `||` 误判，生产代码常用 `process.env.PORT ?? 3000`（`??` 只在 `null`/`undefined` 时回退）。

#### ② 为什么生产用环境变量而非硬编码

| 维度 | 硬编码 | 环境变量 |
|------|--------|----------|
| 多环境切换 | 改代码、重新打包 | 改环境变量、重启进程 |
| 密钥安全 | 进代码库=泄漏 | 密钥不落代码库，由 CI/CD 或运维注入 |
| 容器化 | 一份镜像一种代码 | 一份镜像多环境，符合 12-Factor App |
| 团队协作 | 配置冲突频繁 | `.env` 本地化、`.env.example` 共享 |
| 审计 | 难以审计 | 集中化密钥管理（KMS、Vault） |

> 这是 [12-Factor App](https://12factor.net/config) 的核心原则之一：**Config 应与 Code 严格分离**。

#### ③ dotenv 与 .env 文件

`dotenv` 把项目根目录下的 `.env` 文件中的键值对加载到 `process.env`：

```bash
npm install dotenv
```

`.env` 文件（**切勿提交到 git**）：

```
PORT=3000
NODE_ENV=development
OPENAI_API_KEY=sk-xxxxx
```

```js
// 入口最早一行
require('dotenv').config();

console.log(process.env.PORT);             // '3000'
console.log(process.env.OPENAI_API_KEY);   // 'sk-xxxxx'
```

工程实践：
- 把 `.env` 加入 `.gitignore`。
- 提交一份 `.env.example`，列出键名但留空值，供新成员参考。
- 区分 `.env`、`.env.test`、`.env.production`，配合 `dotenv-cli` 加载。

#### ④ NODE_ENV 的特殊地位

`NODE_ENV` 不是普通环境变量——**Express、React、Vue 等框架会显式读取它**：

- `NODE_ENV=production`：Express 关闭详细错误、缓存视图、跳过冗余日志；前端构建工具开启压缩、Tree-shaking。
- `NODE_ENV=development`：开启 sourcemap、热更新、详细日志。

> 一个高频坑：在 `NODE_ENV=production` 下 `npm install` 会跳过 `devDependencies`，CI 部署时如果忘了设置可能装不全依赖。

#### ⑤ cross-env 跨平台设置

在 Windows 下，`set NODE_ENV=production && node app.js` 的写法在 Linux/macOS 不可用；反之 `NODE_ENV=production node app.js` 在 Windows cmd 也不可用。`cross-env` 解决这一分裂：

```bash
npm install --save-dev cross-env
```

```json
{
  "scripts": {
    "start": "cross-env NODE_ENV=production node app.js",
    "dev": "cross-env NODE_ENV=development nodemon app.js"
  }
}
```

这样同一份 `package.json` 在 Windows / macOS / Linux 行为一致。

### 2.3 标准流

每个进程都有三条标准流，Node 在 `process` 上直接暴露：

| 流 | 方向 | 类型 | 说明 |
|----|------|------|------|
| `process.stdin` | 进程 ← 终端 | Readable（已暂停） | 读取用户输入 |
| `process.stdout` | 进程 → 终端 | Writable | `console.log` 默认写到这里 |
| `process.stderr` | 进程 → 终端 | Writable | `console.error` 默认写到这里 |

```js
// 监听标准输入（先 resume）
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  console.log('你输入了：', chunk.trim());
});
```

`stdout` 与 `stderr` 的区别：
- 重定向时分别捕获：`node app.js > out.log 2> err.log`（`2>` 即 stderr）。
- `console.log` 走 stdout，`console.warn` / `console.error` 走 stderr。
- 管道场景下，stdout 经常被下游消费（如 `node gen.js | consumer`），调试日志应输出到 stderr，避免污染管道。

### 2.4 进程退出与事件

#### ① process.exit(code)

立即同步终止进程，`code` 作为退出码（0=成功，非 0=失败）。`process.exit(1)` 之后任何代码都不再执行，**已挂起的异步任务也会被丢弃**。

```js
if (!process.env.API_KEY) {
  console.error('缺少 API_KEY');
  process.exit(1); // 非零退出码，shell 脚本据此判断失败
}
```

> 不要在正常流程里随手 `process.exit(0)`——会让尚未 flush 的日志、未完成的写文件操作半途而废。让事件循环自然清空才是最安全的退出。

#### ② exit 事件

进程即将退出（已无法再安排新异步任务）时同步触发：

```js
process.on('exit', (code) => {
  console.log(`进程退出，码=${code}`);
  // 这里只能做同步清理！异步操作不会执行
});
```

#### ③ beforeExit 事件

事件循环“本应退出”（没有更多任务）时触发。**可以在此安排新的异步任务**，Node 会重新进入事件循环：

```js
process.on('beforeExit', (code) => {
  console.log('事件循环空了，准备退出');
  // 可以在此 enqueue 新任务
});
```

| 事件 | 触发时机 | 能否安排异步 | 触发次数 |
|------|----------|--------------|----------|
| `beforeExit` | 事件循环为空（自然结束） | **可以** | 多次（每次重新空了都触发） |
| `exit` | 进程即将真正退出 | **不能**（同步清理） | 一次 |
| `process.exit()` | 主动调用 | — | — |

> 关键差异：`process.exit()` **不会**触发 `beforeExit`，但会触发 `exit`。也就是说，主动退出时 `beforeExit` 回调不会执行。

### 2.5 信号处理

POSIX 系统中，进程可接收信号。Node 把常见信号暴露为 `process` 上的事件：

| 信号 | 触发场景 | 默认行为 | 典型自定义处理 |
|------|----------|----------|----------------|
| `SIGINT` | Ctrl+C | 立即退出（码 130） | 优雅关闭：关 HTTP 服务、flush 日志、清理子进程 |
| `SIGTERM` | `kill <pid>`、容器停止 | 立即退出（码 143） | 同上，Docker/K8s 停容器时发此信号 |
| `SIGHUP` | 终端关闭 | 退出 | 通常用于“重新加载配置”而非退出 |
| `SIGKILL` (`kill -9`) | 强杀 | 立即退出 | **无法捕获**，进程必死 |

优雅退出模板：

```js
let shuttingDown = false;

async function shutdown(signal) {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log(`\n收到 ${signal}，开始清理...`);

  // 1. 停止接受新请求（HTTP server.close）
  // 2. 等待进行中的请求完成（可设超时）
  // 3. 关闭数据库连接、flush 日志
  // 4. 杀掉所有子进程
  await new Promise((r) => setTimeout(r, 200));
  console.log('清理完成，退出');
  process.exit(0);
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
```

> Windows 上 `SIGTERM` / `SIGHUP` 的语义不完全一致，但 `SIGINT`（Ctrl+C）行为可靠。生产环境（Linux 容器）才是这套机制的主战场。

### 2.6 process.nextTick 优先级回顾

`process.nextTick(fn)` 把 `fn` 放入“微任务队列”中的**最高优先级队列**——它会在当前同步代码结束后、**任何 I/O 或定时器之前**执行：

```js
Promise.resolve().then(() => console.log('promise'));
process.nextTick(() => console.log('nextTick'));
setTimeout(() => console.log('timeout'), 0);

// 输出顺序：nextTick → promise → timeout
```

| 队列 | 优先级 | 典型 API |
|------|--------|----------|
| nextTick 队列 | 最高（微任务） | `process.nextTick` |
| Promise 微任务 | 次高（微任务） | `Promise.then`、`queueMicrotask` |
| 定时器 | 宏任务 | `setTimeout`、`setInterval` |
| I/O 回调 | 宏任务 | `fs`、`net` 回调 |
| setImmediate | 宏任务（Check 阶段） | `setImmediate` |

> 陷阱：递归调用 `process.nextTick` 会饿死 I/O——永远轮不到事件循环执行 I/O 回调。`process.nextTick` 应只用于“保证回调在当前操作后立即执行”，不要用于长流程。

---

## 三、子进程 child_process 模块

Node 单线程不适合 CPU 密集任务，但通过 `child_process` 可以“开外挂”：

- 调用外部命令（`git`、`ffmpeg`、`python`、`puppeteer`）。
- 把 CPU 密集计算外包给子进程，主线程继续服务请求。
- 多进程并行加速任务（如批量推理）。

### 3.1 四种方法对比

| 方法 | 返回值 | 启动 shell | 数据传递方式 | IPC 通道 | 典型用途 |
|------|--------|-----------|--------------|----------|----------|
| `exec(command, opts, cb)` | ChildProcess + 缓冲到 cb | **是** | 一次性回调（`stdout`/`stderr` 缓冲） | 否 | 跑一条 shell 命令，输出不大 |
| `execFile(file, args, opts, cb)` | ChildProcess + 缓冲到 cb | 否 | 一次性回调 | 否 | 安全地跑可执行文件，避免 shell 注入 |
| `spawn(cmd, args, opts)` | ChildProcess（流） | 否（除非 `shell:true`） | **流**（`child.stdout`/`stderr` 是 Readable） | 否（可手动开） | 大数据量、长时间任务、流式处理 |
| `spawn` 的 `fork` 特例 | ChildProcess | 否 | 流 + **IPC** | **是**（自动） | Node 子进程、父子双向通信 |

一句话记忆：
- 输出小、要 shell 管道符 → `exec`
- 输出小、不要 shell、要安全 → `execFile`
- 输出大、要流式 → `spawn`
- 子进程是 Node、要 IPC → `fork`

### 3.2 spawn：流式执行

`spawn` 是最底层的方法：返回 `ChildProcess`，其 `stdout` / `stderr` 是真正的 `Readable` 流，可逐块消费，**没有 `maxBuffer` 限制**。

```js
const { spawn } = require('child_process');

// 跨平台兼容：Windows 用 dir，Linux/macOS 用 ls
const isWin = process.platform === 'win32';
const child = spawn(isWin ? 'cmd' : 'ls', isWin ? ['/c', 'dir'] : ['-la']);

child.stdout.on('data', (chunk) => {
  process.stdout.write(`[stdout] ${chunk}`);
});
child.stderr.on('data', (chunk) => {
  process.stderr.write(`[stderr] ${chunk}`);
});
child.on('close', (code) => {
  console.log(`子进程退出，码=${code}`);
});
```

特点：
- **流式**：适合输出可能很大（如视频转码、模型推理日志）。
- **不缓冲**：你必须自己 `on('data')` 收集，或用 `pipeline` 接到 `fs.createWriteStream`。
- **不启动 shell**（默认）：参数直接传给 `execve`，无 shell 解析风险。
- `shell: true` 可强制走 shell（**会带来命令注入风险**，见第六节）。

### 3.3 exec：缓冲执行

`exec` 用 shell 执行整条命令字符串，等子进程结束后一次性回调 `(err, stdout, stderr)`：

```js
const { exec } = require('child_process');
exec('node --version', (err, stdout, stderr) => {
  if (err) { console.error(err); return; }
  console.log('Node 版本：', stdout.trim());
});
```

特点：
- **回调式**：拿到的 `stdout`/`stderr` 是拼接好的字符串。
- **maxBuffer 限制**：默认 `1MB`（`1024 * 1024` 字节），超出会 kill 子进程并返回错误。
- **走 shell**：支持管道符 `|`、重定向 `>`、通配符 `*` 等便利，但**也有命令注入风险**。

何时用：
- 命令输出确定不大（如 `git rev-parse`、`node --version`）。
- 需要利用 shell 语法（管道、通配）。

何时**不用**：
- 命令的某段来自用户输入 → 改用 `execFile` / `spawn` + 参数数组。
- 输出可能 > 1MB → 改用 `spawn`。

### 3.4 execFile：不启动 shell

`execFile` 行为与 `exec` 一致（也是缓冲到回调），但**不启动 shell**——直接调用可执行文件 + 参数数组。这让它更安全也更高效：

```js
const { execFile } = require('child_process');

// 安全：参数是数组，不会被 shell 重新解析
execFile('node', ['--version'], (err, stdout) => {
  console.log(stdout.trim());
});
```

差异要点：

| 维度 | exec | execFile |
|------|------|----------|
| 是否启动 shell | 是 | 否 |
| 命令字符串 | 整条 shell 字符串 | 文件名 + 参数数组 |
| 支持管道符 `\|` | 是 | 否 |
| 注入风险 | 高 | 低 |
| 性能 | 略低（启动 shell） | 略高 |
| Windows | 用 `cmd.exe` | 直接 `CreateProcess` |

> 经验法则：**用户输入参与命令时，永远用 `execFile` 或 `spawn`，不要用 `exec`**。

### 3.5 fork：Node 子进程与 IPC

`fork` 是 `spawn` 的特例，专门用于**启动一个 Node 子进程**，并自动建立 IPC 通道：

```js
const { fork } = require('child_process');
const child = fork('./worker.js');

child.send({ task: 'compute', n: 40 });
child.on('message', (msg) => {
  console.log('子进程回信：', msg);
});
```

`fork('./worker.js')` 等价于 `spawn(process.execPath, ['./worker.js'], { stdio: ['inherit', 'inherit', 'inherit', 'ipc'] })`——把 `process.execPath`（当前 Node 可执行文件）作为命令，自动启用 IPC。

特点：
- 子进程必须是 Node 脚本。
- 自动建立 IPC，父子用 `send` / `on('message')` 通信。
- 适合“把 CPU 密集任务交给另一个 Node 进程”的经典模式。

### 3.6 stdio 选项详解

`spawn` / `fork` 的 `stdio` 选项控制子进程三条流的去向：

```js
const child = spawn('node', ['script.js'], {
  stdio: ['pipe', 'pipe', 'pipe'] // stdin, stdout, stderr
});
```

| 取值 | 含义 | 子进程视角 |
|------|------|------------|
| `'pipe'` | 在父进程创建管道，`child.stdout` 等 | 是 Readable/Writable 流 |
| `'inherit'` | 共享父进程的标准流 | 直接打到当前终端 |
| `'ignore'` | 相当于 `/dev/null` | 写入被丢弃，读取立即 EOF |
| `'null'` | 等价于 `'ignore'`（旧称） | 同上 |
| 数字 fd | 直接复用父进程已打开的 fd | 复用对应文件描述符 |
| `Stream` | 用已有流对象 | 转接到该流 |

常用组合：

```js
// 完全静默
spawn('node', ['script.js'], { stdio: 'ignore' });

// 让子进程直接继承终端（交互式）
spawn('node', ['script.js'], { stdio: 'inherit' });

// fork 默认：stdin/stdout/stderr 继承 + ipc
fork('./worker.js');

// 仅打开 IPC，不显示输出（fork 静默模式）
fork('./worker.js', { silent: true });
```

### 3.7 子进程常用选项

`spawn` / `exec` / `execFile` / `fork` 共用一组 `options`：

| 选项 | 说明 | 默认 |
|------|------|------|
| `cwd` | 子进程工作目录 | 父进程的 `cwd` |
| `env` | 子进程环境变量 | 父进程 `process.env` |
| `timeout` | 超时毫秒数，超时发 `killSignal` | 不超时 |
| `killSignal` | 超时/主动 kill 时发送的信号 | `'SIGTERM'` |
| `maxBuffer` | （exec/execFile）stdout/stderr 最大字节数 | `1024 * 1024` |
| `windowsHide` | 隐藏 Windows 子进程窗口 | `false` |
| `shell` | （spawn）是否经 shell 执行 | `false` |
| `uid` / `gid` | （POSIX）切换用户/组 | — |
| `detached` | （POSIX）让子进程独立成会话，父死后继续运行 | `false` |

```js
spawn('python', ['infer.py'], {
  cwd: '/app/models',
  env: { ...process.env, CUDA_VISIBLE_DEVICES: '0' },
  timeout: 30_000,           // 30 秒超时
  killSignal: 'SIGKILL',     // 超时强杀
  windowsHide: true
});
```

---

## 四、父子进程通信

只有 `fork`（或 `spawn` 时显式开启 `stdio: 'ipc'`）才能用内置 IPC。通信通过 `child.send(msg)` 与 `process.on('message', cb)` / `process.send(msg)` 完成。

### 4.1 单向：父 → 子 → 父

父进程（`parent.js`）：

```js
const { fork } = require('child_process');
const child = fork('./worker.js');

child.send({ type: 'task', payload: 40 });

child.on('message', (msg) => {
  console.log('收到子进程结果：', msg);
  child.disconnect(); // 主动断开 IPC
});

child.on('exit', (code) => {
  console.log('子进程退出，码=', code);
});
```

子进程（`worker.js`）：

```js
process.on('message', async (msg) => {
  if (msg.type === 'task') {
    const result = heavyCompute(msg.payload);
    process.send({ type: 'done', result });
  }
});

function heavyCompute(n) {
  return fibonacci(n);
}
```

### 4.2 双向通信

IPC 是**全双工**的——父子可随时互发消息。可以构建“任务队列”模式：

```js
// 父进程：分发多个任务，收集结果
const tasks = [10, 20, 30, 40];
const child = fork('./worker.js');
let pending = tasks.length;

tasks.forEach((n) => child.send({ type: 'compute', n }));

child.on('message', (msg) => {
  console.log(`结果：fib(${msg.n}) = ${msg.result}`);
  if (--pending === 0) child.send({ type: 'shutdown' });
});

child.on('exit', () => console.log('子进程结束'));
```

```js
// 子进程：循环接收任务，直到收到 shutdown
process.on('message', (msg) => {
  if (msg.type === 'shutdown') {
    process.exit(0);
  }
  if (msg.type === 'compute') {
    process.send({ n: msg.n, result: fibonacci(msg.n) });
  }
});
```

### 4.3 disconnect

- 父进程调 `child.disconnect()` 或子进程调 `process.disconnect()`，IPC 通道关闭，触发双方的 `disconnect` 事件。
- IPC 关闭后，子进程若没有其他事件循环任务，会自然退出；也可主动 `process.exit()`。
- **重要**：`disconnect` 是“关通信”，不是“杀进程”。需要终止时用 `child.kill(signal)` 或 `child.send({ type: 'shutdown' })` 让子进程自退。

```js
child.on('disconnect', () => {
  console.log('IPC 通道已关闭');
});
```

> 消息序列化走 JSON，**无法传递函数、循环引用、Class 实例**，只能传可结构化克隆的纯数据。

---

## 五、实用场景

### 5.1 调用 Python 脚本做 AI 模型推理

Node 不擅长跑深度学习模型，常见做法是 Node 编排 + Python 推理：

```js
const { spawn } = require('child_process');

function runInference(imagePath) {
  // spawn python script.py <imagePath>
  const child = spawn('python', ['infer.py', imagePath], {
    timeout: 30_000
  });

  let stdout = '';
  let stderr = '';
  child.stdout.on('data', (c) => (stdout += c));
  child.stderr.on('data', (c) => (stderr += c));

  return new Promise((resolve, reject) => {
    child.on('close', (code) => {
      if (code === 0) resolve(JSON.parse(stdout));
      else reject(new Error(`推理失败：${stderr}`));
    });
    child.on('error', reject);
  });
}
```

完整示例见 `Code/call-python.js`，把 `python` 换成 `ffmpeg` / `puppeteer` 命令即可复用同样模板。

### 5.2 并行任务：Promise.all 包多个 spawn

```js
const images = ['a.jpg', 'b.jpg', 'c.jpg'];
const results = await Promise.all(images.map(runInference));
console.log(results);
```

注意：并发数过多会撑爆 CPU/内存，建议用 `p-limit` 等并发控制库。

### 5.3 CPU 密集任务外包给子进程

主线程跑 HTTP 服务时，遇到耗时计算（如 50 位斐波那契、图像处理）应交给子进程或 worker_threads，否则会**阻塞事件循环**导致所有请求超时：

```js
const { fork } = require('child_process');
const worker = fork('./heavy-worker.js');

app.get('/compute', (req, res) => {
  worker.send({ n: Number(req.query.n) });
  worker.once('message', (msg) => res.json(msg));
});
```

### 5.4 调用 ffmpeg / puppeteer

```js
// 视频转码，输出流式日志
spawn('ffmpeg', ['-i', 'in.mp4', '-vcodec', 'h264', 'out.mp4']);

// 用 puppeteer 做网页截图（headless 浏览器是外部进程）
execFile('node', ['screenshot.js', url, outFile], { timeout: 60_000 });
```

---

## 六、安全注意事项

### 6.1 命令注入风险

`exec`（以及 `spawn` 配合 `shell: true`）会把命令字符串交给 shell 解析，**用户输入中的 shell 元字符会被执行**：

```js
// ❌ 危险！
const { exec } = require('child_process');
const userInput = 'foo; rm -rf /';  // 假装这是用户提交的文件名
exec(`wc -l ${userInput}`, (err, stdout) => {
  // 实际执行：wc -l foo; rm -rf /
});
```

更隐蔽的注入：
- `$(cmd)` 命令替换。
- `` `cmd` `` 反引号命令替换。
- `&&` / `||` 命令串联。
- `> /etc/passwd` 重定向。

### 6.2 正确做法：用参数数组

`execFile` / `spawn` 默认不走 shell，参数以**数组**形式传入，OS 层面就是 `argv`，**不会被重新解析**：

```js
// ✅ 安全
const { execFile } = require('child_process');
execFile('wc', ['-l', userInput], (err, stdout) => {
  // userInput 只作为单个参数，不会被解释为命令
});
```

即便 `userInput` 是 `'; rm -rf /'`，它也只是 `wc -l` 的第二个参数，被当成一个文件名。

### 6.3 shell: true 的风险

`spawn(cmd, args, { shell: true })` 会把 `cmd` 与 `args` 拼成字符串交给 shell，**注入风险等同于 `exec`**：

```js
// ❌ 危险：shell: true + 用户输入
spawn('wc', ['-l', userInput], { shell: true });
```

何时仍需 `shell: true`：
- 命令依赖 shell 内建（如 `dir` 是 cmd 内建）。
- 需要管道符、通配符等 shell 语法。
- 此时应**严格校验/转义**用户输入，或干脆不让用户输入参与命令构造。

### 6.4 安全清单

| 规则 | 做法 |
|------|------|
| 用户输入参与命令 | 一律用 `execFile` / `spawn` + 参数数组 |
| 需要校验 | 白名单正则校验，不通过即拒绝 |
| 文件名 | 用 `path.resolve` 锁定目录，禁止 `..` |
| 密钥/参数 | 走 `env`，不要拼到命令行（命令行可见于 `ps`） |
| 永远不要 `eval` 用户输入 | 这是 JS 层面的注入 |

---

## 七、worker_threads 模块速览

`child_process` 创建的是**新进程**（独立 V8 实例、独立内存），开销大但隔离好。`worker_threads` 创建的是**新线程**——同一进程内多个 V8 worker，共享 `SharedArrayBuffer`，开销小，是 Node 真正的“多线程”。

### 7.1 基本用法

主线程：

```js
const { Worker } = require('worker_threads');

const worker = new Worker('./heavy-worker.js', { workerData: { n: 40 } });
worker.on('message', (msg) => console.log('结果：', msg));
worker.on('error', (err) => console.error(err));
worker.on('exit', (code) => console.log('worker 退出', code));
```

worker 线程（`heavy-worker.js`）：

```js
const { parentPort, workerData } = require('worker_threads');
const result = fibonacci(workerData.n);
parentPort.postMessage(result);
```

### 7.2 SharedArrayBuffer

多个 worker 可共享一段内存，**零拷贝**传递大数据：

```js
const sab = new SharedArrayBuffer(4 * 1024 * 1024); // 4MB
const view = new Float32Array(sab);
// 把 sab 传给 worker，worker 直接读写同一段内存
```

AI 场景下，可以把模型权重放进 `SharedArrayBuffer`，多个推理 worker 共享，避免每个进程都加载一份。

### 7.3 与 child_process 对比

| 维度 | child_process（fork/spawn） | worker_threads |
|------|------------------------------|----------------|
| 本质 | 新进程 | 新线程（同进程） |
| 内存 | 独立 | 可通过 `SharedArrayBuffer` 共享 |
| 启动开销 | 大（MB 级） | 小（KB 级） |
| 通信开销 | JSON 序列化（IPC） | `postMessage` 或共享内存 |
| 隔离 | 强（一个崩不影响另一个） | 弱（worker 崩可能拖垮进程） |
| 适用 | 调用外部命令、跑异构语言 | CPU 密集计算（同语言内） |
| 多核利用 | 是 | 是 |
| 调试难度 | 中 | 高（线程安全、竞态） |
| AI 场景 | 调 Python/ffmpeg | 模型预处理、张量计算并行 |

经验法则：
- 调外部命令 / 异构语言 → `child_process`。
- 纯 Node 内的 CPU 密集（如纯 JS 实现的矩阵运算、大 JSON 解析）→ `worker_threads`。
- 既要并行又要隔离 → 多进程（如 PM2 cluster）。
- AI 推理本身一般交给 Python/ONNX/CUDA，Node 层只用 `child_process` 编排，少数预处理用 `worker_threads`。

---

## 八、关键知识点总结

1. **process 是全局对象**，无需 `require`；代表当前进程，同时是 `EventEmitter`。
2. **核心属性**：`env`（配置）、`argv`（CLI 参数从 2 起）、`pid`、`platform`、`memoryUsage`（看 `rss` 与 `external` 排查内存）、`cwd`。
3. **环境变量是配置的最佳载体**：用 `dotenv` 加载 `.env`，用 `cross-env` 跨平台设置；`.env` 必须进 `.gitignore`，提交 `.env.example`。
4. **三条标准流**：`stdin`（Readable）、`stdout`/`stderr`（Writable）；`console.log` 走 stdout、`console.error` 走 stderr；调试日志走 stderr 避免污染管道。
5. **退出三件套**：`process.exit(code)` 主动退出（慎用，会丢异步）；`exit` 事件（同步清理）；`beforeExit` 事件（可安排新异步，但 `process.exit()` 不触发它）。
6. **信号处理**：`SIGINT`（Ctrl+C）、`SIGTERM`（kill/容器停止）可捕获以实现优雅退出；`SIGKILL` 无法捕获。
7. **process.nextTick 优先级最高**，会饿死 I/O，慎用；递归 `nextTick` 是经典死锁。
8. **子进程四方法**：`exec`（shell+缓冲，小输出）、`execFile`（无 shell+缓冲，安全）、`spawn`（无 shell+流式，大输出）、`fork`（Node 子进程+IPC）。
9. **stdio 选项**：`pipe`（默认，父端拿流）、`inherit`（共享父流）、`ignore`（丢弃）、`ipc`（fork 自动开）。
10. **父子 IPC**：仅 `fork` 自动支持；`child.send` / `process.on('message')`；消息走 JSON，不能传函数；`disconnect` 只断通信不杀进程。
11. **命令注入是高频安全坑**：用户输入参与命令时一律用 `execFile` / `spawn` + 参数数组，避免 `exec` 与 `shell: true`。
12. **worker_threads 是真多线程**：开销小、可共享 `SharedArrayBuffer`，适合纯 Node 内 CPU 密集；`child_process` 适合调外部命令与异构语言；AI 场景多为“Node 编排 + Python 推理”的组合。

---

## 九、实战练习

> 以下练习在 `Code/` 目录基础上扩展，建议独立完成后再对照本篇结论自查。

### 练习一：实现一个支持优雅退出的"定时任务守护进程"

**目标**：写一个 `daemon.js`，每秒打印一次“心跳 i=N”，收到 `SIGINT`（Ctrl+C）或 `SIGTERM` 时停止接收新任务，等当前任务完成后打印“已优雅退出”再 `process.exit(0)`。

**要求**：

1. 用 `setInterval` 每秒打印心跳；用一个 `state` 变量记录是否正在 shutdown。
2. 监听 `SIGINT` 与 `SIGTERM`；收到后取消 `setInterval`，等 500ms（模拟清理）后退出。
3. 再次 Ctrl+C 时直接 `process.exit(1)`（用户不耐烦了）。
4. 思考：为什么不能在信号回调里直接 `process.exit(0)`？

**考察点**：信号处理、状态机、优雅退出模式、`exit` 与 `beforeExit` 的差异。

### 练习二：用 spawn + Promise 封装一个"并发受限"的命令执行器

**目标**：实现 `runTasks(tasks, concurrency)`，`tasks` 是字符串数组（如 `['python infer.py a.jpg', 'python infer.py b.jpg', ...]`），`concurrency` 限制并发数。

**要求**：

1. 每个 task 用 `spawn` 执行（不要用 `exec`，便于流式）。
2. 返回 `Promise<{task, code, stdout, stderr}>[]`。
3. 自己实现一个简易并发池（不要装第三方库），用计数器控制并发。
4. 加 `timeout` 选项，超时 `child.kill('SIGKILL')`。

**考察点**：`spawn` 流式收集、`child.kill`、并发控制、`Promise` 组合。

### 练习三：fork + IPC 模拟"模型推理任务队列"

**目标**：构建一个简易“推理服务”——父进程接收 N 个推理请求，分发给 2 个 fork 子进程并行处理，子进程模拟耗时计算后回传结果。

**要求**：

1. `server.js` fork 出 2 个 `inference-worker.js`。
2. 模拟 10 个推理任务（如 `fib(35)` 不同输入），用“轮询”或“空闲 worker”策略分发给 2 个 worker。
3. 父进程收集所有结果后打印总耗时。
4. 对比：单进程串行跑 10 个 `fib(35)` vs 2 进程并行，耗时是否约减半？
5. 思考：为什么 4 个 worker 不一定让耗时再减半？（CPU 核数限制）

**考察点**：`fork` + IPC 双向通信、任务分发策略、并行性能测量、CPU 密集任务的多进程加速效果。

---

> 完成本篇后，你已经掌握 Node 进程自身的控制能力与“跳出单进程”的两种方式（子进程 / 多线程）。下一篇将进入**网络编程进阶**或**Node 与数据库集成**主题，逐步把 AI 推理编排、文件处理、任务队列等能力组合成一个可上线的 AI 后端。
