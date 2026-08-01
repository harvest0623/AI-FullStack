# Project References —— 项目引用配置说明

> Project References 是 TS 提供的「多 tsconfig 编排」机制，用于把一个大型项目拆成多个互相引用的子项目，让 `tsc` 仅编译发生变化的子项目，从而显著缩短大型 monorepo 的构建时间。

---

## 一、核心字段

### 1.1 `references`

写在 tsconfig 顶层（不在 `compilerOptions` 内），值为对象数组，每项指向一个子项目的 tsconfig：

```jsonc
// tsconfig.json（解决方案根 solution）
{
  "files": [],
  "references": [
    { "path": "./packages/shared" },
    { "path": "./packages/server" },
    { "path": "./packages/web" }
  ]
}
```

### 1.2 `composite: true`

被引用的子项目必须设置 `composite: true`，它强制以下约束：

- 必须设置 `rootDir`（默认为包含 tsconfig 的目录）
- 必须开启 `declaration`（生成 `.d.ts` 供引用方使用）
- 会强制开启 `incremental`，生成 `.tsbuildinfo` 缓存
- `include` / `files` 必须精确列出本子项目的源码，不能越界

```jsonc
// packages/shared/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "rootDir": "./src",
    "outDir": "./dist",
    "tsBuildInfoFile": "./dist/.tsbuildinfo"
  },
  "include": ["src/**/*.ts"]
}
```

### 1.3 `incremental` 与 `.tsbuildinfo`

`incremental: true` 让 tsc 把上一次的类型图、文件依赖关系序列化到 `.tsbuildinfo` 文件，下次编译只重新检查受影响的文件。`composite` 会自动开启它。

---

## 二、典型 monorepo 目录结构

```
my-monorepo/
├── tsconfig.base.json          # 严格性、target、module 等公共配置
├── tsconfig.json               # solution root，仅 references，不直接编译
├── packages/
│   ├── shared/
│   │   ├── tsconfig.json       # composite:true
│   │   └── src/
│   ├── server/
│   │   ├── tsconfig.json       # composite:true，references 指向 shared
│   │   └── src/
│   └── web/
│       ├── tsconfig.json       # composite:true，references 指向 shared
│       └── src/
└── package.json                # workspaces: ["packages/*"]
```

子项目引用其他子项目：

```jsonc
// packages/server/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "rootDir": "./src",
    "outDir": "./dist",
    "tsBuildInfoFile": "./dist/.tsbuildinfo"
  },
  "references": [
    { "path": "../shared" }
  ],
  "include": ["src/**/*.ts"]
}
```

代码侧引用：

```ts
// packages/server/src/index.ts
import { formatDate } from '@my/shared';   // 在 shared 的 package.json name 中声明
```

---

## 三、构建命令

### 3.1 `tsc --build`

`--build` 模式是 Project References 的「官方驱动」，它会：

1. 按 references 拓扑排序，确定依赖顺序
2. 仅编译「自上次构建后发生变化」的子项目
3. 失败时停止后续构建，避免错误雪崩

```bash
# 全量构建（首次或想清理后重建）
tsc --build --verbose

# 增量构建（只编译变化的子项目）
tsc --build

# 清理产物（删除 outDir 与 .tsbuildinfo）
tsc --build --clean

# 强制重新构建（忽略增量缓存）
tsc --build --force

# 监听变化
tsc --build --watch
```

### 3.2 推荐的 npm scripts

```jsonc
{
  "scripts": {
    "build": "tsc --build",
    "build:clean": "tsc --build --clean",
    "watch": "tsc --build --watch",
    "type-check": "tsc --build --noEmit"
  }
}
```

---

## 四、Project References 的实战价值

### 4.1 加速增量编译

一个 10 万行的单 tsconfig 项目，改一行代码也要全量类型检查。拆成 5 个子项目后，仅受影响的项目重新编译，构建时间常从分钟级降到秒级。

### 4.2 强制模块边界

子项目只能 `import` 被引用子项目的「公开导出」，不能跨 `src` 直接深入内部文件。配合 ESLint `no-restricted-imports` 可强制执行架构分层。

### 4.3 独立的编译目标

`web` 子项目可设 `target: ES2020` + `module: ESNext`，`server` 子项目可设 `target: ES2022` + `module: CommonJS`，互不干扰。

### 4.4 与 monorepo 工具协作

- **pnpm workspaces / npm workspaces**：负责包之间的依赖安装与软链
- **tsc --build**：负责跨包类型检查与产物编译
- **turbo / nx / lerna**：在上层做任务编排与缓存

---

## 五、常见陷阱

1. **忘记 `composite: true`**：被 references 引用的子项目必须开 composite，否则 `tsc --build` 直接报错 `Referenced project must have setting composite: true`。

2. **`include` 越界**：子项目 A 的 `include` 写到子项目 B 的源码上，会导致 B 的源码被 A 重复编译，产物冲突。每个子项目的 `include` 必须严格限定在自身 `src` 下。

3. **路径别名跨项目失效**：`paths` 在 references 模式下不传递，每个子项目需各自配置 `baseUrl` / `paths`，或通过包名 `@my/shared` 引用（推荐后者，配合 workspaces 软链）。

4. **`.tsbuildinfo` 入库**：构建缓存文件必须加入 `.gitignore`，否则跨开发者环境不一致会触发莫名其妙的「跳过编译」。

5. **references 不等于 import**：在 tsconfig 里写 `references` 只是声明「构建顺序依赖」，业务代码仍需 `import` 才能使用对方导出；反过来，若只 import 不写 references，tsc 会报「找不到模块」或无法解析类型。

---

## 六、何时该用、何时不该用

| 场景 | 是否推荐 |
| --- | --- |
| 单包小型项目 | ❌ 单 tsconfig 即可，引入 references 是过度工程化 |
| 多包 monorepo，包之间有依赖 | ✅ 增量收益显著 |
| 前后端同仓，前端用 bundler 后端用 tsc | ✅ 可分别为两端配 tsconfig |
| 仅想拆分类型声明与运行时 | ⚠️ 用 `declaration` + `isolatedModules` 更轻量 |
| 临时想加速单项目编译 | ⚠️ 先试 `incremental: true`，收益不足再上 references |
