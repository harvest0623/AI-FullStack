# Day20 - 性能优化与部署上线

> 本篇是 Node.js 板块的"毕业篇"：把一个能跑的服务，推向一个**快、稳、安全、可上线**的服务。前端工程师习惯于"打包即上线"，但服务端的上线意味着：进程要扛住并发、内存不能泄漏、依赖不能有漏洞、容器要小、流量前要有反向代理、停机要不丢请求。本篇从**性能测量**出发，依次讲透 CPU / 内存 / 网络 I/O 三大优化维度，再过一遍安全加固清单与部署上线流程（PM2 / Docker / Nginx / CI/CD），最后落到 AI 全栈视角：如何把模型推理服务化并稳定地暴露给前端。这是后续做 Agent 后端、模型 API 网关的工程底座。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 性能优化三大维度](#21-性能优化三大维度)
  - [2.2 性能测量工具](#22-性能测量工具)
  - [2.3 常见性能瓶颈](#23-常见性能瓶颈)
- [三、CPU 优化](#三cpu-优化)
- [四、内存优化](#四内存优化)
- [五、网络 I/O 优化](#五网络-io-优化)
- [六、数据库优化](#六数据库优化)
- [七、安全加固清单](#七安全加固清单)
- [八、部署上线](#八部署上线)
- [九、生产环境配置清单](#九生产环境配置清单)
- [十、AI 全栈视角](#十ai-全栈视角)
- [十一、关键知识点总结](#十一关键知识点总结)
- [十二、实战练习](#十二实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说出服务端性能优化的三大维度（CPU 计算 / 内存 / 网络 I/O），并针对每个维度各举一个典型瓶颈与对应解法。
2. 选用合适的性能测量工具：`console.time` 粗测、`performance.now` 精确对比、`process.memoryUsage/cpuUsage` 资源监控、`node --inspect` + Chrome DevTools 在线调试、`clinic.js` 与 `0x` 火焰图定位热点。
3. 解释"同步阻塞事件循环"的危害，并用 `setImmediate` 分片或 `worker_threads`/子进程把 CPU 密集任务移出主事件循环。
4. 实现一个内存 LRU 缓存，说明它为何能大幅降低读多写少场景的延迟，以及何时必须升级到 Redis。
5. 区分 `readFile` 整体加载与 Stream 流式处理的内存差异，说出对象池、Buffer 共享内存、避免闭包持有大对象等内存优化手段。
6. 配置 HTTP keep-alive、gzip/brotli 压缩、HTTP/2、静态资源缓存与 CDN，解释每一项压缩了哪一段延迟。
7. 识别 N+1 查询问题，给出索引、分页、避免 `SELECT *`、JOIN/populate、查询缓存、连接池调优等数据库优化手段。
8. 落地一套生产安全配置：`npm audit` 依赖审计、Helmet、CORS 白名单、限流、输入校验、日志脱敏、HTTPS/HSTS、Cookie 安全属性。
9. 编写多阶段 Dockerfile（非 root、HEALTHCHECK、exec 形式 CMD）、Nginx 反向代理配置、PM2 cluster 配置，并说明三者各自的职责边界。
10. 区分存活探针 `/health` 与就绪探针 `/ready`，实现带优雅退出标志的健康检查端点（呼应 Day16 优雅停机）。
11. 从 AI 全栈视角描述模型推理服务化的关键工程点：常驻加载、限流队列、流式响应、GPU 资源管理、推理耗时与成功率监控。

---

## 二、理论知识讲解

### 2.1 性能优化三大维度

服务端的"慢"通常来自三个地方，优化前必须先分清瓶颈在哪，否则南辕北辙：

| 维度 | 瓶颈特征 | 典型场景 | 优化方向 |
|------|----------|----------|----------|
| **CPU 计算** | 进程 CPU 打满，单核 100%；事件循环被同步任务卡住 | 加密、JSON 序列化、图像处理、大模型预处理 | 移出主线程（worker/子进程）、算法优化、缓存 |
| **内存** | `heapUsed` 持续上涨不回落，GC 频繁暂停；OOM 崩溃 | 大文件全量加载、对象未释放、闭包持有、内存泄漏 | Stream、对象池、排查泄漏、调大堆 |
| **网络 I/O** | CPU/内存都不高，但响应慢；大量时间花在"等" | 数据库往返、HTTP 调用、未分页、N+1 查询 | 连接池、批量化、缓存、CDN、压缩 |

> **前端经验对照**：浏览器里"慢"多半是渲染或脚本阻塞主线程；服务端"慢"则更常是"在等外部资源"（数据库、下游服务）。一个新手的典型误区是把 CPU 优化技巧（算法复杂度）用在本质上属于 I/O 等待的瓶颈上——再快的算法也快不过一次未发起的数据库查询。

**判别方法**：先看监控——CPU 高 → 查 CPU 维度；CPU 不高但慢 → 多半是 I/O 等待；内存涨 → 查内存泄漏。**没有测量就没有优化**，下一节讲工具。

### 2.2 性能测量工具

"先量后优"是铁律。Node 生态有一套从粗到精的工具链：

| 工具 | 粒度 | 适用场景 | 用法速览 |
|------|------|----------|----------|
| `console.time/timeEnd` | 粗（毫秒） | 快速验证"哪段慢" | `console.time('x'); ...; console.timeEnd('x')` |
| `performance.now()` | 精（亚毫秒浮点） | 对比两段代码、基准测试 | `const t=performance.now(); ...; performance.now()-t` |
| `process.memoryUsage()` | 进程级内存 | 监控堆/rss，排查泄漏 | `process.memoryUsage().heapUsed` |
| `process.cpuUsage()` | 进程级 CPU | 区分 user/system 时间 | `process.cpuUsage(prev)` 取差值 |
| `node --inspect` + Chrome DevTools | 在线交互 | 实时调试、断点、CPU/内存 profile | `node --inspect app.js` → chrome://inspect → Memory/CPU |
| `clinic.js` | 自动诊断 | 定位"是 CPU / I/O / 事件循环"哪类问题 | `clinic doctor -- node app.js` |
| `0x` | 火焰图 | 定位 CPU 热点函数 | `0x -o profile.json -- node app.js` |

**几个关键说明：**

- **`console.time` vs `performance.now`**：前者简单但精度受限且只能输出到控制台；后者来自 `perf_hooks`，返回浮点毫秒，可参与计算与日志记录，是基准测试首选。本篇 `Code/performance-measure.js` 同时用两者对比同一段代码。

- **`process.memoryUsage()` 的四个指标**：
  - `rss`（Resident Set Size）：进程实际占用的物理内存，包含堆、栈、C++ 对象。OOM 判断看它。
  - `heapTotal`：V8 已申请的堆总量。
  - `heapUsed`：堆中实际使用的部分，**排查泄漏的核心指标**——若它持续上涨且 GC 后不回落，基本就是泄漏。
  - `external`：V8 之外的 C++ 对象内存（如 Buffer 内容），Buffer 大量使用时关注它。

- **`--inspect` 调试流**：`node --inspect app.js` 启动后，打开 Chrome 访问 `chrome://inspect`，点击 "inspect" 即可连上。DevTools 的 **Memory** 面板能抓堆快照（Heap Snapshot）对比两次快照找出"只增不减"的对象；**Performance** 面板能录 CPU profile。**注意生产环境不要开 `--inspect=0.0.0.0`**，否则等于把调试端口暴露给公网。

- **`clinic.js` 三件套**：
  - `clinic doctor`：综合体检，给出"是 CPU / I/O / 事件循环延迟 / 内存"哪类问题的判断。
  - `clinic bubbleprof`：把异步操作画成气泡图，看 I/O 等待链路。
  - `clinic flame`：火焰图，定位 CPU 热点函数。

- **`0x` 火焰图**：把 V8 采样 profile 渲染成可交互的火焰图，横轴是调用栈、纵轴是耗时占比，哪个函数"最宽"就是热点。适合"CPU 打满了但不知道是谁干的"。

> **AI 场景提示**：大模型推理本身是 GPU/CPU 密集 + 网络 I/O 混合负载。测量时要分开记录"请求进入→推理开始"的排队时间与"推理开始→结束"的计算时间，否则分不清是模型慢还是队列堵。详见第十节。

### 2.3 常见性能瓶颈

这些是 Node 服务端"踩过最多次"的坑，按出现频率排序：

| 瓶颈 | 现象 | 根因 | 解法 |
|------|------|------|------|
| **同步阻塞事件循环** | 整个服务间歇性卡顿，所有请求一起变慢 | 一段同步 CPU 密集代码独占主线程 | 分片/移到 worker/子进程 |
| **N+1 查询** | 列表接口慢，DB 查询数 = 1 + N | 循环里逐条查关联数据 | JOIN / populate / 批量 IN 查询 |
| **未分页** | 数据量上来后单次响应几十 MB | 一次返回全部记录 | 分页 limit/offset 或游标 |
| **大 JSON 序列化** | CPU 飙高、响应慢 | `JSON.stringify` 巨大对象阻塞主线程 | 流式序列化、分页、按需字段 |
| **内存泄漏** | 运行越久内存越高，最终 OOM 重启 | Map/闭包无限增长、监听器未解绑 | heapdump 排查、LRU 限容 |
| **未用流** | 处理大文件时内存暴涨 | `fs.readFile` 一次性读全量 | `fs.createReadStream` + pipeline |
| **连接未复用** | 每次请求新建 DB/HTTP 连接，握手耗时 | 未配置连接池 / keep-alive | 连接池、Agent keepAlive |

---

## 三、CPU 优化

### 3.1 避免阻塞事件循环

Node 是单线程事件循环模型：所有 JS 代码跑在同一个主线程上。一段同步代码跑 500ms，这 500ms 内**所有**其他请求、定时器、I/O 回调都得排队。这是 Node 最需要建立的心智。

> 一个直观实验见 `Code/performance-measure.js`：一个 50ms 触发一次的定时器作为"事件循环探针"。同步跑 8 百万次循环时探针一次都不响；改成每 50 万次用 `setImmediate` 让出一次，探针就能持续触发——代价是总耗时略增。

三种处理 CPU 密集任务的策略，按"侵入性"递增：

1. **`setImmediate` 分片**：把大任务切成小块，每块跑完 `setImmediate(runNextChunk)` 让出事件循环。适合"想留在主线程又不想卡死"的场景，如大批量数据处理。缺点是总耗时略增（调度开销）。

2. **`worker_threads`**：Node 内置的多线程模块，适合 CPU 密集且需要共享内存的场景。每个 worker 是独立 V8 实例，通过 `MessagePort` 通信。适合加解密、图像处理、大模型预处理。

   ```js
   const { Worker } = require('worker_threads');
   const worker = new Worker('./heavy-task.js');
   worker.postMessage({ data });
   worker.on('message', (result) => { /* 拿到结果 */ });
   ```

3. **子进程（`child_process` / `fork`）**：完全独立的进程，适合调用外部程序（如 Python 脚本、CLI 工具）。开销比 worker 大，但隔离性最好。Day15 已详述。

> 经验法则：**I/O 密集用异步回调即可（Node 擅长）；CPU 密集必须移出主线程**。前端工程师常误以为"异步 = 不阻塞"，但 `Promise` 里包一段同步循环照样卡死事件循环——异步只是改变了"等待 I/O"的方式，不改变"同步计算"的独占性。

### 3.2 缓存

缓存是性价比最高的优化：与其算第二次，不如直接拿第一次的结果。

- **内存 LRU 缓存**：单进程内，命中延迟亚毫秒级。本篇 `Code/caching-demo.js` 实现了一个基于 `Map` 的 LRU：`Map` 保持插入顺序，访问时 `delete + set` 即可"提到最新"，超容时淘汰 `map.keys().next().value`（最久未用）。实测把 20ms 的模拟 DB 查询降到 0ms。
- **Redis 缓存**：跨进程、跨实例共享，支持 TTL、LRU、发布订阅。多实例部署时**必须**用 Redis，否则每个实例各自缓存，既不一致又重复。
- **缓存策略**：读时查缓存 → 未命中查 DB → 回填缓存；写时更新 DB → 删除（而非更新）缓存，避免并发写导致脏数据。

> 缓存的代价是**一致性**：缓存有 TTL，期间 DB 改了缓存看不到。对"配置""热门数据""模型元信息"这类读多写少、可容忍短暂不一致的场景最合适；对"余额""库存"等强一致场景要慎用或配合失效策略。

### 3.3 算法与数据结构选择

这是放之四海皆准的优化，但在 Node 里有个特殊点：**V8 的 JIT（即时编译）对数据形状敏感**。

- 选对数据结构：查重用 `Set`（O(1)）而非 `Array.includes`（O(n)）；键值映射用 `Map` 而非普通对象（Map 对任意键、对象对字符串键且遍历顺序更可控）。
- 减少 O(n²)：嵌套循环找关联时，先建索引表（`Map`）再查，把 O(n×m) 降到 O(n+m)。

### 3.4 JIT 友好代码

V8 会对"热点代码"做 JIT 编译优化，但以下写法会"反优化"（deoptimization）：

- **保持对象形状稳定**：总是以相同顺序、相同键初始化对象。V8 按形状（hidden class）优化，形状变了就得重新编译。
- **避免在热路径用 `try/catch`**：早期 V8 中 `try/catch` 块内的代码难以被优化（新版已大幅改善，但热路径仍建议把易错代码抽成独立函数）。
- **避免频繁删除属性**：`delete obj.x` 会破坏隐藏类，不如置为 `undefined`。
- **类型稳定**：别让同一个变量一会儿存数字一会儿存字符串，V8 会放弃单态优化退化成多态。

---

## 四、内存优化

### 4.1 Stream 替代 readFile

Day06 已讲过 Stream。从内存角度再看一次：`fs.readFile` 会把整个文件读进内存再返回，处理一个 1GB 文件就吃 1GB 堆；`fs.createReadStream` 分块读取，内存占用恒定（取决于 highWaterMark，默认 64KB）。

```js
// ❌ 大文件全量加载, 内存暴涨
const data = await fs.readFile('big.json');
const json = JSON.parse(data); // 又一份大对象

// ✅ 流式处理, 内存恒定
const { pipeline } = require('stream/promises');
await pipeline(fs.createReadStream('big.json'), process.stdout);
```

JSON 这种格式天然不易流式解析，可用 `JSONStream` / `stream-json` 等库逐字段处理超大 JSON。Day06 的 `jsonl-reader.js` 展示了按行流式读 JSONL（AI 训练数据常用格式）。

### 4.2 对象池复用

频繁创建/销毁大对象会加重 GC 压力。对象池预先创建一批对象循环复用，避免反复分配：

```js
class BufferPool {
  constructor(size) { this.pool = new Array(size).fill(null).map(() => Buffer.alloc(8192)); this.cursor = 0; }
  acquire() { return this.pool[this.cursor++ % this.pool.length]; }
}
```

适合"高频短生命周期"场景，如二进制协议解析、批量任务缓冲区。日常业务用得少，但在性能敏感的中间件/网关里常见。

### 4.3 避免闭包持有大对象

闭包会捕获其引用的外层变量，只要闭包存活，被引用的对象就不会被 GC。一个隐蔽的泄漏：

```js
function handler() {
  const huge = loadHuge();           // 大对象
  return () => huge.id;              // 闭包只用到 id, 但整个 huge 都被持有
}
```

修复：只捕获真正需要的值 `const id = huge.id; return () => id;`。同理，定时器/事件监听器里的闭包若长期存活，其捕获的大对象都会泄漏。

### 4.4 Buffer 共享内存 subarray

`Buffer.subarray(start, end)` 返回的是**视图**（与原 Buffer 共享内存），不复制；而 `Buffer.slice()`（已废弃）行为相同但语义易混。需要副本时用 `Buffer.from(buf.subarray(...))` 显式拷贝。处理大 Buffer 时善用 subarray 可避免大量内存复制。

### 4.5 内存泄漏排查

工具链：

1. **`--inspect` + Chrome Memory 面板**：抓两次堆快照（Heap Snapshot），用 "Comparison" 视图对比，找出"只增不减"的对象。
2. **`heapdump` 库**：代码里按需触发快照，结合压力测试在内存上涨后 dump。
3. **`process.memoryUsage()` 打点**：定时记录 `heapUsed`，画出趋势曲线，持续上涨即泄漏信号。

常见泄漏源：未解绑的事件监听器（`on` 没有配对的 `off`）、`Map`/`Set` 无限增长（用 LRU 限容）、全局缓存无淘汰、定时器未 `clearInterval`、闭包持有。

### 4.6 调大堆 --max-old-space-size

Node 默认堆上限约 4GB（64 位）。处理大数据时可能遇到 `JavaScript heap out of memory`。可用 `--max-old-space-size=4096`（单位 MB）调大。但这只是**缓兵之计**——真有泄漏或设计问题，调大只是延后崩溃。优先修代码，确实需要才调大。

```bash
node --max-old-space-size=4096 app.js
```

---

## 五、网络 I/O 优化

网络 I/O 的核心思路：**减少往返次数、复用连接、压缩传输体积、就近访问**。

### 5.1 连接池

每次新建数据库/HTTP 连接都要握手（TCP 三次握手 + TLS 握手），开销显著。连接池预先建好一批连接循环复用：

- **数据库连接池**：如 `mysql2` 的 `createPool`、`pg` 的 `Pool`、`mongoose` 内置池。池大小要合理（见第六节），过大反而拖累 DB。
- **HTTP Agent keepAlive**：Node 默认 `http.Agent` 每次请求新建连接。设 `keepAlive: true` 复用 TCP 连接，对高频调用下游服务收益巨大。

  ```js
  const http = require('http');
  const agent = new http.Agent({ keepAlive: true, maxSockets: 50 });
  http.get(url, { agent });
  ```

### 5.2 HTTP keep-alive

keep-alive 让一个 TCP 连接可承载多个 HTTP 请求，避免反复握手。`fetch`（Node 18+）和 `axios` 都支持。Nginx 到上游也可配 `keepalive`（见 `Code/nginx.conf`）。

### 5.3 gzip / brotli 压缩

文本响应（JSON/HTML/CSS/JS）压缩率极高，gzip 通常能压到原体积的 10%-20%。Express 用 `compression` 中间件一行接入：

```js
app.use(compression());
```

本篇 `Code/compression-demo.js` 实测：一份约 1MB 的大 JSON，开启 gzip 后传输体积降到 ~5%。注意：

- 客户端必须带 `Accept-Encoding: gzip`，中间件才会压缩（协商）。
- 已压缩格式（图片、视频、zip）不要再压，浪费 CPU。
- Brotli（`br`）压缩率比 gzip 更高，现代浏览器都支持，但压缩更耗 CPU。

### 5.4 HTTP/2

HTTP/2 支持多路复用（一个连接并行多个请求）、头部压缩、服务器推送。Node 原生支持 `http2` 模块。通常由 Nginx（`listen 443 ssl http2`）或 CDN 终结 HTTP/2，后端 Node 走 HTTP/1.1 即可。

### 5.5 静态资源缓存

静态资源（JS/CSS/图片）几乎不变，应强缓存：

- **`Cache-Control: max-age=31536000, immutable`**：带 hash 的文件（如 `app.a1b2c3.js`）可缓存一年，浏览器不再发请求。
- **`ETag` / `Last-Modified`**：协商缓存，资源可能变时用。浏览器发 `If-None-Match`/`If-Modified-Since`，未变则返回 304（无 body）。
- **缓存层级**：浏览器缓存 → CDN 缓存 → Nginx 缓存 → 应用缓存。

### 5.6 CDN

CDN 把静态资源复制到全球边缘节点，用户就近访问，延迟大幅降低。动态接口不走 CDN，但可走 CDN 厂商的动态加速（路由优化）。

### 5.7 合并请求 / 批量接口

前端一个列表页若要发 N 个详情请求，往返延迟 ×N。提供批量接口（`POST /api/articles/batch?ids=1,2,3`）一次取回，把 N 次 RTT 降到 1 次。GraphQL 也是这种思路的极致——前端声明所需字段，后端一次组装。

---

## 六、数据库优化

数据库通常是 Web 应用的头号瓶颈，优化收益也最大。

### 6.1 索引

为查询条件（`WHERE`、`JOIN ON`、`ORDER BY`）建索引，把全表扫描 O(n) 降到 O(log n)。要点：

- 索引不是越多越好：写操作要维护索引，索引过多会拖慢写入。
- 复合索引遵循"最左前缀"：`(a, b, c)` 索引可服务 `WHERE a`、`WHERE a AND b`，但**不能**服务 `WHERE b`。
- 用 `EXPLAIN` 看执行计划，确认是否命中索引。

### 6.2 分页

绝不要一次返回全部记录。分页有两种：

- **`LIMIT offset, size`**：简单，但深分页（`OFFSET 100000`）要扫前 10 万行，越翻越慢。
- **游标分页**（`WHERE id > lastId ORDER BY id LIMIT size`）：深分页也快，但不支持跳页。无限滚动列表首选。

### 6.3 避免 SELECT *

`SELECT *` 返回所有列，浪费网络与内存。只查需要的列：

```sql
-- ❌
SELECT * FROM users WHERE id = 1;
-- ✅
SELECT id, name, avatar FROM users WHERE id = 1;
```

ORM 里也要显式 `select`，避免默认全字段。

### 6.4 N+1 问题

最经典的性能反模式：查 1 个列表 + 循环查 N 条关联数据 = 1+N 次查询。

```js
// ❌ N+1: 1 次查文章 + N 次查作者
const articles = await db.query('SELECT * FROM articles LIMIT 10');
for (const a of articles) {
  a.author = await db.query('SELECT * FROM users WHERE id = ?', a.authorId);
}

// ✅ 2 次查询: 先取所有 authorId, 再一次性 IN 查询
const authorIds = articles.map(a => a.authorId);
const authors = await db.query('SELECT * FROM users WHERE id IN (?)', [authorIds]);
// 或用 JOIN 一次查出
// 或用 ORM 的 populate/eager loading (mongoose 的 .populate(), prisma 的 include)
```

ORM 里 `populate`（mongoose）/`include`（prisma）就是为解决 N+1 而生，但要记得用，别在循环里手动查。

### 6.5 查询缓存

高频读查询的结果可缓存（Redis）。注意缓存失效：数据变更时删除对应缓存键。MySQL 有内置 query cache，但高并发写场景下命中率低、锁竞争大，新版已移除——应用层缓存更可控。

### 6.6 慢查询日志

开启 DB 的慢查询日志（如 MySQL `slow_query_log`，阈值 1s），定期用 `pt-query-digest` 分析，找出最该优化的几条 SQL。

### 6.7 连接池大小

连接池不是越大越好。DB 能承受的并发连接数有限（MySQL 默认 151），过大反而互相争抢。经验值：池大小 ≈ `(CPU 核数 × 2) + 磁盘数`，通常 10-20 起步。Node 单实例配 10-20，多实例时按实例数分配。

---

## 七、安全加固清单

上线前必须过的安全清单（`Code/security-checklist.js` 有可运行示例）：

| 项 | 做法 | 说明 |
|----|------|------|
| **依赖审计** | `npm audit` / `npm audit fix` / Dependabot | 第三方包可能有已知漏洞，定期审计并升级 |
| **安全响应头** | `helmet()` 中间件 | 一键设置 `X-Content-Type-Options`、`X-Frame-Options`、CSP、HSTS 等 |
| **CORS 严格配置** | 白名单 origin，禁用 `*` + credentials | 只放行已知前端域名，防跨域滥用 |
| **限流** | `express-rate-limit`，登录类接口更严 | 防 brute force / CC / 爬虫 |
| **输入校验** | `joi` / `express-validator` | 防 SQL 注入、NoSQL 注入、命令注入；参数化查询是底线 |
| **日志脱敏** | 不记密码/token，掩码手机号 | 防日志泄露成为攻击面 |
| **HTTPS 强制** | 全站 HTTPS，HTTP 301 跳转 | 防中间人窃听篡改 |
| **HSTS** | `Strict-Transport-Security` 头 | 强制浏览器后续都走 HTTPS，防降级 |
| **Cookie 安全** | `httpOnly` + `secure` + `sameSite` | 防 XSS 偷 cookie、防 CSRF、防明文传输 |

**Cookie 三属性详解**（前端工程师常忽略，因为浏览器里看不见 httpOnly 的 cookie）：

- `httpOnly: true`：JS 无法通过 `document.cookie` 读取，防 XSS 窃取。
- `secure: true`：仅 HTTPS 下发送，防明文。
- `sameSite: 'lax'` / `'strict'`：限制跨站携带，防 CSRF。现代浏览器默认 `lax`，但敏感操作建议 `strict`。

**输入校验防注入的底线**：永远用参数化查询，永不字符串拼接 SQL。即使用户传 `' OR 1=1 --`，参数化也会把它当普通字符串值而非 SQL 语法。

---

## 八、部署上线

### 8.1 环境变量管理

**密钥绝不进代码库**。用 `dotenv` 从 `.env` 文件加载环境变量，`.env.production` 放生产配置，加入 `.gitignore`：

```js
require('dotenv').config();  // 加载 .env 到 process.env
const dbUrl = process.env.DATABASE_URL;
```

- `.env.example` 进库作为模板（只有键名无值），`.env`/`.env.production` 不进库。
- 生产环境更推荐用容器编排（k8s Secret）/ 云厂商密钥服务，而非文件。
- 呼应 Day14：日志里也别打印 `process.env` 全量，防密钥进日志。

### 8.2 Node 进程管理（PM2）

单进程 Node 无法利用多核，且崩溃后无人拉起。PM2 解决两件事：**多核 cluster** 与**自动重启**。本篇 `Code/ecosystem.config.js` 是生产配置：

- `exec_mode: 'cluster'` + `instances: 'max'`：按 CPU 核数起多个进程，内置负载均衡分发请求。
- `max_memory_restart: '300M'`：内存超限自动重启，兜底泄漏。
- `kill_timeout: 5000`：发 SIGTERM 后等 5s 让应用优雅退出（呼应 Day16）。
- `env_production`：注入生产环境变量。

> 呼应 Day16：PM2 cluster 模式下，每个 worker 是独立进程，共享端口靠的是 Node 的 `cluster` 模块（master 接收连接分发给 worker）。优雅停机时 master 会逐个重启 worker，期间流量不中断。

### 8.3 Docker 化

Docker 把应用与依赖打包成不可变镜像，保证"本地、测试、生产环境一致"。本篇 `Code/Dockerfile` 是多阶段构建示例，要点逐条对应：

| 指令 | 作用 | 关键点 |
|------|------|--------|
| `FROM node:18-alpine AS builder` | 阶段1：构建 | alpine 体积小（~50MB vs 完整版 ~300MB） |
| `COPY package.json` 先于源码 | 利用层缓存 | 源码改不动不重装 node_modules |
| `RUN npm ci --omit=dev` | 装生产依赖 | `npm ci` 比 `install` 快且严格按 lock 文件 |
| `FROM node:18-alpine AS runner` | 阶段2：运行 | 只拷贝产物，不带构建工具 |
| `USER node` | 非 root 运行 | 镜像内置 node 用户，被攻破也非 root |
| `EXPOSE 3000` | 声明端口 | 文档作用，真正发布靠 `-p` |
| `HEALTHCHECK` | 容器健康检查 | 调 `/health`，失败标记 unhealthy |
| `CMD ["node", "app.js"]` | exec 形式 | node 成为 PID 1，正确接收 SIGTERM |

**多阶段构建的价值**：builder 阶段可以装 devDependencies、跑构建工具，最终镜像只拷贝运行所需文件，体积从几百 MB 降到几十 MB。这是 Docker 最佳实践，也为后续 Docker 专题板块铺垫。

> **CMD 的两种形式**：shell 形式 `CMD node app.js` 会被包装成 `sh -c "node app.js"`，node 不是 PID 1，收不到 SIGTERM；exec 形式 `CMD ["node","app.js"]` 让 node 直接作为 PID 1，能正确接收信号做优雅退出。**生产一律用 exec 形式**。

### 8.4 Nginx 反向代理

在 Node 前面加一层 Nginx，承担：**SSL 终止、负载均衡、静态资源、压缩、超时控制**。本篇 `Code/nginx.conf` 是完整示例：

- **upstream + 负载均衡**：多个 Node 实例间轮询，`keepalive` 复用到上游的连接。
- **SSL 终止**：证书由 Nginx 持有，后端 Node 走明文 HTTP，Node 不必处理证书。
- **静态资源**：`location /static/` 直接由 Nginx 托管，不进 Node，释放 Node 算力。
- **proxy_set_header**：透传 `X-Real-IP` / `X-Forwarded-For`，否则 Node 看到的全是 Nginx 的 IP。
- **gzip**：在 Nginx 层压缩，省 Node CPU。

> 经验：让 Nginx 做"重活"（SSL、静态、压缩、限流前置），Node 专注业务逻辑。这是 LAMP 时代就有的分层思想：Web 服务器在前，应用服务器在后。

### 8.5 CI/CD 简述

CI/CD 把"提交代码 → 测试 → 构建 → 部署"自动化。GitHub Actions 示例思路：

```yaml
# .github/workflows/deploy.yml (思路示意)
name: deploy
on:
  push:
    branches: [main]
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '18', cache: 'npm' }
      - run: npm ci                    # 安装依赖
      - run: npm test                  # 跑测试
      - run: npm audit --audit-level=high  # 安全审计
      - run: docker build -t app:${{ github.sha }} .  # 构建镜像
      - run: docker push ...           # 推到镜像仓库
      # - 远程 ssh 拉新镜像并重启 (或触发 k8s rollout)
```

核心原则：**每次提交都过完整流水线**，main 分支随时可部署。密钥用 GitHub Secrets，绝不写进 yml。

### 8.6 健康检查端点

两个端点职责不同，**必须分开**（见 `Code/health-check.js`）：

| 端点 | 名称 | 检查内容 | 失败后果 |
|------|------|----------|----------|
| `/health` | 存活探针 (liveness) | 进程还活着 | 重启容器 |
| `/ready` | 就绪探针 (readiness) | 依赖(数据库等)就绪 + 未在退出中 | 摘除流量（不重启） |

**为什么要分？** 启动时数据库还没连上，`/ready` 返回 503，负载均衡不导流量进来，但 `/health` 返回 200（进程没死）——避免被误判崩溃而重启。退出时同理：`/ready` 立即 503 摘流量，`/health` 仍 200，让在途请求处理完再退。

### 8.7 优雅退出

呼应 Day16，本篇 `Code/health-check.js` 完整实现：

1. 收到 `SIGTERM`/`SIGINT` → 置 `shuttingDown = true`。
2. `/ready` 立即返回 503，LB 摘流量。
3. 等待 1s 让探针生效。
4. `server.close()` 停止接受新连接，等在途请求完成。
5. 关闭数据库连接。
6. `process.exit(0)`。兜底 10s 超时强杀。

PM2 的 `kill_timeout` / k8s 的 `terminationGracePeriodSeconds` 要大于应用的优雅退出耗时，否则会在退出完成前被 SIGKILL。

### 8.8 日志收集

呼应 Day14：生产环境多实例的日志分散在各容器/机器，必须采集到集中式系统检索。典型链路：winston 写文件 → Filebeat/Promtail 采集 → ELK/Loki 存储 → Kibana/Grafana 查询。容器场景推荐 stdout 输出，由容器日志驱动统一收集。

---

## 九、生产环境配置清单

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| `NODE_ENV` | `production` | Express 等据此启用缓存、关闭详细错误 |
| stack 暴露 | 关闭 | 错误响应不返回堆栈，仅开发环境返回 |
| 日志级别 | `info`+ | 关 `debug`，避免日志量爆炸与信息泄露 |
| 压缩 | 开启 gzip/brotli | 文本响应压缩，省带宽 |
| 连接池大小 | 10-20 起步 | 按 DB 承受能力与实例数调 |
| 请求体限制 | `10kb`-`1mb` | 防大 payload 攻击，按业务收紧 |
| 请求超时 | `10s`-`30s` | 慢请求及时中断，防连接耗尽 |
| CORS 白名单 | 显式域名 | 禁用 `*`，尤其配合 credentials 时 |
| `max-old-space-size` | 按需（如 4096） | 大数据场景调大堆，优先修代码 |
| 限流 | 全局 + 敏感接口加严 | 防 CC/暴力破解 |

---

## 十、AI 全栈视角

把上面的工程能力套到 AI 场景，几个关键工程点：

### 10.1 模型推理服务化

模型不能"塞在前端"，必须封装成后端服务（HTTP/gRPC），前端调接口拿结果。原因：模型文件大（动辄几百 MB-几 GB）、推理需要 GPU/CPU 算力、API key 不能暴露给前端。典型架构：

```
前端 → Node 网关 (限流/鉴权/日志) → 推理服务 (Python/ONNX Runtime/Triton) → 返回
```

Node 适合做"网关层"：处理鉴权、限流、日志、流式转发，把推理请求转给后端 Python 服务或直接调用模型 API（如 OpenAI）。

### 10.2 模型加载到内存常驻

模型加载是重操作（几秒到几十秒）。绝不能每个请求都重新加载。启动时一次性加载到内存/显存常驻，请求只做推理。这也是为什么推理服务要用 `worker_threads` 或独立进程：模型常驻 worker，主线程收请求转发。

### 10.3 推理请求限流与队列

GPU 是稀缺资源，并发推理数有上限。超过上限时不能直接拒绝，应排队（队列）或限流：

- **限流**：`express-rate-limit` 限制每用户每分钟请求数，防滥用。
- **队列**：用 BullMQ / RabbitMQ 把推理任务排队，worker 串行/并行处理，避免过载。
- **背压**：队列满了返回 429 + `Retry-After`，让前端稍后重试。

### 10.4 GPU 资源管理

Node 本身不直接操作 GPU，但作为网关要感知后端 GPU 负载：

- 多个推理服务实例轮询（Nginx upstream），避免单卡过载。
- 监控 GPU 利用率（nvidia-smi / DCGM），过载时自动扩容或限流。
- 大模型推理用批处理（batching）：攒几个请求一起推理，提升吞吐。

### 10.5 流式响应给前端

大模型生成是"逐 token"的，全量返回要等几十秒，体验差。用 **SSE（Server-Sent Events）** 或 **HTTP 流式** 把 token 逐个推给前端，前端边收边渲染（打字机效果）。Node 用 `res.write()` + `Transfer-Encoding: chunked` 实现流式：

```js
res.setHeader('Content-Type', 'text/event-stream');
for await (const token of llmStream(prompt)) {
  res.write(`data: ${JSON.stringify({ token })}\n\n`);
}
res.write('data: [DONE]\n\n');
res.end();
```

> 这是 AI 全栈的核心交互模式，后续 Agent 板块会大量用到。前端用 `EventSource` 或 `fetch` 的 `ReadableStream` 消费。

### 10.6 监控推理耗时与成功率

AI 接口要额外监控：

- **首 token 耗时（TTFT）**：用户看到第一个字的时间，体验关键指标。
- **总推理耗时**：完整生成用了多久。
- **成功率**：推理失败（超时、内容审核、限流）比例。
- **token 用量**：按用户/模型统计，用于成本控制与计费。

这些指标结构化记进日志（呼应 Day14），聚合到 Prometheus + Grafana 做大盘与告警。

---

## 十一、关键知识点总结

1. **三大性能维度**：CPU（进程 CPU 打满）、内存（heap 持续涨）、网络 I/O（CPU 不高但慢，在等外部资源）。先量后优，用监控定位瓶颈维度。
2. **测量工具链**：`console.time` 粗测 → `performance.now` 精测 → `process.memoryUsage/cpuUsage` 资源监控 → `--inspect` + DevTools 在线调试 → `clinic.js` 自动诊断 → `0x` 火焰图定位热点。
3. **CPU 优化**：同步阻塞事件循环是头号坑；CPU 密集任务用 `setImmediate` 分片或 `worker_threads`/子进程移出主线程；缓存（内存 LRU / Redis）是性价比最高的优化；JIT 喜欢稳定类型、避免热路径 try/catch。
4. **内存优化**：Stream 替代 `readFile` 全量加载；对象池复用；避免闭包持有大对象；Buffer `subarray` 共享内存；泄漏用 `--inspect` 堆快照对比排查；`--max-old-space-size` 调大堆是缓兵之计。
5. **网络 I/O 优化**：连接池复用连接；keep-alive；gzip/brotli 压缩文本；HTTP/2 多路复用；静态资源强缓存 + ETag 协商缓存；CDN 就近访问；批量接口减少 RTT。
6. **数据库优化**：索引（最左前缀）、游标分页、避免 `SELECT *`、消灭 N+1（JOIN/populate/批量 IN）、查询缓存、慢查询日志、连接池大小适度。
7. **安全清单**：`npm audit` 审计、Helmet 安全头、CORS 白名单、限流、输入校验防注入、日志脱敏、HTTPS 强制 + HSTS、Cookie `httpOnly+secure+sameSite`。
8. **部署**：密钥用 dotenv 进环境变量绝不进库；PM2 cluster 多核 + 内存重启 + 优雅停机；Docker 多阶段构建（alpine、非 root、HEALTHCHECK、exec CMD）；Nginx 做 SSL 终止/负载均衡/静态/压缩；CI/CD 自动化流水线。
9. **健康检查**：`/health` 存活（进程活着就 200，失败重启）与 `/ready` 就绪（依赖就绪且未退出才 200，失败摘流量）**必须分开**；优雅退出先置 not-ready 摘流量再关连接。
10. **AI 全栈**：模型服务化（Node 做网关）、模型常驻内存、推理限流+队列、GPU 负载感知、SSE 流式响应、监控 TTFT/成功率/token 用量。

---

## 十二、实战练习

> 以下练习在 `Code/` 目录基础上扩展，建议独立完成后再对照本篇结论自查。

### 练习一：用 `--inspect` 定位并修复一个内存泄漏

**目标**：掌握 Chrome DevTools 排查内存泄漏的标准流程。

**要求**：

1. 新建 `leak-demo.js`，启动一个 Express 服务，写一个 `/leak` 接口：每次请求把一个大对象（如 1MB 的 Buffer）push 进一个全局数组 `cache`，且永不清理。
2. 用 `node --inspect leak-demo.js` 启动，Chrome 打开 `chrome://inspect` 连上。
3. 用 `curl` 连发 20 次请求后，在 Memory 面板抓第一次堆快照；再连发 20 次，抓第二次快照。
4. 用 "Comparison" 视图对比两次快照，找出"只增不减"的对象（应能看到 Buffer 数量增长）。
5. 修复：把全局数组改成 `LRUCache`（参考 `caching-demo.js`）限容 10 条，验证修复后 `heapUsed` 不再持续上涨。

**考察点**：`--inspect` 调试、堆快照对比、用 LRU 限容治泄漏。

### 练习二：实现一个带限流与流式响应的 AI 接口

**目标**：把第十节的 AI 工程点串成一个最小可用接口。

**要求**：

1. 在 `compression-demo.js` 基础上新增 `POST /api/chat`，body 为 `{ prompt }`。
2. 用 `express-rate-limit` 给该接口限流：每 IP 每分钟 5 次。
3. 用 `setInterval` 模拟大模型流式输出：每 100ms 生成一个"token"（字符），通过 SSE（`Content-Type: text/event-stream`）推给客户端，10 个 token 后结束。
4. 客户端断开连接时（监听 `req.on('close')`）立即停止生成，避免无谓计算。
5. 用 `curl -N http://localhost:3001/api/chat -d '{"prompt":"hi"}' -H "Content-Type: application/json"` 观察流式输出效果。

**考察点**：SSE 流式响应、接口级限流、连接断开清理。这是 AI 全栈的高频范式。

### 练习三：为健康检查服务补充 Docker Compose 编排

**目标**：把单容器推向多服务编排，为后续 Docker 板块铺垫。

**要求**：

1. 新建 `docker-compose.yml`，定义两个服务：`app`（用本篇 Dockerfile 构建）和 `redis`（用官方 `redis:7-alpine`）。
2. `app` 依赖 `redis`，并通过环境变量 `REDIS_URL=redis://redis:6379` 注入连接地址。
3. 给 `app` 配置健康检查（`healthcheck` 调 `/health`），并设 `restart: unless-stopped`。
4. 端口映射 `3000:3000`。
5. 思考：为什么在 compose 里 `app` 能用 `redis` 这个主机名连到 Redis？（提示：Docker 网络 / DNS）

**考察点**：多阶段构建复用、服务编排、容器网络与 DNS、健康检查与重启策略。

---

> 完成本篇后，你已具备把一个 Node.js 服务从"能跑"推向"快、稳、安全、可上线"的完整工程能力。Node.js 板块至此告一段落——性能测量、缓存、安全、Docker、Nginx、PM2、健康检查、优雅退出这些"上线即刚需"的技能都已就位。后续 Docker 专题板块会深入容器化与编排，AI 板块会把本篇的"模型服务化、流式响应、限流队列"扩展成完整的 Agent 后端。这是从前端走向 AI 全栈的关键一跃。
