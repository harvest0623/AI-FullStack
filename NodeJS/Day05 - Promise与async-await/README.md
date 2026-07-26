# Day05 - Promise 与 async/await

> 本篇聚焦 JavaScript 异步编程的两块基石：**Promise** 与 **async/await**。它们是 Node.js 后端、AI 接口调用、批量推理编排的核心心智模型。理解透彻后，你才能从容应对并发请求、超时控制、错误重试等工程场景。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 Promise 的三种状态与不可逆性](#21-promise-的三种状态与不可逆性)
  - [2.2 Promise 链式调用原理](#22-promise-链式调用原理)
  - [2.3 then / catch / finally](#23-then--catch--finally)
  - [2.4 Promise 链中的错误冒泡机制](#24-promise-链中的错误冒泡机制)
  - [2.5 Promise.all / allSettled / race / any 对比](#25-promiseall--allsettled--race--any-对比)
  - [2.6 async/await 的语法糖本质](#26-asyncawait-的语法糖本质)
  - [2.7 async 函数的返回值](#27-async-函数的返回值)
  - [2.8 await 的暂停语义](#28-await-的暂停语义)
  - [2.9 try/catch 捕获 await 错误](#29-trycatch-捕获-await-错误)
  - [2.10 并发 vs 串行](#210-并发-vs-串行)
  - [2.11 顶层 await（Top-level await）](#211-顶层-awaittop-level-await)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 Promise 相比回调的优势](#31-promise-相比回调的优势)
  - [3.2 async/await 相比 Promise 的优势](#32-asyncawait-相比-promise-的优势)
  - [3.3 常见反模式（Anti-patterns）](#33-常见反模式anti-patterns)
- [四、错误处理策略对比](#四错误处理策略对比)
- [五、关键知识点总结](#五关键知识点总结)
- [六、实战练习](#六实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 准确描述 Promise 的三种状态及其不可逆性，画出状态流转图。
2. 解释 `then` 为什么能链式调用，理解“返回新 Promise”的内部机制。
3. 区分 `Promise.all` / `allSettled` / `race` / `any` 的行为差异，并能根据业务场景选择正确的合并器。
4. 说明 async/await 是 Generator + 自动执行器的语法糖，理解其与 Promise 的等价关系。
5. 用 `try/catch` 正确捕获 `await` 抛出的错误，避免“未处理拒绝”警告。
6. 对比串行 `for...of await` 与 `Promise.all` 并发的性能差异，掌握批量任务编排思路。
7. 了解顶层 await 的使用条件与 ESM / CommonJS 差异。
8. 识别并规避三类常见异步反模式。
9. 在 Node 18+ 环境中用原生 `fetch` + `Promise.race` 实现超时控制。

---

## 二、理论知识讲解

### 2.1 Promise 的三种状态与不可逆性

一个 Promise 实例必然处于以下三种状态之一：

| 状态 | 含义 | 触发方式 |
|------|------|----------|
| `pending` | 初始态，尚未敲定 | `new Promise((resolve, reject) => {...})` 刚创建时 |
| `fulfilled` | 已成功，持有最终值 | 执行器调用 `resolve(value)` |
| `rejected` | 已失败，持有拒绝原因 | 执行器调用 `reject(reason)` 或抛出异常 |

**状态流转规则**：

```
   pending
     │
     ├──resolve(value)──► fulfilled（不可再变）
     │
     └──reject(reason)──► rejected（不可再变）
```

**关键性质：不可逆性（Settled is forever）**。一旦从 `pending` 转为 `fulfilled` 或 `rejected`，就**永远定格**，后续的 `resolve` / `reject` 调用都会被静默忽略，值也无法被改写。这是 Promise 可靠性的基石——你可以把一个 Promise 交给多方监听，它们看到的结果一定一致。

```js
const p = new Promise((resolve, reject) => {
  resolve('第一次的值');  // 生效
  resolve('第二次的值');  // 静默忽略
  reject('想要反悔');     // 静默忽略
});

p.then(v => console.log(v)); // 永远输出 "第一次的值"
```

> 💡 **AI 场景联想**：调用大模型推理接口时，一个请求要么成功返回 token，要么超时失败。把请求包装成 Promise 后，状态不可逆性保证了“回调只触发一次”，避免重复扣费或重复写入。

### 2.2 Promise 链式调用原理

`then` / `catch` / `finally` 都会**返回一个全新的 Promise**，而不是修改原 Promise。这是链式调用能够成立的根本原因。

```js
const p1 = new Promise(resolve => resolve(1));
const p2 = p1.then(v => v + 1);

console.log(p1 === p2); // false —— 两个不同的对象
```

**`then` 回调的返回值如何决定新 Promise 的状态**：

| `then` 回调返回的内容 | 新 Promise 的结果 |
|----------------------|-------------------|
| 普通值（数字、字符串、对象等） | 立即 `fulfilled`，值为该返回值 |
| 一个 Promise | “ Adopt（收养）”该 Promise 的最终状态与值 |
| 一个 thenable 对（有 `.then` 方法） | 调用其 `.then` 进一步展开 |
| `throw` 抛出异常 | 立即 `rejected`，原因为抛出的值 |
| 没有返回（`undefined`） | `fulfilled`，值为 `undefined` |

“返回一个 Promise 时会被 adopt”这一规则，是异步串联的关键：

```js
fetch('/api/user')          // 返回 Promise<Response>
  .then(res => res.json())  // 返回 Promise<Object>，被 adopt
  .then(user => fetch(`/api/order?uid=${user.id}`)) // 再次返回 Promise
  .then(res => res.json())
  .then(orders => console.log(orders));
```

每一环都会等待上一环“敲定”后才执行，自然形成了串行流水线。

### 2.3 then / catch / finally

三者都是注册回调的方法，但语义不同：

- **`then(onFulfilled, onRejected)`**：可同时接收成功与失败回调。实践中推荐只用第一个参数，失败交给 `catch`。
- **`catch(onRejected)`**：等价于 `then(undefined, onRejected)`，专门处理链上方的错误。
- **`finally(onFinally)`**：无论成功失败都会执行，**不接收任何参数**，且**不会改变**链上传递的值或拒绝原因，常用于释放资源（关闭连接、隐藏 loading）。

```js
doSomething()
  .then(result => process(result))
  .catch(err => {
    console.error('出错了：', err);
    return fallbackValue;   // 可以“兜底”返回一个默认值，让链继续往下走
  })
  .finally(() => {
    hideLoading();          // 不影响后续值的传递
  })
  .then(final => console.log(final));
```

> ⚠️ `finally` 回调里 `return` 的值会被忽略——除非它 `throw`，否则不会改变链的状态。

### 2.4 Promise 链中的错误冒泡机制

与同步代码的异常冒泡类似，Promise 链中的 `reject` / `throw` 会**沿链向下传递**，直到遇到第一个 `catch`（或 `then` 的第二个参数）。中间任何 `then` 没有处理失败，错误都会“跳过”它们的成功回调继续往下。

```js
Promise.resolve()
  .then(() => { throw new Error('第一步就炸了'); })
  .then(() => console.log('我不会被打印'))   // 被跳过
  .then(() => console.log('我也不会'))        // 被跳过
  .catch(err => console.log('捕获到：', err.message)); // 在这里兜住
```

**两条要点**：

1. `catch` 之后如果还有 `then`，链会以 `catch` 返回的值“恢复”为 `fulfilled` 继续往下走；除非 `catch` 自己又 `throw`。
2. 如果整条链都没有 `catch`，未处理的拒绝会冒泡到全局，触发 `unhandledrejection` 事件（浏览器）或 Node 的 `unhandledRejection` 事件，新版 Node 甚至可能直接退出进程。

```js
// catch 之后的 then 会继续执行
asyncThing()
  .then(work)
  .catch(err => '默认值')   // 错误被“吞掉”，返回默认值
  .then(v => console.log(v)); // 打印 "默认值"
```

### 2.5 Promise.all / allSettled / race / any 对比

四个“合并器（Combinator）”都接收一个可迭代对象（通常是数组），返回一个 Promise，但敲定逻辑截然不同：

| 方法 | 全部成功时 | 有失败时 | 适用场景 |
|------|-----------|---------|---------|
| `Promise.all` | 全部 fulfilled → 结果数组按原顺序 | **第一个 reject 即整体 reject**，但其余任务**不会取消**（仍会跑完，只是结果被忽略） | 多个请求必须**全部成功**才有意义，如并行拉取拼装页面数据 |
| `Promise.allSettled` | —— | **永远 fulfilled**，结果形如 `[{status:'fulfilled', value}, {status:'rejected', reason}]` | 批量上报、日志收集、希望知道**每一个**任务的结果而不想被某个失败打断 |
| `Promise.race` | 第一个敲定（无论成功失败）即整体敲定 | 同左，第一个 reject 也整体 reject | 超时控制、多源竞速取最快响应 |
| `Promise.any`（ES2021） | 第一个 fulfilled 即整体 fulfilled | **只有全部 reject 才整体 reject**，拒绝原因是 `AggregateError` | 多个镜像源抢答，只要有一个能用就行；容错性比 `race` 强 |

> 🔑 **记忆口诀**：
> - `all` = “全成才成，一个败即败”
> - `allSettled` = “全都跑完，永不失败”
> - `race` = “第一个说了算（无论成败）”
> - `any` = “只要一个成就成，全败才败”

**注意“不可取消”这一点**：JavaScript 的 Promise 本身没有取消语义。`race` 里落败的任务依旧会执行完毕，只是其结果不被采纳。如需真正的取消，需借助 `AbortController`（见 `fetch-data.mjs`）。

```js
// 超时控制的经典套路：race + setTimeout
function withTimeout(promise, ms) {
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error(`超时 ${ms}ms`)), ms)
  );
  return Promise.race([promise, timeout]);
}
```

### 2.6 async/await 的语法糖本质

`async/await` 让异步代码“看起来像同步”，但它的本质是 **Generator + 自动执行器** 的语法糖。理解这一点有助于你看懂早期的 `co` 库，也能更好地排错。

**手写版对照**：

```js
// async/await 写法
async function run() {
  const a = await step1();
  const b = await step2(a);
  return a + b;
}

// 等价的 Generator + 自动执行器（简化版）
function* runGen() {
  const a = yield step1();
  const b = yield step2(a);
  return a + b;
}

function autoRun(gen) {
  const it = gen();
  function step(prev) {
    const { value, done } = it.next(prev);
    if (done) return Promise.resolve(value);
    return Promise.resolve(value).then(step, e => it.throw(e));
  }
  return step();
}
autoRun(runGen);
```

V8 在底层会编译期把 `async` 函数转换为类似的状态机，省去了手写自动执行器。所以：

- `await x` 本质是 `yield x`，把控制权交还给运行时；
- `async` 函数本质是一个返回 Promise 的 Generator wrapper。

### 2.7 async 函数的返回值

`async` 函数**永远返回一个 Promise**，无论你 `return` 的是什么：

| 函数体内 | 实际返回的 Promise |
|----------|-------------------|
| `return 42` | `Promise.resolve(42)` |
| `return promise` | 直接返回该 promise（已 adopt） |
| `return thenable` | 包装成 Promise 后展开 |
| `throw err` | `Promise.reject(err)` |
| 无 `return` | `Promise.resolve(undefined)` |

```js
async function f() { return 42; }
f().then(v => console.log(v)); // 42

async function g() { throw new Error('boom'); }
g().catch(e => console.log(e.message)); // boom
```

> 因此，**async 函数内部抛出的错误不会让进程崩溃**，而是变成一个 rejected Promise，必须由调用方 `catch`。

### 2.8 await 的暂停语义

`await` 的作用是：**暂停当前 async 函数的执行，等待右侧表达式敲定，然后恢复执行并把值取出**。

需要注意两点：

1. **只暂停当前函数，不阻塞主线程**。函数被挂起后，事件循环照常处理其他任务（I/O、定时器、其他请求）。这正是 Node 单线程能高并发的关键。
2. **`await` 右侧的表达式会立即求值**。如果右侧是一个已经是 fulfilled 的 Promise（或普通值），`await` 仍会让出一次微任务轮次才恢复——它不会“同步跳过”。

```js
async function demo() {
  console.log(1);
  await Promise.resolve();   // 让出一次微任务
  console.log(3);
}
console.log(0);
demo();
console.log(2);
// 输出顺序：0 1 2 3
```

### 2.9 try/catch 捕获 await 错误

`await` 会把右侧 Promise 的 rejection 转化为同步 `throw`，因此用 `try/catch` 包裹即可捕获，这比 `.catch()` 更贴近同步思维。

```js
async function load() {
  try {
    const res = await fetch('/api/xxx');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('加载失败：', err.message);
    return null;   // 兜底返回
  }
}
```

**注意**：`catch` 只能捕获它**之前**的 `await` 抛出的错误。如果错误发生在 `catch` 之后的 `await`，需要再套一层 `try/catch` 或在调用方 `.catch`。

也可以混用：对单个 `await` 用 `.catch` 兜底，避免大块 `try`：

```js
const data = await fetch('/api/xxx').catch(() => null);
if (!data) return;
```

### 2.10 并发 vs 串行

这是性能优化的高频考点。同样是“跑 3 个任务”，写法不同耗时天差地别。

**串行写法（`for...of` + `await`）**——前一个完成才启动下一个：

```js
for (const task of tasks) {
  await task();   // 一个接一个
}
```

**并发写法（`Promise.all`）**——同时启动，等最慢的那个：

```js
await Promise.all(tasks.map(t => t()));  // 全部并发
```

**性能差异**：假设有 3 个各耗时 500ms 的任务，

- 串行：500 + 500 + 500 = **1500ms**
- 并发：max(500, 500, 500) = **≈500ms**（约 3 倍提速）

但并发不是万能：

- 对方限流（如 OpenAI API 的 RPM/TPM 限制）时，并发过高会触发 429；
- 任务间有依赖（B 需要 A 的结果）时只能串行；
- 大量并发会耗尽连接池/内存，工程上常用“**并发上限**”模式（见 `parallel-vs-serial.js`）。

> 💡 **AI 场景联想**：批量向 LLM 发送 100 条 prompt，串行可能要几分钟；无脑并发又会被限流。解法是分批 + `Promise.all`，每批 N 个。

### 2.11 顶层 await（Top-level await）

从 ES2022 起，**ES Module** 中可以直接在模块顶层使用 `await`，无需包裹在 async 函数里：

```js
// config.mjs  —— 顶层 await
export const config = await fetch('/api/config').then(r => r.json());
```

**限制与注意**：

| 运行环境 | 是否支持顶层 await | 说明 |
|----------|-------------------|------|
| `.mjs` 文件（ESM） | ✅ 支持 | 原生支持 |
| `package.json` 设 `"type": "module"` 的 `.js` | ✅ 支持 | 视作 ESM |
| CommonJS（`.cjs` 或默认 `.js`） | ❌ 不支持 | 会报 `SyntaxError: await is only valid in async functions` |
| 旧版 Node (< 14.8) | ❌ 不支持 | 需要实验 flag |

**顶层 await 的“传染性”**：一个模块用了顶层 await，**导入它的模块也会被阻塞**，直到该模块的顶层 await 完成。这会拖慢启动速度，应谨慎用于“启动时必须加载的配置”等场景。

CommonJS 中的替代写法是顶层 IIFE：

```js
// CommonJS 中模拟顶层 await
(async () => {
  const config = await fetch('/api/config').then(r => r.json());
  // ...
})();
```

本篇的 `fetch-data.mjs` 就是 `.mjs` 文件，可演示顶层 await。

---

## 三、核心概念解析

### 3.1 Promise 相比回调的优势

回调（Callback）是 Node 早期处理异步的主流方式，典型风格是“错误优先”：

```js
fs.readFile('a.txt', (err, data) => {
  if (err) return console.error(err);
  // 处理 data
});
```

**回调的三大痛点 vs Promise 的解法**：

| 痛点 | 回调的问题 | Promise 的解法 |
|------|-----------|---------------|
| 回调地狱 | 嵌套层层缩进，难以阅读与维护 | 链式 `.then`，扁平化结构 |
| 控制反转 | 把回调交给第三方，无法信任它会被调用几次、何时调用 | 状态不可逆 + 只敲定一次，语义可靠 |
| 错误处理分散 | 每层都要手动 `if (err)` | 错误沿链冒泡，一个 `catch` 兜底 |
| 并发编排困难 | 需手动计数器或引入 `async` 库 | 内置 `all / allSettled / race / any` |
| 无法取消/中途 | 几乎无能为力 | 配合 `AbortController` 可取消 fetch |

一句话：**Promise 把“异步流程”变成了“可传递、可组合、可监听的一等值”**。

### 3.2 async/await 相比 Promise 的优势

`async/await` 不是替代 Promise，而是**建立在 Promise 之上**的更友好的写法。它的优势：

1. **代码更接近同步思维**，`try/catch` 而非 `.catch`，条件分支、循环里使用 `await` 自然流畅。
2. **调试友好**：在 `await` 行可以打断点，调用栈完整；`.then` 链的栈常常断在匿名函数里。
3. **避免 `return` 遗漏**：Promise 链里忘记 `return` 是高频 bug，async/await 用赋值语义天然规避。
4. **跨 `await` 的变量共享更简单**：不用为了在链下游访问上游变量而层层闭包。

```js
// Promise 链：忘记 return 是经典坑
getUser()
  .then(user => {
    getOrders(user.id);   // ❌ 忘记 return，下游拿到 undefined
  })
  .then(orders => render(orders));

// async/await：天然没有这个问题
async function show() {
  const user = await getUser();
  const orders = await getOrders(user.id); // 一目了然
  render(orders);
}
```

### 3.3 常见反模式（Anti-patterns）

#### 反模式 1：用 `new Promise` 包裹已有的 Promise

已有 Promise 或 thenable 时，再 `new Promise` 是冗余且容易出错的。

```js
// ❌ 反模式
function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(), ms);   // 还能理解
  });
}
function badFetch(url) {
  return new Promise((resolve, reject) => {
    fetch(url)                          // ❌ fetch 已经是 Promise
      .then(res => resolve(res.json()))
      .catch(reject);
  });
}

// ✅ 正确：直接返回
function goodFetch(url) {
  return fetch(url).then(res => res.json());
}
```

只有把“非 Promise 的回调式 API”（如 `setTimeout`、`fs.readFile`）转成 Promise 时，`new Promise` 才有意义。Node 提供了 `util.promisify` 简化这一过程。

#### 反模式 2：在 `forEach` 中使用 `await`

`forEach` 不等待回调返回的 Promise，会“立即返回 undefined”，导致 `await` 形同虚设、并发失控。

```js
const urls = [/* ... */];

// ❌ 反模式：forEach 不会等待，三个请求几乎同时发出，且无法捕获错误
urls.forEach(async url => {
  await fetch(url);
});
console.log('done');  // 几乎立刻打印，请求还没完成

// ✅ 正确写法一：串行 for...of
for (const url of urls) {
  await fetch(url);
}

// ✅ 正确写法二：并发 Promise.all
await Promise.all(urls.map(url => fetch(url)));
```

`map` + `Promise.all` 是并发版；`for...of` + `await` 是串行版——两者都比 `forEach` 正确。

#### 反模式 3：忘记 `return` 链

```js
// ❌ 忘记 return，doNext 拿到 undefined，且错误无法冒泡
function work() {
  doAsync().then(result => {
    return doNext(result);   // ❌ 外层没有 return
  });
}

// ✅ 正确
function work() {
  return doAsync().then(result => doNext(result));
}
```

async/await 天然规避此类问题，这也是推荐用 async/await 的理由之一。

---

## 四、错误处理策略对比

| 策略 | 写法 | 适用层级 | 优点 | 缺点 |
|------|------|---------|------|------|
| **`try/catch`** | `try { await x } catch(e) {...}` | 函数内部 / 局部块 | 同步思维、栈清晰、可与条件分支混用 | 大块 try 会掩盖未预期错误；嵌套易混乱 |
| **`.catch()`** | `p.then(...).catch(e => ...)` | Promise 链 | 链式扁平、可集中兜底、可“恢复”返回默认值 | 链较长时错误来源不直观；容易忘记在末尾加 |
| **统一错误中间件** | Express/Koa 的错误处理中间件 | Web 框架全局 | 业务代码不写 try/catch、错误格式统一、便于日志与监控 | 需要框架支持；异步错误需主动 `next(err)` 传递 |

**实践建议**：

- **局部关键操作**用 `try/catch`，保证上下文足够清晰。
- **链式编排**用 `.catch` 在末尾兜底。
- **Web 服务**用统一错误中间件 + 一个 `asyncHandler` wrapper，把 async 函数的错误自动转给中间件：

```js
// Express 中常见的 wrapper，让你不用每处写 try/catch
const asyncHandler = fn => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next);

router.get('/user', asyncHandler(async (req, res) => {
  const user = await getUser(req.params.id);
  res.json(user);
  // 抛出的错误会自动进错误中间件
}));
```

---

## 五、关键知识点总结

1. **Promise 三态不可逆**：pending → fulfilled/rejected 是单向、一次性的，这是可靠性的根基。
2. **链式调用的本质**：`then` 返回新 Promise；返回 Promise 时被 adopt，返回普通值时立即 fulfilled，throw 时 rejected。
3. **错误冒泡**：reject/throw 沿链下行，遇 `catch` 即停；`catch` 之后链恢复为 fulfilled。
4. **四个合并器**：
   - `all`：全成才成，一败即败；
   - `allSettled`：永不失败，逐个汇报；
   - `race`：第一个敲定说了算（成败皆可）；
   - `any`：一成就成，全败才败（`AggregateError`）。
5. **async/await 是语法糖**：本质 Generator + 自动执行器，永远返回 Promise，`await` 抛出的 rejection 可被 `try/catch` 捕获。
6. **并发 vs 串行**：`for...of await` 串行累加耗时；`Promise.all` 并发取最慢者。生产中常用“并发上限”分批。
7. **顶层 await**：仅 ESM 支持，会传染阻塞导入方，CommonJS 需用 IIFE 模拟。
8. **三类反模式**：多余 `new Promise` 包裹、`forEach` 里 `await`、忘记 `return` 链。
9. **Promise 不可取消**：`race` 落败任务仍会跑完，真正取消需 `AbortController`。
10. **错误处理三层**：局部 `try/catch` → 链尾 `.catch` → 框架统一中间件。

---

## 六、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：Promise 状态与链（对应 `promise-basic.js`）

实现一个 `fakeFetch(success, delayMs)` 函数：返回一个 Promise，`success` 为 `true` 时在 `delayMs` 毫秒后 resolve `'OK'`，否则 reject 一个 `Error('FAIL')`。

要求：

1. 调用成功分支，用 `.then` 链把结果转成大写并打印。
2. 调用失败分支，用 `.catch` 打印错误信息。
3. 写一段代码验证“状态不可逆”：在 resolve 之后再调用 reject，观察是否被忽略。

### 练习 2：合并器对比（对应 `promise-combinators.js`）

构造 4 个模拟 API：3 个会在不同延迟后 resolve，1 个会 reject。分别用 `Promise.all`、`Promise.allSettled`、`Promise.race`、`Promise.any` 合并它们，观察：

- 哪些会整体 reject？拒绝原因是什么？
- `allSettled` 返回的结构长什么样？
- `race` 和 `any` 的第一个结果分别是什么？

把观察结论以注释形式写在代码里。

### 练习 3：并发 vs 串行 + 超时控制（对应 `parallel-vs-serial.js` 与 `fetch-data.mjs`）

1. 编写 3 个各耗时 500ms 的异步任务，分别用 `for...of await`（串行）和 `Promise.all`（并发）执行，用 `Date.now()` 或 `performance.now()` 测量并打印两种写法的总耗时，验证并发约为串行的 1/3。
2. 用原生 `fetch` 请求 `https://jsonplaceholder.typicode.com/users/1`，配合 `Promise.race` + `setTimeout` 实现 800ms 超时控制；再尝试把超时改成 1ms 观察错误是否被 `try/catch` 捕获。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/promise-basic.js` | 手动创建 Promise，演示三态与 then 链 |
| `Code/promise-combinators.js` | all / allSettled / race / any 四种合并对比 |
| `Code/async-await-demo.js` | async/await 串行请求模拟 |
| `Code/parallel-vs-serial.js` | 串行 await vs Promise.all 并发耗时对比 |
| `Code/fetch-data.mjs` | 原生 fetch + Promise.race 超时控制 |

运行方式（Node 18+）：

```bash
node Code/promise-basic.js
node Code/promise-combinators.js
node Code/async-await-demo.js
node Code/parallel-vs-serial.js
node Code/fetch-data.mjs
```

---

> 📚 **延伸阅读**
> - MDN：[Using promises](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Guide/Using_promises)
> - MDN：[async function](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Statements/async_function)
> - Node.js 官方文档：[HTTP / fetch](https://nodejs.org/api/globals.html#fetch)
> - ECMA 规范：Promise Objects 与 Async Functions 章节
