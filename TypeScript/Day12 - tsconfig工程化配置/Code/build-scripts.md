# 常用构建脚本速查

> 面向 TS 5+ 的工程化构建场景，覆盖「类型检查 / 编译 / watch / 路径别名处理 / dev server / bundler 集成」六类常用命令。

---

## 一、纯类型检查（不产出 JS）

最常用、最高频的命令。CI 流水线必跑，IDE 后台也在跑。

```bash
# 默认读取 ./tsconfig.json，只检查不产出
tsc --noEmit

# 指定 tsconfig（多环境场景）
tsc -p tsconfig.dev.json --noEmit
tsc -p tsconfig.prod.json --noEmit

# 跨多个 tsconfig（Project References）
tsc --build --noEmit
```

**适用场景**：CI 卡口、提交前钩子（husky + lint-staged）、IDE 后台。

---

## 二、单次编译产出

```bash
# 默认读取 tsconfig.json
tsc

# 指定 tsconfig
tsc -p tsconfig.prod.json

# Project References 增量构建
tsc --build
tsc --build --force      # 忽略缓存全量重建
tsc --build --clean      # 清理产物与 .tsbuildinfo
```

**产物位置**：由 tsconfig 的 `outDir` 决定（本示例为 `./dist/prod`）。

---

## 三、watch 模式（开发期常驻）

### 3.1 原生 `tsc --watch`

```bash
tsc -p tsconfig.dev.json --watch
# 简写
tsc -p tsconfig.dev.json -w
```

- 内置增量编译，文件改动后秒级重新编译
- 仅做编译，不执行产物；适合「编译 + 由 nodemon / PM2 单独跑产物」的链路
- 不带 `onSuccess` 钩子

### 3.2 `tsc-watch`（带 onSuccess 钩子）

```bash
tsc-watch -p tsconfig.dev.json \
  --onSuccess "node dist/dev/main.js" \
  --onFirstSuccess "echo 'first build ok'" \
  --noClear
```

- 在 tsc 基础上叠加「编译成功后自动重启 node 进程」
- 适合纯后端 Node 项目，无需 bundler
- `--noClear` 避免每次清屏丢失日志

### 3.3 `ts-node-dev`（直接跑源码 + 热重启）

```bash
ts-node-dev --respawn --transpile-only paths-demo.ts
# 简写：rsd --respawn --transpile-only paths-demo.ts
```

- 跳过类型检查（`--transpile-only`），启动极快
- 文件改动后自动重启
- 适合开发期快速迭代，类型检查交给 IDE / CI

### 3.4 `nodemon` 配合 `ts-node`

`nodemon.json`：

```jsonc
{
  "watch": ["src"],
  "ext": "ts",
  "ignore": ["dist"],
  "exec": "ts-node --transpile-only src/main.ts",
  "env": { "NODE_ENV": "development" }
}
```

```bash
nodemon
```

- 灵活度最高，可对接任意启动命令
- 重启速度比 ts-node-dev 略慢，但生态成熟

---

## 四、路径别名（paths）运行时处理

`tsc` 不会在产物 JS 中替换 `@/*` 别名，运行时 Node 原生无法解析，必须借助以下工具之一：

### 4.1 开发期 —— `ts-node` 内置 paths 解析

```bash
ts-node -T paths-demo.ts
```

ts-node 会读取 tsconfig 的 `paths` 字段并在运行时做映射。`-T` 等价于 `--transpile-only`，跳过类型检查加速启动。

### 4.2 生产期 —— `tsc-alias` 后处理产物

```bash
# 先编译，再扫描 dist/prod/**/*.js 把 @/xxx 替换为相对路径
tsc -p tsconfig.prod.json && tsc-alias -p tsconfig.prod.json
```

- 纯后端 Node 项目无 bundler 时的首选
- 也可指定 `--outDir` 与 `--baseUrl` 显式覆盖

### 4.3 运行时注册 —— `tsconfig-paths`

```bash
node -r tsconfig-paths/register dist/prod/main.js
```

- 不修改产物，运行时通过 require hook 解析别名
- 适合不方便改产物（如 Docker 镜像复用）的场景

### 4.4 bundler 内置（推荐）

webpack / esbuild / vite / rollup 各自有 alias 配置，构建产物已替换为相对路径，无需 tsc-alias：

```ts
// vite.config.ts
import { defineConfig } from 'vite';
import { resolve } from 'node:path';

export default defineConfig({
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@config': resolve(__dirname, 'src/config'),
      '@utils': resolve(__dirname, 'src/utils'),
    },
  },
});
```

```ts
// esbuild 配置（build.js）
import { build } from 'esbuild';
import alias from 'esbuild-plugin-alias';

build({
  entryPoints: ['src/main.ts'],
  bundle: true,
  outfile: 'dist/main.js',
  plugins: [
    alias({
      '@': resolve('./src'),
      '@config': resolve('./src/config'),
    }),
  ],
});
```

---

## 五、与打包工具集成（简述）

| 工具 | 角色 | 是否需要 tsc | 是否需要 tsc-alias |
| --- | --- | --- | --- |
| `tsc` 单独使用 | 编译 + 类型检查 | ✅ 自身 | ⚠️ 配合 tsc-alias |
| `webpack` + `ts-loader` | 打包 + 编译 | ❌ webpack 接管 | ❌ webpack resolve.alias |
| `esbuild` | 极速打包 + 转译 | ⚠️ 仅做类型检查（tsc --noEmit） | ❌ 插件 alias |
| `vite` | 开发 server + 打包 | ⚠️ 仅做类型检查（vite build 时不检查） | ❌ vite resolve.alias |
| `swc` | 转译 | ⚠️ 需 tsc 做类型检查 | ❌ swc 自身或 @swc/register |

**主流推荐分工**：

- 类型检查：`tsc --noEmit`（CI / husky 钩子，独立于打包流程）
- 打包转译：bundler（esbuild / vite / webpack）
- 这样既享受 bundler 的速度，又保留 tsc 的完整类型检查

---

## 六、本仓库 scripts 对照（package.json）

| 脚本 | 命令 | 用途 |
| --- | --- | --- |
| `type-check` | `tsc -p tsconfig.base.json --noEmit` | 仅检查基础配置 |
| `type-check:dev` | `tsc -p tsconfig.dev.json --noEmit` | 检查 dev 配置 |
| `type-check:prod` | `tsc -p tsconfig.prod.json --noEmit` | 检查 prod 配置（CI 卡口） |
| `build` | `tsc -p tsconfig.prod.json` | 生产编译（不含 alias 替换） |
| `watch` | `tsc -p tsconfig.dev.json --watch` | 原生 watch 编译 |
| `tsc-watch` | `tsc-watch -p tsconfig.dev.json --onSuccess "..."` | 编译成功后跑产物 |
| `dev` | `ts-node-dev --respawn --transpile-only paths-demo.ts` | 源码直跑热重启 |
| `run:paths` | `ts-node -T paths-demo.ts` | 通过 ts-node 内置 paths 运行 |
| `build:alias` | `tsc -p tsconfig.prod.json && tsc-alias -p tsconfig.prod.json` | 生产编译 + 别名替换 |

---

## 七、CI 流水线推荐最小集

```yaml
# .github/workflows/ci.yml（节选）
- name: Install
  run: npm ci

- name: Type Check
  run: npm run type-check:prod

- name: Build
  run: npm run build:alias

- name: Test
  run: npm test
```

核心原则：**类型检查与编译解耦**。类型检查作为独立阶段，失败立即阻断流水线；编译产物供后续测试 / 部署使用。
