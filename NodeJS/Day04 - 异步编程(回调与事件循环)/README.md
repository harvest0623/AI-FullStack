# Day 04 · 异步编程（回调与事件循环）

> 目标读者：已经熟悉 JavaScript/浏览器异步、ES6+ 语法，现在系统学习 Node.js 异步底层原理

> 运行环境：Node.js 18+

---

## 📑 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 同步 vs 异步](#21-同步-vs-异步)
  - [2.2 阻塞 vs 非阻塞](#22-阻塞-vs-非阻塞)
  - [2.3 Node.js 单线程与异步 I/O 原理](#23-nodejs-单线程与异步-io-原理)
  - [2.4 回调函数模式与"错误优先"约定](#24-回调函数模式与错误优先约定)
  - [2.5 回调地狱（Callback Hell）](#25-回调地狱callback-hell)
  - [2.6 事件循环（Event Loop）详解：六个阶段](#26-事件循环event-loop详解六个阶段)
  - [2.7 微任务 vs 宏任务执行顺序](#27-微任务-vs-宏任务执行顺序)
  - [2.8 I/O 多路复用（libuv 的 epoll/kqueue/IOCP）](#28-io-多路复用libuv-的-epollkqueueiocp)
- [三、核心概念解析](#三核心概念解析)
- [四、事件循环阶段执行顺序图](#四事件循环阶段执行顺序图)
- [五、关键知识点总结](#五关键知识点总结)
- [六、实战练习](#六实战练习)

---

## 一、学习目标

完成本节内容后，你将能够：

1. **厘清四组易混概念**：同步/异步、阻塞/非阻塞、并发/并行、I/O 密集/CPU 密集。
2. **解释 Node.js 单线程为何能高并发**：理解事件循环 + 非阻塞 I/O + libuv 线程池的协作机制。
3. **写出符合 Node.js 规范的回调**：掌握 `error-first callback` 约定，避免吞掉异常。
4. **识别并重构回调地狱**：理解问题成因，为后续 Promise/async-await 做铺垫。
5. **完整描述事件循环六个阶段**：timers → pending callbacks → idle,prepare → poll → check → close callbacks。
6. **预测任意代码片段的输出顺序**：在 `setTimeout`、`setInterval`、`setImmediate`、`Promise.then`、`process.nextTick`、`queueMicrotask` 混用场景下准确判断执行次序。
7. **使用 EventEmitter 构建松耦合模块**：掌握 `on/once/emit/off`、监听器上限、`error` 事件约定。
8. **理解 libuv 跨平台 I/O 多路复用底层**：epoll(Linux) / kqueue(macOS/BSD) / IOCP(Windows)。

---

## 二、理论知识讲解

### 2.1 同步 vs 异步

| 概念 | 调用方是否等待结果 | 类比 |
| --- | --- | --- |
| 同步（Synchronous） | 是，调用后阻塞直到拿到返回值 | 在餐厅柜台点餐后站在原地等叫号 |
| 异步（Asynchronous） | 否，调用后立即返回，结果通过回调/Promise/事件在未来某一刻送达 | 点完餐坐下，服务员端来时通知你 |

在 Node.js 中，几乎所有 I/O 操作（文件、网络、DNS、子进程）默认都是异步的。同步版本（如 `fs.readFileSync`）虽然存在，但会阻塞事件循环，仅在启动脚本或 CLI 工具中谨慎使用。

### 2.2 阻塞 vs 非阻塞

阻塞与非阻塞描述的是**调用方在被调用方处理 I/O 时的状态**：

- **阻塞 I/O**：调用 `read()` 后，操作系统把当前线程挂起，直到数据从磁盘/网卡到达内核缓冲区并复制到用户空间，线程才被唤醒。线程在等待期间无法做其他事。
- **非阻塞 I/O**：调用 `read()` 后立即返回（可能返回 `EAGAIN` 错误表示"还没准备好"），线程可以继续执行其他逻辑，稍后再来轮询或被通知。

> ⚠️ 易混点：**异步一定非阻塞，但非阻塞不一定是异步**。非阻塞 I/O 通常需要配合 I/O 多路复用（如 `epoll`）才能实现真正的"异步通知"——这正是 libuv 在做的事。

### 2.3 Node.js 单线程与异步 I/O 原理

很多人误以为 "Node.js = 单线程"，这句话只对了一半。准确表述是：

> **Node.js 的 JavaScript 代码执行在单个主线程上**，但底层 libuv 维护了一个**线程池**（默认 4 个线程，可通过 `UV_THREADPOOL_SIZE` 调整），用于处理那些操作系统没有提供异步接口的操作（如 `fs` 文件 I/O、`crypto.pbkdf2`、`dns.lookup` 等）。

整体架构：

```
┌──────────────────────────────────────────────────────────────┐
│                     JavaScript 主线程                          │
│   ┌──────────────┐    ┌─────────────┐    ┌──────────────┐    │
│   │  V8 引擎     │    │  事件循环    │    │ 用户的 JS 代码│    │
│   └──────────────┘    └─────────────┘    └──────────────┘    │
└──────────────────────┬───────────────────────────────────────┘
                       │  调用 Node API
              ┌────────▼─────────┐
              │   Node C++ 绑定层 │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │      libuv        │
              │  ┌────────────┐   │
              │  │ 事件循环    │   │
              │  ├────────────┤   │
              │  │ 线程池(4)  │   │  ← 处理 fs / crypto / dns.lookup
              │  └────────────┘   │
              └────────┬─────────┘
                       │
              ┌────────▼─────────────────────────┐
              │  操作系统异步 I/O 接口            │
              │  Linux: epoll  macOS: kqueue     │
              │  Windows: IOCP                   │
              └──────────────────────────────────┘
```

**单线程高并发的核心逻辑**：

1. 主线程遇到 I/O 请求，把请求交给 libuv（不等待）。
2. libuv 把请求交给操作系统（epoll/kqueue/IOCP）或线程池，主线程立即继续执行下一条 JS。
3. 当 I/O 完成，操作系统通知 libuv，libuv 把对应的回调放入事件循环队列。
4. 主线程在事件循环的 `poll` 阶段取出回调并执行。

因此 Node.js 适合 **I/O 密集型**场景（API 网关、聊天服务器、代理），不适合 **CPU 密集型**场景（视频编码、加密计算），因为主线程被 CPU 任务占满时无法处理 I/O 回调。AI 推理若放主线程会立即拖垮服务，后续课程会讲到 `worker_threads` 与子进程方案。

### 2.4 回调函数模式与"错误优先"约定

**回调函数（callback）**：把一个函数作为参数传给另一个函数，让被调用方在合适的时机（如 I/O 完成）执行它。这是 Node.js 最早期的异步编程范式。

**错误优先约定（error-first callback / Node-style callback）**：

> 回调函数的第一个参数永远是错误对象（`Error` 实例或 `null`），后续参数才是真正的数据。如果操作成功，第一个参数必须为 `null` 或 `undefined`。

形如：

```js
function callback(err, data) {
  if (err) {
    // 处理错误
    return;
  }
  // 使用 data
}
```

为什么是第一个参数放错误？因为函数只能有一个返回值/单一"出口"，把错误放在最显眼的位置可以强制调用方先面对异常，避免"吞错"。Node.js 核心模块（`fs`、`http`、`crypto`）和早期 npm 生态（Express 中间件、MongoDB 驱动）都遵循此约定。

### 2.5 回调地狱（Callback Hell）

当多个异步操作存在依赖关系——比如"先读配置 → 再请求用户信息 → 再请求订单 → 再请求商品详情"——时，回调会层层嵌套，形成类似箭头形状的代码：

```js
getUser(userId, function (err, user) {
  if (err) return handleError(err);
  getOrders(user, function (err, orders) {
    if (err) return handleError(err);
    getProducts(orders, function (err, products) {
      if (err) return handleError(err);
      render(products);
    });
  });
});
```

**回调地狱带来的问题**：

1. **可读性差**：嵌套层级深，代码向右"金字塔"膨胀。
2. **错误处理分散**：每一层都要重复写 `if (err) ...`，容易遗漏。
3. **无法正常 `return` / `throw`**：异步回调里的 `throw` 不会被外层 `try/catch` 捕获，会直接变成 `uncaughtException`。
4. **难以复用与测试**：业务逻辑与控制流耦合在嵌套里，无法单独抽取中间步骤。
5. **变量泄漏**：内层作用域能访问外层变量，容易出现意外的闭包陷阱。

后续 Day05 会用 Promise / async-await 解决这些问题。

### 2.6 事件循环（Event Loop）详解：六个阶段

Node.js 的事件循环由 libuv 实现，是一个无限循环（只要还有待处理的回调或定时器）。**每一轮（tick）** 按顺序经过以下六个阶段：

#### 阶段 1：timers（定时器阶段）

执行到期的 `setTimeout` 和 `setInterval` 回调。注意：定时器的"到期时间"只是最早可能执行时间，实际执行可能被推迟——因为 timers 阶段之间可能穿插了其他阶段的耗时回调。

#### 阶段 2：pending callbacks（待处理回调阶段）

执行**系统级**回调，例如 TCP 错误回调（`ECONNREFUSED`）、DNS 错误、操作系统信号回调等。这些通常不是用户主动注册的，而是底层网络栈产生的。

#### 阶段 3：idle, prepare（空闲与准备阶段）

libuv 内部使用，主要做一些轮询前的准备工作。**JavaScript 代码几乎不会在这里执行**，可以忽略。

#### 阶段 4：poll（轮询阶段）—— 最重要

1. 检索新的 I/O 事件，执行 I/O 回调（除了 close、timers、setImmediate 之外的几乎全部回调都在这里执行）。
2. 如果没有已就绪的 I/O 回调：
   - 如果有 `setImmediate` 回调等待，则跳到 check 阶段。
   - 如果没有，则在此阶段**阻塞等待** I/O 事件到来（阻塞时长由最近的 timer 到期时间决定），直到事件到来或定时器到期。
3. poll 阶段会决定事件循环是继续转下一轮还是退出。

#### 阶段 5：check（检查阶段）

执行 `setImmediate` 回调。`setImmediate` 设计的初衷就是"在 poll 阶段结束后立即执行"。

#### 阶段 6：close callbacks（关闭回调阶段）

执行关闭事件的回调，如 `socket.on('close', ...)`、`http.Server` 关闭等。

#### 微任务穿插

**每一阶段切换之间**，Node.js 会清空两类微任务队列：

1. `process.nextTick` 队列（**最高优先级**）
2. `Promise.then` / `queueMicrotask` 队列

> 注意：微任务不是六个阶段之一，而是在阶段之间"插队"执行。

### 2.7 微任务 vs 宏任务执行顺序

#### 三种微任务

| API | 所属队列 | 优先级 |
| --- | --- | --- |
| `process.nextTick(fn)` | nextTick 队列 | **最高**（在所有微任务前） |
| `Promise.resolve().then(fn)` | Promise 微任务队列 | 次高 |
| `queueMicrotask(fn)` | Promise 微任务队列 | 次高（与 Promise.then 同队列） |

> ⚠️ `process.nextTick` 是 Node.js 独有，浏览器没有。它会在**当前操作完成后、下一个事件循环阶段开始前**执行，优先级高于所有微任务。
>
> ⚠️ 滥用 `process.nextTick` 会"饿死"I/O，因为它会在每次切换前递归清空，可能让事件循环永远进不到 poll 阶段。

#### 四种宏任务

| API | 所在阶段 |
| --- | --- |
| `setTimeout(fn, 0)` | timers |
| `setInterval(fn, 0)` | timers |
| `setImmediate(fn)` | check |
| I/O 回调（`fs.readFile` 等） | poll |

#### 执行顺序口诀

> **同一阶段内**：先清空 nextTick，再清空 Promise/queueMicrotask，然后才进入下一阶段。

### 2.8 I/O 多路复用（libuv 的 epoll/kqueue/IOCP）

操作系统层面有多种 I/O 模型，libuv 在不同平台选择最优的**多路复用**机制：

| 平台 | 机制 | 特点 |
| --- | --- | --- |
| Linux | `epoll` | 基于事件回调，O(1) 复杂度，支持边缘触发和水平触发，是 Linux 高并发的事实标准 |
| macOS / BSD | `kqueue` | 类似 epoll，基于过滤器（filter）机制，性能优秀 |
| Windows | `IOCP`（I/O Completion Port） | 真正的异步 I/O（completion 模型），与 epoll/kqueue 的就绪模型（readiness）不同 |
| 较老 Unix | `poll` / `select` | 兼容性回退方案，性能差 |

**多路复用核心思想**：用一个线程同时监听多个文件描述符（socket/pipe），哪个 fd 有事件（可读/可写/出错）就处理哪个，避免每个连接一个线程的浪费。

**libuv 的统一抽象**：libuv 把上述机制封装成统一的 `uv__io_t` 结构，对上层提供一致的接口。所以 Node.js 代码在不同平台上的事件循环行为基本一致，无需关心底层用的是 epoll 还是 IOCP。

**对于无异步接口的操作**（如文件 I/O，Linux 上没有真正完美的异步文件系统接口），libuv 使用**线程池**模拟异步：在线程池里跑阻塞 I/O，完成后把回调扔回事件循环。

---

## 三、核心概念解析

### 3.1 宏任务 vs 微任务对比

| 维度 | 宏任务（Macrotask） | 微任务（Microtask） |
| --- | --- | --- |
| 代表 API | `setTimeout`、`setInterval`、`setImmediate`、I/O 回调 | `Promise.then`、`queueMicrotask`、`process.nextTick` |
| 执行时机 | 在事件循环的特定阶段 | 阶段切换之间（每阶段清空） |
| 数量限制 | 每阶段只处理一批，剩余留下轮 | 一次清空到底（可能递归） |
| 是否阻塞事件循环 | 单个回调慢会拖慢但不"饿死" | `process.nextTick` 递归会饿死 I/O |
| 浏览器/Node 差异 | 基本一致 | Node 多了 `process.nextTick` |

### 3.2 `setTimeout(fn, 0)` vs `setImmediate` 执行顺序

这是一个经典面试题，答案**取决于调用位置**：

#### 情况 A：在主模块（顶层代码）中调用

**顺序不确定**，两者都可能先执行。原因：

- 主模块代码执行完后，事件循环启动。
- `setTimeout(fn, 0)` 在 Node 中实际被强制为 `setTimeout(fn, 1)`（最小 1ms）。
- 进入 timers 阶段时，是否到达 1ms 取决于进程启动耗时——可能已经超过 1ms（先执行 setTimeout），也可能没到（先进入 check 阶段执行 setImmediate）。

#### 情况 B：在 I/O 回调中调用

**顺序确定：`setImmediate` 一定先于 `setTimeout` 执行**。原因：

- I/O 回调在 poll 阶段执行。
- poll 阶段结束后，事件循环**必然先进入 check 阶段**（执行 setImmediate），然后才进入下一轮的 timers 阶段（执行 setTimeout）。

```js
// 在 I/O 回调内
fs.readFile('a.txt', () => {
  setTimeout(() => console.log('timeout'), 0);
  setImmediate(() => console.log('immediate'));
});
// 输出稳定：immediate → timeout
```

这个特性让 `setImmediate` 在 I/O 处理后立即继续处理逻辑时非常合适——它保证在下一轮 timers 之前执行。

### 3.3 EventEmitter 核心类

`events.EventEmitter` 是 Node.js 中几乎所有"事件型"对象的基类（`http.Server`、`stream.Readable`、`fs.FSWatcher` 等）。

#### 核心 API

| 方法 | 说明 |
| --- | --- |
| `emitter.on(event, listener)` | 注册监听器，每次 `emit` 都会触发 |
| `emitter.once(event, listener)` | 注册只触发一次的监听器 |
| `emitter.emit(event, ...args)` | 同步触发事件，依次调用所有监听器 |
| `emitter.off(event, listener)` / `removeListener` | 移除指定监听器（需保留函数引用） |
| `emitter.removeAllListeners(event)` | 移除某事件全部监听器 |
| `emitter.setMaxListeners(n)` | 设置监听器数量上限，`0` 表示无限制 |
| `emitter.listeners(event)` | 返回该事件的监听器数组 |

#### 监听器上限与 `setMaxListeners`

默认单个事件最多 **10** 个监听器。超过会触发 `MaxListenersExceededWarning` 警告（注意是警告，不是错误，代码会继续执行）。这是为了防止**内存泄漏**——典型场景是反复注册回调却忘了移除（如每次请求都 `on('data', ...)` 却从不 `off`）。

```js
emitter.setMaxListeners(20);  // 提升上限
emitter.setMaxListeners(0);   // 完全关闭警告（慎用）
```

#### `error` 事件约定

> 如果 `emit('error', err)` 时**没有注册 `error` 监听器**，整个进程会抛出 `err` 并崩溃（`uncaughtException`）。

因此使用 EventEmitter 时必须：

1. 总是注册 `error` 监听器，或
2. 使用 `try/catch` 包裹 `emit`（不推荐，因为监听器是同步抛出），或
3. 至少设置一个全局的 `process.on('uncaughtException', ...)` 兜底。

```js
const emitter = new EventEmitter();
emitter.on('error', (err) => {
  console.error('捕获到错误事件:', err.message);
});
emitter.emit('error', new Error('something went wrong')); // 不会崩
```

---

## 四、事件循环阶段执行顺序图

下图展示了一轮事件循环（one tick）的完整流程，包括六个阶段与微任务的插队时机：

```
                      ┌─────────────────────────────────────────┐
                      │          事件循环开始 (tick)              │
                      └─────────────────┬───────────────────────┘
                                        │
                                        ▼
                      ┌─────────────────────────────────────────┐
        阶段 1         │   timers —— 执行到期的 setTimeout /      │
                      │              setInterval 回调              │
                      └─────────────────┬───────────────────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │  清空 nextTick 队列          │ ← 微任务
                          │  清空 Promise/queueMicrotask │ ← 微任务
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                      ┌─────────────────────────────────────────┐
        阶段 2         │   pending callbacks —— 系统级错误回调     │
                      │   (TCP ECONNREFUSED / DNS 错误等)         │
                      └─────────────────┬───────────────────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │  清空 nextTick 队列          │
                          │  清空 Promise/queueMicrotask │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                      ┌─────────────────────────────────────────┐
        阶段 3         │   idle, prepare —— libuv 内部使用         │
                      └─────────────────┬───────────────────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │  清空 nextTick 队列          │
                          │  清空 Promise/queueMicrotask │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                      ┌─────────────────────────────────────────┐
        阶段 4         │   poll —— 检索新的 I/O 事件，执行 I/O     │
                      │   回调。若空且无 setImmediate，阻塞等待    │
                      └─────────────────┬───────────────────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │  清空 nextTick 队列          │
                          │  清空 Promise/queueMicrotask │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                      ┌─────────────────────────────────────────┐
        阶段 5         │   check —— 执行 setImmediate 回调         │
                      └─────────────────┬───────────────────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │  清空 nextTick 队列          │
                          │  清空 Promise/queueMicrotask │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                      ┌─────────────────────────────────────────┐
        阶段 6         │   close callbacks —— socket.on('close') │
                      └─────────────────┬───────────────────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │  清空 nextTick 队列          │
                          │  清空 Promise/queueMicrotask │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                      ┌─────────────────────────────────────────┐
                      │   是否还有待处理回调/定时器？               │
                      │   是 → 回到阶段 1（开启下一 tick）         │
                      │   否 → 退出事件循环，进程结束              │
                      └─────────────────────────────────────────┘
```

### 执行顺序示例

```js
console.log('1: 同步开始');

setTimeout(() => console.log('5: setTimeout 宏任务'), 0);
setImmediate(() => console.log('6: setImmediate 宏任务'));

Promise.resolve().then(() => console.log('3: Promise 微任务'));
process.nextTick(() => console.log('2: nextTick 微任务'));
queueMicrotask(() => console.log('4: queueMicrotask 微任务'));

console.log('7: 同步结束');
```

**输出顺序**：

```
1: 同步开始
7: 同步结束
2: nextTick 微任务
3: Promise 微任务
4: queueMicrotask 微任务
5: setTimeout 宏任务       ← 5 和 6 的顺序在主模块内不确定
6: setImmediate 宏任务
```

**分析**：

1. 同步代码先执行：`1` 和 `7`。
2. 同步代码结束后，事件循环启动前，先清空微任务：nextTick 优先 → `2`，然后 Promise/queueMicrotask 按 FIFO → `3`、`4`。
3. 进入 timers 阶段执行 setTimeout → `5`。
4. 进入 check 阶段执行 setImmediate → `6`（主模块内两者顺序不稳定，此处假定 timers 先到）。

---

## 五、关键知识点总结

### ✅ 必须记住的 10 条

1. **Node.js 单线程 ≠ 全部单线程**：JS 主线程单线程，libuv 有线程池处理 fs/crypto 等。
2. **事件循环六个阶段顺序**：timers → pending callbacks → idle,prepare → poll → check → close callbacks。
3. **微任务优先级**：`process.nextTick` > `Promise.then` ≈ `queueMicrotask` > 任何宏任务。
4. **微任务执行时机**：每个阶段切换之间清空，不是只在 tick 末尾。
5. **error-first 约定**：回调第一个参数永远是 error，成功时为 `null`。
6. **回调地狱根因**：异步串行依赖 + 控制流嵌套，可被 Promise/async-await 解决。
7. **`setTimeout(fn, 0)` 实际为 `setTimeout(fn, 1)`**：浏览器和 Node 都有最小延迟。
8. **setTimeout vs setImmediate 顺序**：主模块内不确定；I/O 回调内一定 setImmediate 先。
9. **EventEmitter 默认 10 个监听器上限**：超过会警告，用 `setMaxListeners` 调整。
10. **未监听的 `error` 事件会让进程崩溃**：必须注册 error 处理器。

### 🚫 常见误区

| 误区 | 正解 |
| --- | --- |
| Node.js 是单线程，所以不能并发 | JS 单线程，但 I/O 并发；事件循环让它能处理高并发 I/O |
| `setTimeout(fn, 0)` 立即执行 | 最小 1ms 延迟，且要等当前阶段结束 |
| `process.nextTick` 是微任务 | 它有自己的 nextTick 队列，优先级高于所有微任务 |
| Promise 一定比 setTimeout 先执行 | 不一定，要看是否在同一阶段内 |
| setImmediate 一定比 setTimeout 先执行 | 主模块内不一定，I/O 回调内一定 |
| 监听器上限是错误 | 只是警告，代码继续执行 |

### 🎯 学习心法

> **事件循环是 Node.js 的心脏**。理解它的关键不是死记六阶段，而是建立"时间轴"思维：把每段代码贴到时间轴上的某个阶段，再考虑阶段切换时的微任务插队。当你能闭眼画出执行顺序图，并解释任何混合场景的输出，就真正入门 Node.js 异步了。

---

## 六、实战练习

### 练习 1：手写错误优先回调的链式调用

**目标**：在不使用 Promise 的前提下，用 error-first 回调实现"读取用户 → 读取订单 → 读取商品"的三步串行调用。

**要求**：

1. 模拟三个异步函数 `getUser(id, cb)`、`getOrders(userId, cb)`、`getProducts(orderId, cb)`，每个用 `setTimeout` 模拟 200ms 延迟。
2. 三处都可能随机失败（用 `Math.random() < 0.3` 模拟 30% 失败率）。
3. 任何一步失败，必须立即终止链路并把错误传给最终回调。
4. 成功时最终回调收到商品列表。

**提示**：参考 `Code/callback-demo.js` 和 `Code/callback-hell.js`，体验"为什么需要 Promise"。

### 练习 2：预测输出顺序

阅读下面代码，**先不运行**，在纸上写出输出顺序，再用 `node` 运行验证：

```js
console.log('A');

setImmediate(() => {
  console.log('B');
  process.nextTick(() => console.log('C'));
});

setTimeout(() => {
  console.log('D');
}, 0);

Promise.resolve().then(() => console.log('E'));

process.nextTick(() => console.log('F'));

queueMicrotask(() => console.log('G'));

fs.readFile(__filename, () => {
  console.log('H');
  setTimeout(() => console.log('I'), 0);
  setImmediate(() => console.log('J'));
  Promise.resolve().then(() => console.log('K'));
});

console.log('L');
```

**验证要求**：

- 解释 `H / I / J` 三者顺序为何如此（这是 `setTimeout` vs `setImmediate` 在 I/O 回调内的经典场景）。
- 解释 `B` 和 `C` 的相对位置。

### 练习 3：自定义 EventEmitter 实现"任务进度条"

**目标**：用 `EventEmitter` 模拟一个文件下载器，对外抛出 `start`、`progress`、`done`、`error` 四个事件。

**要求**：

1. 自定义类 `Downloader extends EventEmitter`，构造时传入文件名。
2. `start()` 方法内用 `setInterval` 每 100ms 触发一次 `progress` 事件，payload 为百分比（0~100）。
3. 进度到 100% 时触发 `done`，并 `clearInterval`。
4. 有 10% 概率随机触发 `error` 事件并停止。
5. 调用方注册 `on('progress', ...)`、`once('done', ...)`、`on('error', ...)`，把进度打印到控制台。
6. 设置 `setMaxListeners(20)` 避免警告（假设多个模块都监听 progress）。

**提示**：参考 `Code/eventemitter-demo.js`，注意 `error` 事件不处理会导致进程崩溃。

---

## 📂 配套代码

| 文件 | 内容 |
| --- | --- |
| `Code/callback-demo.js` | 错误优先回调示例：模拟读取用户信息 |
| `Code/callback-hell.js` | 回调地狱演示：三层嵌套定时器与文件操作 |
| `Code/event-loop-order.js` | 微任务与宏任务混合执行顺序 |
| `Code/eventemitter-demo.js` | 自定义事件类继承 EventEmitter |
| `Code/timer-vs-immediate.js` | 主模块内 vs I/O 内 setTimeout 与 setImmediate 顺序对比 |

运行方式：

```bash
cd "Day04 - 异步编程(回调与事件循环)/Code"
node callback-demo.js
```

---

## 🔗 延伸阅读

- [Node.js 官方文档：The Node.js Event Loop](https://nodejs.org/en/docs/guides/event-loop-timers-and-nexttick)
- [libuv 官方设计文档](https://docs.libuv.org/en/v1.x/design.html)
- [Node.js 源码：libuv bindings](https://github.com/nodejs/node/tree/main/deps/uv)

---

**下一节预告**：Day 05 将用 Promise 与 `async/await` 重构回调地狱，深入理解 `Promise` 的状态机、错误传播链与 `Promise.all/race/allSettled` 的应用场景。
