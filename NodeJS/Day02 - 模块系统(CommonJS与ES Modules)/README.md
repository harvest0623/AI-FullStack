# Day02 - 模块系统（CommonJS 与 ES Modules）

> 面向从前端转向 AI 全栈开发的工程师
> 运行环境：Node.js 18+

## 一、学习目标

完成本节后，你将能够：

- 理解为什么 JavaScript 需要模块化，以及它在 Node.js 服务端场景下的特殊性。
- 讲清 CommonJS 规范的原理，包括 `require` 的解析步骤、模块缓存、模块包装函数。
- 区分 `exports` 与 `module.exports`，并避开常见陷阱。
- 掌握 ES Modules（ESM）的静态 `import/export`、动态 `import()` 与 `import.meta`。
- 在同一项目中正确配置 `"type": "module"`、`.mjs/.cjs` 扩展名，处理两套模块系统的互操作。
- 识别并缓解循环依赖问题。

## 二、理论知识讲解

### 2.1 为什么需要模块化

前端工程师熟悉的「原生 JS 写在一个 `<script>` 里」的写法，在服务端是行不通的：

1. **作用域污染**：Node.js 文件被多个模块复用，若全部共享全局作用域，变量会冲突。
2. **依赖管理**：服务端依赖动辄上百个，需要明确「谁依赖谁、按什么顺序加载」。
3. **可复用性**：把功能拆成独立单元，便于测试、复用与维护。
4. **加载性能**：服务端可以从磁盘缓存读取模块，模块化让缓存成为可能。

JavaScript 早期没有原生模块系统，社区涌现了多种方案：AMD（RequireJS）、CMD（SeaJS）、UMD、**CommonJS**（Node.js 的事实标准）。直到 ES2020 才正式落地原生 **ES Modules**。

### 2.2 CommonJS 规范原理

CommonJS（CJS）由 Kevin Dangoor 在 2009 年发起，最初是为服务端 JS 设计的模块规范，其核心约定：

- 每个文件就是一个模块，拥有独立作用域。
- 通过 `require` 导入模块，通过 `module.exports` 导出成员。
- 模块**同步**加载（因为服务端文件就在本地磁盘，同步 IO 没问题）。
- 模块在**首次**被 require 时执行一次，之后从缓存返回。

### 2.3 Node.js 模块加载机制（require 的解析步骤）

当我们写下 `require('./math')`，Node.js 内部会经历以下几步：

#### 步骤 1：解析模块标识符

`require(X)` 会根据 `X` 的形式分流：

| 标识符形式 | 示例 | 处理方式 |
| --- | --- | --- |
| 核心模块 | `require('fs')` | 直接返回 Node 内置模块，不走文件解析 |
| 以 `./` `../` `/` 开头 | `require('./math')` | 按相对/绝对路径解析为文件模块 |
| 裸模块（bare） | `require('lodash')` | 从当前目录向上逐层查找 `node_modules` |

#### 步骤 2：文件模块的路径解析

当 `X` 是 `./math` 这种相对路径时，Node 会依次尝试：

1. `X` 本身（如果是完整文件名）
2. `X.js`
3. `X.json`
4. `X.node`（C++ 扩展）
5. `X/index.js`、`X/index.json`、`X/index.node`（目录模块）

#### 步骤 3：目录模块

如果 `X` 指向一个目录，Node 会读取该目录下的 `package.json` 的 `main` 字段定位入口；若没有 `package.json` 或 `main` 缺失，则回退到 `index.js`。

#### 步骤 4：node_modules 向上查找

对于裸模块 `require('lodash')`，Node 会从当前文件所在目录开始，依次向上层目录的 `node_modules` 查找，直到文件系统根：

```
/d/app/Code/node_modules/lodash
/d/app/node_modules/lodash
/d/node_modules/lodash
/node_modules/lodash
```

这就是为什么把依赖装在项目根 `node_modules` 后，任意子目录都能 require 到。

#### 步骤 5：缓存机制 Module._cache

模块**首次**加载后，会被以「绝对路径」为 key 缓存到 `Module._cache` 中。再次 `require` 同一模块时，直接返回缓存中的 `module.exports`，**不会重新执行**模块代码。

```js
// 查看缓存
console.log(require.cache);
// 删除某个模块的缓存（热更新场景）
delete require.cache[require.resolve('./math')];
```

> ⚠️ 这也意味着：修改了模块导出的对象后，所有引用方拿到的都是**同一个引用**，修改会互相影响。

### 2.4 模块包装函数

Node.js 并没有真的「原生化」模块作用域，而是用了一个巧妙的技巧：**每个模块文件都被包进一个函数**。你写的代码实际上是这样运行的：

```js
(function (exports, require, module, __filename, __dirname) {
  // 你的模块代码原封不动放在这里
  const fs = require('fs');
  module.exports = { /* ... */ };
});
```

这就是为什么你在每个文件里都能直接用 `require`、`module`、`__dirname`、`__filename`——它们其实是这个包装函数的参数。这也意味着这些变量**不是全局变量**，而是每个模块私有的。

### 2.5 exports 与 module.exports 的区别与陷阱

这是 CommonJS 最经典的坑。先记住一句话：**`module.exports` 才是真正的导出对象，`exports` 只是指向它的一个引用。**

```js
// 模块加载时实际做了：
// module.exports = {};
// exports = module.exports;
```

正确用法：

```js
// ✅ 给 module.exports 添加属性
exports.add = (a, b) => a + b;
// 等价于 module.exports.add = ...

// ✅ 整体替换 module.exports
module.exports = { add: (a, b) => a + b };
```

常见陷阱：

```js
// ❌ 陷阱 1：整体赋值给 exports
exports = { add: (a, b) => a + b };
// exports 不再指向 module.exports，导出的是空对象 {}
```

```js
// ❌ 陷阱 2：先整体赋值，再用 exports 添加
module.exports = { add: ... };
exports.sub = ...; // exports 仍指向旧的 {}，sub 不会被导出
```

经验法则：**要么始终用 `module.exports.xxx =`，要么整体 `module.exports = {}`，不要混用 `exports` 与整体赋值。**

### 2.6 ES Modules（ESM）规范

ESM 是 ECMAScript 官方的模块标准，从 ES2020 起被 Node.js 正式支持（`--experimental-modules` 在 12.x 已经可用，14+ 默认稳定）。

核心特征：

- **静态结构**：`import`/`export` 必须在顶层，不能放在 `if` 里，路径必须是字符串字面量。
- **导出的是绑定（live binding）**：导入方拿到的不是值的拷贝，而是对导出变量的引用，导出方修改后导入方能看到。
- **异步加载**：ESM 设计上支持异步加载，便于浏览器与服务端的统一。
- **严格模式**：ESM 默认启用严格模式，没有 `this = window/global`，顶层 `this` 是 `undefined`。

### 2.7 import/export 的静态特性

```js
// ✅ 合法：静态导入，编译期确定依赖
import { add } from './math.js';

// ❌ 非法：不能在条件分支里
if (cond) {
  import { add } from './math.js'; // SyntaxError
}

// ❌ 非法：路径不能是变量
const path = './math.js';
import { add } from path; // SyntaxError
```

静态特性的好处：**摇树优化（tree-shaking）**——打包工具能分析出哪些导出没被使用，直接删除。CommonJS 因为是动态 `require`，无法做到这一点。

### 2.8 动态 import()

当确实需要按条件、按变量加载模块时，使用动态 `import()`：

```js
const moduleName = './math.js';
const math = await import(moduleName); // 返回 Promise<Module>
console.log(math.add(1, 2));
```

`import()` 是**异步**的，返回一个 Promise，解析为模块命名空间对象。它同时支持 ESM 和 CommonJS 模块：

- 加载 ESM 模块：返回命名空间对象，包含所有命名导出与 `default`。
- 加载 CommonJS 模块：命名空间对象的 `default` 即 `module.exports`，命名导出通过静态分析尽力提供。

### 2.9 CommonJS 与 ESM 互操作

两套系统并存就会遇到互操作问题：

#### require(ESM) 的限制

在 CommonJS 中**不能**直接 `require` 一个 ESM 模块，会报错：

```
Error [ERR_REQUIRE_ESM]: require() of ES Module ... not supported.
```

因为 ESM 是异步加载的，而 `require` 是同步的。解决方案：

1. 改用动态 `import()`（返回 Promise）。
2. 使用 `module.createRequire` 在 ESM 中使用 require（仅用于加载 CJS）。
3. Node.js 22+ 提供了实验性的同步 `require(esm)`，需 `--experimental-require-module` 标志。

#### 命名导出互导

- ESM 导入 CJS：CJS 的 `module.exports` 整体作为 `default` 命名空间，命名导出通过静态分析尽力提取（依赖 CJS 模块的可静态分析性）。
- CJS 导入 ESM：必须用 `await import()`，无法同步获得。

```js
// ESM 导入 CJS（推荐用 default）
import pkg from './cjs-module.cjs';   // pkg === module.exports
import { named } from './cjs-module.cjs'; // 可行但依赖静态分析

// CJS 导入 ESM
const esm = await import('./esm-module.mjs');
console.log(esm.default, esm.named);
```

### 2.10 package.json 的 "type" 字段

`package.json` 的 `"type"` 字段决定项目默认的模块系统：

```json
{
  "name": "my-app",
  "type": "module"
}
```

| `type` 值 | `.js` 文件被当作 | 默认推荐 |
| --- | --- | --- |
| `"module"` | ESM | 现代项目、库 |
| `"commonjs"`（默认） | CommonJS | 传统 Node 项目 |
| 未设置 | CommonJS | — |

### 2.11 .mjs / .cjs 扩展名

扩展名可以**覆盖** `type` 字段的默认行为，用于在混合项目中精确控制每个文件：

- `.mjs`：无论 `package.json` 怎么设置，都是 ESM。
- `.cjs`：无论 `package.json` 怎么设置，都是 CommonJS。
- `.js`：跟随 `package.json` 的 `type` 字段。

经验法则：**混合项目优先用显式扩展名**，避免依赖 `type` 字段带来认知负担。

### 2.12 循环依赖问题

当 A 依赖 B，B 又依赖 A 时，就形成循环依赖。

#### CommonJS 中的循环依赖

由于 CJS 同步加载 + 缓存机制，循环发生时，被循环引用的模块会返回**已经执行到那一行**的部分导出：

```js
// a.js
const b = require('./b');
console.log('a: b =', b);
module.exports = { a: 1 };

// b.js
const a = require('./a'); // 此时 a.js 还没执行完，拿到的是空 {}
console.log('b: a =', a);
module.exports = { b: 2 };

// 执行 node a.js：
// b: a = {}
// a: b = { b: 2 }
```

#### ESM 中的循环依赖

ESM 由于是 live binding，循环依赖时拿到的是**变量绑定**，等模块执行完后能拿到最终值。但如果在模块顶层立即使用对方导出，仍可能拿到 `undefined`。

#### 缓解策略

1. **重构**：把循环依赖的部分抽到第三个模块 C，让 A、B 都依赖 C。
2. **延迟访问**：把对对方导出的访问延迟到函数内部（运行时才取值），而不是模块加载时。
3. **优先 ESM**：ESM 的 live binding 对循环依赖更友好。

## 三、核心概念解析

### 3.1 模块作用域

每个模块文件有自己的顶层作用域，模块内 `var`/`let`/`const` 声明的变量不会污染全局。这是通过**模块包装函数**（CJS）或**模块记录**（ESM）实现的。

### 3.2 module 对象属性

在 CommonJS 模块内，`module` 是一个对象，常见属性：

| 属性 | 含义 |
| --- | --- |
| `module.id` | 模块的唯一标识，通常是绝对路径（入口模块为 `.`） |
| `module.filename` | 模块的绝对文件路径 |
| `module.loaded` | 模块是否已加载完毕（布尔） |
| `module.parent` | 首次 require 它的模块（已废弃，Node 14+ 用 `module.children` 与调用栈判断） |
| `module.children` | 该模块 require 的子模块数组 |
| `module.paths` | 查找 `node_modules` 的路径列表 |
| `module.exports` | 模块对外导出的对象 |

### 3.3 模块包装函数参数

```
(exports, require, module, __filename, __dirname)
```

- `exports`：`module.exports` 的别名，用于挂载导出成员。
- `require`：用于导入其他模块的函数。
- `module`：当前模块对象。
- `__filename`：当前模块文件的绝对路径。
- `__dirname`：当前模块所在目录的绝对路径。

> 在 ESM 中 `__dirname` 和 `__filename` 不存在，需要通过 `import.meta.url` 自行派生。

### 3.4 ESM 中的 import.meta

`import.meta` 是 ESM 的元信息对象，最重要的属性是 `import.meta.url`——当前模块文件的 URL（如 `file:///d:/.../foo.mjs`）。

在 ESM 中模拟 `__dirname` 和 `__filename`：

```js
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
```

`import.meta.url` 在 AI 全栈项目中很常用，比如用它定位训练数据、模型文件、配置文件的绝对路径，避免依赖 `process.cwd()`。

## 四、两种模块系统对比

| 维度 | CommonJS（CJS） | ES Modules（ESM） |
| --- | --- | --- |
| 导入语法 | `const x = require('m')` | `import x from 'm'` |
| 导出语法 | `module.exports = ...` / `exports.x = ...` | `export ...` / `export default ...` |
| 加载时机 | 运行时同步加载 | 编译期静态分析 + 运行时异步求值 |
| 是否支持顶层 `await` | ❌ 不支持（须在 async 函数内） | ✅ 支持（顶层 await） |
| 导出特性 | 值的拷贝（基本类型）/ 引用（对象） | live binding（实时绑定） |
| 严格模式 | 默认非严格 | 默认严格 |
| Tree-shaking | ❌ 困难 | ✅ 支持 |
| `require(ESM)` | ❌ 默认不支持 | — |
| `import(CJS)` | — | ✅ 支持（default 即 module.exports） |
| `this` 顶层值 | `module.exports` | `undefined` |
| `__dirname`/`__filename` | ✅ 内置 | ❌ 需通过 `import.meta.url` 派生 |
| 适用场景 | 传统 Node 服务、老项目 | 新项目、库、与前端共享代码、AI/TS 工程 |

## 五、关键知识点总结

1. **模块化的本质**：作用域隔离 + 依赖管理 + 可缓存加载。
2. **require 解析顺序**：核心模块 → 文件路径（含扩展名补全）→ 目录（`package.json` 的 `main`/`index.js`）→ `node_modules` 向上查找。
3. **缓存**：`Module._cache` 以绝对路径为 key，模块只执行一次；热更新需手动 `delete require.cache`。
4. **包装函数**：每个 CJS 文件被包进 `(function(exports, require, module, __filename, __dirname){...})`，这就是 `require`/`module`/`__dirname` 的来源。
5. **`exports` vs `module.exports`**：永远以 `module.exports` 为准；不要整体赋值给 `exports`。
6. **ESM 静态性**：`import` 必须顶层、路径必须是字面量 → 支持静态分析与 tree-shaking；动态需求用 `import()`。
7. **互操作**：CJS 不能同步 `require(ESM)`；ESM 可 `import` CJS（`default` 即 `module.exports`）。
8. **`type: "module"` + 扩展名**：用 `.mjs`/`.cjs` 显式覆盖默认行为，混合项目更安全。
9. **循环依赖**：CJS 返回部分导出，ESM 返回 live binding；最佳解法是抽公共模块或延迟访问。
10. **`import.meta.url`**：ESM 中获取模块绝对路径的标准方式，AI 工程中常用于定位数据/模型/配置文件。

## 六、实战练习

### 练习 1：CommonJS 工具库与调用

在 `Code/` 下创建 `math-commonjs.js`，导出 `add`、`subtract`、`multiply`；再创建 `app-commonjs.js`，`require` 引入并打印 `1+2`、`5-3`、`4*6` 的结果，同时打印 `__dirname` 与 `__filename`。

运行：`node app-commonjs.js`

**验收标准**：能解释为什么多次 `require('./math-commonjs')` 只执行一次模块代码。

### 练习 2：ESM 命名导出与默认导出

创建 `circle-area.mjs`，分别用**命名导出**导出 `area`（计算圆面积）、`circumference`（周长），用**默认导出**导出一个包含 `{ area, circumference }` 的对象。再创建 `use-esm.mjs`，分别演示三种导入方式：命名导入、默认导入、命名空间导入（`* as`），并打印 `import.meta.url`。

运行：`node use-esm.mjs`

**验收标准**：能说清默认导出与命名导出在导入语法上的差异。

### 练习 3：动态 import 与互操作

创建 `dynamic-import.js`（CJS），在 `async` 函数内用 `await import('./circle-area.mjs')` 加载 ESM 模块，调用其命名导出与默认导出。观察并记录：CJS 中能否拿到 ESM 的命名导出？`default` 是什么？

运行：`node dynamic-import.js`

**验收标准**：能解释「为什么 CJS 不能同步 `require(ESM)`，但可以用 `await import()`」。

### 进阶挑战（可选）

1. 故意构造一个 CommonJS 循环依赖（A↔B），运行并解释输出顺序与部分导出现象。
2. 在 `Code/` 下放一个 `package.json`（`"type": "module"`），观察 `.js` 文件行为变化；再创建一个 `.cjs` 文件验证扩展名覆盖效果。

---

## 附：代码文件清单

| 文件 | 模块系统 | 说明 |
| --- | --- | --- |
| `Code/math-commonjs.js` | CommonJS | 导出 `add`/`subtract`/`multiply`，演示 `module.exports` |
| `Code/app-commonjs.js` | CommonJS | `require` 引入并演示 `__dirname`/`__filename` |
| `Code/circle-area.mjs` | ESM | 命名导出 + 默认导出，演示 `import.meta.url` |
| `Code/use-esm.mjs` | ESM | 三种导入方式演示 |
| `Code/dynamic-import.js` | CommonJS | 动态 `import()` 加载 ESM，演示互操作 |
