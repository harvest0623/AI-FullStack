# Day08 - Path 与 OS 等核心模块

> 前端开发中，路径通常是 `/assets/logo.png` 这种写死的字符串；到了 Node.js 后端，文件路径会跨平台、跨用户目录、跨容器挂载点，再叠加 ESM/CommonJS 的 import.meta.url，"拼路径"就成了一个高频却暗藏坑点的工作。本篇聚焦五个被严重低估的"工具型"内置模块：**path、os、url、util、crypto**——它们既不涉及网络 I/O，也不参与事件循环，但却是任何一份生产级 Node 代码的底座：加载配置文件、按 CPU 核数分配推理 worker、给 API key 加密、把回调风格的 fs 包成 Promise……几乎每一处都会用到。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、path 模块详解](#二path-模块详解)
  - [2.1 为什么不要用字符串拼接路径](#21-为什么不要用字符串拼接路径)
  - [2.2 path.join vs path.resolve](#22-pathjoin-vs-pathresolve)
  - [2.3 路径解析与重组：normalize / parse / format](#23-路径解析与重组normalize--parse--format)
  - [2.4 取片段：dirname / basename / extname](#24-取片段dirname--basename--extname)
  - [2.5 平台差异：sep / delimiter / posix / win32](#25-平台差异sep--delimiter--posix--win32)
  - [2.6 判断与相对化：isAbsolute / relative](#26-判断与相对化isabsolute--relative)
  - [2.7 AI 场景联想](#27-ai-场景联想)
- [三、os 模块详解](#三os-模块详解)
  - [3.1 系统信息](#31-系统信息)
  - [3.2 CPU 信息与负载](#32-cpu-信息与负载)
  - [3.3 内存信息](#33-内存信息)
  - [3.4 网络接口](#34-网络接口)
  - [3.5 EOL 换行符](#35-eol-换行符)
  - [3.6 用户信息与常量](#36-用户信息与常量)
  - [3.7 AI 场景联想](#37-ai-场景联想)
- [四、url 模块](#四url-模块)
  - [4.1 legacy url.parse 与 WHATWG URL](#41-legacy-urlparse-与-whatwg-url)
  - [4.2 URL 对象的属性](#42-url-对象的属性)
  - [4.3 URLSearchParams](#43-urlsearchparams)
  - [4.4 fileURLToPath 与 pathToFileURL](#44-fileurltopath-与-pathtofileurl)
  - [4.5 相对 URL 解析](#45-相对-url-解析)
- [五、querystring（已废弃）与 URLSearchParams](#五querystring已废弃与-urlsearchparams)
- [六、util 模块](#六util-模块)
  - [6.1 util.promisify：回调转 Promise](#61-utilpromisify回调转-promise)
  - [6.2 util.inspect：深度打印对象](#62-utilinspect深度打印对象)
  - [6.3 util.format：格式化字符串](#63-utilformat格式化字符串)
  - [6.4 util.types：精确类型判断](#64-utiltypes精确类型判断)
  - [6.5 util.deprecate 与 callbackify](#65-utildeprecate-与-callbackify)
- [七、crypto 模块速览](#七crypto-模块速览)
  - [7.1 哈希：createHash](#71-哈希createhash)
  - [7.2 HMAC：带密钥的签名](#72-hmac带密钥的签名)
  - [7.3 随机数：randomBytes / randomInt](#73-随机数randombytes--randomint)
  - [7.4 对称加解密：AES-256-GCM](#74-对称加解密aes-256-gcm)
  - [7.5 AI 场景联想](#75-ai-场景联想)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说清楚"为什么不能直接用 `+` 拼接路径"，并能在不同操作系统上预测 `path.sep`、`path.delimiter` 的取值。
2. 准确区分 `path.join` 与 `path.resolve`，知道前者只拼接、后者会返回**绝对路径**，并能解释空字符串参数在两者中的不同行为。
3. 熟练使用 `parse / format / dirname / basename / extname` 完成路径的拆解与重组。
4. 通过 `os.cpus().length`、`os.totalmem() / freemem()` 等接口动态决定并发数与是否加载大模型，避免在低配机器上把进程跑挂。
5. 用 WHATWG `new URL()` 正确解析带查询串与 hash 的 URL，并通过 `URLSearchParams` 增删改查参数。
6. 在 ESM 中用 `import.meta.url` + `fileURLToPath` 拿到当前文件的绝对路径，告别 `__dirname` 缺失的烦恼。
7. 用 `util.promisify` 把 `fs.readFile` 这类错误优先回调风格 API 转成 Promise，并理解其参数顺序约定。
8. 用 `util.inspect` 自定义深度打印嵌套对象，避免 `console.log` 截断大对象时只能看到 `[Object]`。
9. 用 `crypto.createHash('sha256')` 计算文件指纹、用 `crypto.createHmac` 做接口签名、用 `AES-256-GCM` 加解密 API key。
10. 识别 `querystring` 模块已废弃的事实，新代码统一使用 `URLSearchParams`。

---

## 二、path 模块详解

`path` 是 Node 内置的纯函数模块（无 I/O、无副作用），所有 API 都只针对**字符串**做处理，不检查文件是否真实存在。它的唯一职责就是：**让你跨平台地、安全地操作路径字符串**。

### 2.1 为什么不要用字符串拼接路径

前端同学最容易写出的"反模式"是：

```js
// ❌ 反模式：硬编码分隔符
const configPath = __dirname + '/config/' + 'default.json';
```

这段代码在 macOS / Linux 上能跑，但在 Windows 上会产出形如 `C:\project\config/default.json` 的"混合分隔符"路径。多数情况下 Windows API 能容错，但一旦遇到严格校验（如某些 shell 命令、容器挂载校验、权限比较），就会出问题。更深层的坑在 `__dirname` 为空字符串、`config` 以盘符开头等边界场景。

**正确写法**：始终用 `path.join`：

```js
const path = require('path');
const configPath = path.join(__dirname, 'config', 'default.json');
```

`path.join` 会自动用当前平台的 `path.sep`（POSIX 是 `/`，Windows 是 `\`）连接，并自动处理多余的 `/` 与 `..`。

| 平台 | `path.sep` | `path.delimiter`（PATH 分隔） | 路径示例 |
|------|-----------|------------------------------|----------|
| POSIX（macOS / Linux） | `/` | `:` | `/usr/local/bin/node` |
| Windows | `\`（也接受 `/`） | `;` | `C:\Program Files\nodejs` |

> ⚠️ Windows 实际上同时接受 `/` 与 `\`，但 `path.win32` 系列函数返回的字符串里只会用 `\`。这意味着同一台机器上 `path.join('a','b')` 在不同平台输出不同，跨平台项目应始终用 `path` API 而不是字符串字面量。

### 2.2 path.join vs path.resolve

两者都能"把多段拼成路径"，但语义差异巨大，是被问爆的面试题：

| API | 是否返回绝对路径 | 空字符串参数的行为 | 典型用途 |
|-----|-----------------|-------------------|----------|
| `path.join([...paths])` | **否**，只做拼接与规范化 | 被忽略，对结果无影响 | 拼接相对路径片段 |
| `path.resolve([...paths])` | **是**，从右往左找到第一个绝对路径为止，找不到则补 `process.cwd()` | 视为当前工作目录 `.` | 把相对路径解析成绝对路径 |

```js
const path = require('path');

// join：只拼接，不会强行变成绝对路径
path.join('/foo', 'bar', 'baz');      // '/foo/bar/baz'
path.join('foo', 'bar');              // 'foo/bar'
path.join('foo', '..', 'bar');       // 'foo/../bar' → 规范化后等价于 'bar' 所在目录的相对路径

// resolve：一定返回绝对路径
path.resolve('/foo/bar', './baz');   // '/foo/bar/baz'
path.resolve('foo', 'bar');          // '/<当前工作目录>/foo/bar' ← 注意这里前缀是 cwd
path.resolve();                      // 等价于 process.cwd()

// join 对空字符串"忽略"
path.join('foo', '', 'bar');          // 'foo/bar'
// resolve 对空字符串视为当前目录
path.resolve('foo', '', 'bar');      // '<cwd>/foo/bar'（中间插入了一层 cwd 的效果）
```

一个高频用例：**拿到"当前文件所在目录的某个相对文件"的绝对路径**——

```js
// CommonJS
const configPath = path.join(__dirname, 'config.json');

// ESM（无 __dirname，需借助 import.meta.url，详见 url 模块章节）
import { fileURLToPath } from 'node:url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const configPath = path.join(__dirname, 'config.json');
```

### 2.3 路径解析与重组：normalize / parse / format

**`path.normalize(p)`** 把路径里的 `.`、`..`、多余分隔符清干净：

```js
path.normalize('/foo/bar//baz/..//qux/');   // '/foo/bar/qux'（POSIX）
path.normalize('C:\\temp\\\\foo\\..\\bar');  // 'C:\temp\bar'（Windows）
```

它**只动字符串**，不会去文件系统检查 `..` 是否真的能往上一级。如果路径里包含符号链接的越界情况，`normalize` 的结果可能与你"以为的真实路径"不一致——这种情况要用 `fs.realpath`。

**`path.parse(p)`** 把一条路径拆成 5 个字段的字面量对象：

```js
path.parse('/home/user/docs/report.tar.gz');
// {
//   root: '/',
//   dir: '/home/user/docs',
//   base: 'report.tar.gz',
//   name: 'report',
//   ext: '.gz'          ← 注意：只取最后一个 .，不是 '.tar.gz'
// }
```

> ⚠️ `extname` 只取**最后一个**点号后的内容。`report.tar.gz` 的扩展名是 `.gz`，不是 `.tar.gz`。这对"按扩展名分发"的逻辑很关键——你不能用一个 `if (ext === '.tar.gz')` 来兜住所有双扩展名场景。

**`path.format(obj)`** 是 `parse` 的逆运算，用它把片段重新拼回路径：

```js
path.format({
  dir: '/home/user/docs',
  name: 'report',
  ext: '.pdf'
});
// '/home/user/docs/report.pdf'
```

`format` 的优先级规则：`base` 优先于 `name + ext`，`root` 优先于 `dir`。如果你同时给了 `base` 和 `ext`，`ext` 会被忽略。

### 2.4 取片段：dirname / basename / extname

| API | 作用 | 示例（输入 `/a/b/c.txt`） |
|-----|------|---------------------------|
| `path.dirname(p)` | 取目录部分（去掉最后一层文件名） | `/a/b` |
| `path.basename(p)` | 取文件名（带扩展） | `c.txt` |
| `path.basename(p, ext)` | 取文件名并去掉指定扩展 | `path.basename('/a/b/c.txt', '.txt')` → `c` |
| `path.extname(p)` | 取扩展名（含点号） | `.txt` |

```js
const file = '/data/models/chatglm-6b/model.bin';
path.dirname(file);     // '/data/models/chatglm-6b'
path.basename(file);    // 'model.bin'
path.basename(file, '.bin'); // 'model'
path.extname(file);     // '.bin'
path.extname('README'); // ''  ← 没扩展名返回空字符串，不是 undefined
```

### 2.5 平台差异：sep / delimiter / posix / win32

`path` 模块的默认行为由当前运行平台决定。但有时候你需要"在 Windows 上模拟 POSIX 路径"（比如构造给容器内 Linux 用的路径），此时使用 `path.posix` 或 `path.win32`：

```js
// 当前在 Windows 上运行
path.sep;              // '\\'
path.win32.sep;        // '\\'
path.posix.sep;        // '/'   ← 强制走 POSIX 规则

// delimiter 用于拆 PATH 环境变量
process.env.PATH.split(path.delimiter);
// Windows: ['C:\\...;D:\\...'] 按 ';' 拆
// Linux:   ['/usr/local/bin:/usr/bin'] 按 ':' 拆
```

**AI 场景**：当你的代码本地在 Windows 跑、镜像构建时却是 Linux，写 Docker volume 挂载路径要用 `path.posix.join('/app', 'data', 'x.json')`，否则会输出 `C:\...` 这种容器内不存在的路径。

### 2.6 判断与相对化：isAbsolute / relative

- **`path.isAbsolute(p)`**：判断是否以根开头。
  - POSIX：`/` 开头才算绝对路径。
  - Windows：`C:\`、`C:/`、`\\server\share` 都算。

```js
path.isAbsolute('/foo');    // true (POSIX) / true (Windows 也接受)
path.isAbsolute('foo');     // false
path.isAbsolute('C:\\foo'); // Windows: true / POSIX: false
```

- **`path.relative(from, to)`**：求从 `from` 到 `to` 的相对路径，相当于"`cd from && cd to` 走过的路径"。

```js
path.relative('/data/a/b', '/data/a/c/d');
// '../c/d'

path.relative('/data/a', '/data/a');
// ''  ← 同一目录返回空字符串，注意别误判为 falsy 出错
```

### 2.7 AI 场景联想

1. **拼接数据文件路径**：训练好的模型权重、向量库索引、embedding 缓存通常放在项目外的固定目录。用 `path.join(os.homedir(), '.myapp', 'models', 'chatglm.bin')` 可以在 Linux/Mac/Windows 三种环境一致地指向用户目录。
2. **构建 ESM 模块路径**：`import.meta.url` 是 ESM 中获取"当前文件 URL"的唯一标准方式，再配合 `fileURLToPath` 转 `path` 才能拿到本地文件系统路径，详见 `url-demo.js`。
3. **跨平台容器路径**：本地用 `path.posix` 生成挂载到容器的路径，避免 Windows 上的反斜杠泄漏到 Linux 容器。

---

## 三、os 模块详解

`os` 模块提供操作系统层面的只读信息：什么平台、几个 CPU 核、多少内存、网卡的 IP 是什么……它本身不消耗资源，几乎所有方法都是同步且廉价的，可以放心在启动时调用。

### 3.1 系统信息

| API | 返回 | 示例 |
|-----|------|------|
| `os.platform()` | 平台标识 | `'darwin'` / `'linux'` / `'win32'` |
| `os.arch()` | CPU 架构 | `'x64'` / `'arm64'` |
| `os.type()` | 操作系统名 | `'Darwin'` / `'Linux'` / `'Windows_NT'` |
| `os.release()` | 内核版本 | `'22.1.0'`（Darwin）/ `'10.0.22621'`（Win） |
| `os.hostname()` | 主机名 | `'worker-01'` |
| `os.homedir()` | 当前用户家目录 | `/Users/xxx` 或 `C:\Users\xxx` |
| `os.tmpdir()` | 系统临时目录 | `/var/folders/...` 或 `C:\Users\xxx\AppData\Local\Temp` |
| `os.endianness()` | 字节序 | `'BE'` 或 `'LE'`（x86/ARM 几乎都是 LE） |

> 💡 `os.platform()` 返回 `'win32'` 是历史遗留，并不代表 32 位——**64 位 Windows 也是 `'win32'`**。判断位数要用 `os.arch()`。

### 3.2 CPU 信息与负载

**`os.cpus()`** 返回一个数组，每个元素描述一个逻辑核心：

```js
const cpus = os.cpus();
// cpus.length === 逻辑核数（开启超线程后通常 == 物理核数 * 2）
// 每个元素：
// {
//   model: 'Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz',
//   speed: 2600,          // MHz
//   times: { user, nice, sys, idle, irq }   // 各类时间片累计（ms）
// }
```

**`os.loadavg()`** 返回 1/5/15 分钟的平均负载（仅在 POSIX 平台有意义；Windows 上返回 `[0, 0, 0]`）：

```js
os.loadavg(); // [1.23, 0.87, 0.65]  ← 数值代表"平均有几个进程在等 CPU"
```

经验值：loadavg 持续大于 `cpus.length * 0.7` 就要警惕 CPU 瓶颈了。

### 3.3 内存信息

| API | 含义 | 备注 |
|-----|------|------|
| `os.totalmem()` | 系统物理内存总量（字节） | 含被其他进程占用的部分 |
| `os.freemem()` | 当前可用内存（字节） | 实际可能更少（被 buffer/cache 占用） |
| `process.memoryUsage()` | **当前 Node 进程**占用 | 不在 os 模块，但常一起看 |

> ⚠️ `os.freemem()` 返回的是 OS 视角下的"空闲"，不是 Node 进程视角下的"可用堆"。Node 进程能用的堆大小由 `--max-old-space-size` 决定，与 `os.freemem` 没有直接关系。

### 3.4 网络接口

**`os.networkInterfaces()`** 返回所有网卡信息，是判断本机 IP 的标准方式：

```js
const nets = os.networkInterfaces();
// {
//   'en0': [
//     { address: '192.168.1.10', family: 'IPv4', mac: 'xx:xx', netmask: '255.255.255.0', cidr: '192.168.1.10/24' },
//     { address: 'fe80::1', family: 'IPv6', ... },
//   ],
//   'lo0': [ { address: '127.0.0.1', ... } ]
// }
```

取本机局域网 IP 的常见套路：遍历所有 IPv4 排除 `127.0.0.1` 和内网虚拟网卡。

### 3.5 EOL 换行符

**`os.EOL`** 是当前平台的"标准换行符"：

- POSIX：`'\n'`
- Windows：`'\r\n'`

写跨平台文件时强烈建议用 `os.EOL` 替代硬编码的 `'\n'`：

```js
fs.writeFileSync('log.txt', ['line1', 'line2'].join(os.EOL));
```

### 3.6 用户信息与常量

**`os.userInfo()`** 返回当前用户信息：

```js
os.userInfo();
// {
//   uid: 501,       // POSIX 才有，Windows 返回 -1
//   gid: 20,        // 同上
//   username: 'alice',
//   homedir: '/Users/alice',
//   shell: '/bin/zsh'
// }
```

**`os.constants`** 暴露两类常量：

- `os.constants.signals`：信号编号，如 `SIGHUP`、`SIGTERM`、`SIGKILL`。
- `os.constants.errno`：错误码常量，如 `EACCES`、`ENOENT`、`EADDRINUSE`。

```js
process.on('SIGTERM', () => {
  console.log(`收到 SIGTERM (${os.constants.signals.SIGTERM})，准备退出`);
  server.close();
});
```

### 3.7 AI 场景联想

1. **按 CPU 核数设置并发 worker**：

   ```js
   const cpuCount = os.cpus().length;
   const workerCount = Math.max(1, cpuCount - 1); // 留 1 核给主进程
   // 或者直接用 cluster / worker_threads 模块按 cpuCount 起 worker
   ```

   对 CPU 密集型任务（如图像预处理、向量计算），合理的并发数 ≈ 逻辑核数；对 I/O 密集型任务（如 API 转发），并发数与核数关系不大。

2. **判断内存是否够加载大模型**：

   ```js
   const MODEL_SIZE_GB = 6; // 6B 量化模型约 4-6GB
   const freeGB = os.freemem() / 1024 ** 3;
   if (freeGB < MODEL_SIZE_GB + 1) {
     throw new Error(`内存不足：剩余 ${freeGB.toFixed(1)}GB，至少需要 ${MODEL_SIZE_GB + 1}GB`);
   }
   ```

3. **容器内识别"是不是被限制了"**：容器里 `os.cpus()` 经常返回**宿主机**的全部核数，而不是 cgroup 限制后的核数。要拿到真实限制，得读 `/sys/fs/cgroup/cpu/cpu.cfs_quota_us` 等 cgroup 文件——这是常见的"在 2 核容器里起了 32 个 worker 把进程跑挂"事故的根源。

---

## 四、url 模块

`url` 模块经历过一次大改版。Node 早期只有 `url.parse`（legacy API，被 `url.format` / `url.resolve` 配套使用），后来 WHATWG URL 标准落地后，Node 实现了 `new URL()` 的同款 API，并明确建议新代码全部用 WHATWG 形式。

### 4.1 legacy url.parse 与 WHATWG URL

```js
const url = require('url');

// ❌ legacy 风格：宽松但有歧义
const legacy = url.parse('https://a.com:8080/p?q=1#h');
// 返回一个 Url 对象，prototype 上有 query 字段（字符串）

// ✅ WHATWG 风格：与浏览器一致
const modern = new URL('https://a.com:8080/p?q=1#h');
// 返回 URL 实例，有 searchParams（URLSearchParams 实例）
```

**legacy `url.parse` 的坑**：它对"特殊字符没编码的 URL"过于宽容，会把 `//` 开头当成协议相对 URL，且 query 是字符串而非对象，容易出现安全漏洞（如开放重定向）。**新代码绝对不要再用 `url.parse`，统一使用 `new URL()`**。

### 4.2 URL 对象的属性

`new URL()` 实例的所有属性都是**只读 getter**，但部分支持 setter（赋值会重新序列化）：

| 属性 | 含义 | 示例（输入 `https://user:pass@a.com:8080/p/q?x=1#top`） |
|------|------|--------------------------------------------------------|
| `origin` | 协议 + 域名 + 端口 | `https://a.com:8080` |
| `protocol` | 协议（带冒号） | `https:` |
| `username` / `password` | 用户名/密码 | `user` / `pass` |
| `host` | 域名 + 端口 | `a.com:8080` |
| `hostname` | 仅域名 | `a.com` |
| `port` | 仅端口（字符串） | `8080` |
| `pathname` | 路径 | `/p/q` |
| `search` | 查询串（带 `?`） | `?x=1` |
| `searchParams` | 查询参数对象 | `URLSearchParams { 'x' => '1' }` |
| `hash` | 锚点（带 `#`） | `#top` |
| `href` | 完整 URL | 整串 |

```js
const u = new URL('https://a.com:8080/p/q?x=1#top');
u.host;       // 'a.com:8080'
u.hostname;   // 'a.com'
u.port;       // '8080'  ← 注意是字符串
u.pathname;   // '/p/q'

// 修改会自动重新序列化
u.searchParams.set('x', '2');
u.search;     // '?x=2'
```

> ⚠️ `new URL('xxx')` 必须传**绝对 URL**，否则会抛 `TypeError [ERR_INVALID_URL]`。要解析"相对 URL"必须传第二个参数 `base`，见 4.5。

### 4.3 URLSearchParams

`URLSearchParams` 是专门操作查询串的工具，既能从 `new URL().searchParams` 拿到，也能独立创建：

```js
const sp = new URLSearchParams('a=1&b=2&a=3');
sp.get('a');      // '1'   ← 只取第一个
sp.getAll('a');  // ['1', '3']
sp.has('b');     // true
sp.set('a', '9'); // 覆盖所有同名 → '?a=9&b=2'
sp.append('a', '0'); // 追加 → '?a=9&b=2&a=0'
sp.delete('b');
sp.toString();   // 'a=9&a=0'  ← 会自动做 URL 编码
```

它**自带 URL 编解码**：`set('q', '中文 测试')` 会自动 `encodeURIComponent`，`get` 时自动 `decodeURIComponent`。再也不用手动 `encodeURIComponent` 拼字符串了。

### 4.4 fileURLToPath 与 pathToFileURL

ESM 中 `import.meta.url` 拿到的是一个 `file:` URL（如 `file:///home/user/app/main.mjs`），不能直接当文件路径用，必须转：

```js
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const __filename = fileURLToPath(import.meta.url);  // '/home/user/app/main.mjs'
const __dirname = path.dirname(__filename);        // '/home/user/app'

// 反向：把本地路径转成 file: URL（用于动态 import 一个绝对路径）
const moduleURL = pathToFileURL('/abs/path/to/worker.mjs');
const worker = await import(moduleURL.href);
```

> ⚠️ Windows 上 `import.meta.url` 长这样：`file:///C:/Users/xxx/app/main.mjs`（盘符前会多一个 `/`）。`fileURLToPath` 会正确处理为 `C:\Users\xxx\app\main.mjs`，**绝对不要手动做字符串替换**。

### 4.5 相对 URL 解析

`new URL(relative, base)` 能根据 base 解析相对 URL，规则与浏览器完全一致：

```js
new URL('/api/v1', 'https://a.com:8080/page');   // 'https://a.com:8080/api/v1'
new URL('sub', 'https://a.com/a/b/');            // 'https://a.com/a/b/sub'
new URL('../up', 'https://a.com/a/b/c');         // 'https://a.com/a/up'
new URL('?x=1', 'https://a.com/p');              // 'https://a.com/p?x=1'
new URL('#hash', 'https://a.com/p');            // 'https://a.com/p#hash'
```

这是拼接 API endpoint 的标准姿势，比 `${baseUrl}${path}` 安全得多——后者在 `baseUrl` 末尾多或少一个 `/` 时会失效。

---

## 五、querystring（已废弃）与 URLSearchParams

Node 早期内置 `querystring` 模块用于解析 `a=1&b=2` 形式：

```js
const qs = require('querystring');
qs.parse('a=1&b=2');  // { a: '1', b: '2' }
qs.stringify({ a: 1 }); // 'a=1'
qs.escape('中');         // '%E4%B8%AD'
```

**自 Node 18 起，`querystring` 被标记为 Deprecated**，原因：

1. 它对 URL 编码的处理与 WHATWG 标准不完全一致（特殊字符 `%`、`+` 的处理有差异）。
2. 已被 `URLSearchParams` 完全覆盖，功能等价。
3. 维护方建议新代码全面切换。

**等价写法对照**：

| 旧 querystring | 新 URLSearchParams |
|----------------|--------------------|
| `querystring.parse(s)` | `Object.fromEntries(new URLSearchParams(s))` |
| `querystring.stringify(obj)` | `new URLSearchParams(obj).toString()` |
| `querystring.escape(s)` | `encodeURIComponent(s)` |
| `querystring.unescape(s)` | `decodeURIComponent(s)` |

> 新代码请一律用 `URLSearchParams`。看到老代码里的 `querystring`，可以在重构时一并替换。

---

## 六、util 模块

`util` 是个"杂货箱"，里面装着 Node 自带的几个工具函数。最常用的有 `promisify`、`inspect`、`format`、`types`。

### 6.1 util.promisify：回调转 Promise

把"错误优先回调风格"的函数转成返回 Promise 的版本：

```js
const util = require('util');
const fs = require('fs');

const readFile = util.promisify(fs.readFile);
const stat = util.promisify(fs.stat);

// 现在可以 await
const content = await readFile('./config.json', 'utf8');
const info = await stat('./config.json');
```

**约定**：原函数必须是 `(...args, callback)` 形式，`callback` 签名为 `(err, value)`。`promisify` 后的函数会去掉最后的 callback 参数，返回 Promise，resolve 值是 callback 的第二个参数（及以后）。

⚠️ 注意以下情况 `promisify` **无法直接套用**：
- 回调不是错误优先风格（比如 `setTimeout` 的 `(arg)` 单参数回调）。
- 回调有多个成功参数（如 `child_process.exec` 的 `(err, stdout, stderr)`），`promisify` 默认只保留第一个成功参数，需要用 `util.promisify.custom` 自定义符号。

> 💡 **现代项目几乎不用 `promisify` 了**——`fs/promises`、`util.parseArgs` 等子模块已经原生提供 Promise 版本。但理解 `promisify` 的工作原理，仍是看懂老代码、写自定义 promisify 的基础。

### 6.2 util.inspect：深度打印对象

`console.log` 默认只展开 2 层嵌套，看到大对象经常是 `[Object: null prototype] {}` 或者 `... 3 more items`，调试时很恼火。`util.inspect` 可以精确控制：

```js
const util = require('util');

util.inspect(obj, {
  depth: null,        // 不限层级，全展开（默认 2）
  colors: true,       // 带颜色（终端有效）
  compact: false,     // 每个属性换行（更易读）
  maxArrayLength: null, // 数组不限长度（默认 100）
  maxStringLength: null, // 字符串不截断（默认 10000）
  sorted: true,       // 按 key 字母序排列
  breakLength: 80,    // 超过 80 字符就换行
});
```

如果你只想"按 console.log 的方式但更深入"，`console.dir(obj, { depth: null, colors: true })` 是 `inspect` 的便捷封装。

### 6.3 util.format：格式化字符串

类似 `printf` 的格式化函数，`%s` / `%d` / `%j` / `%o` / `%O` / `%%` 是占位符：

```js
util.format('Name: %s, Age: %d', 'Tom', 18);
// 'Name: Tom, Age: 18'

util.format('JSON: %j', { a: 1 });
// 'JSON: {"a":1}'

util.format('%o', { a: 1 });        // 用 inspect 风格打印对象
util.format('100%%');               // '100%'
```

> 当占位符多于参数时，多余的占位符原样输出；参数多于占位符时，多余的参数以空格连接追加。`console.log` 实际上就是 `process.stdout.write(util.format(...) + '\n')`。

### 6.4 util.types：精确类型判断

判断"是不是某种内置类型"时，`typeof` 和 `instanceof` 都有盲区（跨 realm 时 instanceof 会失效）。`util.types` 提供了一系列严谨的判断函数：

```js
const util = require('util');

util.types.isPromise(Promise.resolve()); // true
util.types.isPromise({ then: () => {} });  // false（不是原生 Promise）
util.types.isMap(new Map());               // true
util.types.isSet(new Set());               // true
util.types.isArrayBuffer(new ArrayBuffer(8)); // true
util.types.isAsyncFunction(async () => {});   // true
util.types.isProxy(new Proxy({}, {}));        // true
```

> ⚠️ `util.types.isPromise` 比 `obj instanceof Promise` 严格——它只认原生 Promise，认不出第三方 polyfill 或 thenable。这个严格性在跨 realm 场景（如 vm 沙箱、worker_threads）很有用。

### 6.5 util.deprecate 与 callbackify

- **`util.deprecate(fn, msg)`**：把函数标记为废弃。调用时会打印警告到 stderr，但仍正常执行。

  ```js
  const oldFn = util.deprecate(() => 'hello', 'oldFn 已废弃，请用 newFn');
  oldFn(); // 输出 'hello'，stderr 同时打印 DeprecationWarning
  ```

- **`util.callbackify(asyncFn)`**：`promisify` 的逆操作——把返回 Promise 的 async 函数转回错误优先回调风格。仅在"老接口要求回调、新实现是 async"的桥接场景才会用到。

---

## 七、crypto 模块速览

`crypto` 是 Node 内置的密码学模块，依赖 OpenSSL。它能完成：哈希、HMAC、对称加解密、非对称签名、随机数等。**它不依赖任何 npm 包**，可以直接 `require('crypto')`。

> ⚠️ `crypto` 的 API 比底层，新手上手会觉得繁琐。如果你只是要哈希字符串，社区有 `bcrypt`（密码哈希）、`jsonwebtoken`（JWT）等封装包；但理解原生 API 仍是排查问题、看懂源码的必备。

### 7.1 哈希：createHash

单向不可逆的指纹算法。常用：MD5（已不安全，仅兼容老系统）、SHA-1（也已弱化）、SHA-256 / SHA-512（推荐）。

```js
const crypto = require('crypto');

const hash = crypto.createHash('sha256');
hash.update('hello');
hash.update(' world');      // 可以分块 update，最终等价于一次性 update('hello world')
const digest = hash.digest('hex');   // 64 位 16 进制字符串
// 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
```

`digest` 的编码参数常用 `'hex'`、`'base64'`、`'binary'`。**`digest` 只能调用一次**，再调用会抛错——流已经结束。

典型用途：文件去重、内容寻址存储、API 签名中的nonce、密码哈希（推荐 bcrypt 而非直接 sha256）。

### 7.2 HMAC：带密钥的签名

HMAC = Hash + MAC，需要一把**密钥**。它能验证"消息来自持有密钥的人"——只要密钥不泄漏，攻击者就无法伪造合法签名。

```js
const hmac = crypto.createHmac('sha256', 'my-secret-key');
hmac.update('message to sign');
const signature = hmac.digest('hex');
```

用途：GitHub Webhook 签名校验（`X-Hub-Signature-256`）、阿里云/腾讯云 API 签名、Slack 请求验证。这类场景的"对端校验"逻辑就是同样算一次 HMAC，比对签名是否一致。

### 7.3 随机数：randomBytes / randomInt

`Math.random()` 是**伪随机**且**不安全**，绝不能用于生成 token、密码、API key。

```js
// 1. 生成 16 字节的随机数据（可用于 token、IV、盐）
const buf = crypto.randomBytes(16);     // 返回 Buffer
const token = buf.toString('hex');      // 32 字符的 hex 串

// 2. 生成随机整数（包含 min，不包含 max）
const dice = crypto.randomInt(1, 7);    // 1 到 6

// 3. 生成 UUID v4（Node 19+）
const uuid = crypto.randomUUID();      // '1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed'
```

`randomBytes` 底层调用 OpenSSL 的密码学安全 PRNG，适合所有安全场景。

### 7.4 对称加解密：AES-256-GCM

对称加密 = 加解密用同一把密钥。AES-256-GCM 是当下推荐的对称算法，**GCM 模式自带认证**——解密时会校验密文是否被篡改，比 CBC 模式更安全。

**完整流程**：每次加密需要生成一个**新的随机 IV**（初始向量），密文要连同 IV 与 authTag 一起保存，三者缺一不可解密。

```js
const crypto = require('crypto');

// 约定：32 字节密钥（AES-256）+ 12 字节 IV（GCM 推荐 12 字节）
const KEY = crypto.randomBytes(32);  // 实际项目应从环境变量/KMS 读取，不要每次随机

function encrypt(plainText) {
  const iv = crypto.randomBytes(12);                 // 每次 IV 必须随机
  const cipher = crypto.createCipheriv('aes-256-gcm', KEY, iv);
  const enc = Buffer.concat([
    cipher.update(plainText, 'utf8'),
    cipher.final(),
  ]);
  const authTag = cipher.getAuthTag();               // 16 字节认证标签
  return { iv, enc, authTag };                       // 三个都要传给解密方
}

function decrypt({ iv, enc, authTag }) {
  const decipher = crypto.createDecipheriv('aes-256-gcm', KEY, iv);
  decipher.setAuthTag(authTag);                       // 必须设置，否则会抛错
  const dec = Buffer.concat([
    decipher.update(enc),
    decipher.final(),                                // 这里会校验 authTag，不匹配会抛 AEAD_BAD_TAG
  ]);
  return dec.toString('utf8');
}

const cipher = encrypt('sk-my-openai-api-key-123');
const plain = decrypt(cipher);
console.log(plain);  // 'sk-my-openai-api-key-123'
```

> ⚠️ **CBC 模式已不推荐**：旧的 `createCipher` / `createDecipher`（不带 iv 后缀）在 Node 10 就被废弃，CBC 模式如果没有正确的 MAC 也容易遭 padding oracle 攻击。新代码一律用 GCM。

### 7.5 AI 场景联想

1. **API key 加密存储**：把 `OPENAI_API_KEY` 用 AES-256-GCM 加密后写进配置文件，运行时解密——避免直接明文写在 `.env` 里被误传到 git。
2. **接口签名**：自建模型服务对外提供 API，可用 HMAC-SHA256 + timestamp + nonce 做防重放签名。
3. **数据指纹**：用户上传文档后用 `sha256` 计算 hash，存进向量库作为去重 key。
4. **生成会话 ID**：用 `crypto.randomUUID()` 生成 conversation_id，比手写时间戳更安全。

---

## 八、关键知识点总结

1. **路径处理务必用 `path` 模块**：`path.join` 跨平台拼接，`path.resolve` 拿绝对路径，`path.sep` / `path.delimiter` 反映平台差异。
2. **`join` vs `resolve`**：`join` 只拼不绝对化，`resolve` 必返回绝对路径；空字符串在两者中行为不同。
3. **`extname` 只取最后一个 `.`**：`a.tar.gz` 的扩展名是 `.gz`。
4. **`os` 模块按需调用**：`os.cpus().length` 算并发、`os.freemem()` 估内存、`os.networkInterfaces()` 取 IP，注意容器中 `cpus` 可能返回宿主机核数。
5. **`os.EOL` 跨平台换行**：写文件时用它替换硬编码 `'\n'`。
6. **新代码全部用 `new URL()`**：legacy `url.parse` 弃用；解析相对 URL 用 `new URL(rel, base)`。
7. **`URLSearchParams` 替代 `querystring`**：自带 URL 编解码，新代码不要再 `require('querystring')`。
8. **ESM 拿 `__dirname`**：`path.dirname(fileURLToPath(import.meta.url))`，Windows 下也能正确处理盘符。
9. **`util.promisify` 是回调→Promise 的桥梁**：但现代项目优先用 `fs/promises` 等原生 Promise 版本。
10. **`util.inspect` 自定义深度打印**：`{ depth: null, colors: true }` 是调试大对象的标准姿势。
11. **`util.types` 跨 realm 判断类型**：比 `instanceof` 严格，原生 Promise/Map/Set 才认。
12. **`crypto.createHash('sha256')` + `digest('hex')` 是哈希套路**；`digest` 只能调一次。
13. **AES-256-GCM 三件套**：`iv` + `密文` + `authTag` 必须一起保存，IV 每次必须随机。
14. **`Math.random()` 不安全**：所有 token、密钥、nonce 用 `crypto.randomBytes` 或 `crypto.randomUUID`。

---

## 九、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：跨平台路径拼接器（对应 `path-demo.js`）

写一个工具函数 `buildConfigPath(appName, fileName)`：

1. 在用户家目录下创建一个隐藏目录 `.<appName>`（macOS/Linux）或 `%APPDATA%\<appName>`（Windows）。
2. 返回指向该目录下 `fileName` 的**绝对路径**。
3. 用 `path.join` 而不是字符串拼接。
4. 用 `os.homedir()` 拿家目录，用 `os.platform()` 判断平台。
5. **额外要求**：调用 `path.parse` 把返回的绝对路径拆开，打印 `root / dir / base / name / ext` 四个字段。

预期：函数在 macOS 返回 `/Users/<user>/.myapp/config.json`，在 Windows 返回 `C:\Users\<user>\AppData\Roaming\myapp\config.json` 之类的合理结果（具体目录可以自己定，但要保证跨平台一致）。

### 练习 2：自适应并发池（对应 `os-demo.js`）

实现一个 `concurrencyHint()` 函数：

1. 读取 `os.cpus().length`、`os.freemem()`、`os.totalmem()` 三项。
2. 计算推荐并发数：
   - 默认 = `cpuCount - 1`，最小为 1。
   - 如果 `freemem < 1GB`，把并发数砍半。
   - 如果 `loadavg()[0] > cpuCount * 0.8`（仅 POSIX 有意义），把并发数砍到 1。
3. 打印诊断信息：CPU 核数、内存、loadavg、最终推荐并发数。
4. 用 `os.networkInterfaces()` 找出本机第一个非环回 IPv4 地址，一并打印。

### 练习 3：URL 与加密综合（对应 `url-demo.js` 与 `crypto-demo.js`）

模拟一次"用环境变量里的密钥加密 API key 并生成带签名的请求 URL"：

1. 用 `new URL('https', 'api.example.com')` 拼出 endpoint，再用 `URLSearchParams` 加上 `model=gpt-4` 与 `ts=<当前时间戳>`。
2. 把整个 querystring 用 HMAC-SHA256 + 一个 secret 算出 `signature`，再 `append` 进 searchParams。
3. 把 secret 本身用 AES-256-GCM 加密，输出 `iv:enc:authTag` 的 hex 字符串。
4. 用 `util.inspect` 把最终 URL 对象、密文 hex、签名 hex 一起打印出来（`depth: null`）。
5. 写一个对应的 `decrypt` 函数，验证能从密文恢复出原 secret。

要求：所有路径处理用 `path`、所有 OS 信息用 `os`、URL 用 `new URL()`、加密用 `crypto`，**不要引入任何第三方 npm 包**。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/path-demo.js` | `join / resolve / parse / dirname / basename / extname / sep` 全套演示，含跨平台对比 |
| `Code/os-demo.js` | 输出平台 / CPU 核数 / 内存 / 网络接口 / 负载，演示按 CPU 核数计算并发 |
| `Code/url-demo.js` | WHATWG URL 解析、searchParams 操作、fileURLToPath 转 ESM 路径 |
| `Code/util-demo.js` | `promisify` 把 `fs.readFile` 转 Promise、`inspect` 深度打印、`types` 判断 |
| `Code/crypto-demo.js` | sha256 哈希、HMAC 签名、randomBytes、AES-256-GCM 完整加解密 |

运行方式（Node 18+）：

```bash
cd "Day08 - Path与OS等核心模块"
node Code/path-demo.js
node Code/os-demo.js
node Code/url-demo.js
node Code/util-demo.js
node Code/crypto-demo.js
```

---

> 📚 **延伸阅读**
> - Node.js 官方文档：[path](https://nodejs.org/api/path.html)
> - Node.js 官方文档：[os](https://nodejs.org/api/os.html)
> - Node.js 官方文档：[url](https://nodejs.org/api/url.html)
> - Node.js 官方文档：[util](https://nodejs.org/api/util.html)
> - Node.js 官方文档：[crypto](https://nodejs.org/api/crypto.html)
> - MDN：[WHATWG URL API](https://developer.mozilla.org/zh-CN/docs/Web/API/URL)
