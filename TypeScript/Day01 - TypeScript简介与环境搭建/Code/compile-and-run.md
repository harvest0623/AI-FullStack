# 编译与运行步骤说明

本文件梳理 Day01 中 TS 代码的四种主要运行方式。所有命令在 `Code/` 目录下执行，需先完成 `npm install`。

## 前置准备

```bash
cd Code
npm install
```

安装完成后，`node_modules/` 中应包含 `typescript`、`ts-node`、`tsx`、`@types/node`。验证：

```bash
npx tsc --version   # 应输出 5.x.x
```

---

## 方式一：tsc 编译 + node 运行（看产物）

最直观的方式，能看清「TS 编译为 JS」这一事实。

```bash
# 编译整个项目（依据 tsconfig.json）
npx tsc

# 编译产物在 dist/ 目录下
node dist/hello.js
node dist/types-vs-js.js
```

若只编译单个文件（不走 tsconfig.json，使用默认配置）：

```bash
npx tsc hello.ts --outDir ./dist
node dist/hello.js
```

**适用场景**：理解编译过程、调试编译产物、CI/CD 构建。

---

## 方式二：ts-node 直接运行（开发调试）

无需产出 `.js` 文件，`ts-node` 在内存中即时编译并执行。

```bash
npx ts-node hello.ts
npx ts-node types-vs-js.ts
```

也可通过 `package.json` 中已定义的脚本：

```bash
npm run hello
```

**适用场景**：脚本调试、快速验证逻辑。注意 `ts-node` 启动略慢，不适合大型项目高频重启。

---

## 方式三：tsx 现代运行器（推荐）

基于 esbuild，启动速度比 `ts-node` 快一个数量级，且原生支持 ESM。

```bash
npx tsx hello.ts
npx tsx types-vs-js.ts
```

通过 `package.json` 脚本：

```bash
npm start          # 等价于 tsx hello.ts
npm run compare    # 等价于 tsx types-vs-js.ts
```

**适用场景**：日常开发、脚本运行，新项目首选。

---

## 方式四：watch 模式（监听文件变化自动重跑）

### 4.1 tsc --watch（编译监听）

```bash
npx tsc --watch
# 或
npm run watch
```

监听所有 `.ts` 文件变化，自动增量编译到 `dist/`。需另开一个终端运行 `node dist/hello.js`（或配合 `nodemon`）才能看到执行结果。

### 4.2 tsx watch（运行监听）

```bash
npx tsx watch hello.ts
# 或
npm run dev
```

文件变化自动重跑，**编译+执行一体化**，是开发期最高效的方式。

### 4.3 配合 nodemon（中大型项目）

在 `package.json` 的 `scripts` 中加入：

```json
{
  "scripts": {
    "dev:nodemon": "nodemon --exec tsx hello.ts"
  }
}
```

`nodemon` 提供更精细的监听配置（`ignore`、`delay`、`verbose`），适合中大型项目统一管理进程重启。

---

## 类型检查（不产出文件）

CI 或提交前只做类型检查、不生成 `.js`：

```bash
npx tsc --noEmit
# 或
npm run build:check
```

`--noEmit` 让 `tsc` 只做类型检查、不写盘，速度更快。建议加入 CI 流水线作为质量门禁。

---

## 常见问题

### Q1：报错 `Cannot find module 'tsx'` / `Cannot find module 'ts-node'`

未执行 `npm install`，或执行时不在 `Code/` 目录。重新执行：

```bash
cd Code
npm install
```

### Q2：报错 `error TS2307: Cannot find module 'node'`

缺少 `@types/node`。确认 `package.json` 的 `devDependencies` 中有 `@types/node`，重新 `npm install`。

### Q3：`tsc` 编译报错 `Option 'strict' cannot be specified without 'useDefineForClassFields'`

TS 版本过旧。升级到 `typescript@5+`：

```bash
npm install -D typescript@^5
```

### Q4：`tsx` 运行 ESM 报错 `ERR_UNKNOWN_FILE_EXTENSION`

确保 `tsconfig.json` 的 `module` 与 `package.json` 的 `type` 一致。本章示例使用 `commonjs`，无需在 `package.json` 中设 `"type": "module"`。

---

## 速查表

| 任务 | 命令 |
| --- | --- |
| 安装依赖 | `npm install` |
| 类型检查（不产出） | `npx tsc --noEmit` |
| 编译到 `dist/` | `npx tsc` |
| 运行编译产物 | `node dist/hello.js` |
| ts-node 直接运行 | `npx ts-node hello.ts` |
| tsx 直接运行 | `npx tsx hello.ts` |
| tsx watch 监听运行 | `npx tsx watch hello.ts` |
| tsc 监听编译 | `npx tsc --watch` |
