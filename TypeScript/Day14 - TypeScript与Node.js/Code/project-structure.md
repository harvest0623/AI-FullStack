# TypeScript + Node.js 项目结构建议

本文档给出一个生产可用的 TS + Node.js 项目骨架，覆盖目录分层、`tsconfig` 配置、`package.json` scripts 与构建产物布局。

## 一、推荐目录结构

```
my-app/
├── src/
│   ├── index.ts              # 应用入口：启动 HTTP 服务、初始化依赖
│   ├── config/
│   │   └── index.ts          # 读取环境变量、配置 schema
│   ├── routes/               # 路由层：解析请求、调用 service、组装响应
│   │   ├── user.routes.ts
│   │   └── auth.routes.ts
│   ├── services/             # 业务层：核心业务逻辑、事务编排
│   │   ├── user.service.ts
│   │   └── auth.service.ts
│   ├── repositories/         # 数据访问层：DB / 外部 API
│   │   └── user.repository.ts
│   ├── middlewares/          # 中间件：日志、鉴权、错误处理
│   │   └── error-handler.ts
│   ├── utils/                # 工具函数：纯函数、无副作用
│   │   ├── logger.ts
│   │   └── hash.ts
│   └── types/                # 全局类型声明、共享 interface
│       ├── express.d.ts      # 扩展 Express Request
│       └── domain.ts         # 业务实体类型
├── tests/                    # 测试：与 src 同构
│   ├── unit/
│   └── integration/
├── dist/                     # tsc 编译输出（gitignore）
├── node_modules/             # gitignore
├── .env.example
├── .eslintrc.cjs
├── .prettierrc
├── package.json
├── tsconfig.json
├── tsconfig.build.json       # 生产构建专用
└── README.md
```

## 二、分层职责

| 层 | 职责 | 不应做 |
|----|------|--------|
| `routes/` | 解析 HTTP 请求、参数校验、调用 service、返回响应 | 不直接访问 DB |
| `services/` | 业务规则、事务、编排多个 repository | 不感知 HTTP（不引用 req/res） |
| `repositories/` | 数据访问，SQL/ORM 调用 | 不含业务规则 |
| `utils/` | 纯工具函数 | 不做 IO、不持有状态 |
| `types/` | 共享类型声明 | 不含运行时代码 |

依赖方向：`routes → services → repositories → utils`；任何反向引用都应被视为坏味道。

## 三、tsconfig 配置（开发 + 构建）

### `tsconfig.json`（开发时用，type-check + IDE）

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "types": ["node"],
    "strict": true,
    "useUnknownInCatchVariables": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] },
    "noEmit": true
  },
  "include": ["src", "tests"]
}
```

### `tsconfig.build.json`（构建用，emit 到 dist）

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "noEmit": false,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src"],
  "exclude": ["tests", "dist", "node_modules"]
}
```

## 四、package.json scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "start": "node dist/index.js",

    "type-check": "tsc --noEmit",
    "build": "rimraf dist && tsc -p tsconfig.build.json",

    "lint": "eslint src --ext .ts",
    "format": "prettier --write \"src/**/*.ts\"",

    "test": "vitest run",
    "test:watch": "vitest",

    "ci": "npm run lint && npm run type-check && npm run test && npm run build"
  }
}
```

要点：

- **`dev`**：`tsx watch` 提供亚秒级热重载，比 `tsc -w + node` 快一个数量级
- **`type-check`**：CI 中独立类型检查，不输出 JS，只验证类型
- **`build`**：先清理 `dist/`，再以 `tsconfig.build.json` 编译输出
- **`ci`**：lint → type-check → test → build 的串行流水线

## 五、构建与运行分离

```
开发：  tsx watch src/index.ts        （源码热重载，无编译产物）
构建：  tsc -p tsconfig.build.json    （生成 dist/）
运行：  node dist/index.js            （生产环境，无需 TS 工具链）
```

生产部署时只需 `npm ci && npm run build && npm start`，运行环境不必安装 `typescript` / `tsx`，把它们留在 `devDependencies` 即可。

## 六、ESM vs CJS 选型建议

| 场景 | 推荐 |
|------|------|
| 纯 Node.js 后端、生态成熟库 | `module: CommonJS`（最稳） |
| 库 + Node 18+ + 前沿生态 | `module: NodeNext` + `type: module` |
| 同时发布 CJS + ESM 双产物 | 用 `.cts` / `.mts` + 双 `tsconfig` + `exports` 字段 |
| 单仓库、用打包器（tsup/esbuild） | `module: ESNext` + `moduleResolution: Bundler` |

## 七、Express 项目扩展 Request 类型

在 `src/types/express.d.ts` 中扩展 Express 的 `Request`：

```ts
import { User } from './domain';

declare module 'express-serve-static-core' {
  interface Request {
    user?: User;        // 鉴权中间件挂上去
    requestId: string;  // 链路追踪 ID
  }
}
```

这样在所有 controller 里 `req.user` 都有正确类型，无需每次 `as User`。

## 八、常见坑位

1. **`@types/node` 必须装到 devDependencies**：它只在编译期需要，运行时是 `node` 全局对象。
2. **`tsx` 与 `ts-node` 二选一**：tsx 走 esbuild，更快且对 ESM 友好；ts-node 对 ESM 配置繁琐。
3. **`paths` 别名在运行时不存在**：构建产物里仍是相对路径，需要 `tsc-alias` 或 `tsconfig-paths` 才能解析 `@/`。
4. **`import type` 在 `isolatedModules` 下强制**：纯类型导入必须用 `import type`，否则打包器无法判断是否可擦除。
5. **`__dirname` 在 ESM 不可用**：改用 `fileURLToPath(import.meta.url)` + `dirname()`。
