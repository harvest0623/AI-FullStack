# Code/ - npm 本地调试演示

本目录是 Day03 的代码示例，重点演示 **`npm link` 本地联调流程** 与 `package.json` 的 `scripts` 配置。

## 文件清单

| 文件 | 作用 |
| --- | --- |
| `package.json` | 演示含 `pre/post` 钩子、串并行、跨平台环境变量的 scripts；`main` 指向 `math-util.js` |
| `math-util.js` | 工具模块，被 `main` 引用；包含 `add`、`subtract`、`factorial`、`isPrime`、`primesInRange` |
| `use-npx-demo.js` | 注释 + 自检脚本，演示 `npx` 的常见用法 |
| `.npmrc` | 配置镜像源、scope 分流、鉴权、严格模式等 |

## 快速运行

```bash
cd "Day03 - npm包管理与package.json/Code"

# 1. 直接运行模块自检
node math-util.js

# 2. 启动入口（npm start 会执行 use-npx-demo.js）
npm start

# 3. 体验 pre/post 钩子触发顺序
npm run build
# 期望输出：
#   [prebuild] 清理 dist 目录...
#   [build] 模拟构建产物...
#   [postbuild] 构建完成 ✅

# 4. 体验跨平台环境变量（需先装 cross-env）
# npm i -D cross-env
npm run dev:env

# 5. 跑测试（Node 18+ 内置 test runner）
npm test
```

---

## npm link 本地调试流程（重点）

### 场景

你在写一个包 `day03-math-util`（就是本目录），同时另一个项目想用它。传统做法是 `npm publish` 再 `npm install`——但每改一行代码都得发版，太蠢。`npm link` 用**符号链接**解决这个问题。

### 原理

```
全局 node_modules/day03-math-util   →  软链  →  本目录
                  ↑
测试项目 node_modules/day03-math-util   →  软链  →  全局软链
```

修改 `math-util.js` 后，测试项目**无需重新安装**立刻生效，因为读的是同一份文件。

### 完整步骤

#### Step 1：在源包目录建立全局软链

```bash
cd "Day03 - npm包管理与package.json/Code"
npm link
# 输出类似：
# added 1 package, and audited 1 package in 123ms
# found 0 vulnerabilities
# +
#   day03-math-util@1.0.0
```

`npm link` 实际做了两件事：

1. 在全局 `node_modules/` 创建一个名为 `day03-math-util` 的符号链接，指向当前目录。
2. 把 `package.json` 中 `bin` 字段声明的可执行命令也注册到全局 PATH（本例没有 `bin`，跳过）。

#### Step 2：在消费项目里建立软链

```bash
# 任意目录
mkdir link-test && cd link-test
npm init -y
npm link day03-math-util
```

现在 `link-test/node_modules/day03-math-util` 是一个软链，链到全局软链，再链到源目录。

#### Step 3：使用

创建 `link-test/test.js`：

```js
const { add, factorial, isPrime, primesInRange } = require('day03-math-util');

console.log('add(2, 3)         =', add(2, 3));
console.log('factorial(6)      =', factorial(6));
console.log('primesInRange(1, 30) =', primesInRange(1, 30));
```

运行：

```bash
node test.js
# add(2, 3)         = 5
# factorial(6)      = 720
# primesInRange(1, 30) = [ 2, 3, 5, 7, 11, 13, 17, 19, 23, 29 ]
```

#### Step 4：验证"修改即生效"

回到 `Code/math-util.js`，把 `add` 改成：

```js
function add(a, b) {
  return a + b + 1000;   // 故意改动
}
```

回到 `link-test/` 再次 `node test.js`：

```bash
add(2, 3)         = 1005   # 立刻看到变化，无需重新安装
```

这就是 `npm link` 的核心价值。

#### Step 5：清理

```bash
# 在测试项目里解除引用
cd link-test
npm unlink day03-math-util

# 在源项目里移除全局软链
cd "Day03 - npm包管理与package.json/Code"
npm unlink
```

---

## 常见坑

### 坑 1：Monorepo 中的"多份实例"

React 项目用 `npm link` 调试组件库时，常报：

```
Invalid hook call. Hooks can only be called inside the body of a function component.
```

原因：组件库软链过去后，它内部 `require('react')` 解析到的是**源目录**的 `node_modules/react`，而宿主项目用的是自己 `node_modules/react`，于是同时存在两份 React 实例，`useState` 等 hook 比对失败。

解决方案：

1. 在组件库 `package.json` 把 `react` 移到 `peerDependencies`。
2. 或在源项目 `node_modules/react` 之外，把 `react` 也 `npm link` 到宿主项目的 react。
3. 或直接用 pnpm workspace，原生支持本地包联调，不需要 `npm link`。

### 坑 2：`npm unlink` 后 require 仍能找到

因为软链删除后，`node_modules/` 残留空目录。手动删除或 `rm -rf node_modules/day03-math-util`。

### 坑 3：Windows 权限

Windows 上 `npm link` 需要管理员权限或开启开发者模式，否则创建符号链接会失败。

---

## 替代方案

| 方案 | 适用场景 |
| --- | --- |
| **pnpm workspace** | Monorepo 内多包互相依赖，原生支持，无需 link |
| **yarn workspace** | 同上 |
| **npm link** | 临时跨项目调试，简单直接 |
| **Verdaccio 本地 registry** | 想模拟真实发布流程（含版本号、tag） |
| **`file:` 协议** | `"my-utils": "file:../math-util"` 简单粗暴，但不会随源码改动热更新 |

---

## 与 Day03 主 README 的对应关系

- 主 README [2.7 节](../README.md#27-npx-的作用与原理) 讲解了 npx 原理，本目录的 `use-npx-demo.js` 是配套演示。
- 主 README [5.1 节](../README.md#51-prepost-钩子) 讲解了 pre/post 钩子，本目录 `package.json` 的 `build`/`dev`/`test` 都配了钩子。
- 主 README [练习 2](../README.md#练习-2体验-npm-link-本地联调) 即本目录的实操。
