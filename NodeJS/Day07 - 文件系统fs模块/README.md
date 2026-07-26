# Day07 - 文件系统 fs 模块

> 在浏览器里，前端同学接触到的“文件操作”大多是 `<input type="file">` 加上传接口；而到了 Node.js 后端，**读写本机文件** 是一项基础设施级能力。无论是加载训练数据（`.jsonl`/`.csv`）、缓存向量索引、写推理日志，还是落地模型权重，都绕不开 `fs` 模块。本篇将系统讲解 `fs` 的三种 API 风格、文件与目录的完整操作链路、流式处理大文件的思路，以及在 AI 工程场景下的最佳实践。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 fs 模块概述](#21-fs-模块概述)
  - [2.2 三种 API 风格：同步 / 回调 / Promise](#22-三种-api-风格同步--回调--promise)
  - [2.3 路径处理：绝对路径、相对路径与 cwd](#23-路径处理绝对路径相对路径与-cwd)
  - [2.4 文件描述符 fd 概念](#24-文件描述符-fd-概念)
  - [2.5 编码问题：utf8 与 null](#25-编码问题utf8-与-null)
- [三、文件操作详解](#三文件操作详解)
  - [3.1 读文件：readFile vs createReadStream](#31-读文件readfile-vs-createreadstream)
  - [3.2 写文件：writeFile / appendFile 与 flag 选项](#32-写文件writefile--appendfile-与-flag-选项)
  - [3.3 删除：unlink / rm 递归](#33-删除unlink--rm-递归)
  - [3.4 复制：copyFile](#34-复制copyfile)
  - [3.5 重命名与移动：rename](#35-重命名与移动rename)
  - [3.6 文件信息：stat 与 lstat](#36-文件信息stat-与-lstat)
  - [3.7 监听文件变化：watch / watchFile](#37-监听文件变化watch--watchfile)
  - [3.8 文件权限与 mode：chmod / chown](#38-文件权限与-modechmod--chown)
  - [3.9 软链接与硬链接：symlink / link](#39-软链接与硬链接symlink--link)
- [四、目录操作](#四目录操作)
  - [4.1 创建：mkdir recursive](#41-创建mkdir-recursive)
  - [4.2 读取：readdir withFileTypes](#42-读取readdir-withfiletypes)
  - [4.3 删除：rmdir / rm recursive](#43-删除rmdir--rm-recursive)
  - [4.4 临时目录：mkdtemp](#44-临时目录mkdtemp)
- [五、路径与 fs 的配合](#五路径与-fs-的配合)
- [六、最佳实践](#六最佳实践)
- [七、关键知识点总结](#七关键知识点总结)
- [八、实战练习](#八实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说出 `fs` 模块提供的三种 API 风格（`xxxSync` / 回调式 / `fs/promises`）的差异，并在新项目中默认选择 `fs/promises`。
2. 区分绝对路径、相对路径与 `process.cwd()` 的关系，理解为什么 `__dirname` 更可靠。
3. 解释文件描述符（fd）是什么，知道 `open` / `read` / `write` / `close` 这套底层 API 的存在意义。
4. 说明 `readFile` 与 `createReadStream` 的取舍：小文件整体读、大文件流式读，并知道为什么“整体读”会撑爆内存。
5. 用 `flag` 选项控制写文件行为：`'w'` 覆盖、`'a'` 追加、`'r+'` 读写不创建。
6. 区分 `stat` 与 `lstat`：处理符号链接时一个跟链、一个不跟链。
7. 理解文件权限 `mode` 的八进制表示（如 `0o644` / `0o755`），能调用 `chmod` 修改权限。
8. 区分软链接（`symlink`）与硬链接（`link`）的底层差异与适用场景。
9. 用 `mkdir recursive` 创建多层目录、用 `rm recursive` 安全删除目录树、用 `mkdtemp` 创建临时目录。
10. 用 `createReadStream` + `createWriteStream` + `pipeline` 实现大文件复制，理解“背压（backpressure）”机制。
11. 用 `readline` 逐行读取 `.jsonl` 文件，模拟处理 AI 训练数据。
12. 掌握“原子写入”（先写临时文件再 `rename`）、“避免循环内 `await`”、“文件锁”等生产实践。

---

## 二、理论知识讲解

### 2.1 fs 模块概述

`fs`（File System）是 Node.js 内置的核心模块，无需 `npm install`，直接 `require('fs')` 或 `import from 'fs'` 即可使用。它对操作系统的文件系统调用做了 JavaScript 层的封装，提供文件读写、目录管理、权限控制、链接、监听等几十种能力。

> 💡 **从前端视角理解**：浏览器出于安全考虑，JavaScript 不能直接读写用户硬盘上的任意文件；Node.js 运行在服务端或本地，拥有和 Python/Go 同等的文件系统权限——这是它能充当“脚本工具”与“后端服务”的前提。

`fs` 模块的特点：

- **同步与异步并存**：早期只有回调式异步 API；后来为方便脚本场景，加入了 `xxxSync` 同步 API；ES Module 时代又提供了 `fs/promises`。
- **底层基于 libuv**：异步文件 I/O 通过 libuv 的线程池实现（默认 4 个线程），不占用主事件循环，因此不会阻塞 JavaScript 主线程。
- **大文件友好**：提供流式（Stream）API，避免一次性把大文件载入内存。
- **跨平台**：同一套 API 在 Windows / macOS / Linux 上行为基本一致，仅权限模型与路径分隔符有细节差异。

### 2.2 三种 API 风格：同步 / 回调 / Promise

`fs` 对同一个能力通常提供三种写法。以“读取文件内容”为例：

| 风格 | 写法 | 是否阻塞 | 错误处理 | 推荐度 |
|------|------|---------|---------|--------|
| 同步 | `fs.readFileSync(path, 'utf8')` | ✅ 阻塞主线程 | `try/catch` | 仅限启动脚本、构建工具 |
| 回调式 | `fs.readFile(path, 'utf8', (err, data) => {})` | ❌ 非阻塞 | 错误优先回调第一参数 | 旧代码维护，新代码不推荐 |
| Promise | `await fs.promises.readFile(path, 'utf8')` | ❌ 非阻塞 | `try/catch` | ✅ 新项目首选 |

**三种风格对照示例**：

```js
const fs = require('fs');
const fsp = require('fs/promises');

// ① 同步：简单粗暴，但会卡住主线程
try {
  const data = fs.readFileSync('./a.txt', 'utf8');
  console.log('同步读取:', data);
} catch (err) {
  console.error('同步出错:', err.message);
}

// ② 回调式：错误优先（err 永远是第一个参数）
fs.readFile('./a.txt', 'utf8', (err, data) => {
  if (err) return console.error('回调出错:', err.message);
  console.log('回调读取:', data);
});

// ③ Promise（fs/promises）：可读性最好，配合 async/await
(async () => {
  try {
    const data = await fsp.readFile('./a.txt', 'utf8');
    console.log('Promise 读取:', data);
  } catch (err) {
    console.error('Promise 出错:', err.message);
  }
})();
```

**为什么推荐 `fs/promises`？**

1. **不阻塞主线程**，天然适配 Web 服务的并发模型。
2. **错误处理统一**，用 `try/catch` 替代层层 `if (err)`，告别回调地狱。
3. **可与 `Promise.all` 等合并器组合**，做并发批量 I/O。
4. **调试友好**，调用栈不会被回调切断。

**何时用同步 `xxxSync`？** 仅在“启动期加载配置、构建脚本、CLI 一次性工具”这类场景，且数据量极小、不在乎阻塞时使用。例如读取 `package.json`、加载 `.env`。**任何 HTTP 请求处理路径上都禁止使用同步 I/O。**

### 2.3 路径处理：绝对路径、相对路径与 cwd

`fs` 的所有 API 都接受一个 `path` 参数。路径分两类：

- **绝对路径**：从根目录开始，如 `/etc/hosts`（Linux）或 `D:\Coding\AI-FullStack`（Windows）。
- **相对路径**：相对于 `process.cwd()`（当前工作目录）解析，如 `./data/train.jsonl`。

> ⚠️ **新手高频坑**：相对路径**不是**相对于“当前 JS 文件”，而是相对于“启动 `node` 进程时所在的目录”。你在 `D:\` 下执行 `node D:\Coding\AI-FullStack\app.js`，`process.cwd()` 是 `D:\`，而不是 `D:\Coding\AI-FullStack`。

```js
console.log(process.cwd());  // 当前工作目录，取决于你在哪启动 node
```

**如何写出“与启动位置无关”的路径？** 用 `__dirname`（CommonJS）或 `import.meta.url`（ESM）拿到当前文件所在目录，再拼接：

```js
// CommonJS
const path = require('path');
const fs = require('fs');

const dataFile = path.join(__dirname, 'data', 'train.jsonl');
// __dirname 是当前 .js 文件所在目录的绝对路径，无论在哪启动 node 都一致

fs.readFileSync(dataFile, 'utf8');
```

```js
// ESM
import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
```

> 💡 **AI 场景联想**：训练脚本通常以 `node train.js --data ./dataset.jsonl` 形式启动。若脚本里用相对路径读 dataset，部署到不同目录就会找不到文件。统一用 `path.resolve(process.cwd(), argv.data)` 把用户传入的相对路径转成绝对路径，是更稳健的做法。

### 2.4 文件描述符 fd 概念

**文件描述符（File Descriptor，fd）** 是操作系统层面的一个非负整数句柄，用来标识“进程已打开的某个文件（或套接字、管道）”。在 POSIX 系统中，`0/1/2` 分别预留给标准输入、标准输出、标准错误，新打开的文件从 `3` 开始递增。

Node.js 通过 `fs.open(path, flags, mode, callback)` 打开文件获得 fd，再用 `fs.read(fd, ...)` / `fs.write(fd, ...)` 进行精细的“按字节、按偏移”读写，最后 `fs.close(fd)` 释放。

```js
const fs = require('fs');

fs.open('./a.txt', 'r', (err, fd) => {
  if (err) throw err;
  console.log('文件描述符:', fd);   // 例如 3 或更大的整数
  // ... 用 fs.read(fd, buffer, offset, length, position, cb) 精细读取
  fs.close(fd, () => console.log('已关闭'));
});
```

**为什么要知道 fd？**

1. `readFile` / `writeFile` 是“高层封装”，内部其实就是 `open → read/write → close` 的组合。理解 fd 后，你能用底层 API 做更细粒度控制（如随机位置读写、共享 fd 多次读写）。
2. 监听 `fs.watch` 返回的对象、`ReadStream` 内部也都依赖 fd。
3. 在性能敏感场景（如读取上万个文件），手动复用 fd 池能减少 `open/close` 开销。

> 日常 90% 的需求用 `readFile` / `writeFile` 即可，**不需要手写 `open/read/close`**。本篇主要使用高层 API，但你需要知道它们底层是 fd。

### 2.5 编码问题：utf8 与 null

`fs.readFile` / `readFileSync` 的第二个参数既可以是编码字符串（如 `'utf8'`、`'base64'`），也可以省略。区别在于**返回值类型**：

| 第二参数 | 返回值 | 用途 |
|---------|--------|------|
| `'utf8'`（或 `'utf-8'`） | `string` | 读文本文件（txt/json/jsonl/log/md） |
| 省略 / `null` | `Buffer` | 读二进制文件（图片、模型权重、压缩包） |
| `'base64'` | `string` | 把二进制读成 base64 字符串（用于内嵌到 JSON/HTML） |

```js
const fs = require('fs');

// 文本：传编码，得到 string
const text = fs.readFileSync('./readme.md', 'utf8');

// 二进制：不传编码，得到 Buffer
const buf = fs.readFileSync('./model.bin');
console.log(buf.length, 'bytes');   // 字节数
console.log(buf.slice(0, 4));        // <Buffer 1f 8b 08 00>

// 写入二进制：传 Buffer 即可，无需指定编码
fs.writeFileSync('./copy.bin', buf);
```

**关键点**：

- **`Buffer` 是 Node 独有的二进制容器**，类似前端的 `Uint8Array`。读出来的就是原始字节序列。
- **写文件时**，若内容是 `string`，可省略编码（默认 `'utf8'`）；若是 `Buffer`，则原样写入字节。
- **JSON 文件**：先用 `'utf8'` 读成 string，再 `JSON.parse`。`fs/promises` 没有内置 `readJSON`，需要手动两步。
- **Windows 上中文乱码**：多半是文件实际编码是 GBK 而你按 utf8 读。Node 不内置 GBK 解码，需用 `iconv-lite` 这类第三方库。

> 💡 **AI 场景联想**：大模型的词表（vocab.json）、配置（config.json）是文本，用 `'utf8'` 读；模型权重（`.bin` / `.safetensors`）、tokenizer 的 merge ranks 二进制段是二进制，必须用 `Buffer` 处理。

---

## 三、文件操作详解

### 3.1 读文件：readFile vs createReadStream

#### readFile：整体读取

`fs.readFile(path, options)`（Promise 版在 `fs/promises`）一次性把整个文件读入内存，调用完成后通过回调或 Promise 返回完整内容。

```js
const fsp = require('fs/promises');

const text = await fsp.readFile('./data.json', 'utf8');   // string
const json = JSON.parse(text);

const buf = await fsp.readFile('./image.png');            // Buffer
```

**优点**：API 简单，一行搞定。
**缺点**：文件多大，内存就占多大。读 2GB 的文件就会让进程内存瞬间涨到 2GB 以上（含解析开销），极易触发 V8 堆内存上限或 OOM。

> 经验法则：**文件 < 100MB** 用 `readFile`；**> 100MB** 考虑流式或分块。

#### createReadStream：流式读取

`fs.createReadStream(path, options)` 返回一个 `Readable` 流，按固定大小（默认 64KB，可配 `highWaterMark`）的分块从磁盘读出，逐块触发 `'data'` 事件。

```js
const fs = require('fs');

const rs = fs.createReadStream('./big.log', { encoding: 'utf8', highWaterMark: 64 * 1024 });

rs.on('data', chunk => {
  // 每次拿到一个 64KB 的字符串块
  processChunk(chunk);
});
rs.on('end', () => console.log('读完'));
rs.on('error', err => console.error(err));
```

**优势**：

- **内存恒定**：无论文件多大，内存里始终只有一块 buffer。
- **可.pipe()**：直接接到 `Writable` 流或转换流上，构成处理流水线。

**配合 `readline` 逐行处理**：见 `jsonl-reader.js`，是处理日志、训练数据的标准姿势。

### 3.2 写文件：writeFile / appendFile 与 flag 选项

#### writeFile：覆盖写入

`fs.writeFile(path, data, options)` 会**清空原文件**后写入新内容。若文件不存在则创建。

```js
const fsp = require('fs/promises');

await fsp.writeFile('./out.txt', '第一行内容\n', 'utf8');
await fsp.writeFile('./out.txt', '第二行内容\n', 'utf8');   // 第一行被覆盖！
// 最终 out.txt 内容只有 "第二行内容\n"
```

#### appendFile：追加写入

`fs.appendFile(path, data)` 在文件末尾追加，不破坏原内容；文件不存在则创建。

```js
await fsp.appendFile('./log.txt', `${new Date().toISOString()} 事件A\n`);
await fsp.appendFile('./log.txt', `${new Date().toISOString()} 事件B\n`);
```

#### flag 选项：精确控制打开模式

`writeFile` / `appendFile` / `open` 都接受 `flag` 选项，常用值：

| flag | 含义 | 文件不存在时 |
|------|------|-------------|
| `'r'` | 只读（默认读模式） | 抛错 |
| `'r+'` | 读写（不截断） | 抛错 |
| `'w'` | 只写，**清空原内容** | 创建 |
| `'w+'` | 读写，清空原内容 | 创建 |
| `'a'` | 只写，**追加到末尾** | 创建 |
| `'a+'` | 读写，追加到末尾 | 创建 |
| `'wx'` | 同 `'w'`，但**文件存在则失败** | 创建（防覆盖） |

```js
// 'a' 与 appendFile 等价
await fsp.writeFile('./log.txt', '一行\n', { flag: 'a' });

// 'wx' 防止误覆盖：常用于“创建一次性输出文件”
await fsp.writeFile('./result.lock', 'done', { flag: 'wx' });
// 若 result.lock 已存在，抛 EEXIST 错误
```

> ⚠️ `'wx'` 是实现“文件锁”与“原子创建”的原语之一，见 [6.4 原子写入](#64-原子写入先写临时文件再-rename)。

### 3.3 删除：unlink / rm 递归

- `fs.unlink(path)`：删除**文件**（不能删目录）。
- `fs.rm(path, { recursive: true, force: true })`：Node 14+ 引入，**既能删文件也能删目录树**，是现在的推荐方式。
- `fs.rmdir(path, { recursive: true })`：旧 API，**仅删目录**，且 `recursive` 在 Node 16+ 已废弃。

```js
const fsp = require('fs/promises');

await fsp.unlink('./temp.txt');                    // 删文件

await fsp.rm('./old-folder', { recursive: true }); // 递归删目录树
await fsp.rm('./maybe-missing', { force: true });  // 不存在也不抛错
```

> ⚠️ `rm recursive` 不可逆，**不要在用户传入的路径上盲目调用**。建议先 `stat` 校验是否在允许的工作目录内，再做删除。

### 3.4 复制：copyFile

`fs.copyFile(src, dest, mode)` 把源文件复制到目标路径。`mode` 是可选的位掩码常量：

- `fs.constants.COPYFILE_EXCL`：目标存在则失败（防覆盖）。
- `fs.constants.COPYFILE_FICLONE`：优先用“写时复制”（Linux `ioctl FICLONE`），秒级复制大文件。
- `fs.constants.COPYFILE_FICLONE_FORCE`：强制用写时复制，不支持则失败。

```js
const fsp = require('fs/promises');
const { COPYFILE_EXCL } = require('fs').constants;

await fsp.copyFile('./a.txt', './a.bak.txt', COPYFILE_EXCL);
// 若 a.bak.txt 已存在则抛 EEXIST
```

**`copyFile` 的局限**：它**不复制目录**，也不复制文件元数据（权限、mtime）。要复制目录树需自己递归，或用社区库 `fs-extra`。大文件复制更推荐用流（见 `stream-copy.js`）。

### 3.5 重命名与移动：rename

`fs.rename(oldPath, newPath)` 既能改名也能移动：

- 同目录下改名：`./a.txt` → `./b.txt`。
- 跨目录移动：`./dir1/a.txt` → `./dir2/a.txt`（要求两个目录在同一卷上，跨卷会失败）。

```js
await fsp.rename('./draft.txt', './final.txt');         // 改名
await fsp.rename('./in/a.txt', './out/a.txt');          // 移动
```

> 💡 `rename` 在同一文件系统上是**原子操作**，这是“原子写入”模式的基础：先写临时文件，再 `rename` 成正式文件，要么完整生效、要么完全不生效。

### 3.6 文件信息：stat 与 lstat

`fs.stat(path)` 返回一个 `Stats` 对象，包含文件大小、时间戳、权限、类型等信息。常用字段：

| 字段 / 方法 | 含义 |
|------------|------|
| `size` | 文件字节数 |
| `mtime` | 最后修改时间（`Date`） |
| `ctime` | 最后状态改变时间 |
| `atime` | 最后访问时间 |
| `birthtime` | 创建时间 |
| `isFile()` | 是否普通文件 |
| `isDirectory()` | 是否目录 |
| `isSymbolicLink()` | 是否符号链接（仅 `lstat` 返回 true） |
| `mode` | 权限位（八进制） |

```js
const fsp = require('fs/promises');

const st = await fsp.stat('./a.txt');
console.log(st.size, 'bytes');
console.log(st.mtime.toISOString());
console.log('是文件?', st.isFile());
```

**`stat` vs `lstat` 的区别**：

| API | 遇到符号链接时的行为 |
|-----|---------------------|
| `stat` | **跟随链接**，返回链接所指向的目标文件的属性 |
| `lstat` | **不跟随**，返回链接文件本身的属性 |

```js
// 假设 ./shortcut 是指向 ./real.txt 的符号链接
await fsp.stat('./shortcut');     // 等价于 stat('./real.txt')
await fsp.lstat('./shortcut');    // 返回“这是一个符号链接”的属性
// lstat(...).isSymbolicLink() === true
```

> 想判断“用户给的是不是软链”，必须用 `lstat`。否则 `stat` 会跟着链接跑到目标上，`isSymbolicLink()` 永远是 false。

### 3.7 监听文件变化：watch / watchFile

`fs` 提供两种监听方式：

#### fs.watch：基于操作系统通知（推荐）

```js
const fs = require('fs');

const watcher = fs.watch('./config.json', (eventType, filename) => {
  console.log(`事件: ${eventType}, 文件: ${filename}`);
});
watcher.on('error', err => console.error(err));
// 停止监听
// watcher.close();
```

- 优点：底层调用 inotify（Linux）/ FSEvents（macOS）/ ReadDirectoryChangesW（Windows），开销小。
- 缺点：**不同平台行为不一致**，常出现“一次保存触发两次 `change` 事件”的怪现象；某些网络盘不支持。

#### fs.watchFile：基于轮询（兼容性好但效率低）

```js
fs.watchFile('./config.json', { interval: 1000 }, (curr, prev) => {
  if (curr.mtimeMs !== prev.mtimeMs) {
    console.log('文件被修改了');
  }
});
// 停止：fs.unwatchFile('./config.json')
```

- 底层是 `setInterval` 定期 `stat`，跨平台一致但开销大。
- 适合在不支持 `watch` 的网络盘上使用。

> 生产环境做“配置热更新”或“目录变化触发任务”，更推荐用社区库 [`chokidar`](https://github.com/paulmillr/chokidar)，它封装了上述差异并解决了重复触发的坑。

### 3.8 文件权限与 mode：chmod / chown

#### 权限的八进制表示

POSIX 权限分三组：**所有者 / 同组用户 / 其他用户**，每组三位 `rwx`。常用八进制表示：

| 八进制 | 二进制 | 含义 |
|--------|--------|------|
| `0o755` | `111 101 101` | 所有者可读写执行，其他人可读可执行（目录、可执行文件默认） |
| `0o644` | `110 100 100` | 所有者可读写，其他人只读（普通文件默认） |
| `0o600` | `110 000 000` | 仅所有者可读写（私钥文件） |
| `0o444` | `100 100 100` | 全员只读 |

```js
const fsp = require('fs/promises');

await fsp.chmod('./private.key', 0o600);   // 私钥，仅所有者可读写
await fsp.chmod('./deploy.sh', 0o755);     // 脚本可执行
```

> ⚠️ Windows 的权限模型与 POSIX 不同，`chmod` 在 Windows 上**只影响“只读位”**，不能完整模拟 POSIX 权限。AI 服务通常部署在 Linux，按 Linux 规范设置即可。

#### chown：改所有者

`fs.chown(path, uid, gid)` 修改文件的所有者 uid 和组 gid。需要 root 权限，常用于安装脚本：

```js
await fsp.chown('./app.log', 1000, 1000);
```

### 3.9 软链接与硬链接：symlink / link

| 类型 | API | 创建方式 | 是否跨文件系统 | 删除原文件后 |
|------|-----|---------|----------------|-------------|
| 软链接（symbolic link / symlink） | `fs.symlink(target, path)` | 创建一个独立的“链接文件”，内容是目标路径字符串 | ✅ 可跨卷 | 链接失效（dangling） |
| 硬链接（hard link） | `fs.link(existingPath, newPath)` | 在目录表里新增一个指向同一 inode 的条目 | ❌ 同卷内 | 仍可访问，内容不丢失 |

```js
const fsp = require('fs/promises');

// 软链接
await fsp.symlink('./real.txt', './shortcut.txt');
// 读写 ./shortcut.txt 实际操作 ./real.txt

// 硬链接
await fsp.link('./real.txt', './hardlink.txt');
// 两个路径指向同一份数据，删其一不影响另一个
```

**用途对比**：

- **软链接**像“快捷方式”，常用于：依赖目录别名、版本切换（`node` → `node@18`）、把大文件放到外部盘后在项目里建软链。
- **硬链接**是“同一份数据的多个名字”，常用于：增量备份（rsync 的 `--link-dest`）、节省存储重复文件。

> 📌 硬链接的 `inode` 相同，用 `fs.stat` 看 `stats.nlink`（链接数）能知道有多少硬链接指向同一文件。`fs.stat` 对软链接会“跟随”，要看软链本身用 `lstat`。

---

## 四、目录操作

### 4.1 创建：mkdir recursive

`fs.mkdir(path, { recursive: true })` 创建目录。`recursive` 选项允许一次性创建多层不存在的父目录，类似 `mkdir -p`。

```js
const fsp = require('fs/promises');

// 不加 recursive：父目录不存在会抛错
await fsp.mkdir('./a/b/c');                       // 若 a/b 不存在，抛 ENOENT

// 加 recursive：自动创建 a、a/b、a/b/c
await fsp.mkdir('./a/b/c', { recursive: true });  // ✅
// 目录已存在不会抛错，幂等
```

> `recursive: true` 是 AI 项目里管缓存的利器：`./cache/vecstore/shards/2026-07` 这种多层路径一次性建好，不用担心父级缺失。

### 4.2 读取：readdir withFileTypes

`fs.readdir(path, { withFileTypes: true })` 列出目录下的条目。加上 `withFileTypes` 后返回的是 `Dirent` 对象数组，可直接调用 `isFile()` / `isDirectory()` / `isSymbolicLink()`，**省去对每个条目再 `stat` 一次的开销**。

```js
const fsp = require('fs/promises');
const path = require('path');

const entries = await fsp.readdir('./data', { withFileTypes: true });
for (const ent of entries) {
  const full = path.join('./data', ent.name);
  if (ent.isDirectory()) {
    console.log('[目录]', ent.name);
  } else if (ent.isFile()) {
    console.log('[文件]', ent.name);
  } else if (ent.isSymbolicLink()) {
    console.log('[软链]', ent.name);
  }
}
```

### 4.3 删除：rmdir / rm recursive

如前述 [3.3](#33-删除unlink--rm-递归)，删除目录树用 `fs.rm(path, { recursive: true })`。`fs.rmdir` 仅删空目录（旧版 `recursive` 参数已废弃，不要用）。

```js
await fsp.rm('./old-cache', { recursive: true, force: true });
// recursive: 递归删子内容；force: 不存在不抛错
```

### 4.4 临时目录：mkdtemp

`fs.mkdtemp(prefix)` 在系统临时目录（`os.tmpdir()`）下创建一个**带随机后缀**的目录，返回完整路径。常用于单元测试、批处理中间产物。

```js
const fsp = require('fs/promises');
const os = require('os');
const path = require('path');

// 注意：prefix 是路径前缀，不是完整路径，建议用绝对路径前缀
const tmpDir = await fsp.mkdtemp(path.join(os.tmpdir(), 'ai-job-'));
console.log('临时目录:', tmpDir);
// 例如: /tmp/ai-job-Xk3p9aQb
```

> ⚠️ `mkdtemp` 的 `prefix` 若传相对路径，结果会落在 `process.cwd()` 下而非 `/tmp`。务必用 `path.join(os.tmpdir(), prefix)` 保证落在系统临时目录。

---

## 五、路径与 fs 的配合

`path` 模块是 `fs` 的天然搭档。常用方法：

| 方法 | 作用 | 示例 |
|------|------|------|
| `path.join(...)` | 拼接路径（自动用平台分隔符） | `path.join('a','b','c.txt')` → `a\b\c.txt`（Windows） |
| `path.resolve(...)` | 拼接并解析为绝对路径 | `path.resolve('a','b')` → `<cwd>/a/b` |
| `path.dirname(p)` | 取目录部分 | `path.dirname('/a/b/c.txt')` → `/a/b` |
| `path.basename(p)` | 取文件名 | `path.basename('/a/b/c.txt')` → `c.txt` |
| `path.extname(p)` | 取扩展名 | `path.extname('/a/b/c.txt')` → `.txt` |
| `path.parse(p)` | 解析成 `{root,dir,base,name,ext}` | |
| `path.sep` | 平台分隔符（`\\` 或 `/`） | |
| `path.isAbsolute(p)` | 是否绝对路径 | |

**经典组合：写“与启动位置无关”的文件路径**：

```js
// CommonJS
const path = require('path');
const fsp = require('fs/promises');

// __dirname 是当前 .js 文件所在目录
const dataFile = path.join(__dirname, '..', 'data', 'train.jsonl');
// 从当前文件的目录向上一级，再进 data 目录

const text = await fsp.readFile(dataFile, 'utf8');
```

**ESM 中没有 `__dirname`，需要从 `import.meta.url` 派生**：

```js
import path from 'path';
import { fileURLToPath } from 'url';
import fsp from 'fs/promises';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dataFile = path.join(__dirname, '..', 'data', 'train.jsonl');
const text = await fsp.readFile(dataFile, 'utf8');
```

**把用户传入的相对路径转成绝对路径**：

```js
// CLI 接受 --data 参数，可能是绝对或相对路径
function resolveDataPath(p) {
  return path.isAbsolute(p) ? p : path.resolve(process.cwd(), p);
}
```

---

## 六、最佳实践

### 6.1 异步优先，拒绝 xxxSync

在 Web 服务、AI 推理网关这类需要并发处理多请求的场景，**任何同步 I/O 都会让所有请求排队等待**。规则：

- ✅ 服务运行时：只用 `fs/promises` 或回调式 API。
- ✅ 进程启动期（读 `package.json`、`.env`、加载词典）：可以 `readFileSync`，但只执行一次。
- ❌ HTTP 处理函数内：禁止 `readFileSync` / `writeFileSync` / `statSync`。

### 6.2 错误处理：永远 try/catch 或 .catch

`fs/promises` 的失败会变成 rejected Promise，**不 catch 就会冒泡成 `unhandledRejection`**，新版 Node 会直接让进程退出。常见错误码：

| 错误码 | 含义 | 处理建议 |
|--------|------|---------|
| `ENOENT` | 文件/目录不存在 | 创建或返回 404 |
| `EACCES` | 权限不足 | 检查 `chmod` / 运行用户 |
| `EEXIST` | 文件已存在（多见于 `wx` flag） | 视业务决定覆盖还是放弃 |
| `EISDIR` | 把目录当文件操作 | 提前 `stat` 判断类型 |
| `ENOTDIR` | 把文件当目录操作 | 同上 |
| `EMFILE` | 打开文件过多（fd 耗尽） | 检查是否漏 `close`，或调高 `ulimit -n` |

```js
try {
  await fsp.writeFile(out, data);
} catch (err) {
  if (err.code === 'ENOENT') {
    await fsp.mkdir(path.dirname(out), { recursive: true });
    await fsp.writeFile(out, data);  // 重试
  } else {
    throw err;
  }
}
```

### 6.3 避免在循环中 await，用 Promise.all

```js
// ❌ 串行：慢
for (const id of ids) {
  const data = await fsp.readFile(`./${id}.json`, 'utf8');
  process(data);
}

// ✅ 并发：快（但要注意 fd 上限，不要一次几万个）
await Promise.all(ids.map(async id => {
  const data = await fsp.readFile(`./${id}.json`, 'utf8');
  process(data);
}));
```

**注意 fd 上限**：`Promise.all` 一次打开几万个文件会触发 `EMFILE`。用 [6.5 并发上限](#65-并发上限分批-promiseall) 的分批模式，或用社区库 `p-limit`。

### 6.4 原子写入：先写临时文件再 rename

直接 `writeFile` 写正式文件，写到一半进程崩溃会留下**截断的脏文件**。原子写入模式：

1. 写到同一目录下的临时文件 `xxx.tmp`。
2. `fs.rename(tmp, final)` 把临时文件改名成正式文件。`rename` 在同一文件系统上是原子操作。

```js
async function atomicWrite(file, content) {
  const tmp = file + '.tmp.' + process.pid;
  await fsp.writeFile(tmp, content, 'utf8');
  await fsp.rename(tmp, file);   // 原子替换
}

await atomicWrite('./config.json', JSON.stringify(newConfig, null, 2));
```

**为什么必须同一目录？** `rename` 跨文件系统会降级为“复制+删除”，不再原子。把临时文件放在目标同目录可保证同卷。

### 6.5 并发上限：分批 Promise.all

借鉴 Day05 的 `parallelWithLimit` 模式：

```js
async function mapWithLimit(items, limit, worker) {
  const results = [];
  const executing = new Set();
  for (const item of items) {
    const p = Promise.resolve().then(() => worker(item));
    results.push(p);
    executing.add(p);
    p.finally(() => executing.delete(p));
    if (executing.size >= limit) {
      await Promise.race(executing);
    }
  }
  return Promise.all(results);
}

// 每批最多 8 个并发
await mapWithLimit(files, 8, f => fsp.unlink(f));
```

### 6.6 大文件用流，避免 readFile 撑爆内存

```js
const { pipeline } = require('stream/promises');
const fs = require('fs');

await pipeline(
  fs.createReadStream('./input.bin'),
  someTransformStream,
  fs.createWriteStream('./output.bin')
);
```

`pipeline` 比 `.pipe()` 更安全：它会自动处理“背压（backpressure）”，并在源出错时关闭下游流，避免内存泄漏。

### 6.7 AI 场景应用速查

| 场景 | 推荐 API |
|------|---------|
| 读取训练数据 `.jsonl` / `.csv` | `createReadStream` + `readline`，逐行解析 |
| 保存模型权重 / 向量索引 | 二进制用 `Buffer` + `writeFile`；大文件用 `pipeline` |
| 写推理日志 | `appendFile` 或 `createWriteStream({ flags: 'a' })` |
| 缓存目录管理 | `mkdir recursive` + `mkdtemp`（临时）+ `rm recursive`（清理） |
| 文件锁（防并发写同一文件） | `open(path, 'wx')` 创建独占锁文件；或 `proper-lockfile` 库 |
| 配置热更新 | `fs.watch`（或更稳的 `chokidar`） |
| 增量备份 / 节省存储 | 硬链接 `fs.link` |
| 版本切换（如多 Python/Node 版本） | 软链接 `fs.symlink` |

---

## 七、关键知识点总结

1. **三种 API 风格**：`xxxSync`（同步阻塞，仅启动期）、回调式（旧代码）、`fs/promises`（新项目首选）。
2. **路径相对的是 `process.cwd()`**，不是当前文件；用 `__dirname`（CommonJS）或 `import.meta.url`（ESM）构造与启动位置无关的路径。
3. **fd 是底层句柄**，`readFile`/`writeFile` 内部即 `open→read/write→close`；高层 API 已够用。
4. **编码**：文本传 `'utf8'` 得 `string`；二进制不传得 `Buffer`；GBK 需 `iconv-lite`。
5. **读文件**：小文件 `readFile`，大文件 `createReadStream` + `readline` 逐行。
6. **写文件 flag**：`'w'` 覆盖、`'a'` 追加、`'wx'` 防覆盖（实现文件锁与原子创建）。
7. **删除**：`unlink` 删文件，`rm recursive` 删目录树，`rmdir` 已废弃。
8. **stat vs lstat**：`stat` 跟随软链，`lstat` 不跟；判断软链必须用 `lstat`。
9. **权限 mode**：八进制如 `0o755` / `0o644` / `0o600`，用 `chmod` 修改。
10. **软链接 vs 硬链接**：软链接是独立文件（路径指针），可跨卷；硬链接是同 inode 的多个名字，同卷、`nlink` 计数。
11. **目录**：`mkdir recursive`、`readdir withFileTypes`（省一次 stat）、`mkdtemp`（落在 `os.tmpdir()`）。
12. **大文件复制**：`createReadStream` + `createWriteStream` + `pipeline`，自动背压。
13. **原子写入**：写临时文件 + `rename`，同卷保证原子性。
14. **并发**：避免循环内 `await`，用 `Promise.all`；fd 多时用并发上限分批。
15. **错误码**：`ENOENT` / `EACCES` / `EEXIST` / `EISDIR` / `ENOTDIR` / `EMFILE` 是高频错误，按 code 分支处理。

---

## 八、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：三种 API 风格对比（对应 `sync-vs-async.js`）

1. 在 `Code/` 下创建 `sample.txt`，内容随意几行。
2. 分别用 `readFileSync`、`readFile`（回调）、`fs/promises.readFile` 三种方式读取同一个文件，把结果打印出来。
3. 在每个分支里加上错误处理（`try/catch` 或 `if (err)`）。
4. 故意读一个不存在的文件，观察三种写法各自如何报错。

**思考**：如果代码运行在 Web 服务的请求处理函数里，三种写法哪种不可用？为什么？

### 练习 2：文件全生命周期 + 原子写入（对应 `file-ops.js`）

1. 用 `fs/promises` 完成：`writeFile` 写入初始内容 → `appendFile` 追加两行 → `stat` 打印 size 和 mtime → `rename` 改名 → 再次 `stat` 验证 → `unlink` 删除。
2. 全程用 `try/catch` 包裹，捕获并打印 `err.code`。
3. 加分项：实现 `atomicWrite(file, content)` 函数（写临时文件 + rename），并测试“目标文件已存在时也能完整替换”。

### 练习 3：目录递归遍历 + 大文件复制 + JSONL 解析（对应 `dir-ops.js` / `stream-copy.js` / `jsonl-reader.js`）

1. 用 `mkdir recursive` 创建多层测试目录（如 `test/a/b/c`），在每层放几个 `.txt` 和子目录。然后写一个 `walk(dir)` 函数，用 `readdir withFileTypes` 递归遍历，打印所有文件的相对路径与大小。最后用 `rm recursive` 清理。
2. 用循环写入生成一个 50MB 的 `big.bin`，然后用 `createReadStream` + `createWriteStream` + `pipeline` 把它复制成 `big-copy.bin`，对比两者 `stat().size` 是否一致，并打印复制耗时。
3. 手写一个 `.jsonl` 文件（每行一个 JSON 对象，比如 `{ "prompt": "...", "answer": "..." }`，10 行左右），用 `readline` 逐行读取并 `JSON.parse`，统计总行数和出现过的所有 `prompt` 字段。注意处理空行和 JSON 解析失败的容错。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/sync-vs-async.js` | 三种 API 风格读取同一文件的对比，演示推荐 `fs/promises` |
| `Code/file-ops.js` | `fs/promises` 实现写/追加/stat/rename/unlink 全流程，含错误处理与原子写入 |
| `Code/dir-ops.js` | `mkdir recursive`、`readdir withFileTypes`、递归遍历、`rm recursive` |
| `Code/stream-copy.js` | `createReadStream` + `createWriteStream` + `pipeline` 大文件复制 |
| `Code/jsonl-reader.js` | `readline` 逐行读取 `.jsonl` 并解析 JSON，模拟 AI 训练数据处理 |

运行方式（Node 18+）：

```bash
node Code/sync-vs-async.js
node Code/file-ops.js
node Code/dir-ops.js
node Code/stream-copy.js
node Code/jsonl-reader.js
```

---

> 📚 **延伸阅读**
> - Node.js 官方文档：[File system](https://nodejs.org/api/fs.html)
> - Node.js 官方文档：[fs/promises](https://nodejs.org/api/fs.html#promise-api)
> - Node.js 官方文档：[Stream](https://nodejs.org/api/stream.html)
> - Node.js 官方文档：[Path](https://nodejs.org/api/path.html)
> - MDN：[Using files from web applications](https://developer.mozilla.org/zh-CN/docs/Web/API/File/Using_files_from_web_applications)（对比浏览器端文件 API）
> - chokidar：[github.com/paulmillr/chokidar](https://github.com/paulmillr/chokidar)
