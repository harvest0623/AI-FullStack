# Day 03 - npm 包管理与 package.json

> 本篇目标是把"会敲 `npm install`"升级为"理解 npm 背后的工程体系"，并能独立设计一个可发布、可维护、可被 AI Agent 安全调用的 Node 模块。

---

## 一、学习目标

完成本天后，你应当能够：

1. 说清 `npm` 到底做了什么，以及它在前端/AI 全栈链路中的位置。
2. 读懂并手写一份生产级的 `package.json`，理解每一个字段背后的语义。
3. 掌握语义化版本（SemVer）规则，能在 `^`、`~`、`=`、`*` 之间做出正确取舍，避免"在我电脑上能跑"的依赖漂移。
4. 理解 `package-lock.json` 与 `node_modules` 扁平化机制，知道哪些文件该提交、哪些该忽略。
5. 会用 `npx` 运行一次性命令、用 `nrm` 切换镜像源、用 `npm audit` 治理供应链安全。
6. 能编写带 `pre/post` 钩子、跨平台环境变量、串并行编排的健壮 `scripts`。
7. 理解 `@scope/name`、私有 registry、`npm link` 本地联调等工程化场景。

---

## 二、理论知识讲解

### 2.1 npm 是什么

`npm`（Node Package Manager）是 Node.js 默认的包管理器，它由三部分组成：

| 组成 | 说明 |
| --- | --- |
| **Registry** | 一个公开的 HTTP 服务，托管全世界发布的包元数据与 tarball（默认 `https://registry.npmjs.org/`） |
| **CLI** | 本地命令行工具 `npm`，负责安装、发布、版本管理、脚本执行等 |
| **Website** | `https://www.npmjs.com`，提供搜索、文档、权限管理界面 |

在 AI 全栈链路里，npm 不仅仅是"装依赖"——它是**模型推理 SDK（如 `openai`、`@anthropic-ai/sdk`）、向量数据库客户端（`@pinecone-database/pg`）、Agent 框架（`langchain`、`@langchain/core`）的统一入口**。一个混乱的 `package.json` 会让线上 Agent 启动时报 `Cannot find module`，这是真实事故的高频来源。

### 2.2 package.json 字段详解

`package.json` 是一个项目的"身份证 + 依赖账本"。下面按**使用频率**讲解关键字段，而非按字母序。

#### 必备字段

```jsonc
{
  "name": "ai-fullstack-demo",   // 必填，全小写、<=214 字符、不能有空格、URL 安全字符
  "version": "1.0.0",            // 必填，遵循 SemVer；发布后该版本号永不可复用
  "description": "一个演示包",   // 用于 npm search，影响可发现性
  "main": "./lib/index.js",     // CommonJS 入口，require('pkg') 时指向这里
  "type": "module",             // 决定 .js 文件按 ESM 还是 CJS 解析
  "exports": { /* 见下文 */ }   // 现代入口与子路径导出，优先级高于 main
}
```

#### `name` 命名规则

- 全小写，允许 `-`、`_`、`.`，但首字符不能是 `.` 或 `_`。
- 若发布 scoped 包，前缀必须为 `@你的用户名/`，例如 `@openai/sdk`。
- 名称一旦被占用即不可再注册（除非走 transfer 流程）。

#### `version` 与 SemVer

见 [2.3 节](#23-语义化版本-semver)。

#### `scripts`

定义可被 `npm run` 触发的脚本。详见 [第 5 节](#五自定义-npm-scripts-实用技巧)。

#### `dependencies` vs `devDependencies` vs `peerDependencies`

| 字段 | 何时安装 | 典型用途 |
| --- | --- | --- |
| `dependencies` | 生产环境也装 | 运行时依赖，如 `express`、`openai` |
| `devDependencies` | 仅开发环境装 | 测试、构建、lint 工具，如 `jest`、`typescript` |
| `peerDependencies` | **不会自动安装**，由宿主项目提供 | 插件机制，如 React 组件库声明 `react` 为 peer，避免多版本 React 共存 |
| `optionalDependencies` | 装失败不报错 | 平台特有依赖，如 `fsevents`（macOS 文件监听） |
| `bundleDependencies` | 打包发布时一并内联 | 离线场景 |

> **坑点**：`npm install --production` 时 `devDependencies` 不会被装，这是 Dockerfile 优化镜像体积的关键。AI 部署时若误把推理 SDK 放进 `devDependencies`，生产容器会直接跑不起来。

#### `engines`

```jsonc
{
  "engines": {
    "node": ">=18.0.0",   // 锁定运行时下限
    "npm": ">=9.0.0"
  }
}
```

默认仅警告。若要硬性拒绝安装，需配合 `.npmrc` 中的 `engine-strict=true`。AI 项目强烈建议开启，避免低版本 Node 跑不起 `fetch`、`structuredClone` 等内置 API。

#### `type`

```jsonc
{
  "type": "module"   // 或 "commonjs"
}
```

- `"module"`：项目内所有 `.js` 文件按 **ESM** 解析，可用 `import`/`export`，不能直接 `require`。
- `"commonjs"`（默认）：`.js` 按 **CJS** 解析。
- 仍可通过 `.mjs`（强制 ESM）/`.cjs`（强制 CJS）后缀覆盖。

#### `main` / `module` / `exports`

- `main`：CJS 时代的入口。
- `module`：webpack 偏好的 ESM 入口（非官方标准，但事实存在）。
- `exports`：**Node 12+ 现代标准**，优先级最高，能同时声明子路径、条件导出与多环境入口。

##### `exports` 子路径导出示例

```jsonc
{
  "name": "ai-toolkit",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",     // TS 类型优先
      "import": "./dist/index.mjs",      // ESM 入口
      "require": "./dist/index.cjs",     // CJS 入口
      "default": "./dist/index.cjs"      // 兜底
    },
    "./prompts": {                       // 子路径导出
      "types": "./dist/prompts.d.ts",
      "import": "./dist/prompts.mjs",
      "require": "./dist/prompts.cjs"
    },
    "./package.json": "./package.json"   // 显式放行
  }
}
```

调用方可以：

```js
import { chat } from 'ai-toolkit';           // 命中 "."
import { systemPrompt } from 'ai-toolkit/prompts';  // 命中 "./prompts"
```

> **为什么 AI 库爱用子路径**：可以把重型依赖（如 `@anthropic-ai/sdk`、`tiktoken`）按需拆分，避免主入口被 tree-shaking 前体积爆炸。

#### `bin`

声明可执行命令，安装后会写入 `node_modules/.bin/`，全局安装则写入系统 `PATH`。

```jsonc
{
  "bin": {
    "ai-cli": "./bin/cli.js"
  }
}
```

`./bin/cli.js` 文件顶部必须写 shebang：

```js
#!/usr/bin/env node
```

`package.json` 文件本身的 `bin` 字段就是 `npm`、`npx`、`prettier`、`eslint` 这类工具能被命令行直接调用的原理。

### 2.3 语义化版本 SemVer

SemVer 规范：<https://semver.org/lang/zh-CN/>

版本号格式：`MAJOR.MINOR.PATCH`，例如 `4.2.1`。

| 位 | 何时 +1 | 含义 |
| --- | --- | --- |
| `MAJOR`（主版本） | **破坏性变更**（不向后兼容） | 升级后调用方代码可能要改 |
| `MINOR`（次版本） | 新增功能，**向后兼容** | 升级后代码应继续工作 |
| `PATCH`（修订号） | Bug 修复，**向后兼容** | 仅修复，无新 API |

预发布标识：`1.0.0-beta.1`、`2.0.0-rc.0`，优先级低于正式版。

#### 版本范围符号对比

在 `package.json` 中，依赖版本常写成带前缀的范围：

| 写法 | 名称 | 匹配范围（以 `1.2.3` 为例） | 是否允许 MAJOR 升级 |
| --- | --- | --- | --- |
| `^1.2.3` | **Caret**（插入号，默认） | `>=1.2.3 <2.0.0` | 否（锁定 MAJOR） |
| `~1.2.3` | **Tilde**（波浪号） | `>=1.2.3 <1.3.0` | 否（锁定 MAJOR.MINOR） |
| `=1.2.3` | 精确匹配 | 仅 `1.2.3` | 否 |
| `1.2.3` | 不带前缀 | 仍被解析为 `^1.2.3`（npm v7+ 行为，但建议显式写 `^`） | 否 |
| `*` 或空 | 任意版本 | `>=0.0.0` | **是**（危险） |
| `>1.2.3` | 大于 | `>=1.3.0` | 可能 |
| `<2.0.0` | 小于 | `<2.0.0` | 取决于上下限 |
| `>=1.2.3 <2.0.0` | 区间 | 区间内任意 | 否 |
| `1.x` | x 通配 | `>=1.0.0 <2.0.0` | 否 |
| `~1.2` | 缺省 patch | `>=1.2.0 <1.3.0` | 否 |

##### 对比示例

假设当前已安装 `axios@1.2.3`，registry 上存在 `1.2.4`、`1.3.0`、`2.0.0`：

| 写法 | `npm update` 会升到 |
| --- | --- |
| `^1.2.3` | `1.3.0`（不会到 2.0.0） |
| `~1.2.3` | `1.2.4`（不会到 1.3.0） |
| `=1.2.3` | 不升级 |
| `*` | `2.0.0`（最高版） |

> **AI 项目实践建议**：
> - 业务项目（不发布）：用默认 `^`，配合 `package-lock.json` 锁定。
> - 发布给他人用的库：用 `^` 锁定 MAJOR，但**关键依赖**（如 `openai`、`react`）改用 `peerDependencies` 声明，避免版本冲突。
> - **禁止用 `*`**——一次"最新版"可能引入破坏性 API 变更，导致 Agent 调用链整体崩溃。

### 2.4 package-lock.json

#### 作用

`package.json` 只声明**范围**，而 `package-lock.json` 记录**每个依赖（含嵌套子依赖）的精确版本、下载 URL、完整性哈希（integrity）**。

没有 lock 文件时，不同机器、不同时间 `npm install` 可能装出**不同的 `node_modules`**——这就是经典的"在我电脑上能跑"问题。

#### 是否提交

| 场景 | 是否提交 lock |
| --- | --- |
| **应用项目**（后端服务、CLI 工具、Next.js 应用） | **必须提交**，保证 CI/CD、Docker、同事机器装出完全一致的依赖 |
| **库（library）** | 视团队约定；多数推荐**也提交**，便于复现 bug；但发布到 npm 时，安装方会忽略你的 lock |
| **Monorepo** | 根目录提交一份根 lock 即可 |

> **AI 部署红线**：`Dockerfile` 中 `npm ci` 命令**强制要求** lock 文件存在且与 `package.json` 同步，否则构建直接失败。这是防止"线上模型调用突然 500"的最后一道闸门。

#### 不要手改

`package-lock.json` 由 npm 自动维护，**不要手动编辑**。需要更新时用 `npm install pkg@version` 或 `npm update`。

### 2.5 node_modules 嵌套结构与扁平化

#### npm v2 时代：嵌套

每个依赖自己有一份 `node_modules`，导致"依赖地狱"：

```
node_modules/
  A@1.0.0/
    node_modules/
      C@1.0.0/
  B@1.0.0/
    node_modules/
      C@2.0.0/
```

同一个 `C` 被装了两份，磁盘与内存双倍消耗。

#### npm v3+ 时代：扁平化（hoisting）

npm 尽量把所有依赖**提升到顶层 `node_modules/`**，冲突的版本才嵌套：

```
node_modules/
  A@1.0.0/
  B@1.0.0/
  C@1.0.0/         ← 被提升的版本（"赢家"）
  B/
    node_modules/
      C@2.0.0/     ← 冲突版本仍嵌套
```

##### 带来的副作用

1. **"幽灵依赖"（phantom dependency）**：你在 `package.json` 没声明的包，但因为被提升了，`require('C')` 居然能成功。一旦上游卸载 C，你的代码就崩。→ 解决方案：用 `eslint-plugin-import` 检查。
2. **不确定的"赢家"**：谁先被提升取决于安装顺序，这也是 `package-lock.json` 存在的原因之一。

#### 现代替代方案

- **pnpm**：用硬链接 + 符号链接，彻底消除幽灵依赖，磁盘占用极低，**AI 工程团队强烈推荐**。
- **yarn**（v1 classic / v2+ berry）：Plug'n'Play（PnP）模式甚至不生成 `node_modules`。

### 2.6 npm 镜像源配置

#### 为什么需要镜像源

官方 registry 在国内访问慢，常用国内镜像：

| 镜像 | URL |
| --- | --- |
| npmmirror（淘宝镜像，最常用） | `https://registry.npmmirror.com/` |
| tencent | `https://mirrors.cloud.tencent.com/npm/` |
| huawei | `https://mirrors.huaweicloud.com/repository/npm/` |

#### 配置方式

##### 方式 1：命令行（写入全局/项目 `.npmrc`）

```bash
npm config set registry https://registry.npmmirror.com/
```

##### 方式 2：`.npmrc` 文件（推荐，随项目提交）

```ini
registry=https://registry.npmmirror.com/
```

##### 方式 3：`nrm` 镜像源管理工具

```bash
npm install -g nrm         # 安装
nrm ls                     # 列出所有可用镜像
nrm use taobao             # 切换到淘宝镜像
nrm test                   # 测速
nrm add company https://npm.company.com/  # 添加私有 registry
```

> **企业实践**：私有公司包与公共包共存时，用 `.npmrc` 的 `@scope:registry` 配置分流：
> ```ini
> @mycompany:registry=https://npm.company.com/
> registry=https://registry.npmmirror.com/
> ```
> 这样 `@mycompany/foo` 走私有源，其他包走公共镜像。

### 2.7 npx 的作用与原理

#### 解决的问题

想运行 `create-react-app`，传统做法：

```bash
npm install -g create-react-app   # 全局装一次，永远占着
create-react-app my-app
```

问题：全局污染、版本过期、卸载麻烦。

#### npx 做的事

```bash
npx create-react-app my-app
```

执行流程：

1. 检查本地 `node_modules/.bin/` 是否有 `create-react-app`。
2. 没有 → 临时从 registry 下载到缓存目录 `~/.npm/_npx/`。
3. 执行命令。
4. 不污染全局，下次再跑会复用缓存或拉新版本。

#### 常见用途

```bash
npx cowsay "Hello AI"           # 跑一次性的小工具
npx prettier --write .          # 不装也跑格式化
npx eslint --init               # 交互式初始化配置
npx tsx script.ts               # 直接跑 TS（无需 tsc 编译）
npx -p pkg-a -p pkg-b cmd       # 同时临时装多个包
```

#### 原理补充

`npx` 本质是 `npm` 自带的可执行文件查找器。npm v5.2+ 起内置，无需单独安装。它会优先复用**本地已装**的包（如 `node_modules/.bin/eslint`），这就是为什么项目里 `npm i -D eslint` 后，可以直接 `npx eslint .` 而不会再去下载。

### 2.8 semver 安全漏洞与 npm audit

#### 供应链风险

npm 生态的"依赖树"很深——一个 AI 应用依赖 `langchain`，`langchain` 又依赖 `js-yaml`、`p-limit`、`zod`……任何一个**间接依赖**被投毒或爆出 CVE，都会传染你的服务。典型事件：

- **event-stream（2018）**：被植入恶意代码窃取钱包。
- **coa / rc（2021）**：被劫持后发布挖矿木马版本。
- **node-ipc（2022）**：作者在俄乌冲突期间植入政治性破坏代码。

#### npm audit

```bash
npm audit            # 扫描依赖树，列出已知漏洞
npm audit --json     # JSON 格式输出（适合 CI）
npm audit fix        # 自动升级到不破坏兼容性的修复版本
npm audit fix --force  // 强制升级（可能破坏性，慎用）
```

输出示例：

```
# Run  npm install --save-dev jest@29.7.0  to resolve 3 vulnerabilities
 moderate  ...
 high      ...
 critical  ...
```

#### CI 集成实践

```yaml
# GitHub Actions 片段
- run: npm ci
- run: npm audit --audit-level=high
- run: npm test
```

`--audit-level` 可设为 `low|moderate|high|critical`，决定何种级别才让 CI 失败。AI 服务建议设为 `high`。

#### 不足与补充

`npm audit` 依赖 GitHub Advisory Database，更新有延迟。生产级 AI 服务可叠加：

- **Snyk** / **Socket**：更主动的供应链扫描，Socket 甚至会分析包的**网络行为**（是否有可疑外连）。
- **Renovate** / **Dependabot**：自动提交 PR 升级依赖。
- **`npm ci` + lock 锁定**：这是最基础也最有效的一道防线。

---

## 三、核心命令解析

| 命令 | 作用 | 关键参数 | 示例 |
| --- | --- | --- | --- |
| `npm init` | 生成 `package.json` | `-y` 跳过提问用默认值 | `npm init -y` |
| `npm init <template>` | 用脚手架创建项目 | — | `npm init vite@latest` |
| `npm install` | 安装 `package.json` 全部依赖 | `--omit=dev` 跳过 dev | `npm install` |
| `npm install <pkg>` | 安装指定包 | `@version` 指定版本 | `npm install axios@1.6.0` |
| `npm i -S <pkg>` | 装到 `dependencies`（默认行为，可省 `-S`） | `--save` | `npm i express` |
| `npm i -D <pkg>` | 装到 `devDependencies` | `--save-dev` | `npm i -D typescript` |
| `npm i -g <pkg>` | 全局安装（写入系统 PATH） | `--global` | `npm i -g nodemon` |
| `npm install --force` | 强制重装，绕过部分校验 | — | 慎用，可能破坏 lock |
| `npm uninstall <pkg>` | 卸载并从 `package.json` 移除 | `-g` 全局卸载 | `npm un axios` |
| `npm update [pkg]` | 升级到符合范围上限的最新版 | 无参数则升级所有 | `npm update lodash` |
| `npm outdated` | 列出过期的依赖 | — | `npm outdated` |
| `npm run <script>` | 执行 `scripts` 中定义的命令 | 简写 `npm start`、`npm test` | `npm run build` |
| `npm audit` | 扫描漏洞 | `--fix` 自动修复 | `npm audit` |
| `npm publish` | 发布到 registry | `--access public` scoped 包公开 | `npm publish` |
| `npm version <type>` | 升级版本号并打 git tag | `patch|minor|major` | `npm version minor` |
| `npm link` | 把当前包软链到全局，供其他项目调试 | 见 [6 节](#六scope-包与私有-registry) 下文 | `npm link` |
| `npm link <pkg>` | 在当前项目引用全局软链的包 | — | `npm link my-utils` |
| `npm ci` | 基于 lock 文件干净安装，**CI 专用** | 要求 lock 与 package.json 同步 | `npm ci` |
| `npm cache clean --force` | 清空 npm 缓存 | — | 排错时使用 |

> **`npm install` vs `npm ci`**：
> - `install` 会更新 lock、可能改变版本。
> - `ci` 严格按照 lock 安装，先删 `node_modules`，速度快、可复现。**CI/CD 与 Docker 一律用 `npm ci`**。

---

## 四、scope 包与私有 registry

### 4.1 scoped 包 `@scope/name`

scope 是包名的命名空间前缀，格式 `@scope/package-name`：

```bash
# 安装
npm install @anthropic-ai/sdk
npm install @babel/core

# 发布
# 1) 在 package.json 中 name 必须以 scope 开头
{
  "name": "@yourname/ai-utils"
}
# 2) 登录
npm login
# 3) 发布（scoped 包默认私有，需显式声明公开）
npm publish --access public
```

#### scope 的价值

1. **命名隔离**：不与他人重名冲突。
2. **权限分组**：组织内多人协作时，可统一管理 `@org/*` 的发布权限。
3. **registry 分流**：见下文。

### 4.2 私有 registry

企业内部包不发到公共 npm，而是托管在私有服务上。常见方案：

| 方案 | 说明 |
| --- | --- |
| **Verdaccio** | 开源、轻量、可代理上游，本地一行命令起 |
| **Nexus** | 企业级，多语言制品库 |
| **GitHub Packages** | 与 GitHub 仓库集成 |
| **JFrog Artifactory** | 商业级，支持多格式 |

#### 配置示例（`.npmrc`）

```ini
# 默认走淘宝镜像
registry=https://registry.npmmirror.com/

# @company scope 走内部 registry
@company:registry=https://npm.company.com/

# 内部 registry 鉴权 token（敏感，勿提交到 git）
//npm.company.com/:_authToken=${COMPANY_NPM_TOKEN}
```

#### Verdaccio 本地起一个

```bash
npm install -g verdaccio
verdaccio                # 默认监听 4873
# 配置 .npmrc
npm config set registry http://localhost:4873/
npm adduser              # 在 verdaccio 注册账号
npm publish              # 包发布到本地
```

> 这是 AI 团队内部共享"prompt 模板包"、"内部 embedding 客户端"的低成本方案。

---

## 五、自定义 npm scripts 实用技巧

### 5.1 pre/post 钩子

npm 会自动在执行 `xxx` 之前先跑 `prexxx`，之后跑 `postxxx`：

```jsonc
{
  "scripts": {
    "prebuild": "rimraf dist",          // 构建前清空产物
    "build": "tsc",
    "postbuild": "echo 构建完成 ✅",
    "predev": "echo 启动开发服务器",
    "dev": "node --watch app.js",
    "pretest": "tsc --noEmit",          // 测试前先做类型检查
    "test": "node --test",
    "posttest": "echo 测试结束"
  }
}
```

执行 `npm run build` 时，实际依次执行：`prebuild` → `build` → `postbuild`。

> **AI 场景用法**：在 `prestart` 里跑一次"配置校验"或"模型列表刷新"，避免用错误配置拉起 Agent。

### 5.2 串行 `&&` 与并行 `concurrently`

#### 串行：`&&`

```jsonc
{
  "scripts": {
    "build:lint": "eslint . && tsc",   // 先 lint 再 build，前一个失败则不继续
    "build": "npm run build:lint && npm run build:bundle"
  }
}
```

注意：`&&` 在 Windows cmd / PowerShell / macOS bash 行为一致，但**不能并行**。

#### 并行：`concurrently`

```bash
npm install -D concurrently
```

```jsonc
{
  "scripts": {
    "dev": "concurrently \"npm:dev:server\" \"npm:dev:client\"",
    "dev:server": "node --watch server.js",
    "dev:client": "vite"
  }
}
```

`concurrently` 会同时启动多个进程，日志前缀区分来源，任一进程退出可配置是否一起退出。

> **AI 全栈典型场景**：一边 `node --watch` 跑后端 API，一边 `vite` 跑前端，一边 `tsx watch agent.ts` 跑 Agent worker，三个一起并行。

### 5.3 跨平台环境变量：`cross-env`

不同平台设置环境变量的语法不同：

| 平台 | 语法 |
| --- | --- |
| macOS/Linux | `NODE_ENV=production node app.js` |
| Windows cmd | `set NODE_ENV=production && node app.js` |
| Windows PowerShell | `$env:NODE_ENV='production'; node app.js` |

直接写进 `scripts` 会跨平台崩。`cross-env` 抹平差异：

```bash
npm install -D cross-env
```

```jsonc
{
  "scripts": {
    "start": "cross-env NODE_ENV=production node app.js",
    "dev": "cross-env NODE_ENV=development LOG_LEVEL=debug nodemon app.js"
  }
}
```

> **AI 场景**：`OPENAI_API_KEY`、`MODEL_NAME`、`EMBEDDING_DIMENSION` 等配置都通过 `cross-env` 注入，保证团队 Windows/Mac 一致。

### 5.4 实用片段集

```jsonc
{
  "scripts": {
    "//security": "安全",
    "audit": "npm audit --audit-level=high",
    "//lint": "质量",
    "lint": "eslint . --ext .js,.ts",
    "lint:fix": "eslint . --ext .js,.ts --fix",
    "format": "prettier --write .",
    "//test": "测试",
    "test": "node --test",
    "test:watch": "node --test --watch",
    "test:coverage": "c8 --reporter=text node --test",
    "//build": "构建",
    "clean": "rimraf dist coverage",
    "prebuild": "npm run clean",
    "build": "tsc",
    "//release": "发布",
    "prerelease": "npm run test && npm run build",
    "release": "standard-version && npm publish"
  }
}
```

---

## 六、关键知识点总结

1. **`package.json` 是项目契约**：`name`+`version` 唯一标识一个可发布包，`dependencies` 是运行时账本，`scripts` 是任务入口。
2. **`exports` 取代 `main`**：现代包应优先用 `exports`，支持子路径导出与条件导出，便于 tree-shaking 与按需加载。
3. **SemVer 三位规则**：MAJOR 破坏、MINOR 新增、PATCH 修复；`^` 锁 MAJOR、`~` 锁 MAJOR.MINOR，生产环境永远不要用 `*`。
4. **`package-lock.json` 必须提交**：它是可复现构建的基石，CI 用 `npm ci` 强制校验。
5. **`node_modules` 是扁平化+嵌套混合**：扁平化带来"幽灵依赖"风险，pnpm 是更现代的替代。
6. **`npx` 是临时执行器**：不污染全局，优先复用本地 `node_modules/.bin`，找不到才去下载。
7. **`npm audit` 是供应链体检**：CI 集成 `--audit-level=high`，但需配合 Renovate/Snyk 主动升级。
8. **scope + 私有 registry**：`@scope/name` 实现命名隔离与 registry 分流，企业内部包走 Verdaccio / Nexus。
9. **scripts 健壮性三件套**：`pre/post` 钩子、`concurrently` 并行、`cross-env` 跨平台。
10. **AI 项目特殊关注点**：推理 SDK、向量库客户端、Agent 框架属于 `dependencies`；`engines.node` 锁定 18+ 以使用原生 `fetch`；敏感 key 用 `cross-env` 注入而非写进代码。

---

## 七、实战练习

### 练习 1：搭建一个最小可发布的工具库

**目标**：在 `Code/` 目录下完成一个名为 `day03-math-util` 的本地包，使其能被同目录其他文件 `require` 调用。

**步骤**：

1. 进入 `Code` 目录，执行 `npm init -y`。
2. 编辑 `package.json`：
   - `name` 改为 `day03-math-util`
   - `main` 指向 `math-util.js`
   - 添加 `scripts`：`test` 跑 `node --test`、`start` 跑 `node ./use-npx-demo.js`
3. 阅读 `math-util.js`，确认导出的函数（如 `add`、`factorial`、`isPrime`）。
4. 新建 `index.js`，`require('./math-util.js')` 并调用 `add(2, 3)`，打印结果。
5. 运行 `npm start` 验证。

**验收**：

```bash
npm start
# 输出应包含 add(2,3) = 5
```

### 练习 2：体验 npm link 本地联调

**目标**：模拟"开发中的包被另一个项目使用"的场景，不发布、不复制代码。

**步骤**：

1. 在 `Code/` 下执行 `npm link`，把 `day03-math-util` 软链到全局。
2. 在任意目录新建一个测试项目 `link-test/`：
   ```bash
   mkdir link-test && cd link-test
   npm init -y
   npm link day03-math-util
   ```
3. 创建 `test.js`：
   ```js
   const { add } = require('day03-math-util');
   console.log('linked add:', add(10, 20));
   ```
4. 运行 `node test.js`，应输出 `linked add: 30`。
5. 修改 `math-util.js` 中 `add` 的实现（如改为 `a + b + 1`），再次运行 `test.js`，**无需重新安装**即可看到变化——这就是 link 的威力。
6. 解除链接：`npm unlink day03-math-util`（在测试项目）+ `npm unlink`（在源项目）。

**思考题**：为什么 `npm link` 在 Monorepo 中容易出"多份 React 实例"问题？提示：`peerDependencies` + 软链路径。

### 练习 3：scripts 编排与审计

**目标**：为 `Code/package.json` 补充一个生产级 scripts，并跑一次安全审计。

**步骤**：

1. 仿照 [5.4 节](#54-实用片段集) 的实用片段，把 `lint`、`test`、`build`、`audit` 四个脚本补齐（可全部用注释占位）。
2. 为 `build` 加 `prebuild` 钩子，打印 "开始构建"。
3. 执行 `npm run build`，观察钩子触发顺序。
4. 执行 `npm audit`，记录当前依赖树有无漏洞（应是空依赖，无漏洞）。
5. 故意装一个有已知漏洞的旧版包验证：
   ```bash
   npm install lodash@4.17.4
   npm audit
   ```
   观察 audit 报告，再 `npm audit fix` 修复，再次 `npm audit` 确认清零。

**验收**：

- 能用一句话解释 `prebuild` 的触发时机。
- 能读懂 `npm audit` 输出中 `Severity`、`Path`、`Fix available` 三列的含义。

---

## 八、参考与延伸阅读

- [SemVer 规范（中文）](https://semver.org/lang/zh-CN/)
- [npm CLI 官方文档](https://docs.npmjs.com/cli/)
- [Node.js ESM 机制](https://nodejs.org/api/esm.html)
- [Verdaccio 官网](https://verdaccio.org/)
- [concurrently](https://github.com/open-cli-tools/concurrently)
- [cross-env](https://github.com/kentcdodds/cross-env)
- [Socket 供应链安全](https://socket.dev/)

---

> 下一天预告：**Day 04 - CommonJS vs ESM 与模块加载机制**。我们将拆解 `require` / `import` 的底层差异、循环依赖处理、动态导入与顶层 await，并打通"为什么 AI SDK 普遍用 ESM"的工程脉络。
