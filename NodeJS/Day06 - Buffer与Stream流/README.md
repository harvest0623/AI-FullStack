# Day06 - Buffer 与 Stream 流

> 目标读者：已经熟悉 JavaScript/浏览器 API，需要补齐 Node.js 二进制数据处理与流式 I/O 心智模型

> 运行环境：Node.js 18+

前端工程师习惯用 `string` / `JSON` / `Blob` / `File` 思考数据，而真正进入 Node.js 后端与 AI 工程领域后，**字节（byte）** 与 **流（stream）** 才是数据的本来面目：模型权重文件是几个 GB 的二进制块、大模型推理输出是逐 token 涌出的流、向量库的二进制向量载荷、分块上传的音视频……这些都要求你理解 Buffer 与 Stream。本节正是补上这块拼图。

---

## 📑 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 为什么需要 Buffer：前端没有的二进制世界](#21-为什么需要-buffer前端没有的二进制世界)
  - [2.2 Buffer 与 ArrayBuffer / TypedArray / Uint8Array 的关系](#22-buffer-与-arraybuffer--typedarray--uint8array-的关系)
  - [2.3 Buffer 的创建方式](#23-buffer-的创建方式)
  - [2.4 Buffer 的编码](#24-buffer-的编码)
  - [2.5 Buffer 与字符串互转（含中文场景）](#25-buffer-与字符串互转含中文场景)
  - [2.6 Buffer 与文件 / 网络的关系](#26-buffer-与文件--网络的关系)
  - [2.7 零拷贝：subarray 共享内存 vs slice 拷贝](#27-零拷贝subarray-共享内存-vs-slice-拷贝)
- [三、Stream 流详解](#三stream-流详解)
  - [3.1 四种流类型](#31-四种流类型)
  - [3.2 为什么用流：内存效率与大文件分块](#32-为什么用流内存效率与大文件分块)
  - [3.3 流的两种模式：flowing vs paused](#33-流的两种模式flowing-vs-paused)
  - [3.4 背压（backpressure）与 highWaterMark](#34-背压backpressure-与-highwatermark)
  - [3.5 pipe() 管道与 pipeline()](#35-pipe-管道与-pipeline)
  - [3.6 自定义流：Readable / Writable / Transform](#36-自定义流readable--writable--transform)
  - [3.7 迭代器消费流：for await...of](#37-迭代器消费流for-awaitof)
  - [3.8 Web Streams API（Node 18+ 全局 ReadableStream）](#38-web-streams-apinode-18-全局-readablestream)
- [四、核心概念解析](#四核心概念解析)
  - [4.1 Buffer 常用方法速查](#41-buffer-常用方法速查)
  - [4.2 Stream 事件速查](#42-stream-事件速查)
- [五、在 AI 全栈中的应用](#五在-ai-全栈中的应用)
- [六、关键知识点总结](#六关键知识点总结)
- [七、实战练习](#七实战练习)

---

## 一、学习目标

完成本节内容后，你将能够：

1. 解释前端为何几乎不接触二进制，而 Node.js 必须用 Buffer 处理 I/O。
2. 准确描述 Buffer 与 `ArrayBuffer` / `TypedArray` / `Uint8Array` 的继承与转换关系，知道“Buffer 就是 Uint8Array 的子类”。
3. 区分 `alloc` / `allocUnsafe` / `from` / `concat` 四种创建方式的内存安全差异。
4. 在 `utf8` / `base64` / `hex` / `ascii` / `binary` / `latin1` 之间自由转换，并理解中文在 UTF-8 下占 3 字节这一典型坑点。
5. 用 `subarray` 验证“共享内存零拷贝”，用 `slice` 理解“拷贝”，并知道为什么修改 `subarray` 的结果会影响原 Buffer。
6. 说出四种流类型（Readable / Writable / Duplex / Transform）的语义差异。
7. 解释 flowing 与 paused 两种模式的切换条件（`data` / `pause` / `resume` / `pipe`）。
8. 解释背压成因，知道 `write` 返回 `false` 时如何用 `'drain'` 事件解压。
9. 写出 `pipe()` 的局限，并能用 `stream.pipeline()` 做集中错误处理与资源清理。
10. 用 `new Readable({ read })` / `new Writable({ write })` / `new Transform({ transform })` 实现自定义流。
11. 用 `for await...of` 异步迭代消费 Readable 流。
12. 了解 Node 18+ 提供的全局 `ReadableStream` / `getReader()` Web Streams API 及其与传统 Node Stream 的互操作。

---

## 二、理论知识讲解

### 2.1 为什么需要 Buffer：前端没有的二进制世界

前端工程师处理数据时，绝大多数场景只需要 `string` 和 `JSON`：

- 文本输入 → `string`
- 接口返回 → `JSON.parse(string)`
- 文件上传 → `<input type="file">` 拿到 `File`（继承自 `Blob`），交给 `fetch` 直接 POST
- 图片显示 → `<img src="...">` 或 `URL.createObjectURL(blob)`

**浏览器替你把“字节”封装掉了**：`Blob` / `File` / `FileReader` / `Response.arrayBuffer()` 这些 API 让你几乎从不需要手动操作单个字节。

但到了 Node.js 后端：

- 你要 **从磁盘读一个 5GB 的模型权重文件** —— 不可能一次性 `readFile` 进内存。
- 你要 **接收 TCP socket 上的原始字节** —— HTTP 头、二进制协议、WebSocket 帧都是字节。
- 你要 **把 PNG 转 WebP** —— 必须逐字节解析文件头。
- 你要 **写入向量数据库的二进制向量载荷** —— `Float32Array` 的字节布局必须精确。

JavaScript 的 `string` 是 UTF-16 编码，无法直接表示任意字节序列（比如一个值为 200 的字节在 UTF-16 字符串里没有对应字符）。**Buffer 就是 Node.js 提供的“固定长度的字节容器”**，本质是一块堆外内存的视图，每个元素是 0~255 的无符号 8 位整数。

```js
const buf = Buffer.from([72, 105]);  // 两个字节
console.log(buf.toString());          // "Hi"
console.log(buf[0]);                  // 72
console.log(buf.length);              // 2
```

> 💡 **一句话**：前端把字节藏起来了，Node.js 把字节还给你了，Buffer 就是装字节的盒子。

### 2.2 Buffer 与 ArrayBuffer / TypedArray / Uint8Array 的关系

这是初学者最容易绕晕的地方。先看四个名词：

| 名词 | 出身 | 说明 |
|------|------|------|
| `ArrayBuffer` | ES2015（V8/语言层） | 一段**原始的、固定长度的二进制数据块**，本身不能直接读写，必须通过“视图”访问 |
| `TypedArray` | ES2015（语言层） | 一族**类型化数组视图**的统称，包括 `Uint8Array` / `Int32Array` / `Float32Array` 等 9 种，共享底层 `ArrayBuffer` |
| `Uint8Array` | ES2015（语言层） | 8 位无符号整数的 TypedArray，每个元素 0~255，最接近“字节数组”的概念 |
| `Buffer` | Node.js 专属 | Node.js 对 `Uint8Array` 的**子类化扩展**，增加了 `toString(encoding)` / `concat` / `alloc` 等便捷方法 |

**关键关系**：

```
   ArrayBuffer（原始字节块，不可直接访问）
        │  通过 TypedArray 视图访问
        ▼
   Uint8Array（8 位无符号视图）
        │  Node.js 子类化
        ▼
   Buffer（Uint8Array 的子类，多了字符串/编码/concat 等方法）
```

**证明 Buffer 是 Uint8Array 的子类**：

```js
const buf = Buffer.from('hello');
console.log(buf instanceof Uint8Array);   // true
console.log(buf instanceof Buffer);       // true
console.log(Buffer.prototype instanceof Uint8Array); // true
```

**互相转换**：

```js
// Buffer → Uint8Array（零拷贝，共享底层 ArrayBuffer）
const buf = Buffer.from('hello');
const u8 = new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);

// Uint8Array → Buffer（零拷贝）
const u8b = Buffer.from(arr.buffer, arr.byteOffset, arr.byteLength);
// 或
const u8b2 = Buffer.from(arr);  // Node 6+ 自动共享内存

// ArrayBuffer → Buffer
const ab = new ArrayBuffer(8);
const bufFromAb = Buffer.from(ab);  // 共享内存
```

> ⚠️ `Buffer.from(arrayBuffer)` 是**共享内存**而非拷贝。修改一方会影响另一方。若要拷贝请用 `Buffer.copyBytesFrom` 或 `Buffer.from(buffer)`。

### 2.3 Buffer 的创建方式

Node.js 提供四种主流创建方式，**内存安全差异**是面试高频考点：

#### `Buffer.alloc(size, fill, encoding)`

分配 `size` 字节并**用 `fill`（默认 0）填满**，**安全**。旧内存中可能残留别的进程数据，全置零可以避免敏感信息泄漏。

```js
const a = Buffer.alloc(10);        // 10 字节，全是 0
const b = Buffer.alloc(10, 0xff);  // 10 字节，全是 255
```

#### `Buffer.allocUnsafe(size)`

分配 `size` 字节但**不清零**，速度快但**不安全**。底层内存池里可能残留上一次使用的数据，直接暴露可能泄漏密钥、token。**只在你马上会完全覆写每一段时使用**。

```js
const c = Buffer.allocUnsafe(10);  // 10 字节，内容随机
c.fill(0);                         // 手动清零后就安全了
```

> 💡 Node 内部为了性能，`Buffer.allocUnsafe` 会优先从一个 8KB 的预分配池（`Buffer.poolSize`）切一块出来，避免每次都向操作系统申请内存。`Buffer.alloc` 则不使用池（怕被未清零的邻居污染）。

#### `Buffer.from(source, offsetOrEncoding, length)`

最常用的“从已有数据创建”，会**拷贝**：

```js
Buffer.from('hello', 'utf8');          // 字符串 → 字节
Buffer.from([1, 2, 3]);                // 数组 → 字节
Buffer.from(anotherBuffer);            // 复制一份（深拷贝）
Buffer.from(arrayBuffer);              // 共享底层 ArrayBuffer（特殊！不拷贝）
Buffer.from(typedArray);               // 共享底层 ArrayBuffer（特殊！不拷贝）
```

> 注意 `from(arrayBuffer)` 与 `from(buffer)` 的差异：前者共享内存，后者拷贝。

#### `Buffer.concat(list, totalLength)`

把多个 Buffer 拼接成一个新 Buffer，常用于流式数据累加。

```js
const parts = [Buffer.from('hello '), Buffer.from('world')];
const all = Buffer.concat(parts);  // "hello world"
console.log(all.toString());
```

**性能提示**：如果事先知道 `totalLength`，传入第二个参数可以让 Node 一次分配到位，避免动态扩容。流处理中累积数据时尤其有用。

#### 四种方式对比

| 方式 | 是否清零 | 是否拷贝 | 安全性 | 典型场景 |
|------|---------|---------|--------|---------|
| `alloc` | ✅ 是 | —— | ✅ 安全 | 默认选择，分配缓冲区 |
| `allocUnsafe` | ❌ 否 | —— | ⚠️ 需手动覆写 | 性能敏感且会立即写满 |
| `from(string/array)` | —— | ✅ 拷贝 | ✅ 安全 | 从已有数据创建 |
| `from(arrayBuffer/typedArray)` | —— | ❌ 共享 | ⚠️ 修改会相互影响 | 零拷贝转换 |
| `concat` | —— | ✅ 拷贝 | ✅ 安全 | 拼接多段 |

### 2.4 Buffer 的编码

`Buffer` 在与字符串互转时必须指定编码，默认 `utf8`。Node 支持以下编码：

| 编码 | 含义 | 1 字符占多少字节 | 用途 |
|------|------|----------------|------|
| `utf8` | UTF-8 变长编码 | 1~4（中文 3） | 默认，绝大多数文本 |
| `utf16le` | UTF-16 小端 | 2 或 4 | Windows 内部、JS 字符串内部 |
| `latin1` | ISO-8859-1 单字节 | 1 | 仅 0~255 范围字符 |
| `binary` | `latin1` 的别名 | 1 | 历史遗留，等同 `latin1` |
| `ascii` | 7 位 ASCII | 1 | 仅 0~127，高位被丢弃 |
| `base64` | Base64 编码 | 4/3（每 3 字节编 4 字符） | 二进制转文本传输（图片内联、JWT） |
| `base64url` | URL 安全的 Base64 | 同 base64 | URL/JWT 中替换 `+/` 为 `-_` |
| `hex` | 每字节转 2 个十六进制字符 | 2 | 哈希值、加密摘要展示 |

```js
const buf = Buffer.from('A', 'utf8');   // <Buffer 41>
const b64 = buf.toString('base64');     // "QQ=="
const hex = buf.toString('hex');        // "41"
Buffer.from('QQ==', 'base64').toString('utf8');  // "A"
```

> ⚠️ **易混点**：`ascii` 编码写入时，**任何大于 127 的字节都会被截断为低 7 位**，会破坏非 ASCII 数据。除非确定数据是纯 ASCII，否则用 `utf8` 或 `latin1`。

### 2.5 Buffer 与字符串互转（含中文场景）

**字符串 → Buffer**：`Buffer.from(str, encoding)`

**Buffer → 字符串**：`buf.toString(encoding, start, end)`

**中文场景的典型坑**：

UTF-8 下，一个汉字通常占 **3 字节**（部分生僻字 4 字节）。这是初学者最常踩的坑——以为 `slice(0, 1)` 能拿到第一个字，结果拿到的是半个字节序列，`toString` 后变成乱码。

```js
const zh = Buffer.from('你好世界', 'utf8');
console.log(zh.length);              // 12（4 个汉字 × 3 字节）
console.log(zh.toString('utf8', 0, 3));  // "你" —— 必须按 3 字节切
console.log(zh.toString('utf8', 0, 1));  // 乱码（半个“你”）

// 逐字遍历的正确姿势：用 for...of（按码点）
for (const ch of '你好世界') {
  const b = Buffer.from(ch, 'utf8');
  console.log(ch, b.length, b.toString('hex'));
}
// 你 3 e4bda0
// 好 3 e5a5bd
// 世 3 e4b896
// 界 3 e7958c
```

**安全切割含中文的 Buffer**：用 `TextDecoder` 的 `stream: true` 选项，或在已知编码是 UTF-8 时用 `Buffer.from(str).subarray` 配合码点边界。更稳妥的做法是**先 toString 再用字符串 slice**，避免在字节层切断多字节字符。

```js
// 错误：直接按字节切，可能切断汉字
function badSlice(buf, byteStart, byteEnd) {
  return buf.subarray(byteStart, byteEnd).toString('utf8');
}

// 正确：先转字符串，再按字符切
function safeSlice(buf, charStart, charEnd) {
  return buf.toString('utf8').slice(charStart, charEnd);
}
```

> 💡 **AI 场景联想**：大模型流式输出时，一个 token 可能是半个汉字（BPE 分词会把常见汉字拆成多字节 token）。后端必须用“流式解码器”（`TextDecoder({ stream: true })`）累积跨 chunk 的不完整字节，否则前端会看到乱码。这就是为什么 OpenAI SDK 内部用 `TextDecoder` 而不是直接 `chunk.toString()`。

### 2.6 Buffer 与文件 / 网络的关系

Node.js 中几乎一切二进制 I/O 都以 Buffer 为载体：

| 模块 | 返回 / 接收的数据形式 |
|------|---------------------|
| `fs.readFile(path, cb)` | 回调第二参数是 `Buffer` |
| `fs.writeFile(path, data)` | `data` 可以是 `Buffer` / `string` / `TypedArray` |
| `fs.createReadStream(path)` | `Readable` 流，`'data'` 事件载荷是 `Buffer` |
| `http.IncomingMessage` | 请求/响应体流，`'data'` 载荷是 `Buffer` |
| `net.Socket` | TCP 套接字，`'data'` 载荷是 `Buffer` |
| `dgram.Socket`（UDP） | `message` 事件载荷是 `Buffer` |
| `crypto` 哈希/加密 | `update()` 接收 `Buffer`，`digest()` 返回 `Buffer` |

**核心心智模型**：

```
   字符串/JSON（应用层）  ──编码──►  Buffer（字节层）  ──I/O──►  文件/网络
        ▲                                                   │
        └──────────────解码─────────────────────────────────┘
```

- **文件 I/O**：磁盘上的文件本质是字节序列。`fs.readFile` 把整份读进内存成一个大 Buffer；`fs.createReadStream` 则把这份字节序列切成一块块小 Buffer 通过流吐出。
- **网络 I/O**：TCP socket 收到的数据本身就是字节流，HTTP body 是其中一段。Node 把每次 `'data'` 事件的载荷给你一个 Buffer，你需要自己拼接、按协议解析。
- **加密 I/O**：哈希、HMAC、对称加密的输入输出都是字节，文本要先用 `Buffer.from(str, 'utf8')` 转成字节再喂给 `crypto`。

> ⚠️ 在 Node 中处理大文件，**永远优先用流而非 `readFile`**。后者会把整个文件读进内存，几 GB 的文件直接 OOM（Out of Memory）。

### 2.7 零拷贝：subarray 共享内存 vs slice 拷贝

Buffer 的“切片”有两个 API，行为截然不同：

| API | 行为 | 是否共享内存 | 性能 | 修改切片是否影响原 Buffer |
|-----|------|------------|------|------------------------|
| `buf.subarray(start, end)` | 返回同一段底层内存的视图 | ✅ 共享 | 快 | ✅ 影响 |
| `buf.slice(start, end)` | 返回一份新拷贝 | ❌ 拷贝 | 慢 | ❌ 不影响 |

```js
const parent = Buffer.from('hello world');

// subarray：共享内存
const sub = parent.subarray(0, 5);
console.log(sub.toString());      // "hello"
sub[0] = 72;                       // 'H'
console.log(parent.toString());    // "Hello world" —— 原缓冲被修改！

// slice：拷贝
const sl = parent.slice(0, 5);
sl[0] = 104;                       // 'h'
console.log(parent.toString());    // "Hello world" —— 原缓冲未变
```

**为什么 `subarray` 是零拷贝**：它只是创建了一个新的 Buffer 对象，但底层 `ArrayBuffer`、`byteOffset`、`byteLength` 都指向原 Buffer。在流处理中，常常用 `subarray` 把大 Buffer 切成若干块交给下游处理，避免每切一次就拷贝一次内存。

**为什么还需要 `slice`**：当你需要把切片交给**不可信的下游**（比如返回给外部调用方），不希望对方修改影响你的原数据时，必须用 `slice` 做防御性拷贝。

> ⚠️ 注意：旧版 Node 文档里 `Buffer.prototype.slice` 与 `Uint8Array.prototype.subarray` 行为相同（都是共享内存）。但为了安全，Node 在 Buffer 上把 `slice` 改成了拷贝语义，`subarray` 保持共享语义。**新代码请优先用 `subarray` 表达“共享内存”意图，用 `slice` 表达“要拷贝”意图**，避免歧义。本节配套代码 `buffer-basic.js` 用实验验证这一行为。

---

## 三、Stream 流详解

### 3.1 四种流类型

Node.js 的 `stream` 模块定义了四种流：

| 类型 | 方向 | 代表 API | 典型场景 |
|------|------|---------|---------|
| **Readable** | 可读（数据源 → 消费者） | `fs.createReadStream`、`http.IncomingMessage`、`process.stdin` | 读文件、接收 HTTP 请求体、读取标准输入 |
| **Writable** | 可写（生产者 → 数据汇） | `fs.createWriteStream`、`http.ServerResponse`、`process.stdout` | 写文件、返回 HTTP 响应、输出到控制台 |
| **Duplex** | 双向（同时可读可写，读写独立） | `net.Socket`、`tls.TLSSocket` | TCP 套接字、WebSocket |
| **Transform** | 变换（可读 + 可写，写入的数据经变换后从读端流出） | `zlib.createGzip()`、`crypto.createCipheriv()` | 压缩/解压、加解密、转码 |

**Duplex 与 Transform 的区别**：

- Duplex 的读端和写端是**两条独立的通道**（比如 socket：读端收对方数据，写端发数据给对方，互不转换）。
- Transform 的读端和写端是**同一条流水线**（写进去的数据经过 `transform()` 函数处理后，从读端吐出）。Transform 是 Duplex 的特例。

```
Readable:    [源] ──►  ──► 消费者
Writable:    生产者 ──► ──► [汇]
Duplex:      [源] ──►  ──► 消费者     （两路独立）
             生产者 ──► ──► [汇]
Transform:   生产者 ──► [变换函数] ──► 消费者   （一路加工）
```

### 3.2 为什么用流：内存效率与大文件分块

**反例：一次性读取大文件**

```js
// ❌ 危险：5GB 模型权重文件直接 readFile
fs.readFile('model.bin', (err, buf) => {
  // 进程内存瞬间涨到 5GB+，可能 OOM 崩溃
  doSomething(buf);
});
```

**正例：流式分块处理**

```js
// ✅ 安全：每次只在内存里放一小块（默认 64KB / highWaterMark）
const rs = fs.createReadStream('model.bin');
const ws = fs.createWriteStream('model.copy.bin');
rs.pipe(ws);
// 内存占用恒定，无论文件多大都能跑
```

**核心优势**：

1. **内存效率**：只把当前处理的“块”放内存，处理完即释放。1GB 文件用流可能只占 64KB 内存。
2. **时间效率（管道并行）**：读取、处理、写入可同时进行——读一块就处理一块就写一块，不必等整个文件读完。
3. **可组合性**：多个流用 `pipe` / `pipeline` 串联，像 Unix 管道一样组合：`读 → 解压 → 解密 → 解析`。

**心智对比**：

| 模式 | 内存占用 | 启动延迟 | 适用场景 |
|------|---------|---------|---------|
| 一次性读/写（`readFile`） | = 数据总量 | 高（要全部读完） | 配置文件、小 JSON |
| 流式（`createReadStream`） | ≈ `highWaterMark` | 低（首块就绪即开始） | 大文件、音视频、模型权重、流式响应 |

### 3.3 流的两种模式：flowing vs paused

**Readable 流有两种工作模式**，决定了数据“怎么吐出来”：

#### paused 模式（暂停模式，默认）

流创建后处于 paused 模式，数据**不会主动推送**，必须由消费者**主动调用 `stream.read()`** 拉取。这种模式让消费者可以按自己的节奏取数据。

```js
const rs = fs.createReadStream('a.txt');
rs.on('readable', () => {
  let chunk;
  while ((chunk = rs.read()) !== null) {
    console.log('读到', chunk.length, '字节');
  }
});
```

#### flowing 模式（流动模式）

一旦监听了 `'data'` 事件、调用了 `resume()`、或用了 `pipe()`，流就切换到 flowing 模式，数据**会尽可能快地主动推送**给 `'data'` 监听器。

```js
const rs = fs.createReadStream('a.txt');
rs.on('data', chunk => {
  console.log('读到', chunk.length, '字节');
});
rs.on('end', () => console.log('读完'));
```

#### 模式切换规则

| 操作 | 模式变化 |
|------|---------|
| 创建流 | paused |
| 监听 `'data'` 事件 | paused → flowing |
| 调用 `rs.pipe(dest)` | paused → flowing |
| 调用 `rs.resume()` | paused → flowing |
| 调用 `rs.pause()` | flowing → paused |
| 移除所有 `'data'` 监听器（`rs.off('data', ...)`） | flowing → paused（如果没有其他 `'data'` 监听器且未 pipe） |

```js
const rs = fs.createReadStream('a.txt');
rs.on('data', chunk => {
  console.log('chunk:', chunk.length);
  rs.pause();              // 暂停，等处理完再继续
  setTimeout(() => rs.resume(), 100);
});
```

> ⚠️ 如果同时监听 `'data'` 又调用 `read()`，行为未定义且容易出错。**选定一种模式就坚持用到底**：要么 flowing（`'data'`），要么 paused（`'readable'` + `read()`）。

### 3.4 背压（backpressure）与 highWaterMark

#### highWaterMark（高水位线）

每个流内部有一个**缓冲区**，`highWaterMark` 是这个缓冲区的“水位线”：

- Readable 流：内部缓冲的**最大字节数**（默认 64KB，对象模式 16 个对象）。超过此值时，流会**停止从底层资源读取**，等消费者取走一些再继续。
- Writable 流：内部缓冲的**最大字节数**（默认 16KB）。超过此值时，`write()` 会返回 `false`，提示生产者“我吃不下了，先别喂”。

#### 背压（backpressure）

**背压 = 消费速度跟不上生产速度时，反向施加给生产者的“压力”**。

典型场景：用 `readable.pipe(writable)` 时，Readable 读得飞快，Writable 写磁盘很慢。如果不加控制，Writable 内部缓冲会无限堆积，最终撑爆内存。Node 的解法是：

1. Writable 的 `write(chunk)` 返回 `false` 时，表示“缓冲超过 highWaterMark，我吃不下了”。
2. 此时生产者应该**停止写入**，并监听 Writable 的 `'drain'` 事件。
3. 当 Writable 把缓冲排空到水位线以下，会触发 `'drain'`，生产者再继续写。

**手动处理背压的标准模式**：

```js
function writeData(rs, ws) {
  rs.on('data', chunk => {
    const ok = ws.write(chunk);
    if (!ok) {
      // 写不动了，暂停读取
      rs.pause();
      ws.once('drain', () => {
        // 缓冲排空，恢复读取
        rs.resume();
      });
    }
  });
  rs.on('end', () => ws.end());
}
```

**`pipe()` 内部已经实现了这套背压逻辑**——这是为什么推荐用 `pipe` / `pipeline` 而不是手动监听 `data` 然后 `write`。

#### highWaterMark 调参

- 调大（如 1MB）：吞吐量上升，但内存占用上升，延迟波动大。
- 调小（如 4KB）：内存占用小，但 syscall 次数多，CPU 开销大。
- 默认值（16KB/64KB）是平衡点，**绝大多数场景不要动**。

> 💡 **AI 场景联想**：把大模型流式输出 pipe 到 HTTP 响应时，如果客户端网速慢，HTTP 响应流的 `write` 会返回 `false`，触发背压，让大模型 SDK 暂停拉取。这正是“流式响应 + 自动背压”让服务不会因慢客户端而 OOM 的关键。

### 3.5 pipe() 管道与 pipeline()

#### `readable.pipe(writable)`

把可读流的数据**自动**泵到可写流，内置背压处理：

```js
const fs = require('fs');
const zlib = require('zlib');

fs.createReadStream('input.txt')
  .pipe(zlib.createGzip())      // 中间可以串 Transform
  .pipe(fs.createWriteStream('input.txt.gz'));
```

#### `pipe()` 的三个致命缺陷

1. **错误不传播**：如果中间某个流抛错，`pipe` 不会把错误传到上下游，**目标流不会被关闭**，造成**文件描述符泄漏**和**僵尸流**。
2. **没有完成回调**：你不知道整条管道什么时候真正结束，难以串联后续逻辑。
3. **错误处理分散**：每个流都要单独 `.on('error', ...)`，遗漏一个就崩。

```js
// ❌ pipe 的经典坑：source 出错时 dest 不会被关闭
src.pipe(transform).pipe(dest);
src.on('error', () => {/* dest 仍打开着，fd 泄漏 */});
```

#### `stream.pipeline(...streams, callback)`

`stream.pipeline` 是官方推荐的替代方案，解决了上述三个问题：

```js
const { pipeline } = require('stream');

pipeline(
  fs.createReadStream('input.txt'),
  zlib.createGzip(),
  fs.createWriteStream('input.txt.gz'),
  (err) => {
    if (err) {
      console.error('管道失败：', err);
      // 所有流都会被自动销毁（destroy），fd 不会泄漏
      return;
    }
    console.log('管道完成');
  }
);
```

**pipeline 相比 pipe 的优势**：

| 维度 | `pipe()` | `pipeline()` |
|------|---------|-------------|
| 错误传播 | ❌ 不会传到上下游 | ✅ 任一流出错，全部销毁并回调 |
| 资源清理 | ❌ 出错时 fd 泄漏 | ✅ 自动 `destroy()` 所有流 |
| 完成回调 | ❌ 没有 | ✅ 有 callback（也支持 Promise 版） |
| 推荐度 | ⚠️ 简单场景可用 | ✅ 生产环境首选 |

**Promise 版**（Node 15+）：

```js
const { pipeline } = require('stream/promises');

await pipeline(
  fs.createReadStream('input.txt'),
  zlib.createGzip(),
  fs.createWriteStream('input.txt.gz')
);
console.log('完成');
```

> 🚫 **最佳实践**：生产代码一律用 `pipeline`，`pipe` 仅用于临时脚本或教学演示。

### 3.6 自定义流：Readable / Writable / Transform

#### 自定义 Readable

实现 `_read(size)` 方法，在其中调用 `push(chunk)` 推数据，`push(null)` 表示结束：

```js
const { Readable } = require('stream');

class CounterStream extends Readable {
  constructor(max, options) {
    super(options);
    this.max = max;
    this.current = 0;
  }
  _read() {
    this.current++;
    if (this.current > this.max) {
      this.push(null);    // 结束
    } else {
      const chunk = Buffer.from(`${this.current}\n`, 'utf8');
      this.push(chunk);
    }
  }
}

const counter = new CounterStream(5);
counter.on('data', c => process.stdout.write(c));
counter.on('end', () => console.log('结束'));
```

#### 自定义 Writable

实现 `_write(chunk, encoding, callback)`，处理完数据后调用 `callback()` 通知流“我处理完了，可以喂下一块”：

```js
const { Writable } = require('stream');

class LogStream extends Writable {
  _write(chunk, encoding, callback) {
    console.log('写入：', chunk.toString().trim());
    callback();   // 必须调用，否则流卡住
  }
}

const logger = new LogStream();
logger.write('hello\n');
logger.write('world\n');
logger.end();
```

#### 自定义 Transform

实现 `_transform(chunk, encoding, callback)`，在其中调用 `callback(err, transformedChunk)` 把变换后的数据推到读端：

```js
const { Transform } = require('stream');

const upper = new Transform({
  transform(chunk, encoding, callback) {
    callback(null, Buffer.from(chunk.toString().toUpperCase()));
  }
});

process.stdin.pipe(upper).pipe(process.stdout);
```

> 三种自定义流的 `_read` / `_write` / `_transform` 都是**下划线开头**，表示“由流框架内部调用”，业务代码不要直接调。

### 3.7 迭代器消费流：for await...of

Node 10+ 起，Readable 流**实现了异步迭代协议**（`Symbol.asyncIterator`），可以直接用 `for await...of` 消费：

```js
const fs = require('fs');

async function consume() {
  const rs = fs.createReadStream('a.txt');
  for await (const chunk of rs) {
    console.log('chunk:', chunk.length, '字节');
  }
  console.log('完成');
}
consume();
```

**相比 `'data'` 事件的优势**：

1. **天然串行**：`for await` 一次只处理一个 chunk，处理完再取下一个，避免回调并发。
2. **天然背压**：循环体内 `await` 任何异步操作时，流会自动暂停（等同 paused 模式），不会堆积。
3. **错误用 try/catch**：与同步 `for...of` 一致的心智模型。
4. **自动清理**：循环 `break` / `throw` 时，流会被自动 `destroy()`。

> ⚠️ `for await...of` 消费时流处于“类似 paused”的模式，`'data'` 事件不会触发。**不要混用**两种消费方式。

### 3.8 Web Streams API（Node 18+ 全局 ReadableStream）

从 Node 18 起，浏览器标准的 **Web Streams API** 在 Node 全局可用，无需 import：

- `ReadableStream`：可读流
- `WritableStream`：可写流
- `TransformStream`：变换流
- `ReadableStreamDefaultReader`：通过 `getReader()` 获取的阅读器

```js
// Web Streams API：手动构造一个 ReadableStream
const stream = new ReadableStream({
  start(controller) {
    controller.enqueue('hello ');
    controller.enqueue('world');
    controller.close();
  }
});

const reader = stream.getReader();
const decoder = new TextDecoder();
(async () => {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    console.log(value);
  }
})();
```

**与 Node Streams 的差异**：

| 维度 | Node Streams | Web Streams API |
|------|-------------|----------------|
| 起源 | Node 早期 | 浏览器标准（Fetch、whatwg） |
| 事件模型 | EventEmitter（`on('data')`） | Promise + Reader（`reader.read()`） |
| 全局可用 | 需 `require('stream')` | Node 18+ 全局 |
| 默认数据类型 | Buffer | `Uint8Array` |
| 背压 | `write` 返回 `false` + `'drain'` | Reader 不 `read()` 即自然背压 |
| 互操作 | —— | `Readable.fromWeb()` / `Readable.toWeb()` |

**互操作**：Node 提供了双向适配器，让两种流可以互相转换。

```js
const { Readable } = require('stream');
const nodeStream = fs.createReadStream('a.txt');
const webStream = Readable.toWeb(nodeStream);     // Node → Web
const backToNode = Readable.fromWeb(webStream);   // Web → Node
```

> 💡 **未来趋势**：`fetch` 返回的 `response.body` 就是 Web `ReadableStream`；新版 SDK（如 OpenAI Node SDK v4）已支持直接返回 Web Streams。掌握两套 API 并能互转，是 AI 全栈工程师的必备技能。

---

## 四、核心概念解析

### 4.1 Buffer 常用方法速查

| 方法 | 作用 | 是否改变原 Buffer | 返回值 |
|------|------|-----------------|--------|
| `Buffer.alloc(size, fill)` | 分配并清零 | —— | 新 Buffer |
| `Buffer.allocUnsafe(size)` | 分配不清零 | —— | 新 Buffer |
| `Buffer.from(source)` | 从源创建（拷贝/共享视源而定） | —— | 新 Buffer |
| `Buffer.concat([bufs], total)` | 拼接多个 | —— | 新 Buffer |
| `Buffer.byteLength(str, enc)` | 字符串在指定编码下的字节数 | —— | number |
| `Buffer.isBuffer(x)` | 判断是否 Buffer | —— | boolean |
| `buf.toString(enc, start, end)` | 转字符串 | 否 | string |
| `buf.write(str, offset, enc)` | 在指定偏移写入字符串 | ✅ 是 | 写入字节数 |
| `buf.slice(start, end)` | 切片（拷贝） | 否 | 新 Buffer |
| `buf.subarray(start, end)` | 切片（共享内存） | 否（但修改切片会影响原） | 视图 Buffer |
| `buf.copy(target, targetStart, start, end)` | 拷贝到目标 | ✅ 修改 target | 拷贝字节数 |
| `buf.fill(value, start, end)` | 填充 | ✅ 是 | 原 Buffer |
| `buf.equals(other)` | 内容相等比较 | 否 | boolean |
| `buf.compare(other)` | 字典序比较 | 否 | -1/0/1 |
| `buf.indexOf(value)` | 查找子序列 | 否 | number |
| `buf.readUInt8(offset)` 等 | 按整数类型读 | 否 | number |
| `buf.writeUInt8(value, offset)` 等 | 按整数类型写 | ✅ 是 | offset+字节数 |

### 4.2 Stream 事件速查

#### Readable 流事件

| 事件 | 触发时机 | 回调参数 |
|------|---------|---------|
| `'data'` | flowing 模式下有新数据块 | `chunk` |
| `'readable'` | paused 模式下有数据可读（或缓冲有变化） | 无 |
| `'end'` | 流中所有数据已读完（`push(null)` 后） | 无 |
| `'error'` | 读取发生错误 | `Error` |
| `'close'` | 流底层资源关闭（如文件描述符释放） | 无 |
| `'pause'` | 调用 `pause()` | 无 |
| `'resume'` | 调用 `resume()` | 无 |

#### Writable 流事件

| 事件 | 触发时机 | 回调参数 |
|------|---------|---------|
| `'drain'` | 缓冲从超水位降到水位以下，可继续写 | 无 |
| `'finish'` | 调用 `end()` 且缓冲全部写完 | 无 |
| `'error'` | 写入发生错误 | `Error` |
| `'close'` | 底层资源关闭 | 无 |
| `'pipe'` | 有 Readable 通过 `pipe()` 接入 | `src` 流 |
| `'unpipe'` | 有 Readable 解除 `pipe()` | `src` 流 |

> 💡 **`'end'` vs `'finish'`**：Readable 用 `'end'`，Writable 用 `'finish'`，记忆口诀“读完 end，写完 finish”。

---

## 五、在 AI 全栈中的应用

Buffer 与 Stream 在 AI 工程中无处不在，掌握它们是从“调 API 的前端”走向“搭基础设施的全栈”的分水岭。

### 5.1 模型文件与向量数据的二进制处理

**模型权重文件**：PyTorch `.pt`、ONNX `.onnx`、GGUF `.gguf` 动辄几 GB。下载、校验、分发都必须流式：

```js
// 流式下载模型并计算 SHA256 校验和（不把文件读进内存）
// 思路：用一个 Transform 流在数据落盘的同时“顺带”喂给 hash
const { pipeline } = require('stream/promises');
const crypto = require('crypto');
const fs = require('fs');
const https = require('https');

function createHashTee(hash) {
  // 小技巧：把 Transform 当“三通”，写入时同步 update hash，再原样吐出
  return new (require('stream').Transform)({
    transform(chunk, encoding, callback) {
      hash.update(chunk);
      callback(null, chunk);   // 原样转发，hash 顺带算
    }
  });
}

async function downloadWithChecksum(url, destPath) {
  const hash = crypto.createHash('sha256');
  await pipeline(
    https.get(url),                 // HTTP 响应流
    createHashTee(hash),            // tee：边算哈希边转发
    fs.createWriteStream(destPath)
  );
  return hash.digest('hex');        // 文件落盘同时算出哈希
}
```

**向量二进制载荷**：向量数据库（如 Qdrant、Milvus、pgvector）为了节省空间和加速传输，常把 embedding 存成 `Float32Array` 的二进制（每维 4 字节）。JSON 里一个 768 维向量是 768 个数字字符串，约 6KB；二进制只有 3072 字节，省一半且无解析开销。

```js
// embedding（Float32Array）↔ Buffer 互转
const embedding = new Float32Array([0.1, 0.2, 0.3]);
const buf = Buffer.from(embedding.buffer);          // 零拷贝
// 写入向量库 / 网络
const restored = new Float32Array(
  buf.buffer, buf.byteOffset, buf.byteLength / 4
);
```

### 5.2 流式响应：SSE 与大模型流式输出

**SSE（Server-Sent Events）** 是大模型流式输出的标准协议。后端把推理结果分成 token，用 `data: ...\n\n` 帧逐个推给前端。Node 中典型实现：

```js
// Express 路由：转发 OpenAI 流式响应
app.get('/chat/stream', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const upstream = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'gpt-4', stream: true, messages: [...] })
  });

  // upstream.body 是 Web ReadableStream
  const reader = upstream.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value, { stream: true });  // 流式解码，处理跨 chunk 的多字节字符
      // 解析 SSE 帧，原样转发给前端
      res.write(text);
    }
  } finally {
    res.end();
  }
});
```

**关键点**：

1. `TextDecoder({ stream: true })`：累积跨 chunk 的不完整 UTF-8 序列，避免汉字乱码（见 2.5）。
2. **背压**：如果前端网速慢，`res.write` 返回 `false`，应暂停从上游 `read`，否则内存堆积。
3. **错误清理**：用 `pipeline` 或 `try/finally` 确保上游 reader 被释放。

### 5.3 文件分块上传

大文件（音视频、数据集）上传常采用分块策略：前端切片 POST，后端拼接。后端用 Writable 流接收每片，最终用 `fs.createWriteStream` 的 `start` 选项写入正确偏移，或用 `pipeline` 把多片合并。

```js
// 后端：接收分片并写入到对应偏移
app.post('/upload/:chunkIndex', (req, res) => {
  const ws = fs.createWriteStream(destPath, {
    flags: 'r+',                          // 读写模式
    start: req.params.chunkIndex * CHUNK_SIZE
  });
  pipeline(req, ws, (err) => {
    if (err) return res.status(500).end();
    res.end('ok');
  });
});
```

> 💡 `req`（`http.IncomingMessage`）本身就是 Readable 流，可以直接 `pipeline` 到文件 Writable，无需中间 `await` 拼接 Buffer。

---

## 六、关键知识点总结

### ✅ 必须记住的 12 条

1. **Buffer 是字节容器**：固定长度的 8 位无符号整数数组，用于处理 Node 中一切二进制 I/O。
2. **Buffer 是 Uint8Array 的子类**：`buf instanceof Uint8Array === true`，与 `ArrayBuffer` / `TypedArray` 可零拷贝互转。
3. **`alloc` 安全，`allocUnsafe` 快但不安全**：`allocUnsafe` 必须立即完全覆写，否则可能泄漏残留数据。
4. **`from(arrayBuffer)` 共享内存，`from(buffer)` 拷贝**：两者行为不同，搞混会导致意外的内存共享或意外拷贝。
5. **UTF-8 下中文占 3 字节**：按字节切片会切断汉字，需用 `toString` 后按字符切，或用 `TextDecoder({stream:true})`。
6. **`subarray` 共享内存，`slice` 拷贝**：修改 `subarray` 结果会影响原 Buffer，`slice` 不会。
7. **四种流类型**：Readable / Writable / Duplex / Transform；Transform 是 Duplex 的特例（一进一出经过变换）。
8. **流有两种模式**：paused（默认，需 `read()`）与 flowing（`'data'` 事件 / `pipe` / `resume` 触发），不可混用。
9. **背压 = 消费慢于生产**：`write` 返回 `false` 时暂停，`'drain'` 触发后恢复；`pipe` / `pipeline` 内置背压。
10. **`pipeline` 优于 `pipe`**：自动错误传播、资源清理、完成回调；生产代码一律用 `pipeline`。
11. **`for await...of` 消费 Readable**：天然串行 + 背压 + try/catch，比 `'data'` 事件更安全。
12. **Web Streams API 全局可用**（Node 18+）：`ReadableStream` / `getReader()`，与 Node Streams 通过 `Readable.toWeb/fromWeb` 互转。

### 🚫 常见误区

| 误区 | 正解 |
|------|------|
| `Buffer.from(string)` 拷贝数据 | 字符串→Buffer 必然新建内存，没有“共享”可言 |
| `allocUnsafe` 一定不安全 | 只要立即完全覆写就安全，Node 内部大量使用它 |
| `slice` 和 `subarray` 行为一样 | Buffer 上不一样：`slice` 拷贝，`subarray` 共享 |
| 流的 `'data'` 和 `'readable'` 可同时用 | 不可，会进入未定义状态 |
| `pipe` 出错会自动关闭目标流 | 不会，这就是 `pipe` 的坑，要用 `pipeline` |
| `for await...of` 会触发 `'data'` 事件 | 不会，它是独立的异步迭代消费方式 |
| 高水位线是“缓冲上限” | 是“水位线”，超过只是停止读/写返回 false，不是硬上限 |

### 🎯 学习心法

> **Buffer 解决“数据是什么”（字节），Stream 解决“数据怎么流”（分块）**。前端工程师习惯了被浏览器呵护的 `Blob` / `fetch`，到了 Node 必须直面字节本身。当你能闭眼画出“字符串 ⇄ Buffer ⇄ 流 ⇄ 文件/网络”的数据通路，并知道每一步是否拷贝、何时背压、出错如何清理，就真正摸到了 AI 全栈基础设施的门槛。

---

## 七、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：Buffer 中文与编码互转（对应 `buffer-basic.js`）

1. 用 `Buffer.from('你好，AI 全栈', 'utf8')` 创建 Buffer，打印其 `length`，解释为什么不是字符个数。
2. 把该 Buffer 分别用 `utf8` / `base64` / `hex` / `latin1` 转 `toString`，观察输出差异，思考 `latin1` 为何乱码。
3. 用 `subarray(0, 3)` 取第一个汉字的字节，验证修改它会影响原 Buffer；再用 `slice(0, 3)` 验证不影响原 Buffer。
4. 构造 3 个 Buffer，用 `Buffer.concat` 拼接，并显式传入 `totalLength`，对比不传时的行为差异（用 `console.time` 测大数组拼接的性能差）。

### 练习 2：自定义 Transform 流 + pipeline（对应 `transform-stream.js` 与 `pipeline-demo.js`）

1. 实现一个 `PrefixTransform` 流：给每个 `chunk` 加前缀 `[log] `，再传给下游。
2. 用 `stream/promises` 的 `pipeline` 把 `process.stdin` → `PrefixTransform` → `process.stdout` 串起来，运行后在终端输入几行文字观察效果。
3. 在中间插入一个会随机抛错的 Transform 流（`Math.random() < 0.3` 时 `callback(new Error('boom'))`），用 `pipeline` 的回调捕获错误，验证所有流被自动销毁、无 fd 泄漏。

### 练习 3：背压与 highWaterMark 可视化（对应 `backpressure-demo.js`）

1. 创建一个高速 Readable 流（每 1ms push 一块 64KB 数据），和一个低速 Writable 流（每次 `write` 用 `setTimeout` 延迟 50ms 才 `callback`）。
2. 用 `'data'` 事件 + 手动 `write` 方式消费，**打印 `write` 的返回值**，观察何时返回 `false`。
3. 实现“暂停-恢复”逻辑：`write` 返回 `false` 时 `rs.pause()`，监听 `ws.once('drain')` 后 `rs.resume()`，打印每次背压发生的时间点。
4. 把 Writable 的 `highWaterMark` 从默认 16KB 调到 1MB，观察背压发生频率的变化，写下结论。

---

## 📂 配套代码

| 文件 | 内容 |
|------|------|
| `Code/buffer-basic.js` | Buffer 创建、编码转换、中文处理、concat、subarray 共享内存验证 |
| `Code/readable-stream.js` | 自定义 Readable 流，演示 `data/end` 事件与 `for await...of` 两种消费方式 |
| `Code/transform-stream.js` | 自定义 Transform 流（加前缀 / 转大写），用 `pipe` 链接 Readable→Transform→Writable |
| `Code/pipeline-demo.js` | 用 `stream.pipeline` 演示大文件读取→转换→写入，对比 `pipe` 的错误处理优势 |
| `Code/backpressure-demo.js` | 演示背压与 `highWaterMark`，`write` 返回 `false` 时的暂停-恢复处理 |

运行方式（Node 18+）：

```bash
cd "Day06 - Buffer与Stream流/Code"
node buffer-basic.js
node readable-stream.js
node transform-stream.js
node pipeline-demo.js
node backpressure-demo.js
```

---

## 🔗 延伸阅读

- [Node.js 官方文档：Buffer](https://nodejs.org/api/buffer.html)
- [Node.js 官方文档：Stream API](https://nodejs.org/api/stream.html)
- [Node.js 官方文档：Web Streams API](https://nodejs.org/api/webstreams.html)
- [MDN：Uint8Array](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Global_Objects/Uint8Array)
- [MDN：ReadableStream](https://developer.mozilla.org/zh-CN/docs/Web/API/ReadableStream)
- [Stream Handbook（社区经典）](https://github.com/substack/stream-handbook)

---

**下一节预告**：Day07 将进入 HTTP 服务与 Web 框架，把 Buffer / Stream 用起来搭建真实 API 服务，处理请求体解析、文件上传与 SSE 流式响应，为接入大模型 API 打下基础。
