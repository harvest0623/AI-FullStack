# Day01 - 初识 Node.js 与运行环境

> 本章节我们将从「Node.js 到底是什么」出发，逐步建立对运行环境、事件模型、工程化工具链的完整认知，并为后续搭建 BFF、数据预处理、模型服务包装等 AI 后端能力打下基础。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 Node.js 是什么](#21-nodejs-是什么)
  - [2.2 Node.js 与浏览器 JS 的区别](#22-nodejs-与浏览器-js-的区别)
  - [2.3 V8 引擎与 libuv 简介](#23-v8-引擎与-libuv-简介)
  - [2.4 事件驱动与非阻塞 I/O](#24-事件驱动与非阻塞-io)
  - [2.5 单线程模型与多线程误区](#25-单线程模型与多线程误区)
  - [2.6 适用场景：I/O 密集型 vs CPU 密集型](#26-适用场景io-密集型-vs-cpu-密集型)
  - [2.7 对 AI 全栈开发的意义](#27-对-ai-全栈开发的意义)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 REPL 交互式环境](#31-repl-交互式环境)
  - [3.2 Node.js 版本管理（nvm / nvm-windows）](#32-nodejs-版本管理nvm--nvm-windows)
  - [3.3 运行脚本的方式](#33-运行脚本的方式)
  - [3.4 global 全局对象](#34-global-全局对象)
  - [3.5 process 与 console 基础](#35-process-与-console-基础)
- [四、环境搭建步骤](#四环境搭建步骤)
- [五、关键知识点总结](#五关键知识点总结)
- [六、实战练习](#六实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **准确描述 Node.js 的本质**：理解它并非「服务端的 JavaScript 语言」，而是「基于 V8 引擎的 JavaScript 运行时」，能区分「语言」与「运行时」两个概念。
2. **辨析 Node.js 与浏览器环境的差异**：从运行宿主、可用 API、全局对象三个维度说清楚二者的边界，避免把 `window`、`document` 等 DOM API 带入 Node.js 思维。
3. **理解事件驱动与非阻塞 I/O 的工作机制**：能用自己的话讲清楚 Event Loop、libuv 线程池如何协作处理高并发 I/O，并指出「单线程」的真实含义。
4. **独立完成 Node.js 开发环境搭建**：使用 nvm 管理多版本 Node.js，验证安装结果，并配置好 IDE（VS Code）的开发与调试体验。
5. **编写并运行第一个 Node.js 脚本**：掌握 `node file.js` 运行、`process.argv` 读取参数、`console` 输出等最基础能力，为后续模块化与异步编程打基础。

---

## 二、理论知识

### 2.1 Node.js 是什么

Node.js 是一个**开源的、跨平台的 JavaScript 运行时（Runtime）**，它让 JavaScript 能够脱离浏览器，在操作系统层面直接运行。

它的核心组成可以简化为：

```
┌─────────────────────────────────────────┐
│              你的 JavaScript 代码         │
├─────────────────────────────────────────┤
│   Node.js 内置模块（fs / http / path…）  │
├─────────────────────────────────────────┤
│   V8 引擎（编译执行 JS）  +  libuv（事件循环 / I/O）│
├─────────────────────────────────────────┤
│           操作系统（Windows / Linux / macOS）      │
└─────────────────────────────────────────┘
```

关键要点：

- **运行时 ≠ 语言**：JavaScript 是语言（由 ECMAScript 规范定义），Node.js 是让这门语言在服务端跑起来的「运行环境」。
- **跨平台**：同一份 JS 代码可在 Windows、Linux、macOS 上运行，得益于 libuv 对不同操作系统 I/O 接口的抽象。
- **官方维护**：由 OpenJS Foundation 维护，长期支持版本（LTS）适合生产环境。

### 2.2 Node.js 与浏览器 JS 的区别

前端工程师最容易踩的坑，就是把浏览器的概念平移到 Node.js。二者差异可从三个维度对比：

| 维度 | 浏览器环境 | Node.js 环境 |
| --- | --- | --- |
| **运行宿主** | 浏览器进程（Chrome、Firefox 等） | 操作系统进程（通过 node 可执行文件启动） |
| **全局对象** | `window`、`document`、`navigator`、`location` | `global`、`process`、`Buffer`、`__dirname`、`__filename` |
| **DOM/BOM API** | 提供 `document.getElementById`、`fetch`、`localStorage` 等 | **没有 DOM**，但提供 `fs`、`http`、`net`、`child_process` 等系统级 API |
| **模块系统** | ES Modules（`import` / `export`）为主 | 既支持 CommonJS（`require` / `module.exports`），也支持 ES Modules |
| **网络能力** | 受同源策略限制，只能发 HTTP 请求 | 可直接创建 TCP/HTTP 服务器，无同源策略限制 |
| **文件系统** | 只能通过用户主动上传获取文件 | 可直接读写本地磁盘文件 |

一个典型误区：在 Node.js 中写 `document.querySelector` 会直接抛出 `ReferenceError`，因为 `document` 这个全局对象在 Node.js 中根本不存在。

### 2.3 V8 引擎与 libuv 简介

Node.js 的「左膀右臂」是两个核心组件：

**V8 引擎**（由 Google 开发）

- 职责：把 JavaScript 源码**编译成机器码**并执行，负责内存管理（垃圾回收）、JIT 即时编译。
- 特点：高性能，Chrome 浏览器也用它。Node.js 直接复用了 V8，因此你在浏览器里能用的 ES 语法（async/await、可选链、私有字段等）在 Node.js 里基本也能用。
- 局限：V8 本身是「单线程」执行 JS 的，且**不负责**网络、文件等 I/O 操作。

**libuv**（由 Node.js 团队开发）

- 职责：提供**跨平台的事件循环**与**异步 I/O 抽象层**，是 Node.js 非阻塞能力的真正来源。
- 组成：事件循环（Event Loop）+ 线程池（默认 4 个线程，可通过 `UV_THREADPOOL_SIZE` 调整）。
- 作用：当 JS 调用 `fs.readFile`、`dns.lookup` 等耗时 I/O 时，libuv 把实际工作交给线程池或操作系统异步接口，完成后再把回调推回事件循环，由 V8 继续执行 JS。

一句话总结：**V8 负责算，libuv 负责等**。二者协作让 Node.js 既能高效执行 JS，又能不阻塞地处理大量 I/O。

### 2.4 事件驱动与非阻塞 I/O

「事件驱动」与「非阻塞 I/O」是 Node.js 最核心的设计哲学，二者一体两面：

- **非阻塞 I/O**：当代码发起一个 I/O 操作（读文件、发网络请求、查数据库）时，**不会停下来等结果**，而是立即继续执行下一条语句。等 I/O 完成后，通过「事件」通知主线程执行回调。
- **事件驱动**：程序的执行流程由「事件」触发。事件循环不断轮询事件队列，有事件就执行对应的回调函数。

一个直观对比例子——读取文件并打印内容：

```js
// 阻塞式（伪代码，Node.js 中已不推荐同步阻塞写法用于生产）
const data = readFileSync('./data.txt'); // 主线程在这里「卡住」等待
console.log(data);
console.log('下一步'); // 必须等文件读完才执行

// 非阻塞式（Node.js 的典型写法）
readFile('./data.txt', (err, data) => {
  console.log(data); // 文件读完后再执行
});
console.log('下一步'); // 立即执行，不等文件
```

在非阻塞写法中，`'下一步'` 会**先**打印，文件内容**后**打印。这种「发起 I/O → 继续干别的 → I/O 完成回调」的模式，让单线程的 Node.js 也能扛住高并发请求。

### 2.5 单线程模型与多线程误区

这是最容易被误解的一点。

**误区**：「Node.js 是单线程的，所以它不能利用多核 CPU，性能差。」

**真相**：

1. **JS 代码确实在单线程中执行**：你的 `.js` 文件里所有的同步逻辑，都跑在唯一一个主线程上。这也是为什么一个死循环会让整个进程卡死。
2. **但 Node.js 进程并非只有一个线程**：libuv 维护一个线程池（默认 4 线程）处理文件 I/O、DNS 等操作；V8 自己也有 GC 线程、JIT 线程。
3. **多核利用需要 `cluster` 或 `worker_threads`**：要真正用满多核 CPU，可通过 `node:cluster` 启动多个进程，或用 `node:worker_threads` 启动工作线程。

记忆要点：

> 单线程指的是「JS 业务逻辑单线程」，而非「整个 Node.js 进程只有一个线程」。

### 2.6 适用场景：I/O 密集型 vs CPU 密集型

理解了上面的模型，就能判断 Node.js 适合做什么、不适合做什么。

**适合（I/O 密集型）** ✅

- Web API 服务、RESTful 接口、BFF 层
- 实时聊天、推送、协作应用（WebSocket）
- 网关、代理、API 聚合
- 数据库读写密集的业务

原因：I/O 操作会被 libuv 异步化，主线程不用等待，单线程也能处理大量并发连接。

**不适合（CPU 密集型）** ❌

- 大量数学计算（矩阵运算、图像处理、视频转码）
- 复杂的数据压缩、加密哈希（大文件）
- 长时间同步循环

原因：CPU 计算占用主线程，期间无法处理任何其他请求，会拖垮整个服务的响应能力。这类任务应交给 C/C++、Rust、Go，或在 Node.js 中通过 `worker_threads` 卸载到子线程。

### 2.7 对 AI 全栈开发的意义

作为前端工程师转向 AI 全栈，Node.js 是最顺滑的「后端入口」，因为它和前端共用一门语言。在 AI 工程中，Node.js 常扮演以下角色：

1. **BFF（Backend For Frontend）层**
   - 在前端与大模型/Python 推理服务之间做一层聚合：鉴权、限流、参数校验、响应裁剪。
   - 前端只和 Node.js BFF 通信，BFF 再并发调用多个下游服务（Python 模型服务、向量库、业务库）。

2. **数据预处理与 ETL**
   - 读取本地或 OSS 上的原始数据（CSV、JSON、日志），清洗、分块、转换格式后写入向量库或对象存储。
   - Node.js 的流（Stream）机制适合处理大文件，避免内存溢出。

3. **模型服务包装（Model Serving Wrapper）**
   - 把 Python 训练好的模型通过 HTTP/gRPC 暴露出来后，用 Node.js 做一层网关：处理鉴权、计费、日志、Prompt 模板管理、流式响应（SSE）转发。
   - 对接 OpenAI、通义千问等大模型 API 时，Node.js SDK 生态成熟。

4. **RAG（检索增强生成）后端**
   - 实现文档上传 → 切片 → 向量化 → 存入向量库 → 检索 → 拼接 Prompt → 调用 LLM 的完整链路。
   - 框架如 LangChain.js、LlamaIndex.TS 让这套流程用纯 JS/TS 即可完成，无需切换语言。

简言之：**Python 负责「训模型」，Node.js 负责「用模型」并连接前端**。掌握 Node.js，你就拥有了 AI 全栈中「连接层」的工程能力。

---

## 三、核心概念解析

### 3.1 REPL 交互式环境

REPL（Read-Eval-Print Loop）是一个交互式命令行环境，输入一行 JS 就立即执行并打印结果，适合做语法试验和快速验证。

启动方式：在终端输入

```bash
node
```

进入后可看到 `>` 提示符，直接输入表达式：

```js
> 1 + 2
3
> const name = 'AI'
undefined
> name.toUpperCase()
'AI'
> process.version
'v20.11.0'
```

常用快捷键：

- `Ctrl + C` 两次：退出 REPL
- `Ctrl + D`：退出 REPL
- `.help`：查看可用点命令
- `.exit`：退出
- `Tab` 键：自动补全

### 3.2 Node.js 版本管理（nvm / nvm-windows）

不同项目可能依赖不同 Node.js 版本，直接装一个固定版本会频繁冲突。**版本管理器**让你在同一台机器上安装多个版本并随时切换。

**nvm（macOS / Linux）**

- 通过 shell 脚本安装，管理 `~/.nvm` 目录下的多版本 Node。
- 常用命令：

```bash
nvm install 20          # 安装 Node.js 20 系列
nvm install --lts       # 安装最新 LTS 版本
nvm use 20              # 切换到 20 系列
nvm ls                  # 列出已安装版本
nvm alias default 20    # 设置默认版本
```

**nvm-windows（Windows）**

- 由于 Windows 没有 bash 环境，使用独立的 [nvm-windows](https://github.com/coreybutler/nvm-windows)（注意：与 macOS 版 nvm 是两个项目，命令基本兼容但实现不同）。
- 安装后命令同样为 `nvm install`、`nvm use`、`nvm list` 等。
- 建议先卸载已有的独立 Node.js，避免 PATH 冲突。

> 提示：版本号偶数为 LTS（长期支持，如 20、22），奇数为 Current（尝鲜版，如 21、23）。生产环境一律选 LTS。

### 3.3 运行脚本的方式

**方式一：直接运行**

```bash
node hello.js
```

最基础的方式，执行完即退出进程。

**方式二：带调试运行（--inspect）**

```bash
node --inspect hello.js
# 或在第一行断点暂停
node --inspect-brk hello.js
```

启动后会开放一个调试协议端口（默认 9229），用 Chrome 浏览器访问 `chrome://inspect`，或直接用 VS Code 的调试器附加，即可打断点、看变量、单步执行。

**方式三：使用 nodemon 热重载**

开发阶段每次改代码都要手动重跑很繁琐，`nodemon` 会在文件变化时自动重启进程：

```bash
# 全局安装
npm install -g nodemon

# 用 nodemon 代替 node 运行
nodemon hello.js
```

适合本地开发调试，**不要**用于生产环境。

**方式四：npm scripts**

在 `package.json` 中定义脚本：

```json
{
  "scripts": {
    "start": "node hello.js",
    "dev": "nodemon hello.js"
  }
}
```

然后通过 `npm run start`、`npm run dev` 执行，便于团队统一命令。

### 3.4 global 全局对象

在浏览器里，顶层 `var` 声明的变量会挂到 `window` 上。在 Node.js 中，每个文件是一个**模块**，有自己的作用域，顶层声明不会污染全局。

Node.js 的全局对象是 `global`（类似浏览器的 `window`），它上面挂载了一些无需 `require` 即可使用的全局变量：

| 全局对象 | 作用 |
| --- | --- |
| `global` | 全局对象本身，可挂自定义全局属性（不推荐） |
| `process` | 当前进程信息与控制（环境变量、参数、退出） |
| `console` | 标准输出（log / error / warn / table） |
| `Buffer` | 处理二进制数据（ES Module 中需 `require` 或 import） |
| `__dirname` | 当前文件所在目录的绝对路径（CommonJS 下可用） |
| `__filename` | 当前文件的绝对路径（CommonJS 下可用） |
| `setTimeout` / `setInterval` | 定时器（与浏览器一致） |
| `queueMicrotask` / `setImmediate` | 微任务与宏任务调度 |

### 3.5 process 与 console 基础

**process 对象**是 Node.js 最常用的全局对象之一，代表当前 Node.js 进程，常用属性与方法：

```js
process.version        // Node.js 版本号，如 'v20.11.0'
process.platform       // 操作系统平台，如 'win32'、'linux'、'darwin'
process.arch           // CPU 架构，如 'x64'、'arm64'
process.cwd()          // 当前工作目录（注意：不是脚本所在目录）
process.argv           // 命令行参数数组
process.env            // 环境变量对象（如 PATH、HOME）
process.pid            // 当前进程 ID
process.exit(code)     // 退出进程，code=0 正常，非 0 异常
process.stdout.write() // 直接写标准输出（不换行）
process.on('exit', cb) // 监听退出事件
```

**console 对象**用于输出信息，常用方法：

```js
console.log(...)       // 标准输出，打印日志
console.error(...)     // 标准错误流输出
console.warn(...)      // 警告
console.table(data)    // 以表格形式输出数组/对象
console.dir(obj)       // 打印对象结构
console.time('label')  // 开始计时
console.timeEnd('label') // 结束计时并打印耗时
```

---

## 四、环境搭建步骤

以下以 Windows 为例（macOS/Linux 步骤类似，把 nvm-windows 换成 nvm 即可）。

### 4.1 安装 nvm-windows

1. 前往 [nvm-windows Releases](https://github.com/coreybutler/nvm-windows/releases) 下载最新的 `nvm-setup.exe`。
2. 双击安装，选择安装目录（如 `C:\nvm`），同时会设置 Node.js 的符号链接目录（如 `C:\Program Files\nodejs`）。
3. 安装完成后打开**新的** PowerShell / CMD 窗口，验证：

```bash
nvm version
# 输出类似 1.1.x 即成功
```

> 注意：若已安装过独立版 Node.js，请先从「控制面板」卸载，并清理残留的 PATH，否则 nvm 切换版本会失效。

### 4.2 安装 Node.js

通过 nvm 安装 LTS 版本：

```bash
# 安装最新 LTS（推荐）
nvm install --lts

# 或指定版本
nvm install 20.11.0

# 切换到已安装版本
nvm use 20.11.0
```

### 4.3 验证安装

```bash
node -v
# v20.11.0

npm -v
# 10.2.4

nvm list
# 会列出已安装版本，当前使用的版本前有 * 标记
```

若三个命令都能正常输出版本号，说明环境搭建成功。

### 4.4 IDE 配置建议（VS Code）

VS Code 对 Node.js 开发有开箱即用的支持，推荐做以下增强配置：

1. **安装扩展**
   - **ESLint**：实时检查代码风格与潜在错误。
   - **Prettier**：代码格式化。
   - **Node.js Modules Intellisense**：自动补全 `require` 的模块路径。

2. **调试配置**
   在项目根目录创建 `.vscode/launch.json`：

   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "type": "node",
         "request": "launch",
         "name": "调试当前文件",
         "skipFiles": ["<node_internals>/**"],
         "program": "${file}"
       }
     ]
   }
   ```

   之后按 `F5` 即可调试当前打开的 JS 文件，支持断点、变量监视、调用栈。

3. **配置 npm 镜像（国内网络推荐）**

   ```bash
   npm config set registry https://registry.npmmirror.com
   npm config get registry   # 验证
   ```

   可大幅提升 `npm install` 速度。

---

## 五、关键知识点总结

- **Node.js 是运行时，不是语言**：它 = V8（执行 JS）+ libuv（事件循环与异步 I/O）+ 内置模块。
- **与浏览器的边界**：Node.js 没有 DOM/BOM，但有 `fs`、`http`、`process` 等系统级能力；全局对象是 `global` 而非 `window`。
- **非阻塞 I/O 是核心竞争力**：I/O 交给 libuv 异步处理，主线程不等待，单线程也能扛高并发。
- **「单线程」指 JS 业务逻辑**：libuv 有线程池，V8 有 GC 线程；多核利用需 `cluster` 或 `worker_threads`。
- **适合 I/O 密集，不适合 CPU 密集**：Web 服务、网关、RAG 后端是强项；纯计算任务交给其他语言或子线程。
- **nvm 管理多版本**：生产用 LTS（偶数版本），开发可尝鲜 Current。
- **运行脚本四件套**：`node file.js`（直接运行）、`--inspect`（调试）、`nodemon`（热重载）、`npm scripts`（统一命令）。
- **全局对象速查**：`global`、`process`、`console`、`Buffer`、`__dirname`、`__filename`。
- **对 AI 全栈的价值**：BFF 聚合、数据预处理、模型服务网关、RAG 后端，是连接前端与 Python 模型层的最佳桥梁。

---

## 六、实战练习

以下三个练习相互独立，建议按顺序完成。每个练习对应 `Code/` 目录下的一个 `.js` 文件，可直接 `node 文件名` 运行验证。

### 练习一：hello.js —— 第一个 Node.js 程序

**任务描述**

编写一个脚本 `hello.js`，完成以下功能：

1. 使用 `console.log` 输出一行欢迎信息，内容包含你的名字（或昵称）。
2. 使用 `console.log` 输出当前 Node.js 的版本号（通过 `process.version` 获取）。
3. 再输出一句对 AI 全栈学习的期待。

**预期输出示例**

```
====================================
欢迎来到 Node.js Day01，我是 AI 全栈学习者！
当前 Node.js 版本：v20.11.0
期待用 Node.js 搭建第一个 AI 后端服务 🚀
====================================
```

**运行方式**

```bash
cd Code
node hello.js
```

### 练习二：system-info.js —— 系统信息探针

**任务描述**

编写一个脚本 `system-info.js`，使用 `process` 对象输出以下系统信息：

1. 操作系统平台（`process.platform`）
2. CPU 架构（`process.arch`）
3. Node.js 版本（`process.version`）
4. 当前工作目录（`process.cwd()`）
5. 环境变量 `PATH` 的前 80 个字符（`process.env.PATH`，注意可能不存在需做容错）

要求：使用 `console.log` 分行格式化输出，并对 `PATH` 可能不存在的情况做容错处理（输出提示而非报错）。

**预期输出示例**

```
【系统信息探针】
操作系统平台：win32
CPU 架构：    x64
Node 版本：   v20.11.0
工作目录：    d:\Coding\AI-FullStack\NodeJS\Day01 - 初识Node.js与运行环境\Code
PATH 前 80 字符：C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\Sys...
```

**运行方式**

```bash
cd Code
node system-info.js
```

### 练习三：args-demo.js —— 命令行参数求和

**任务描述**

编写一个脚本 `args-demo.js`，完成：

1. 读取命令行参数 `process.argv`。
2. 跳过前两项（`node` 路径与脚本路径），将剩余参数解析为数字。
3. 对所有数字求和，并输出计算过程与结果。
4. 若用户未传入任何数字参数，给出友好的使用提示并退出。

**预期输出示例**

```
> node args-demo.js 10 20 30
接收到的参数：[ '10', '20', '30' ]
解析为数字：[ 10, 20, 30 ]
求和结果：10 + 20 + 30 = 60
```

```
> node args-demo.js
未传入任何数字参数。
用法：node args-demo.js <数字1> <数字2> ... 
示例：node args-demo.js 10 20 30
```

**运行方式**

```bash
cd Code
node args-demo.js 10 20 30
node args-demo.js 1.5 2.5 3
node args-demo.js
```

---

## 下节预告

下一节 **Day02** 将进入 **模块化与 npm 包管理**：深入 CommonJS 与 ES Modules 的差异、`package.json` 与 `package-lock.json` 的作用、依赖管理与版本语义化（SemVer），并动手封装第一个工具函数模块。
