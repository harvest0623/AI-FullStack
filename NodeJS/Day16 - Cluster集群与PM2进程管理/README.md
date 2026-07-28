# Day16 - Cluster 集群与 PM2 进程管理

> 本篇聚焦让 Node.js 真正"榨干多核 CPU"的两大能力——内置的 **`cluster` 模块**与生产级进程管理器 **PM2**。Node.js 单进程单线程的模型在前端时代是优势（无并发竞态），但放到 8 核 / 16 核的服务器上，一个 Node 进程只能吃满一个核，其余核全部闲置。`cluster` 模块让你用几行代码 fork 出与 CPU 核数相同的工作进程共享同一端口；PM2 则把"fork worker、崩溃重启、零停机重载、日志管理、开机自启"这一整套运维包袱打包成命令行工具，是裸机部署 Node 服务的事实标准。掌握本篇后，你将有能力把一个跑在单进程的 AI 接口服务升级成"多核并行 + 崩溃自愈 + 平滑发布"的可上线形态，并为后续容器化部署（Docker / K8s）打下判断"何时该用 PM2、何时该交给编排器"的基础。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解：cluster 模块](#二理论知识讲解cluster-模块)
  - [2.1 单进程单线程回顾与多核浪费问题](#21-单进程单线程回顾与多核浪费问题)
  - [2.2 cluster 模块原理](#22-cluster-模块原理)
  - [2.3 cluster.isMaster / isPrimary 与 cluster.isWorker](#23-clusterismaster--isprimary-与-clusterisworker)
  - [2.4 fork 工作进程](#24-fork-工作进程)
  - [2.5 worker 监听 exit 事件后重启](#25-worker-监听-exit-事件后重启)
  - [2.6 worker.disconnect 优雅退出](#26-workerdisconnect-优雅退出)
  - [2.7 cluster.schedulingPolicy：RR vs 共享套接字](#27-clusterschedulingpolicyrr-vs-共享套接字)
  - [2.8 worker.id 与 worker.process](#28-workerid-与-workerprocess)
- [三、cluster 实战](#三cluster-实战)
  - [3.1 创建多核 HTTP 服务器](#31-创建多核-http-服务器)
  - [3.2 监听 worker 上线 / 退出](#32-监听-worker-上线--退出)
  - [3.3 自动重启崩溃 worker](#33-自动重启崩溃-worker)
  - [3.4 零停机重启（逐个重启 worker）](#34-零停机重启逐个重启-worker)
- [四、PM2 进程管理器](#四pm2-进程管理器)
  - [4.1 安装](#41-安装)
  - [4.2 为什么用 PM2](#42-为什么用-pm2)
  - [4.3 核心命令速查](#43-核心命令速查)
  - [4.4 ecosystem.config.js 配置文件](#44-ecosystemconfigjs-配置文件)
  - [4.5 PM2 集群模式 vs fork 模式](#45-pm2-集群模式-vs-fork-模式)
  - [4.6 PM2 reload 零停机原理](#46-pm2-reload-零停机原理)
  - [4.7 日志管理](#47-日志管理)
  - [4.8 PM2 startup 开机自启](#48-pm2-startup-开机自启)
- [五、cluster vs PM2 对比](#五cluster-vs-pm2-对比)
- [六、容器化时代 PM2 的取舍](#六容器化时代-pm2-的取舍)
- [七、优雅退出最佳实践](#七优雅退出最佳实践)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 解释 Node.js 单进程单线程模型在多核服务器上"只吃一个核"的浪费问题，并能用数字说明（如 8 核机器利用率仅 12.5%）。
2. 描述 `cluster` 模块的架构：一个 master 主进程 + N 个 worker 工作进程，worker 间共享同一个服务器端口，底层靠 IPC（父子进程管道）通信。
3. 说出 `cluster.isMaster`（`isPrimary`）与 `cluster.isWorker` 的判别用途，理解为什么同一份脚本既能跑主进程又能跑 worker。
4. 用 `cluster.fork()` 创建工作进程，监听 worker 的 `online` / `exit` / `disconnect` 事件，并在 worker 崩溃后自动重启。
5. 区分 `cluster.schedulingPolicy` 的两种策略：`SCHED_RR`（round-robin 轮询，默认）与 `SCHED_NONE`（共享套接字，由 OS 抢占），并理解它们对请求分发的影响。
6. 读懂 `worker.id`、`worker.process`（ChildProcess 实例）、`worker.send()` 等 API，知道何时该用 `disconnect` 优雅退出而非 `kill` 强杀。
7. 用 `cluster` 手写一个多核 HTTP 服务器，并实现"零停机重启"——逐个重启 worker，新 worker 上线后再停旧 worker。
8. 安装 PM2，说明它相比手写 cluster 的优势（守护进程、自动重启、日志切割、零停机 reload、监控面板）。
9. 编写 `ecosystem.config.js` 配置多应用、设置 `instances: max`、`exec_mode: cluster`、`max_memory_restart`、`env` / `env_production`。
10. 区分 PM2 的 `restart`（杀掉重启，有短暂不可用）与 `reload`（逐个重启 worker，零停机），并能解释 reload 的实现思路。
11. 在容器化（Docker / K8s）场景下判断是否该用 PM2，理解"单容器单进程 + 编排器管理副本"的主流取舍。
12. 写出生产级优雅退出流程：收到 `SIGTERM` → 停止接受新请求 → 处理完在途请求 → 关闭数据库连接 → 超时强杀。

---

## 二、理论知识讲解：cluster 模块

### 2.1 单进程单线程回顾与多核浪费问题

回顾 Day15：Node.js 的主线程跑着一个事件循环，所有 JS 代码都在这一个线程上执行。I/O（网络、磁盘）虽然由 libuv 的线程池异步处理，但 **JS 回调始终在主线程排队执行**。这意味着：

- 一个 CPU 密集的同步计算（如 `fib(45)`）会卡住整个事件循环，期间所有 HTTP 请求都被阻塞。
- 即便是 I/O 密集型服务，单个 Node 进程也只能用满 **一个 CPU 核**。

假设你买了一台 8 核云主机部署 AI 接口服务，直接 `node app.js` 启动：

```
8 核 CPU 利用率：
核1: ████████████ 100%  ← 你的 Node 进程
核2: ░░░░░░░░░░░░   0%  ← 闲置
核3: ░░░░░░░░░░░░   0%  ← 闲置
核4: ░░░░░░░░░░░░   0%  ← 闲置
核5: ░░░░░░░░░░░░   0%  ← 闲置
核6: ░░░░░░░░░░░░   0%  ← 闲置
核7: ░░░░░░░░░░░░   0%  ← 闲置
核8: ░░░░░░░░░░░░   0%  ← 闲置
整体利用率：12.5%
```

7/8 的算力被浪费了。要吃满多核，思路有三种：

| 方案 | 做法 | 缺点 |
|------|------|------|
| 多端口多实例 | 启动 8 个 Node 进程，分别监听 3001~3008，前面挂 Nginx 负载均衡 | 端口管理繁琐、Nginx 配置成本、进程间无法共享状态 |
| `worker_threads` | 进程内开多线程 | 主要适合 CPU 密集计算，不适合 HTTP 服务的多核扩展（线程共享进程，一个崩全崩） |
| **`cluster` 模块** | 一个主进程 fork 多个 worker，**共享同一个监听端口** | 需要自己处理崩溃重启、日志、零停机（或交给 PM2） |

`cluster` 模块是 Node 内置的、专门解决"HTTP 服务多核扩展"的方案，也是 PM2 集群模式的底层基础。

### 2.2 cluster 模块原理

`cluster` 模块的架构如下图：

```
                    ┌─────────────────────────────┐
                    │       master 主进程          │
                    │  (不处理业务，只负责调度)    │
                    │  cluster.fork() 创建 worker │
                    └──────────────┬──────────────┘
                          IPC 管道 │ (父子进程通信)
            ┌───────────┬──────────┴──────────┬───────────┐
            ▼           ▼                     ▼           ▼
       ┌────────┐  ┌────────┐            ┌────────┐  ┌────────┐
       │worker 1│  │worker 2│     ...    │worker N│  │worker N│
       │ pid=A  │  │ pid=B  │            │ pid=.. │  │ pid=.. │
       │共享端口│  │共享端口│            │共享端口│  │共享端口│
       └────────┘  └────────┘            └────────┘  └────────┘
            │           │                     │           │
            ▼           ▼                     ▼           ▼
         处理请求    处理请求               处理请求    处理请求
```

**关键机制：**

1. **主进程不处理业务请求**，只负责 fork worker、监听 worker 崩溃、重启 worker。这让它成为一个轻量的"看门狗"。
2. **所有 worker 共享同一个端口**（如 3000）。这是 cluster 最神奇的地方——你只用 `server.listen(3000)` 一次，多个 worker 都能收到连接。
3. **底层用 IPC 通信**：master 与每个 worker 之间有一条 IPC 管道（来自 `child_process.fork`），可双向 `send` / `on('message')`。
4. **请求分发由调度策略决定**：默认 `SCHED_RR`（round-robin），主进程把连接轮流分给各 worker；也可设 `SCHED_NONE`，让所有 worker 共享同一个套接字、由 OS 内核抢占（惊群效应）。

> 底层实现：`cluster.fork()` 本质是 `child_process.fork()`，但 cluster 会拦截 `server.listen` 调用——worker 调 `listen` 时并不真的在 worker 内绑定端口，而是通过 IPC 把"我要监听"的消息发给 master，由 master 绑定端口并把连接句柄分发给 worker。这就是"多进程共享端口"的真相。

### 2.3 cluster.isMaster / isPrimary 与 cluster.isWorker

由于 master 和 worker 跑的是**同一份脚本**（除非显式分文件），需要一个判别标志区分当前进程的角色：

```js
const cluster = require('cluster');

if (cluster.isMaster) {
  // 主进程：fork worker
  cluster.fork();
} else {
  // worker 进程：启动 HTTP 服务
  require('http').createServer(...).listen(3000);
}
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `cluster.isMaster` | boolean | 当前进程是主进程时为 `true`。**旧 API**，仍可用 |
| `cluster.isPrimary` | boolean | 同上，**Node 16+ 推荐用法**，命名更中性（避免 master/slave 歧义） |
| `cluster.isWorker` | boolean | 当前进程是 worker 时为 `true` |

> Node 16 起，官方把 `isMaster` 重命名为 `isPrimary` 以避免 master/slave 术语争议，`isMaster` 仍保留别名兼容。新代码建议用 `isPrimary`，读老代码时认得 `isMaster` 即可。本篇示例两者都会出现并标注。

### 2.4 fork 工作进程

`cluster.fork([env])` 在主进程中调用，创建一个 worker 子进程：

```js
const cluster = require('cluster');
const os = require('os');

if (cluster.isPrimary) {
  const numCPUs = os.cpus().length;
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork(); // fork 出 cpu 核数个 worker
  }
}
```

要点：

- `fork()` 返回一个 `Worker` 实例，每个 worker 有独立的 `id` 和 `process`（ChildProcess）。
- `fork(env)` 可传入环境变量，仅对本次 fork 生效。
- worker 启动后会从脚本顶部重新执行——这就是为什么必须用 `isPrimary` / `isWorker` 分流，否则 worker 会再次 fork 出孙 worker，无限繁殖。
- worker 数量不必等于 CPU 核数。对于 I/O 密集型服务，可 fork 更多（如核数的 2 倍）；对 CPU 密集型，多于核数反而增加上下文切换开销。常见做法是 `os.cpus().length`。

### 2.5 worker 监听 exit 事件后重启

worker 崩溃（未捕获异常、OOM、段错误）时会触发 `exit` 事件。生产环境必须监听它并重启 worker，否则一个 worker 崩了就少一个处理能力：

```js
cluster.on('exit', (worker, code, signal) => {
  console.log(`worker ${worker.id} (pid=${worker.process.pid}) 退出，code=${code} signal=${signal}`);
  // 重启一个新 worker
  cluster.fork();
});
```

注意：

- `code` 是退出码（0 正常，非 0 异常）；`signal` 是被信号杀死时的信号名（如 `'SIGKILL'`）。
- **不要**在 `exit` 里判断"正常退出就不重启"——worker 主动 `process.exit(0)` 也算正常，但服务少了一个进程仍需补齐。除非你在做"缩容"。
- 防止"崩溃-重启-立即再崩"的死循环：可以加一个计数器，短时间内重启次数过多就停止 fork 并报警。

### 2.6 worker.disconnect 优雅退出

`worker.disconnect()` 关闭 IPC 通道并让 worker 停止接受新连接，是优雅退出的第一步：

```js
// 优雅重启某个 worker
function gracefulRestart(worker) {
  worker.disconnect(); // 1. 关 IPC，worker 不再收新连接
  worker.on('disconnect', () => {
    console.log(`worker ${worker.id} 已断开`);
  });
  // 2. worker 内部 server.close() 处理完在途请求后自然退出
  // 3. 超时未退出则强杀
  setTimeout(() => {
    if (!worker.isDead()) worker.kill('SIGKILL');
  }, 5000);
}
```

`disconnect` vs `kill`：

| 操作 | 行为 | 是否优雅 |
|------|------|----------|
| `worker.disconnect()` | 关 IPC + 停止接受新连接，worker 可处理完在途请求后自退 | 是 |
| `worker.kill(signal)` | 直接发信号，默认 `SIGTERM`，worker 可捕获后清理 | 半优雅（取决于 worker 是否处理信号） |
| `worker.kill('SIGKILL')` | 强杀，worker 立即死亡，在途请求被丢弃 | 否 |

worker 端可监听 `disconnect` 事件配合清理：

```js
// worker 进程内
process.on('message', (msg) => {
  if (msg === 'shutdown') {
    server.close(); // 停止接受新连接，等在途请求完成
    // 处理完后 worker 自然退出
  }
});
```

### 2.7 cluster.schedulingPolicy：RR vs 共享套接字

`cluster.schedulingPolicy` 决定 master 如何把连接分发给 worker：

| 策略 | 常量 | 行为 | 默认 |
|------|------|------|------|
| **Round-Robin** | `cluster.SCHED_RR` | master 收到连接后轮流交给下一个 worker，分配均匀 | 除 Windows 外默认 |
| **共享套接字** | `cluster.SCHED_NONE` | 所有 worker 共享同一个监听套接字，新连接由 OS 内核抢占（可能惊群） | Windows 默认 |

设置方式：

```js
// 必须在 fork 之前设置
cluster.schedulingPolicy = cluster.SCHED_RR;   // 显式轮询
// 或
cluster.schedulingPolicy = cluster.SCHED_NONE;  // 共享套接字
```

**两种策略的权衡：**

- **RR（推荐）**：分配均匀，避免某个 worker 被打满而其他空闲；但 master 进程成为中转站，有轻微开销。
- **共享套接字**：master 不参与分发，开销略低；但 OS 抢占会导致连接分配不均（某些 worker 抢得多），且惊群效应（所有 worker 被唤醒但只有一个拿到连接）浪费 CPU。

> 实际生产中 RR 是默认且推荐策略。共享套接字模式在某些场景（如长连接 WebSocket）可能更合适，但需要谨慎测试。Windows 默认用共享套接字是因为历史原因，新版本也支持 RR。

### 2.8 worker.id 与 worker.process

每个 `Worker` 实例的核心属性：

| 属性 / 方法 | 类型 | 说明 |
|-------------|------|------|
| `worker.id` | number | worker 的唯一标识，从 1 递增，重启的新 worker 会拿到新 id |
| `worker.process` | ChildProcess | 底层子进程对象，可访问 `pid`、`kill()`、`send()` 等 |
| `worker.isConnected()` | method | IPC 通道是否还连着 |
| `worker.isDead()` | method | worker 是否已退出 |
| `worker.send(msg)` | method | 向 worker 发消息（IPC） |
| `worker.disconnect()` | method | 关闭 IPC + 停止接受新连接 |
| `worker.kill([signal])` | method | 发信号杀 worker，默认 `SIGTERM` |

```js
cluster.on('online', (worker) => {
  console.log(`worker 上线: id=${worker.id} pid=${worker.process.pid}`);
  // worker.process 就是 ChildProcess，与 child_process.fork 返回的对象同源
});
```

> `worker.process.pid` 是 OS 层面的进程号（`ps` 能看到），`worker.id` 是 cluster 内部的逻辑编号（重启会变）。日志里两者都记，便于排查"哪个 worker 崩了"。

---

## 三、cluster 实战

### 3.1 创建多核 HTTP 服务器

最经典的 cluster 用法：fork CPU 核数个 worker，每个 worker 跑同一个 HTTP 服务，共享端口。完整代码见 `Code/cluster-http.js`，核心骨架：

```js
const cluster = require('cluster');
const http = require('http');
const os = require('os');

if (cluster.isPrimary) {
  const numCPUs = os.cpus().length;
  console.log(`主进程 pid=${process.pid}，将 fork ${numCPUs} 个 worker`);
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
} else {
  // 每个 worker 都跑一个 HTTP 服务，共享主进程绑定的端口
  http.createServer((req, res) => {
    res.end(`Hello from worker ${cluster.worker.id}, pid=${process.pid}`);
  }).listen(3000);
  console.log(`worker ${cluster.worker.id} 启动，pid=${process.pid}`);
}
```

运行后用浏览器或 `curl http://localhost:3000` 多次访问，会看到响应里 `pid` 在多个值之间轮换——这正是 RR 调度把请求分给了不同 worker。

### 3.2 监听 worker 上线 / 退出

master 上可监听两个事件掌握 worker 生命周期：

```js
cluster.on('online', (worker) => {
  // worker 启动并连上 IPC 后触发
  console.log(`[online] worker ${worker.id} pid=${worker.process.pid}`);
});

cluster.on('exit', (worker, code, signal) => {
  // worker 退出时触发（正常或异常）
  console.log(`[exit] worker ${worker.id} pid=${worker.process.pid} code=${code} signal=${signal}`);
});
```

> 还有 `fork` 事件（`cluster.fork()` 调用时立即触发，早于 `online`）、`listening` 事件（worker 调 `listen` 成功后触发）。`online` 比 `listening` 更早，`listening` 更接近"worker 已就绪可服务"。

### 3.3 自动重启崩溃 worker

生产环境的核心诉求：worker 崩了要立刻补一个。监听 `exit` 并 `fork` 即可：

```js
cluster.on('exit', (worker, code, signal) => {
  console.log(`worker ${worker.id} 挂了 (code=${code})，重启中...`);
  cluster.fork(); // 立即补一个新 worker
});
```

可以故意在 worker 里抛异常测试：

```js
// worker 内
if (Math.random() < 0.05) {
  throw new Error('模拟随机崩溃'); // 5% 概率崩
}
```

观察日志会看到 worker 不断崩溃又被 master 拉起，服务整体不中断（其他 worker 继续处理请求）。

**防雪崩重启：** 若 worker 启动后立刻又崩，会形成"崩溃-重启"死循环榨干 CPU。可加一个时间窗口内的重启计数：

```js
let restartCount = 0;
const RESTART_WINDOW = 10_000; // 10 秒窗口
cluster.on('exit', () => {
  restartCount++;
  if (restartCount > 10) {
    console.error('短时间内重启次数过多，停止 fork，请人工介入');
    process.exit(1);
  }
  cluster.fork();
});
setTimeout(() => { restartCount = 0; }, RESTART_WINDOW).unref();
```

### 3.4 零停机重启（逐个重启 worker）

发布新版本时，如果直接 `kill` 所有 worker 再重启，会有一段所有请求都失败的"空窗期"。零停机重启的思路是**逐个**重启：先 fork 一个新 worker（加载新代码），等它上线能服务后，再 `disconnect` 一个旧 worker，如此循环。完整代码见 `Code/zero-downtime-reload.js`：

```js
function zeroDowntimeReload() {
  const oldWorkers = [...cluster.workers.values()].filter((w) => !w.isDead());
  let restarted = 0;

  function restartNext() {
    if (restarted >= oldWorkers.length) {
      console.log('零停机重启完成');
      return;
    }
    const oldWorker = oldWorkers[restarted];
    // 1. 先 fork 新 worker
    const newWorker = cluster.fork();
    newWorker.on('listening', () => {
      // 2. 新 worker 就绪后再停旧 worker
      oldWorker.disconnect();
      oldWorker.on('disconnect', () => {
        restarted++;
        restartNext(); // 3. 继续下一个
      });
    });
  }
  restartNext();
}
```

关键点：**新 worker `listening` 后才停旧 worker**，确保任意时刻都有足够数量的 worker 在服务。这正是 PM2 `reload` 的底层思路——见 4.6 节。

> 这个手写版本只是演示原理，生产中直接用 PM2 `reload` 即可，它还处理了超时强杀、回滚等边界情况。

---

## 四、PM2 进程管理器

### 4.1 安装

PM2 是一个 npm 全局包，需要 Node 环境即可：

```bash
npm install -g pm2
# 验证
pm2 --version
pm2 --help
```

> 国内网络可配合 `npm config set registry https://registry.npmmirror.com` 加速安装。安装后 `pm2` 命令全局可用。

### 4.2 为什么用 PM2

手写 `cluster` 能实现多核，但生产部署还有一堆"脏活累活"要自己写：

| 痛点 | 手写 cluster | PM2 |
|------|--------------|-----|
| worker 崩溃自动重启 | 自己监听 `exit` + `fork` | 内置，开箱即用 |
| 防雪崩重启计数 | 自己实现 | 内置（`max_restarts`、`exp_backoff_restart_delay`） |
| 零停机发布 | 自己写逐个重启逻辑 | `pm2 reload` 一条命令 |
| 日志收集 | 各 worker 日志混在一起，需自己分流 | 自动按应用分文件，stdout/stderr 分离 |
| 日志切割 | 自己接 winston-daily-rotate | `pm2-logrotate` 模块 |
| 资源监控 | 自己接 prometheus | `pm2 monit` 内置 CPU/内存面板 |
| 开机自启 | 自己写 systemd unit | `pm2 startup` + `pm2 save` 一键生成 |
| 多应用编排 | 一个进程跑一份 cluster | `ecosystem.config.js` 声明多个 app |
| 守护进程 | master 挂了就全挂 | PM2 daemon 独立守护，master 挂了也会被拉起 |

一句话：**PM2 把 cluster 的能力打包成命令行，外加一整套运维工具链**。对裸机部署的 Node 服务，PM2 几乎是事实标准。

### 4.3 核心命令速查

| 命令 | 作用 | 常用示例 |
|------|------|----------|
| `pm2 start` | 启动应用 | `pm2 start app.js` / `pm2 start ecosystem.config.js` |
| `pm2 stop` | 停止应用（保留进程记录，不释放端口直到 stop） | `pm2 stop app` / `pm2 stop all` |
| `pm2 restart` | 重启应用（杀掉再起，**有短暂不可用**） | `pm2 restart app` |
| `pm2 reload` | **零停机重载**（逐个重启 worker，集群模式专属） | `pm2 reload app` |
| `pm2 delete` | 删除应用（从 PM2 进程列表移除） | `pm2 delete app` / `pm2 delete all` |
| `pm2 status` / `pm2 ls` / `pm2 list` | 查看进程列表与状态 | `pm2 status` |
| `pm2 monit` | 终端面板，实时看 CPU/内存/日志 | `pm2 monit` |
| `pm2 logs` | 查看日志（实时滚动） | `pm2 logs app` / `pm2 logs --lines 100` |
| `pm2 save` | 保存当前进程列表到 dump 文件 | `pm2 save` |
| `pm2 resurrect` | 从 dump 文件恢复进程列表（机器重启后用） | `pm2 resurrect` |
| `pm2 startup` | 生成开机自启脚本（systemd/upstart） | `pm2 startup systemd` |
| `pm2 flush` | 清空所有日志文件内容 | `pm2 flush` |
| `pm2 describe` | 查看某应用详细信息 | `pm2 describe app` |

> 速查表另见 `Code/pm2-commands.md`。最常用的是 `start` / `status` / `logs` / `reload` / `monit` 五条。

### 4.4 ecosystem.config.js 配置文件

命令行启动适合临时跑，生产环境推荐用 `ecosystem.config.js` 声明式配置，便于版本管理与多环境切换。完整文件见 `Code/ecosystem.config.js`，核心字段：

```js
module.exports = {
  apps: [
    {
      name: 'ai-api',                // 应用名（pm2 status 里显示的名字）
      script: './app.js',            // 入口脚本
      instances: 'max',              // worker 数量：'max' = CPU 核数，也可写数字如 4
      exec_mode: 'cluster',          // 集群模式（多进程共享端口）；'fork' 为单进程
      max_memory_restart: '500M',    // 单 worker 内存超 500M 自动重启
      env: {                         // 默认环境（开发）
        NODE_ENV: 'development',
        PORT: 3000
      },
      env_production: {              // --env production 时使用
        NODE_ENV: 'production',
        PORT: 8080
      }
    }
  ]
};
```

启动方式：

```bash
# 用默认 env
pm2 start ecosystem.config.js
# 用 env_production（合并到 env 之上，同名键覆盖）
pm2 start ecosystem.config.js --env production
```

**关键字段说明：**

| 字段 | 说明 |
|------|------|
| `name` | 应用名，PM2 用它标识进程组，后续 stop/reload 都用这个名字 |
| `script` | 入口文件路径，相对于配置文件所在目录 |
| `instances` | worker 数量。`'max'` = CPU 核数；数字 = 指定数量；cluster 模式下建议 `max` 或核数 |
| `exec_mode` | `'cluster'`（多进程，共享端口，可用 reload）；`'fork'`（单进程，类似直接 node 启动） |
| `max_memory_restart` | 内存阈值自动重启，防内存泄漏拖垮机器。格式如 `'500M'` / `'1G'` |
| `env` | 基础环境变量，所有模式都生效 |
| `env_<name>` | 用 `--env <name>` 激活的环境变量，会**合并覆盖** `env` |
| `cwd` | 工作目录，默认配置文件所在目录 |
| `watch` | 文件变化自动重启（开发用，生产别开） |
| `ignore_watch` | watch 时忽略的文件/目录 |
| `out_file` / `error_file` | 日志输出文件，默认 `~/.pm2/logs/<name>-out.log` |
| `merge_logs` | 多 worker 日志合并到同一文件 |
| `time` | 日志加时间戳前缀 |
| `max_restarts` | 单位时间内最大重启次数，超过则认为"反复崩溃" |
| `exp_backoff_restart_delay` | 指数退避重启延迟，防雪崩 |

**多应用编排：** `apps` 数组可声明多个应用，一次性管理多个服务（如 API 服务 + 定时任务 worker + WebSocket 服务）：

```js
module.exports = {
  apps: [
    { name: 'api', script: './api.js', instances: 'max', exec_mode: 'cluster' },
    { name: 'worker', script: './worker.js', instances: 1, exec_mode: 'fork' },
    { name: 'ws', script: './ws.js', instances: 2, exec_mode: 'cluster' }
  ]
};
```

`pm2 start ecosystem.config.js` 会一次性启动所有 app，`pm2 reload ecosystem.config.js` 一次性重载。

### 4.5 PM2 集群模式 vs fork 模式

PM2 的两种 `exec_mode`：

| 维度 | `exec_mode: 'cluster'` | `exec_mode: 'fork'` |
|------|------------------------|----------------------|
| 进程数 | N 个 worker 共享端口（底层就是 cluster 模块） | 单进程，与直接 `node app.js` 等价 |
| 多核利用 | 是（N 个 worker 吃 N 个核） | 否（只吃一个核） |
| `pm2 reload` 零停机 | **支持**（逐个重启 worker） | **不支持**（只能 restart，有短暂不可用） |
| 适用 | HTTP / WebSocket 等监听端口的服务 | 定时任务、消费者 worker、不需要多核的脚本 |
| IPC | worker 与 PM2 daemon 通信 | 单进程无 IPC |

经验法则：**监听端口的服务用 cluster 模式 + `instances: 'max'`；不监听端口的消费者/定时任务用 fork 模式 + `instances: 1`**。

### 4.6 PM2 reload 零停机原理

`pm2 reload` 是 PM2 最有价值的能力之一，它实现了真正的零停机发布：

```
reload 之前:  [w1(旧), w2(旧), w3(旧), w4(旧)]  全部服务中

第 1 步: fork w1(新)，等它 listening
         [w1(新), w1(旧), w2(旧), w3(旧), w4(旧)]  ← 多了一个，新代码就绪

第 2 步: w1(旧).disconnect()，等它处理完在途请求退出
         [w1(新), w2(旧), w3(旧), w4(旧)]  ← 旧 w1 优雅退出

第 3 步: fork w2(新)，listening 后 w2(旧).disconnect()
         [w1(新), w2(新), w3(旧), w4(旧)]

... 重复，直到所有 worker 都换为新代码 ...

reload 完成: [w1(新), w2(新), w3(新), w4(新)]
```

任意时刻都有 worker 在服务，外部感受不到停机。这正是 3.4 节手写"逐个重启"逻辑的封装版。

`reload` vs `restart`：

| 命令 | 行为 | 是否零停机 | 适用 |
|------|------|-----------|------|
| `pm2 restart` | 杀掉所有 worker，再重新 fork | **否**（有短暂空窗） | 配置变更、紧急重启 |
| `pm2 reload` | 逐个重启 worker，新旧并存过渡 | **是** | 发布新版本代码（cluster 模式） |

> reload 只对 `exec_mode: 'cluster'` 生效，fork 模式会回退成 restart。reload 也支持超时配置（`--update-env`、`kill_timeout`），超时未退出的旧 worker 会被强杀。

### 4.7 日志管理

PM2 自动为每个应用维护两类日志：

```
~/.pm2/logs/
├── ai-api-out.log      # stdout（console.log）
├── ai-api-error.log    # stderr（console.error）
├── ai-api-out__1.log   # cluster 模式下每个 worker 可单独分文件（不 merge 时）
└── ...
```

常用命令：

```bash
pm2 logs                    # 实时查看所有应用日志
pm2 logs ai-api             # 只看某应用
pm2 logs ai-api --lines 200 # 看最近 200 行
pm2 flush                   # 清空所有日志（文件保留，内容清空）
pm2 install pm2-logrotate   # 安装日志切割模块
```

**日志切割（pm2-logrotate）：**

PM2 默认日志文件会无限增长，必须配 `pm2-logrotate` 切割：

```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M       # 单文件超 10M 切割
pm2 set pm2-logrotate:retain 30          # 保留 30 个历史文件
pm2 set pm2-logrotate:compress true      # 切割后的旧文件 gzip 压缩
pm2 set pm2-logrotate:dateFormat YYYY-MM-DD_HH-mm-ss
pm2 set pm2-logrotate:rotateInterval '0 0 * * *'  # 每天 0 点切割
```

> 日志采集建议：PM2 写文件 → Filebeat / Promtail 采集 → ELK / Loki 集中检索（呼应 Day14 的日志聚合方案）。容器化场景下更推荐直接输出到 stdout/stderr，由容器运行时（Docker / K8s）统一采集，不在容器内做文件切割。

### 4.8 PM2 startup 开机自启

服务器重启后 Node 服务要能自动拉起，PM2 用两步实现：

```bash
# 1. 生成开机自启脚本（自动识别系统类型 systemd/upstart/launchd）
pm2 startup
# 它会打印一条类似下面的命令，复制执行（需要 sudo）：
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u youruser --hp /home/youruser

# 2. 保存当前正在运行的应用列表
pm2 save
# 这会把进程列表写到 ~/.pm2/dump.pm2，开机时 startup 脚本用 pm2 resurrect 恢复
```

原理：`pm2 startup` 生成一个 systemd service（名为 `pm2-youruser`），开机时由 systemd 启动 PM2 daemon，daemon 再执行 `pm2 resurrect` 从 dump 文件恢复所有应用。因此**每次新增/删除应用后都要 `pm2 save` 一次**，否则重启后恢复的是旧列表。

---

## 五、cluster vs PM2 对比

| 维度 | 手写 cluster | PM2 |
|------|--------------|-----|
| **易用性** | 需写 30~100 行 fork / 重启 / 退出逻辑 | 一条 `pm2 start` 命令 |
| **多核扩展** | ✅ 原生支持 | ✅（底层就是 cluster） |
| **崩溃自愈** | 自己监听 `exit` + `fork` | 内置，含防雪崩退避 |
| **零停机发布** | 自己写逐个重启 | `pm2 reload` 一条命令 |
| **日志管理** | 自己接 winston + 轮转 | 内置文件分流 + logrotate 模块 |
| **资源监控** | 自己接 prometheus / grafana | `pm2 monit` 内置面板 |
| **开机自启** | 自己写 systemd unit | `pm2 startup` 一键 |
| **多应用编排** | 一个进程一份代码 | `ecosystem.config.js` 统一声明 |
| **守护进程** | master 挂了全挂 | PM2 daemon 独立守护 |
| **可控性** | 高（完全自定义） | 中（受 PM2 行为约束） |
| **依赖** | 无（内置模块） | 需全局装 PM2 |
| **学习成本** | 中（要懂 IPC / 信号 / 调度） | 低（命令行） |
| **生产推荐** | 学习原理、特殊定制场景 | **裸机部署首选** |

结论：**学 cluster 是为了理解原理、能读 PM2 源码思路；上线裸机部署直接用 PM2**。除非有 PM2 不满足的定制需求（如自定义调度、特殊 IPC 协议），否则没必要手写。

---

## 六、容器化时代 PM2 的取舍

进入 Docker / K8s 时代后，"要不要在容器里用 PM2"成了一个需要权衡的问题。

### 6.1 两种主流思路

**思路 A：单容器单进程 + 编排器管理副本（主流推荐）**

```
Docker Compose:
  api:
    image: ai-api
    deploy:
      replicas: 4        # 4 个容器，每个 1 个 Node 进程
      resources:
        limits:
          cpus: '1'      # 每个容器限 1 核
K8s:
  Deployment: replicas: 4
  每个 Pod 跑 1 个 Node 进程
```

容器内直接 `node app.js`（或 `npm start`），不装 PM2。多核扩展由"多容器副本"实现，崩溃自愈由编排器（K8s 的 `restartPolicy` / Compose 的 `restart: always`）负责。

**思路 B：单容器内 PM2 cluster（传统思路）**

```
Dockerfile:
  CMD ["pm2-runtime", "ecosystem.config.js", "--env production"]
容器内: 1 个 PM2 daemon + N 个 worker（吃满本机多核）
```

容器内用 PM2 fork 多个 worker 利用本机多核，编排器只管 1 个容器副本。

### 6.2 取舍对比

| 维度 | 单容器单进程（思路 A） | 单容器 PM2（思路 B） |
|------|------------------------|----------------------|
| 多核利用 | 靠多副本，每个副本 1 核 | 单容器内多 worker 吃满多核 |
| 水平扩展 | ✅ 天然支持（加副本即可） | ❌ 不直观（要改容器配额） |
| 崩溃自愈 | 编排器重启整个容器 | PM2 重启单个 worker（更快） |
| 零停机发布 | 滚动更新（K8s rolling update） | `pm2 reload`（容器内） |
| 日志采集 | stdout → 容器日志驱动 → 集中 | PM2 文件 → 需额外采集 |
| 资源隔离 | ✅ 容器边界清晰，CPU/内存限额精确 | ❌ 一个 worker OOM 可能影响其他 |
| 进程信号 | 容器停止发 SIGTERM，Node 直接处理 | 信号要穿透 PM2 daemon，行为复杂 |
| 12-Factor | ✅ 符合"单进程"原则 | ❌ 容器内多进程，违背单容器单职责 |
| 运维心智 | 编排器一套语法通吃 | 容器 + PM2 两套，认知负担 |

### 6.3 结论

- **K8s / Compose 编排的生产环境**：推荐思路 A（单容器单进程）。多核扩展交给副本数，自愈交给 `restartPolicy`，零停机交给滚动更新，日志交给 stdout + 集中采集。容器内装 PM2 反而增加信号穿透、日志采集、资源隔离的复杂度。
- **裸机部署、单机多核、无编排器**：推荐 PM2（思路 B）。一台云主机跑一个 PM2，榨干多核，开机自启、日志切割、零停机 reload 一站式解决。
- **过渡阶段**：从裸机 PM2 迁移到 K8s 时，常见做法是把 `ecosystem.config.js` 的 `instances` 改成 `1`、`exec_mode` 改成 `fork`，逐步把多核职责从"容器内 PM2"转移到"容器副本数"。

> 本节为后续 Docker 板块铺垫。记住一个原则：**容器里最好只跑一个进程**，让编排器去做水平扩展与自愈——这是云原生的主流姿势。PM2 的舞台主要在"没有编排器的裸机"。

---

## 七、优雅退出最佳实践

无论是 cluster worker、PM2 进程还是容器内的 Node 服务，收到停止信号后的优雅退出流程都是一致的。这是 Day15 信号处理的进阶应用，也是生产上线的必备能力。

### 7.1 为什么要优雅退出

直接 `kill -9`（SIGKILL）的问题：

- **在途请求被丢弃**：用户正在等响应的请求直接断连，体验差。
- **数据库连接未释放**：连接池里的连接被强杀，数据库侧积累 idle 连接。
- **事务未提交**：写到一半的数据回滚不一致。
- **缓存未持久化**：内存队列里的任务丢失。
- **临时文件未清理**：上传的临时文件残留。

优雅退出要解决这些问题：让进程"把手里活干完再走"。

### 7.2 标准流程

收到 `SIGTERM`（K8s / Docker 停容器、`kill <pid>` 默认信号）或 `SIGINT`（Ctrl+C）后，按以下步骤退出：

```
SIGTERM/SIGINT 到达
       │
       ▼
1. 标记进入 shuttingDown 状态（拒绝新请求，健康检查返回 503）
       │
       ▼
2. server.close() —— 停止接受新连接，但已建立的连接继续处理
       │
       ▼
3. 等待在途请求处理完成（设置超时，如 30s）
       │
       ▼
4. 关闭数据库连接、Redis 连接、消息队列消费者
       │
       ▼
5. flush 日志、清理临时文件
       │
       ▼
6. process.exit(0) 正常退出
       │
       ▼
（超时未完成）→ 强制 process.exit(1)
```

### 7.3 代码模板

完整实现见 `Code/graceful-shutdown.js`，核心逻辑：

```js
const server = http.createServer(handler);
server.listen(3000);

let shuttingDown = false;

async function shutdown(signal) {
  if (shuttingDown) return; // 防止重复触发
  shuttingDown = true;
  console.log(`\n收到 ${signal}，开始优雅退出`);

  // 1. 停止接受新请求
  server.close();

  // 2. 等待在途请求完成（设超时）
  const forceExit = setTimeout(() => {
    console.error('超时仍未退出，强制退出');
    process.exit(1);
  }, 10_000);
  forceExit.unref();

  // 3. 关闭数据库等资源
  await closeDatabase();
  await closeRedis();

  // 4. flush 日志
  logger.on('finish', () => process.exit(0));
  logger.end();
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
```

### 7.4 各场景的超时配合

优雅退出不是单方面的事，需要上下游配合：

| 场景 | 上游给的超时 | 你的退出超时 | 行为 |
|------|-------------|-------------|------|
| K8s 停 Pod | `terminationGracePeriodSeconds`（默认 30s） | 应小于上游，如 25s | K8s 先发 SIGTERM，等宽限期后 SIGKILL |
| Docker stop | `--stop-timeout`（默认 10s） | 应小于上游，如 8s | 同上 |
| PM2 reload | `kill_timeout`（默认 1600ms） | 应小于上游 | PM2 发 SIGTERM，超时 SIGKILL |
| 负载均衡摘除 | 健康检查间隔 × 重试次数 | 摘除后才发 SIGTERM | 先摘流量再停，避免 LB 还在转发 |

> 关键原则：**你的优雅退出超时必须小于上游的强制杀死超时**，否则你还没处理完就被 SIGKILL 了。K8s 默认 30s 宽限期，你的 `server.close` 超时应设为 25s 左右留余量。

### 7.5 健康检查配合

优雅退出的第一步应是**让健康检查失败**，让负载均衡器把流量摘掉，再开始 `server.close`：

```js
// 健康检查端点
app.get('/health', (req, res) => {
  if (shuttingDown) return res.status(503).json({ status: 'shutting down' });
  res.json({ status: 'ok' });
});
```

K8s 的 `preStop` hook 可以先 sleep 一段时间，等 readiness probe 失败、LB 摘流量后再让主进程收 SIGTERM：

```yaml
lifecycle:
  preStop:
    exec:
      command: ["sleep", "10"]   # 给 LB 10s 时间摘流量
```

---

## 八、关键知识点总结

1. **Node 单进程单线程在多核机器上只吃一个核**，8 核服务器直接 `node app.js` 利用率仅 12.5%。多核扩展三大方案：多端口+Nginx、`worker_threads`、`cluster` 模块。
2. **cluster 架构**：1 个 master + N 个 worker，worker 共享同一端口，底层靠 IPC 通信，master 不处理业务只负责调度。`cluster.fork()` 本质是 `child_process.fork()`，但 cluster 拦截 `server.listen` 让多 worker 共享端口。
3. **角色判别**：`cluster.isPrimary`（Node 16+ 推荐）/ `cluster.isMaster`（旧名）判主进程，`cluster.isWorker` 判 worker。同一份脚本靠它分流，否则 worker 会无限 fork。
4. **worker 生命周期**：`fork` 事件 → `online` 事件（连上 IPC）→ `listening` 事件（`listen` 成功）→ `exit` 事件（退出）。生产必须监听 `exit` 自动重启，并加防雪崩计数。
5. **优雅停 worker**：`worker.disconnect()` 关 IPC + 停新连接（优雅），`worker.kill()` 发信号（默认 SIGTERM 可捕获），`worker.kill('SIGKILL')` 强杀。优先 disconnect，超时才强杀。
6. **调度策略**：`cluster.SCHED_RR`（round-robin 轮询，master 分发，分配均匀，非 Windows 默认）vs `cluster.SCHED_NONE`（共享套接字，OS 抢占，Windows 默认）。生产推荐 RR。
7. **worker 对象**：`worker.id`（cluster 内部逻辑编号，重启会变）、`worker.process`（ChildProcess 实例，含 `pid`）、`worker.send()` / `on('message')` 双向 IPC。
8. **零停机重启**：逐个重启——先 fork 新 worker，等它 `listening` 后再 disconnect 旧 worker，确保任意时刻都有 worker 服务。这是 PM2 reload 的底层思路。
9. **PM2 是 cluster 的命令行封装 + 运维工具链**：开箱即用的崩溃自愈、零停机 reload、日志分流、logrotate、monit 监控、startup 开机自启、ecosystem 多应用编排。裸机部署首选。
10. **ecosystem.config.js**：声明式配置，`apps` 数组多应用、`instances: 'max'` 吃满核数、`exec_mode: 'cluster'` 集群模式、`max_memory_restart` 防内存泄漏、`env` / `env_production` 多环境切换。
11. **reload vs restart**：`restart` 杀掉再起有空窗（不零停机），`reload` 逐个重启新旧并存（零停机，仅 cluster 模式）。发布新代码用 reload，配置大改用 restart。
12. **容器化取舍**：K8s/Compose 编排环境推荐单容器单进程（多核靠副本数、自愈靠 restartPolicy、零停机靠滚动更新），PM2 适合裸机部署。容器内最好只跑一个进程是云原生主流姿势。
13. **优雅退出标准流程**：SIGTERM → 标记 shuttingDown（健康检查 503 摘流量）→ `server.close()` 停新连接 → 等在途请求完成 → 关数据库/Redis → flush 日志 → `process.exit(0)`，超时则强杀。退出超时要小于上游（K8s 30s 宽限期）。
14. **健康检查配合**：退出时先让 `/health` 返回 503，等 LB 摘流量（K8s preStop sleep）再 `server.close`，避免 LB 还在往正在关闭的进程转发请求。

---

## 九、实战练习

> 以下练习在 `Code/` 目录基础上扩展，建议独立完成后再对照本篇结论自查。

### 练习一：给 cluster 服务器加"防雪崩重启 + worker 心跳"

**目标**：增强 `cluster-http.js`，避免"崩溃-重启"死循环，并让 master 能感知 worker 是否存活。

**要求**：

1. master 维护一个时间窗口（如 10 秒）内的重启计数，超过阈值（如 5 次）则停止 fork 并 `process.exit(1)`，让上层（PM2 / systemd）介入。
2. worker 启动后每 5 秒通过 IPC 向 master 发一条 `{ type: 'heartbeat', ts: Date.now() }`。
3. master 记录每个 worker 最后心跳时间，若超过 15 秒未收到心跳，则认为 worker 卡死，主动 `worker.kill()` 触发重启。
4. 思考：为什么"卡死但不退出"的 worker 比直接崩溃的 worker 更难处理？

**考察点**：cluster 事件、IPC 双向通信、防雪崩、心跳健康检测。

### 练习二：用 PM2 部署一个 Express 服务并验证零停机

**目标**：把 Day14 的 Express 错误处理服务用 PM2 集群模式跑起来，验证 `reload` 的零停机效果。

**要求**：

1. 写一个简单的 `app.js`，启动 Express 服务监听 3000，根路由返回 `version: 1` 与 `pid`。
2. 写 `ecosystem.config.js`，`instances: 'max'`、`exec_mode: 'cluster'`、`max_memory_restart: '300M'`，区分 `env` 与 `env_production`。
3. `pm2 start ecosystem.config.js --env production` 启动，用 `pm2 status` / `pm2 monit` 观察。
4. 开一个终端持续 `while true; do curl -s http://localhost:3000; echo; done`（Windows 用 PowerShell 循环），观察请求被分到不同 pid。
5. 修改 `app.js` 让根路由返回 `version: 2`，执行 `pm2 reload ecosystem.config.js`，观察：reload 过程中 curl 是否始终能拿到响应？版本号何时从 1 切到 2？有没有 502 / 连接拒绝？
6. 对比：改用 `pm2 restart`，观察是否有短暂连接失败。
7. 思考：为什么 reload 期间偶有请求仍返回旧版本？这是否算"零停机"？

**考察点**：PM2 ecosystem 配置、reload vs restart、零停机验证、负载均衡观察。

### 练习三：实现一个支持优雅退出的 cluster master

**目标**：让 master 收到 `SIGTERM` 后，逐个优雅关闭所有 worker 再退出，而非直接 `process.exit`。

**要求**：

1. master 监听 `SIGTERM` 与 `SIGINT`。
2. 收到信号后，对所有 worker 调用 `disconnect()`，并设置 5 秒超时。
3. 监听每个 worker 的 `exit` 事件，全部退出后 master `process.exit(0)`。
4. 5 秒内未退出的 worker，用 `worker.kill('SIGKILL')` 强杀。
5. 期间拒绝 fork 新 worker（用一个 `isShuttingDown` 标志）。
6. 测试：启动服务，用 `curl` 发起一个耗时 2 秒的请求，立即 `kill` master 进程，确认该请求能正常返回而非中断。
7. 思考：K8s 停 Pod 时，先停 master 还是先停 worker？为什么容器里"单容器单进程"模式反而没有这个主从退出顺序问题？

**考察点**：master 优雅退出、worker.disconnect + 超时强杀、在途请求保护、容器化与主从进程的关系。

---

> 完成本篇后，你已掌握让 Node.js 服务"多核并行 + 崩溃自愈 + 零停机发布 + 优雅退出"的完整能力链，并能根据部署形态（裸机 vs 容器）选择合适的进程管理策略。下一篇将进入 **Docker 容器化** 或 **Node 与数据库集成** 主题，把"能跑多核"的服务推向"可打包、可移植、可弹性伸缩"的云原生形态。
