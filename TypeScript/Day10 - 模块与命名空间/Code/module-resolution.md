# 模块解析策略说明（module-resolution.md）

本文件补充说明 TS 的模块解析策略（`moduleResolution`）与路径别名（`paths`）配置，
对应 `tsconfig.json` 中的相关字段。完整 tsconfig 参数将在 Day12 详解。

---

## 一、五种模块解析策略

| 策略 | 关键字 | 适用场景 | 说明 |
|------|--------|----------|------|
| `classic` | `classic` | 旧版 TS | 仅按相对路径查找，不识别 `node_modules`，已基本弃用 |
| `node` | `Node` | CommonJS 项目 | 模拟 Node.js 的 `require` 解析：先同名文件、再目录 `index`、再 `node_modules` |
| `node16` | `Node16` | Node 16+ | 支持 `package.json` 的 `exports` 子路径导出，区分 ESM/CJS 严格语义 |
| `nodenext` | `NodeNext` | Node 现代 | 等同 `node16`，指向「最新」Node 解析规则 |
| `bundler` | `Bundler` | 打包器项目（Vite/webpack/esbuild） | TS 5 新增，模拟打包器行为，不强制扩展名，支持 `paths`，前端首选 |

---

## 二、TS 5 推荐选择

- **前端项目（Vite/webpack/esbuild）**：`module: ESNext` + `moduleResolution: Bundler`
- **Node.js 项目（CommonJS）**：`module: CommonJS` + `moduleResolution: Node`
- **Node.js 项目（ESM）**：`module: NodeNext` + `moduleResolution: NodeNext`

> 本 Day10 项目选用 `module: CommonJS` + `moduleResolution: Node`，便于 ts-node 直接运行；
> 同时开启 `isolatedModules: true`，模拟现代单文件编译器（Babel / esbuild）行为。

---

## 三、解析查找顺序（Node 策略示例）

对于 `import { add } from './math-utils'`：

1. 尝试 `./math-utils.ts` ✅ 命中
2. 否则尝试 `./math-utils.tsx`
3. 否则尝试 `./math-utils.d.ts`
4. 否则尝试 `./math-utils/index.ts`（目录 + index）

对于裸导入 `import _ from 'lodash'`：

1. 在当前目录的 `node_modules/lodash` 查找
2. 沿目录树向上：`../node_modules/lodash`、`../../node_modules/lodash` ……
3. 命中后按 `package.json` 的 `main` / `types` 字段定位入口

---

## 四、baseUrl 与 paths 路径别名

### 4.1 本项目的配置

`tsconfig.json` 中已配置：

```jsonc
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### 4.2 使用方式

配置后，以下两种写法在**编译期**等价：

```ts
// 相对路径
import { add } from './math-utils';

// 路径别名（@/* 映射到 ./*）
import { add } from '@/math-utils';
```

更常见的项目结构是 `@/*` 指向 `./src/*`：

```jsonc
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@utils/*": ["./src/utils/*"],
      "@components/*": ["./src/components/*"]
    }
  }
}
```

```ts
import { add } from '@utils/math';          // 替代 '../../../utils/math'
import { Button } from '@components/ui';    // 替代 '../../components/ui'
```

### 4.3 运行时注意事项

`paths` 是 **TS 编译期** 的解析能力，运行时（Node / 打包器）需要额外配置：

| 运行环境 | 配置方式 |
|----------|----------|
| Vite | `vite.config.ts` 的 `resolve.alias` |
| webpack | `resolve.alias` |
| Node（ts-node） | 注册 `tsconfig-paths/register`，或开启 `ts-node` 的 `paths` 选项 |
| Node（编译后运行） | 用 `tsc-alias` / `tsconfig-paths` 替换路径 |

> ⚠️ 本 Day10 的示例代码统一使用相对路径，以保证 `ts-node` 直接可运行；
> `paths` 配置仅作演示。可自行将某文件的相对导入改为 `@/` 别名后用 `tsc --noEmit` 验证类型解析。

---

## 五、module（输出格式）与 moduleResolution（解析策略）的对应关系

`module` 决定**编译输出格式**，`moduleResolution` 决定**解析查找方式**，二者需搭配：

| `module` | `moduleResolution` | 输出 / 语义 |
|----------|---------------------|-------------|
| `CommonJS` | `Node` | 输出 `require()`，Node CJS |
| `ESNext` / `ES2020` | `Node` / `Bundler` | 输出 `import/export`，供打包器 |
| `NodeNext` | `NodeNext` | 严格按 Node 的 ESM/CJS 规则，导入需写 `.js` 扩展名 |
| `Preserve`（TS 5.4+） | `Bundler` | 保持输入格式，配合打包器 |

> Day12 会深入讲解 tsconfig 全部字段。
