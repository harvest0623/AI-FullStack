# 第三方库类型说明（third-party-types.md）

本文件补充说明如何在 TS 项目中获取与管理第三方库的类型声明，对应 `tsconfig.json` 的相关配置。

---

## 一、第三方库类型的三种来源

| 来源 | 标识方式 | 典型代表 | 可靠度 |
|------|----------|----------|--------|
| 库自带类型 | `package.json` 的 `types` / `typings` 字段指向 `.d.ts` | axios、vue、zod、dayjs | ⭐⭐⭐ 最高 |
| @types 组织 | `@types/xxx` 独立包，由 DefinitelyTyped 维护 | `@types/lodash`、`@types/express`、`@types/node` | ⭐⭐ 较高 |
| 自己编写 | 项目内手写 `.d.ts` | 内部 JS 工具、无类型的旧库 | ⭐ 取决于自己 |

### 1.1 库自带类型（首选）

越来越多现代库（尤其是 TS 编写的库）直接在发布包内带 `.d.ts`。检查方式：

```bash
# 查看 package.json 是否有 types / typings 字段
cat node_modules/lodash-es/package.json | grep -E 'types|typings'
```

```jsonc
// axios 的 package.json
{
  "main": "index.js",
  "types": "index.d.ts"   // ← 指向同目录的 .d.ts，TS 自动识别
}
```

`types` 与 `typings` 是同义词，前者是新名，后者是旧名，二者均可。

### 1.2 @types 组织（DefinitelyTyped）

对于纯 JS 编写且未自带类型的库，社区在 [DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped) 仓库维护类型补丁，以 `@types/xxx` 的包名发布到 npm。

```bash
# 安装 lodash 的类型（lodash 本身不自带类型）
npm install --save-dev @types/lodash

# 安装 express 的类型
npm install --save-dev @types/express

# 安装 node 的类型（Node.js 内置 API 的类型声明）
npm install --save-dev @types/node
```

### 1.3 自己编写

当 `@types/xxx` 不存在，或类型不满足需求时，可在项目内自建 `.d.ts`：

```ts
// types/legacy-lib.d.ts
declare module 'legacy-lib' {
  export function doSomething(input: string): number;
}
```

---

## 二、@types 的自动加载机制

### 2.1 node_modules/@types/ 自动加载

TS 编译器默认会扫描 `node_modules/@types/` 目录下的所有子目录，把它们作为类型声明自动纳入程序。这意味着：

```bash
npm install --save-dev @types/lodash
```

安装后**无需任何 import 或 reference**，`lodash` 模块立即获得类型。

### 2.2 typeRoots：控制自动加载的根目录

```jsonc
{
  "compilerOptions": {
    // 默认值：["./node_modules/@types"]
    // 显式配置后会「替换」默认值，而非追加
    "typeRoots": [
      "./node_modules/@types",
      "./src/types"
    ]
  }
}
```

> ⚠️ 配置 `typeRoots` 会**替换**默认的 `./node_modules/@types`，因此若要保留默认行为需显式写出。

### 2.3 types：精确控制加载哪些 @types

默认情况下，`node_modules/@types/` 下的**所有**包都会被加载。用 `types` 字段可以白名单限制：

```jsonc
{
  "compilerOptions": {
    // 只加载以下 @types 包，其余即使安装了也不加载
    "types": ["node", "lodash", "express"]
  }
}
```

- **不配置 `types`**：加载 `@types/` 下的全部包（默认行为）。
- **配置 `types: []`**：不自动加载任何 `@types` 包（极简模式，需手动 `/// <reference types="xxx" />`）。
- **配置 `types: ["node"]`**：只加载 `@types/node`，其余忽略。

> 💡 实践建议：中小型项目不配置 `types`，让所有已安装的 `@types` 自动生效；大型项目可用 `types` 白名单减少全局污染。

### 2.4 优先级：自带类型 > @types > 自定义

当一个库同时存在「自带类型」与「@types」时：

```
优先级：package.json types 字段 > @types/xxx > 项目内 .d.ts
```

- 如果库自带类型，TS 优先用自带的，`@types/xxx` 即使安装了也会被忽略。
- `@types/xxx` 仅对「不带类型」的库生效。
- 项目内的 `declare module 'xxx'` 是兜底方案，通常用于 `@types` 不存在的场景。

---

## 三、查看库是否自带类型

### 3.1 命令行检查

```bash
# 方法一：查看 package.json 的 types / typings 字段
node -e "console.log(require('./node_modules/xxx/package.json').types || require('./node_modules/xxx/package.json').typings)"

# 方法二：直接查找 .d.ts 文件
# 用 Glob 工具查找：node_modules/xxx/**/*.d.ts
```

### 3.2 在 TS 代码中验证

```ts
// 如果有类型，鼠标悬停 add 会显示完整签名
import { add } from 'lodash';
//     ^? 如果报 TS7016「找不到声明文件」，说明无类型
```

### 3.3 在 npm registry 查询

```bash
# 查看 npm 包的 tsconfig / types 信息
npm info axios types
npm info lodash types   # 多半返回 undefined，说明无自带类型
```

---

## 四、本项目的配置说明

### 4.1 tsconfig.json 相关字段

```jsonc
{
  "compilerOptions": {
    "lib": ["ES2020", "DOM"],      // 内置标准库：ES2020 + DOM（提供 Window、Document 等）
    // "typeRoots": 不配置，使用默认 ./node_modules/@types
    // "types": 不配置，自动加载所有已安装的 @types
    "skipLibCheck": true            // 跳过 .d.ts 文件的类型检查，加速编译
  }
}
```

### 4.2 本项目安装的 @types

| 包名 | 用途 |
|------|------|
| `@types/node` | Node.js 内置 API（`process`、`Buffer`、`__dirname` 等）的类型 |

### 4.3 本项目自定义的 .d.ts 文件

| 文件 | 作用 |
|------|------|
| `global-declare.d.ts` | 全局变量、window 属性、全局函数、全局命名空间 |
| `module-declare.d.ts` | 为虚构的 `fictional-utils` 模块补充类型，以及通配符声明 |
| `express-augment.d.ts` | 模块扩增：扩展 Express.Request 添加 user 字段 |
| `env.d.ts` | 扩展 NodeJS.ProcessEnv 与 ImportMetaEnv |

这些 .d.ts 文件都在 `include: ["*.ts", "*.d.ts"]` 范围内，被 TS 编译器自动纳入。

---

## 五、常见命令速查

```bash
# 安装类型
npm install --save-dev @types/lodash

# 查看已安装的 @types
npm list --depth=0 | grep @types

# 全量类型检查（不输出文件）
npx tsc --noEmit

# 查看某个 @types 包提供的声明文件
# 用 Glob 工具查找：node_modules/@types/node/*.d.ts
```
