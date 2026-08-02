# Day14 - TypeScript 与 Node.js

> 前十三天我们打磨了 TypeScript 的类型系统：从基础类型到泛型、从装饰器到模块系统。今天把这些知识「落地」到 Node.js 运行时——用 TS 写真正可运行的服务端代码。本篇聚焦三件事：让 TS 真正认识 Node 的内置模块（`fs` / `http` / `crypto` / `events`）、理清 TS 在 Node 上跑起来的三种姿势（`tsc` / `ts-node` / `tsx`）与 CJS / ESM 的取舍、以及如何把类型化思维应用到错误处理、异步流程、事件系统这些日常 Node 开发的核心场景。读完本篇，你应当能用 TS 起一个结构清晰、类型完备、可热重载、可上 CI 的 Node 服务骨架。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、@types/node：让 TS 认识 Node 内置模块](#二typesnode让-ts-认识-node-内置模块)
- [三、TS 写 Node 的三种运行方式](#三ts-写-node-的三种运行方式)
- [四、CommonJS 与 ESM 在 TS 中的处理](#四commonjs-与-esm-在-ts-中的处理)
- [五、ts-node 与 ESM 的坑：为什么推荐 tsx](#五ts-node-与-esm-的坑为什么推荐-tsx)
- [六、package.json 的 type 字段与 .mts/.cts](#六packagejson-的-type-字段与-mtscts)
- [七、用 TS 重写常见 Node 模块](#七用-ts-重写常见-node-模块)
  - [7.1 fs/promises 类型化](#71-fspromises-类型化)
  - [7.2 http 服务器类型化](#72-http-服务器类型化)
  - [7.3 crypto 类型化](#73-crypto-类型化)
- [八、错误处理类型化](#八错误处理类型化)
- [九、异步类型化](#九异步类型化)
- [十、项目结构建议](#十项目结构建议)
- [十一、开发工作流](#十一开发工作流)
- [十二、关键知识点总结](#十二关键知识点总结)
- [十三、实战练习](#十三实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 解释 `@types/node` 的作用，能正确安装并配置 `types: ["node"]`，理解 `process` / `Buffer` / `__dirname` 等全局变量的类型来源。
2. 说出 TS 写 Node 的三种运行方式（`tsc + node`、`ts-node`、`tsx`）的差异、优缺点与适用场景。
3. 区分 `module: commonjs` / `nodenext` / `preserve` 三种编译策略，理解 `import` 编译为 `require` 还是保留 `import` 的判定规则。
4. 在 ESM 模式下用 `import.meta.url` + `fileURLToPath` 替代 `__dirname` / `__filename`，用 `createRequire` 在 ESM 中桥接 `require`。
5. 用 TS 严格类型化 `fs/promises`、`http`、`crypto` 三大常用模块，包括 `Buffer` 类型标注、`IncomingMessage` / `ServerResponse` 扩展、`Hash` / `CipherGCM` 等类型。
6. 在 `useUnknownInCatchVariables` 下正确收窄 `catch (err: unknown)`，会写自定义 `AppError` 错误体系并配合 `instanceof` 收窄。
7. 标注 `Promise<T>`、推断 `async` 函数返回类型、利用 `Promise.all` 的元组类型保留顺序，并为 `EventEmitter` 写出类型化事件。
8. 设计一个分层清晰（routes/services/repositories/utils/types）的 TS Node 项目骨架，配置 `tsconfig` 与 `package.json` scripts。
9. 搭建 `tsx watch` 热重载、`tsc --noEmit` CI 类型检查、构建与运行分离的工程化工作流。

---

## 二、@types/node：让 TS 认识 Node 内置模块

Node.js 本身是用 C++ 写的运行时，它内置的 `fs` / `http` / `path` / `crypto` / `events` 等模块并不自带 TS 类型声明。TS 编译器看到一个裸的 `import * as fs from 'fs'` 时，并不知道 `fs.readFile` 接受什么参数、返回什么类型。

`@types/node` 是 DefinitelyTyped 社区维护的 Node 类型声明包，它为所有 Node 内置模块提供 `.d.ts` 类型定义。

### 安装方式

```bash
npm install --save-dev @types/node
```

注意：

- `@types/node` 是**开发依赖**（`devDependencies`），生产运行时不需要它——Node 本身已经实现了这些 API。
- 安装后，TS 会自动通过 `node_modules/@types/` 目录识别类型，**无需**手动 `/// <reference types="node" />`。
- 大版本要和你的 Node 版本对齐：Node 18 对应 `@types/node@^18`，Node 20 对应 `@types/node@^20`。

### types 字段的显式声明

当 `tsconfig` 的 `types` 字段未指定时，TS 会自动包含 `node_modules/@types/` 下所有包。在大型项目里推荐显式列出，避免无意中加载了多余的全局类型：

```json
{
  "compilerOptions": {
    "types": ["node"]
  }
}
```

这一行决定了三件事：

1. **`process` 全局可用且类型完备**：`process.env.NODE_ENV` 是 `string | undefined`，`process.argv` 是 `string[]`。
2. **`Buffer` 全局可用**：`Buffer.from('x')` 返回 `Buffer`，`buf.subarray(0, 4)` 有正确签名。
3. **`__dirname` / `__filename` / `require` / `module` 在 CJS 文件中可用**：它们的类型也由 `@types/node` 提供。

### 全局类型一览

| 全局对象 | 类型来源 | 仅在 CJS 可用 |
|---------|---------|---------------|
| `process` | `@types/node` → `NodeJS.Process` | 否（ESM 也可用） |
| `Buffer` | `@types/node` → `Buffer` | 否 |
| `console` | `@types/node` | 否 |
| `setTimeout` / `setInterval` | `@types/node`（覆盖 lib.dom） | 否 |
| `__dirname` / `__filename` | `@types/node`（CJS 模块包装器局部变量） | **是** |
| `require` / `module` / `exports` | `@types/node` | **是** |

这就是为什么在 ESM 模式下访问 `__dirname` 会同时报运行时 `ReferenceError` 与编译期 `Cannot find name '__dirname'`——TS 也认为它不在作用域内。

---

## 三、TS 写 Node 的三种运行方式

### 3.1 tsc 编译为 JS 再 node 运行

最传统的方式：用 `tsc` 把 `.ts` 编译成 `.js`，再用 `node` 运行。

```bash
tsc                  # 按 tsconfig 编译到 dist/
node dist/index.js   # 用 Node 运行编译产物
```

**优点**：产物是纯 JS，运行时零额外依赖，最适合生产部署。

**缺点**：每次改代码都要等编译，开发反馈慢；调试需要 source map。

适用场景：CI 构建、生产部署。

### 3.2 ts-node 直接运行

`ts-node` 在内存里把 TS 编译为 JS，然后交给 Node 执行，无需产物落盘。

```bash
ts-node src/index.ts
```

**优点**：零产物、可断点调试、生态成熟。

**缺点**：启动比纯 `node` 慢 1~2 秒；对 ESM 支持繁琐（需要 `--esm`、`tsconfig/esm` 或 `NODE_OPTIONS`）；性能不如 `tsx`。

适用场景：脚本执行、CJS 项目开发。

### 3.3 tsx 现代运行器

`tsx` 基于 `esbuild`，启动是毫秒级，对 ESM 原生友好。

```bash
tsx src/index.ts         # 直接运行
tsx watch src/index.ts   # 热重载
```

**优点**：

- 启动比 `ts-node` 快一个数量级（基于 esbuild 转译）；
- 自动判断 CJS / ESM，`import.meta.url` 直接可用；
- 内置 watch 模式，无需 `nodemon`。

**缺点**：

- 走 esbuild 转译，**不做类型检查**（只做语法转换），需要额外跑 `tsc --noEmit`；
- 不适合做 `ts-node --type-check` 这种「边跑边校验」的场景。

适用场景：日常开发、热重载、需要 ESM 的项目。

### 三者对比

| 维度 | `tsc + node` | `ts-node` | `tsx` |
|------|-------------|-----------|-------|
| 启动速度 | 慢（编译 + 启动） | 中（~1s） | 快（~50ms） |
| 类型检查 | 完整 | 可选（`--type-check`） | 不检查 |
| ESM 支持 | 取决于配置 | 繁琐 | 原生友好 |
| 产物 | `.js` 文件 | 无 | 无 |
| 生产部署 | ✅ 推荐 | ❌ | ❌（仅开发） |
| 调试 | source map | 直接断点 | 直接断点 |

**实践建议**：开发用 `tsx watch`，CI 用 `tsc --noEmit` 做类型检查，部署用 `tsc + node`。

---

## 四、CommonJS 与 ESM 在 TS 中的处理

### 4.1 三种 module 模式对比

`tsconfig.json` 的 `module` 字段决定 TS 把 `import` / `export` 编译成什么：

| `module` 值 | 编译产物 | 适用场景 |
|-------------|---------|---------|
| `commonjs` | `const x = require(...)` / `module.exports = ...` | Node CJS 项目，最稳 |
| `nodenext` / `node16` | 根据 `.mts` / `.cts` / `package.json type` 决定 | Node 项目，混合 CJS+ESM |
| `esnext` / `es2022` | 保留 `import` / `export` | 浏览器、打包器场景 |
| `preserve`（TS 5.4+） | 完全保留 `import`，不做任何转换 | 由下游打包器决定 |

### 4.2 import 编译示例

源码：

```ts
import { readFile } from 'node:fs/promises';
export const hello = 'world';
```

`module: commonjs` 编译为：

```js
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const promises_1 = require("node:fs/promises");
exports.hello = 'world';
```

`module: nodenext` + `type: module` 编译为（基本不变）：

```js
import { readFile } from 'node:fs/promises';
export const hello = 'world';
```

### 4.3 __dirname / __filename 在 ESM 中的替代

CJS 模式下，Node 的模块包装器会注入 `__dirname` / `__filename` / `require` / `module` / `exports` 这五个局部变量。ESM 模式下没有这个包装器，因此这些变量全部 `undefined`，访问会抛 `ReferenceError`。

ESM 中的等价写法：

```ts
// ESM 中获取 __dirname / __filename
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const __filename: string = fileURLToPath(import.meta.url);
const __dirname: string  = dirname(__filename);
```

ESM 中如果一定要用 `require`（比如加载一个老的 CJS 模块），用 `createRequire` 桥接：

```ts
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const oldLib = require('./legacy.cjs');
```

### 4.4 ESM 中 import 路径必须带扩展名

在 `module: nodenext` 下，相对路径 `import` 必须写**编译产物的扩展名**——也就是说，源文件是 `.ts`，但你要写 `import './foo.js'`：

```ts
// src/index.ts
import { greet } from './utils/greet.js';  // 注意是 .js 而非 .ts
```

这是 Node 原生 ESM 的硬性要求，TS 不会自动补全。这是从 CJS 迁移到 ESM 时最容易踩的坑。

### 4.5 moduleResolution 配对

`module` 与 `moduleResolution` 必须配对：

| `module` | 推荐 `moduleResolution` |
|----------|------------------------|
| `commonjs` | `node` |
| `nodenext` / `node16` | `nodenext` / `node16` |
| `esnext` / `es2022` | `bundler`（前端）或 `nodenext`（Node ESM） |
| `preserve` | `bundler` |

错误配对（例如 `module: commonjs` + `moduleResolution: bundler`）会让 TS 报怪异错误。

---

## 五、ts-node 与 ESM 的坑：为什么推荐 tsx

`ts-node` 在 ESM 项目中需要繁琐配置：

1. `package.json` 设 `"type": "module"`；
2. `tsconfig.json` 设 `module: nodenext`；
3. 安装 `ts-node` 后必须用 `ts-node-esm` 入口或 `node --loader ts-node/esm`；
4. `tsconfig` 里加 `"ts-node": { "esm": true, "experimentalSpecifierResolution": "node" }`；
5. `import` 路径必须写 `.js` 扩展名；
6. 部分场景下 `__dirname` polyfill 需要手动加。

而 `tsx` 是「零配置 ESM 运行器」：

- 自动按文件后缀 / `package.json type` 判断模块系统；
- `import.meta.url` 直接可用；
- `__dirname` 在 CJS 文件里直接可用；
- 启动快 5~10 倍。

**结论**：新项目（2024+）直接用 `tsx`，老项目继续用 `ts-node` 也行，但 ESM 优先 `tsx`。

---

## 六、package.json 的 type 字段与 .mts/.cts

`package.json` 的 `type` 字段决定项目里所有 `.js` / `.ts` 文件的默认模块系统：

- `"type": "commonjs"`（默认）：`.js` / `.ts` 视为 CJS
- `"type": "module"`：`.js` / `.ts` 视为 ESM

如果项目同时需要 CJS 与 ESM，可以用扩展名**强制覆盖**默认行为：

| 扩展名 | 强制模块系统 | 编译产物 |
|--------|------------|---------|
| `.cjs` | CJS | — |
| `.mjs` | ESM | — |
| `.cts` | CJS（TS 源） | `.cjs` |
| `.mts` | ESM（TS 源） | `.mjs` |

这是发布「双产物」库的标准做法：源码用 `.cts` / `.mts` 分别编写，`tsconfig` 用 `module: nodenext` + `moduleResolution: nodenext`，编译出 `.cjs` + `.mjs` 双份产物，再在 `package.json` 的 `exports` 字段里声明：

```json
{
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.cjs"
    }
  }
}
```

这样消费者无论是 `import` 还是 `require` 都能拿到正确产物。

---

## 七、用 TS 重写常见 Node 模块

### 7.1 fs/promises 类型化

`fs/promises` 的方法都做了**重载**：传 `encoding` 时返回 `string`，不传时返回 `Buffer`。TS 会根据实参自动收窄：

```ts
import { promises as fs } from 'node:fs';

// 传 encoding → 返回 string
const text: string = await fs.readFile('a.txt', 'utf8');

// 不传 encoding → 返回 Buffer
const buf: Buffer = await fs.readFile('a.txt');

// 写入：string 或 Buffer 都行
await fs.writeFile('b.txt', 'hello', 'utf8');
await fs.writeFile('c.bin', Buffer.from([0x00, 0xff]));
```

`Buffer` 是 `@types/node` 提供的全局类型，无需 `import`。常用操作：

```ts
// 构造
const b1: Buffer = Buffer.from('文字', 'utf8');
const b2: Buffer = Buffer.alloc(16);          // 16 字节，全 0
const b3: Buffer = Buffer.allocUnsafe(16);    // 不初始化，更快

// 转换
const hex: string  = b1.toString('hex');
const b64: string  = b1.toString('base64');
const bytes: number = b1.byteLength;

// 拼接
const merged: Buffer = Buffer.concat([b1, b2]);
```

`stat` 返回 `Stats` 类型：

```ts
const stats = await fs.stat('a.txt');
const meta: { size: number; isFile: boolean } = {
  size: stats.size,
  isFile: stats.isFile(),
};
```

完整示例见 [`Code/fs-typed.ts`](./Code/fs-typed.ts)。

### 7.2 http 服务器类型化

`http.createServer` 的回调签名是 `(req: IncomingMessage, res: ServerResponse) => void`。`IncomingMessage` 是可读流（`Readonly<ReadableStream>`），`ServerResponse` 是可写流。

```ts
import http, { IncomingMessage, ServerResponse } from 'node:http';

const server = http.createServer((req: IncomingMessage, res: ServerResponse) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Hello');
});
```

#### 扩展 Request 接口

中间件往往要在 `req` 上挂自定义字段。直接断言 `req as any` 会丢失类型安全，正确做法是声明一个继承 `IncomingMessage` 的接口：

```ts
interface AppRequest extends IncomingMessage {
  user?: { id: number; name: string };   // 鉴权中间件挂上去
  body?: unknown;                         // body-parser 中间件挂上去
  requestId: string;                      // 链路追踪 ID
}

const server = http.createServer((req, res) => {
  const appReq = req as AppRequest;
  appReq.requestId = crypto.randomUUID();
  // 后续中间件 / handler 里 req.user、req.body 都有类型
});
```

完整路由示例见 [`Code/http-server-typed.ts`](./Code/http-server-typed.ts)。

### 7.3 crypto 类型化

`node:crypto` 是 Node 内置加密模块，类型签名相对复杂。常用 API：

```ts
import {
  createHash,
  createHmac,
  randomBytes,
  createCipheriv,
  type Hash,
  type CipherGCM,
} from 'node:crypto';

// 哈希
const hash: string = createHash('sha256').update('hello').digest('hex');

// HMAC
const sig: string = createHmac('sha256', secret).update(payload).digest('hex');

// 随机字节
const iv: Buffer = randomBytes(12);

// AES-256-GCM 对称加密
const cipher: CipherGCM = createCipheriv('aes-256-gcm', key, iv);
const encrypted: Buffer = Buffer.concat([cipher.update(plain, 'utf8'), cipher.final()]);
const tag: Buffer = cipher.getAuthTag();
```

参数类型严格化的关键：

- 编码字面量联合 `'hex' | 'base64'` 防止误传任意字符串；
- `key` 长度做运行时校验（AES-256 必须 32 字节）；
- 用 `type` 关键字显式导入 `Hash` / `CipherGCM` 等类型，避免值/类型混淆。

完整示例见 [`Code/crypto-typed.ts`](./Code/crypto-typed.ts)。

---

## 八、错误处理类型化

### 8.1 useUnknownInCatchVariables

`strict: true` 隐含开启 `useUnknownInCatchVariables: true`——`try/catch` 里的 `err` 类型从 `any` 变成 `unknown`：

```ts
try {
  await risky();
} catch (err: unknown) {
  // err.message 编译报错：Object is of type 'unknown'
  // 必须先收窄
  if (err instanceof Error) {
    console.error(err.message);
  } else {
    console.error('未知错误:', err);
  }
}
```

这一改动让错误处理**真正类型安全**——你不能假设 `err` 一定是 `Error` 实例，可能是 `string`、`number`、`null`、或者第三方库 throw 的任何东西。

### 8.2 自定义错误类继承 Error

业务错误应当用结构化的错误类，而不是裸 `throw new Error('...')`：

```ts
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'AppError';
    // 修复 extends Error 后原型链丢失（target < ES2022 必须）
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

class ValidationError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, 'VALIDATION_ERROR', 400, details);
    this.name = 'ValidationError';
  }
}

class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}
```

注意 `Object.setPrototypeOf(this, new.target.prototype)` 这一行——`extends Error` 在 TS 编译为 ES5 时会因为 `Error` 构造器的特殊性导致原型链断开，`instanceof` 失效。在 `target: ES2022` 下不再需要，但写上更稳妥。

### 8.3 错误类型收窄

```ts
function normalizeError(err: unknown): AppError {
  if (err instanceof AppError) return err;          // 收窄为 AppError
  if (err instanceof Error) {                        // 收窄为 Error
    return new AppError(err.message, 'INTERNAL_ERROR', 500);
  }
  if (typeof err === 'string') {                     // 收窄为 string
    return new AppError(err, 'UNKNOWN', 500);
  }
  return new AppError('未知错误', 'UNKNOWN', 500);
}
```

把 unknown 错误统一转成 `AppError` 后，上层就可以用 `instanceof` 判断具体子类，决定返回 4xx 还是 5xx：

```ts
app.use((err, req, res, next) => {
  const e = normalizeError(err);
  res.status(e.statusCode).json({ code: e.code, message: e.message });
});
```

完整示例见 [`Code/error-handling.ts`](./Code/error-handling.ts)。

---

## 九、异步类型化

### 9.1 Promise<T> 显式标注

```ts
interface User { id: number; name: string; }

async function fetchUser(id: number): Promise<User> {
  return { id, name: `User-${id}` };
}
```

不写返回类型时，TS 自动推断 `Promise<User>`——但显式标注能避免「return 类型漂移」（例如手滑 return 了 `User | null`，自动推断会让调用方被迫处理 null）。

### 9.2 Promise.all 的元组类型

`Promise.all` 接收元组，返回元组类型——**顺序严格保留**：

```ts
const [user, count, ts] = await Promise.all([
  fetchUser(1),           // Promise<User>
  Promise.resolve(42),    // Promise<number>
  Promise.resolve(new Date()),
]);
// user: User
// count: number
// ts: Date
```

如果传入数组而非元组，类型会退化：

```ts
const arr = [fetchUser(1), Promise.resolve(42)];
const result = await Promise.all(arr);
// result: (User | number)[]   ← 顺序信息丢失
```

补救：用 `as const` 或者显式标注元组：

```ts
const tuple = [fetchUser(1), Promise.resolve(42)] as const;
// 或
const tuple: [Promise<User>, Promise<number>] = [fetchUser(1), Promise.resolve(42)];
```

### 9.3 Promise.allSettled 部分失败

```ts
const results = await Promise.allSettled([fetchUser(1), fetchUser(-1)]);
// results: PromiseSettledResult<User>[]
results.map((r) => {
  if (r.status === 'fulfilled') {
    r.value;  // User
  } else {
    r.reason; // unknown ← 注意，这里是 unknown
  }
});
```

### 9.4 EventEmitter 的类型化事件

原生 `EventEmitter` 是无类型的：`emit('foo', 1)` 和 `on('bar', 'x')` 互不约束。用泛型包装一层可以做到事件名 + payload 双向约束：

```ts
interface TaskEvents {
  start: { taskId: number; at: Date };
  done: { taskId: number; result: string };
  error: { taskId: number; err: Error };
}

class TypedEmitter<E extends Record<string, any>> extends EventEmitter {
  emit<K extends keyof E & string>(event: K, payload: E[K]): boolean {
    return super.emit(event, payload);
  }
  on<K extends keyof E & string>(event: K, listener: (payload: E[K]) => void): this {
    return super.on(event, listener);
  }
}

const runner = new TypedEmitter<TaskEvents>();
runner.on('start', (p) => p.taskId);   // p 类型自动收窄为 { taskId, at }
runner.emit('done', { taskId: 1, result: 'ok' });
// runner.emit('done', { foo: 1 });    // 编译报错
// runner.on('unknown', ...);          // 编译报错
```

完整示例见 [`Code/async-typed.ts`](./Code/async-typed.ts)。

---

## 十、项目结构建议

```
my-app/
├── src/
│   ├── index.ts              # 入口
│   ├── config/               # 环境变量、配置
│   ├── routes/               # 路由层
│   ├── services/             # 业务层
│   ├── repositories/         # 数据访问层
│   ├── middlewares/          # 中间件
│   ├── utils/                # 工具函数
│   └── types/                # 共享类型声明
├── tests/
├── dist/                     # 编译产物（gitignore）
├── tsconfig.json             # 开发用（noEmit）
├── tsconfig.build.json       # 构建用（emit）
└── package.json
```

**分层依赖方向**：`routes → services → repositories → utils`，反向引用视为坏味道。

详细说明见 [`Code/project-structure.md`](./Code/project-structure.md)。

---

## 十一、开发工作流

### 11.1 tsx watch 热重载

```bash
tsx watch src/index.ts
```

文件改动即重启，毫秒级反馈。比 `tsc -w + nodemon dist/` 快一个数量级。

### 11.2 tsc --noEmit 类型检查

```bash
tsc --noEmit
```

不产出 JS，只做类型检查。建议：

- IDE 实时跑（VSCode 内置）；
- git pre-commit hook 跑；
- CI pipeline 跑。

### 11.3 CI 中的类型检查流水线

```json
{
  "scripts": {
    "lint":      "eslint src --ext .ts",
    "type-check":"tsc --noEmit",
    "test":      "vitest run",
    "build":     "rimraf dist && tsc -p tsconfig.build.json",
    "ci":        "npm run lint && npm run type-check && npm run test && npm run build"
  }
}
```

CI 串行执行 lint → type-check → test → build，任一环节失败即终止。

### 11.4 构建与运行分离

```
开发：  tsx watch src/index.ts          （源码热重载，无产物）
构建：  tsc -p tsconfig.build.json      （生成 dist/）
运行：  node dist/index.js              （生产环境，无需 TS 工具链）
```

生产镜像里只需 `npm ci --omit=dev && npm run build && npm start`，无需安装 `typescript` / `tsx`，镜像体积更小、启动更快。

---

## 十二、关键知识点总结

1. **`@types/node` 是开发依赖**：为 Node 内置模块提供类型，生产运行时不需要。
2. **`types: ["node"]` 显式声明**：避免无意中加载多余全局类型，让 `process` / `Buffer` / `__dirname` 类型可用。
3. **三种运行方式分工**：开发用 `tsx watch`，CI 用 `tsc --noEmit`，部署用 `tsc + node`。
4. **`module` 决定编译产物**：`commonjs` 编译为 `require`，`nodenext` 按 `type` 字段判定，`preserve` 完全保留。
5. **ESM 中 `__dirname` 不可用**：改用 `fileURLToPath(import.meta.url)` + `dirname()`；`require` 改用 `createRequire(import.meta.url)`。
6. **ESM import 必须带扩展名**：源文件是 `.ts`，import 路径写 `.js`。
7. **`useUnknownInCatchVariables` 默认开**：`catch (err: unknown)` 必须先收窄再访问。
8. **自定义错误继承 `Error`**：写 `Object.setPrototypeOf(this, new.target.prototype)` 保证 `instanceof` 工作。
9. **`Promise.all` 元组类型保留顺序**：传元组返回元组，传数组退化为联合类型数组。
10. **EventEmitter 类型化**：用泛型包装，把事件名 + payload 双向约束。
11. **`Buffer` 是全局类型**：无需 `import`，由 `@types/node` 提供。
12. **`fs/promises` 方法重载**：传 `encoding` 返回 `string`，不传返回 `Buffer`，TS 自动收窄。
13. **`.mts` / `.cts`**：强制覆盖 `package.json type` 的默认模块系统，用于双产物库。
14. **构建与运行分离**：生产环境不安装 TS 工具链，只跑 `node dist/`。

---

## 十三、实战练习

### 练习 1：类型化文件索引器

用 `fs/promises` + TS 实现一个 `indexDir(dir: string): Promise<FileIndex>` 函数：

- 递归遍历 `dir` 下所有文件（不含目录）；
- 返回 `FileIndex`：

  ```ts
  interface FileIndex {
    total: number;
    byExt: Record<string, string[]>;   // 扩展名 → 文件路径数组
    largest: { path: string; size: number } | null;
  }
  ```

- 用 `Promise.all` 并发 `stat` 所有文件；
- 错误处理：遇到无权限目录用 `Promise.allSettled` 跳过；
- 顶层 `main()` 用 `try/catch` 包裹并打印 `AppError` 的 `code` + `message`。

### 练习 2：类型化 HTTP 路由

在 [`Code/http-server-typed.ts`](./Code/http-server-typed.ts) 基础上扩展：

- 新增 `GET /sum?a=1&b=2` 路由，返回 `{ result: number }`；
- 参数校验：非数字返回 `400 ValidationError`；
- 扩展 `AppRequest` 接口，添加 `parsedQuery: URLSearchParams`；
- 用自定义 `AppError` 体系统一错误响应，`res` 始终返回 `{ code, message, details? }` 结构。

### 练习 3：类型化任务队列

实现一个 `TaskQueue`：

- 继承 `TypedEmitter<TaskQueueEvents>`，事件包括 `task:start` / `task:done` / `task:failed` / `drained`；
- `add(task: () => Promise<T>): Promise<T>` 方法支持并发限制（`maxConcurrency: number`）；
- 用 `Promise.all` 在 `waitForAll()` 中等待所有未完成任务；
- 错误处理：单个任务失败触发 `task:failed` 但不影响其他任务，`add` 的 Promise 必须 reject；
- 写一个 demo 跑 5 个任务，并发度 2，打印每个事件。

---

> 学习提示：本篇代码全部可在 Node 18+ 与 TS 5+ 环境运行。先 `npm install` 安装依赖，再 `npm run fs` / `npm run http` / `npm run crypto` / `npm run error` / `npm run async` / `npm run esm` 跑对应示例。建议边读边改，把每个示例拆开看 TS 的报错信息——这是建立类型直觉最快的方式。
