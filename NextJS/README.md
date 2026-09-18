# NextJS 全栈学习指南

> 系统化掌握 Next.js——基于 React 的现代全栈框架，从模块化架构到路由系统、从数据获取到服务端渲染，构建生产级 AI 前端与全栈应用能力
>
> 共 14 天，覆盖 Next.js 全部核心机制与工程化实战

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是 AI 全栈学习系列的 **前端全栈核心**。Next.js 是建立在 React 之上的生产级框架，提供文件路由（App Router）、服务端组件（RSC）、多种渲染策略（SSR/SSG/ISR/CSR）、API 路由（Route Handlers）、服务端 Actions 等开箱即用的能力。

对 AI 全栈而言，Next.js 承担「交付层」的角色：

- 承载大模型对话的前端界面（聊天、流式输出、可视化）
- 通过 Route Handlers / Server Actions 安全调用大模型 API（避免在前端暴露 Key）
- 作为 Agent / RAG 应用的 Web 交互入口
- 与 NestJS 后端、Python 推理服务协作，构成完整全栈

**学习目标**：完成本板块后，你应能：
- 理解 Next.js App Router 的文件约定与路由机制，设计清晰的页面与嵌套布局
- 熟练运用 Client Component 与 Server Component，掌握「use client」边界划分
- 掌握 SSR / SSG / ISR / CSR 四种渲染策略的适用场景
- 用 Route Handlers 与 Server Actions 构建后端逻辑，安全集成大模型 API
- 掌握状态管理、表单校验、认证授权、样式方案等工程化能力
- 完成项目构建、环境配置与部署上线（Vercel / Docker）

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 代码示例 + 实战练习
- 紧扣 React / TypeScript 板块的知识衔接（组件、Hook、类型）
- 所有讲解脚本可直接运行（.js），示例代码贴合 Next.js 真实写法
- 每天开头直接进入章节简介，不做多余定位

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| React | 熟练 | 组件、状态、Hook（必须完成 React 相关基础） |
| TypeScript | 熟练 | 类型标注、泛型、接口（必须完成 TS 板块） |
| Node.js / npm | 熟练 | 包管理、脚本执行（必须完成 NodeJS 板块） |
| JavaScript 基础 | 熟练 | 异步、模块、ES6+ 语法 |
| HTTP / 网络 | 了解 | 请求响应、REST、SSE 流式概念 |

**环境准备**：
- Node.js 18.17+（推荐 20 LTS 或更高）
- npm / pnpm / yarn 任一包管理器
- 官方脚手架：`npx create-next-app@latest`
- VS Code（推荐 ES7+ React/Redux、Tailwind CSS、ESLint、Prettier 扩展）
- 可选：本地大模型 API（Ollama / OpenAI / DeepSeek 等，Day13 集成演示）

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                Next.js 全栈学习路线（14天）                        │
└─────────────────────────────────────────────────────────────────┘

阶段一：基石与路由（Day01-Day04）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Day01 简介  │  Day02 组件  │  Day03 路由  │  Day04 动态  │
│  与搭建      │  与JSX       │  与页面      │  路由与布局  │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
阶段二：渲染与交互（Day05-Day08）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Day05 渲染  │  Day06 导航  │  Day07 流式  │  Day08 客户端│
│  策略(SSR等) │  与数据获取  │  Suspense    │  Hook与交互  │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
阶段三：工程化能力（Day09-Day12）
┌─────────────────────────────────┬──────────────────────────────┐
│  Day09 Route Handlers           │  Day10 Server Actions         │
│  （API 路由 / 后端接口）         │  （表单处理 / 变更操作）      │
├─────────────────────────────────┼──────────────────────────────┤
│  Day11 状态管理与缓存            │  Day12 样式方案与 UI          │
│  （Zustand / TanStack Query）    │  （CSS Modules / Tailwind）  │
└──────────┬──────────────────────┴──────────┬───────────────────┘
           │                                  │
           ▼                                  ▼
阶段四：实战与部署（Day13-Day14）
┌───────────────────────────────────────────────────────────────┐
│  Day13 认证授权与中间件                                        │
│  （NextAuth / Middleware / 会话与 Cookie）                     │
├───────────────────────────────────────────────────────────────┤
│  Day14 环境配置、AI 集成与生产部署                              │
│  （.env / LLM 流式集成 / Vercel / Docker / 性能优化）          │
└───────────────────────────────────────────────────────────────┘
```

---

## 每日内容详表

### 阶段一：基石与路由

#### Day01 - Next.js 简介与项目搭建
- **核心**：Next.js 定位与设计哲学、SPA 到全栈框架的演进、App Router 与 Pages Router、create-next-app 脚手架、项目结构与配置、首个页面
- **代码**：项目脚手架配置、`app/layout.tsx`、`app/page.tsx`、讲解脚本
- **重点**：理解「前端框架 + 后端能力」一体化的价值

#### Day02 - React 组件模型与 JSX
- **核心**：组件化思维、函数组件与 Props、JSX 语法、状态 useState 与副作用 useEffect、事件处理、条件与列表渲染、Hooks 规则
- **代码**：讲解脚本 + 组件示例 `.tsx`
- **重点**：为后续服务端/客户端组件划分打基础

#### Day03 - 路由系统与页面
- **核心**：App Router 文件路由、`page.tsx` / `layout.tsx`、路由导航 `Link`、嵌套路由、分组路由 Route Group、局部布局
- **代码**：路由结构演示 `.tsx`
- **重点**：理解「文件即路由」的约定式路由

#### Day04 - 动态路由与嵌套布局
- **核心**：动态路由 `[id]`、`generateStaticParams`、`generateMetadata`、并行路由、拦截路由、布局嵌套与 `route.ts`
- **代码**：动态路由页面 + 元数据生成示例
- **重点**：掌握动态段与多级布局组合

### 阶段二：渲染与交互

#### Day05 - 渲染策略（CSR/SSR/SSG/ISR）
- **核心**：四种渲染策略原理与对比、Client vs Server Component、`fetch` 缓存、`revalidate`、`generateStaticParams`、动态渲染
- **代码**：讲解脚本（各策略时序演示）+ 示例 `.tsx`
- **重点**：学会按场景选择渲染策略

#### Day06 - 导航与数据获取
- **核心**：`Link` 导航与预取、`useRouter`、`usePathname`、`fetch` 在 Server Component 中、缓存与去重、并行数据请求
- **代码**：导航与数据获取示例
- **重点**：掌握前后端导航与请求模式

#### Day07 - 流式渲染与加载状态
- **核心**：Suspense、`loading.tsx`、`error.tsx`、`not-found.tsx`、Streaming SSR、骨架屏、渐进式渲染
- **代码**：loading/error/not-found 示例 + 讲解脚本
- **重点**：提升首屏体验与健壮性

#### Day08 - 客户端 Hook 与交互
- **核心**：`use client`、useState / useEffect / useCallback / useMemo、受控组件、自定义 Hook、事件与表单交互
- **代码**：可运行的客户端交互讲解脚本 `.js` + 组件示例
- **重点**：理解「渐进增强」与客户端边界

### 阶段三：工程化能力

#### Day09 - Route Handlers（API 路由）
- **核心**：`route.ts`、GET/POST/PUT/DELETE、请求参数解析、响应构造、流式响应 SSE、与前端 fetch 对接
- **代码**：可运行的 API 处理讲解脚本 + `route.ts` 示例
- **重点**：构建安全的服务端接口层

#### Day10 - Server Actions（服务端操作）
- **核心**：`"use server"`、表单提交、action 定义、revalidatePath、表单校验、乐观更新、安全注意
- **代码**：Server Action 表单示例 + 讲解脚本
- **重点**：理解「无 JS 的 HTML 表单增强」

#### Day11 - 状态管理与缓存
- **核心**：服务端缓存机制、`cookies()` / `headers()`、Zustand 客户端状态、TanStack Query 数据请求缓存、全局状态方案选型
- **代码**：状态管理讲解脚本 + 示例
- **重点**：区分「服务端状态」与「客户端状态」

#### Day12 - 样式方案与 UI
- **核心**：全局 CSS、CSS Modules、Tailwind CSS、CSS-in-JS、响应式设计、主题切换、图片与字体优化
- **代码**：样式方案示例 + 讲解脚本
- **重点**：掌握现代样式组织方式

### 阶段四：实战与部署

#### Day13 - 认证授权与中间件
- **核心**：NextAuth（Auth.js）、Credentials / OAuth 流程、Session 管理、`middleware.ts` 路由保护、`cookies`、RBAC
- **代码**：认证中间件示例 + 讲解脚本
- **重点**：构建安全的用户访问控制

#### Day14 - 环境配置、AI 集成与生产部署
- **核心**：`.env` 环境变量、服务端/客户端变量区分、集成大模型 API（Ollama/OpenAI SSE 流式）、构建产物、Vercel 部署、Docker 部署、性能优化
- **代码**：LLM 流式对话路由示例 + Dockerfile + 部署讲解脚本
- **重点**：跑通「Next.js + 大模型」的完整实战闭环

---

## 目录结构

```
NextJS/
├── README.md                        # 本板块总纲
├── Day01 - Next.js简介与项目搭建/
│   ├── README.md                    # 当天学习文档
│   └── Code/                        # 当天代码
│       ├── nextjs_check.js          # 环境检测脚本
│       └── ...(示例代码)
├── Day02 - React组件模型与JSX/
│   └── ...
├── ...
└── Day14 - 环境配置AI集成与生产部署/
    └── ...
```

每个 `DayXX` 目录包含 **README.md**（当天知识讲解）与 **Code/**（可运行的讲解脚本与示例代码）。

---

## 学习建议

1. **前置必备**：先完成 React 与 TypeScript 基础，否则服务端/客户端组件部分易混淆。
2. **先理论后动手**：每个 Day 先读 README 理解机制，再运行 Code 中的讲解脚本复现现象。
3. **以真实项目为主线**：Day01 搭建项目后，后续每天都在同一项目上增量开发，最终组成一个「AI 对话应用」。
4. **强调渲染模型**：SSR / SSG / ISR 差异是本板块核心，反复做对比实验。
5. **对接 AI 生态**：Day13-14 重点掌握如何在后端安全调用大模型并流式返回前端，这是 AI 全栈的必备技能。

---

## 如何运行代码

本板块的 `Code/` 目录包含两类文件：

- **讲解脚本（.js / .mjs）**：展示渲染策略、数据流、状态管理等逻辑，直接用 Node.js 运行：

  ```bash
  cd "Day01 - Next.js简介与项目搭建/Code"
  node nextjs_check.js
  ```

- **Next.js 示例代码（.tsx / .ts）**：贴近真实项目写法。要实际运行，需先搭建项目（Day01 提供脚手架），把示例文件复制到对应 `app/` 目录后访问开发服务器：

  ```bash
  npx create-next-app@latest my-app
  cd my-app
  npm run dev    # 访问 http://localhost:3000
  ```

> 提示：每个 Day 的 README.md 都标注了对应示例的正确落位路径与运行方式。

---

## 知识点速查

| 主题 | 一句话速记 |
|------|-----------|
| App Router | 以 `app/` 目录的文件结构定义路由，`page.tsx` 即页面 |
| Server Component | 默认渲染在服务端，可直读数据库/文件，不携带 JS 到客户端 |
| Client Component | 以 `'use client'` 标记，可交互，带打包后的 JS 到浏览器 |
| 渲染策略 | SSR(实时)/SSG(构建时)/ISR(定时)/CSR(浏览器) 四种 |
| Route Handlers | 用 `route.ts` 在匹配路径定义后端 API 接口 |
| Server Actions | 用 `'use server'` 定义服务端函数，表单/按钮直接调用 |
| Suspense | 包裹异步组件，配合 `loading.tsx` 实现流式骨架屏 |
| 动态段 | `app/[id]/page.tsx` 捕获 URL 动态参数，props.params 读取 |
| 缓存 | `fetch` 默认缓存 GET，`revalidate` 控制 ISR 刷新间隔 |
| Middleware | 在 `middleware.ts` 统一做鉴权/重定向/请求改写 |
| 环境变量 | `NEXT_PUBLIC_` 前缀才会暴露到客户端，密钥只留服务端 |
| 大模型集成 | 在 Route Handler/Server Action 中调用 LLM，用 SSE 流式返回 |

---

## 后续板块

完成 Next.js 后，可继续深入学习：

- **TypeScript 强化**：全面提升类型安全（若需系统复习）
- **Redis**：缓存、限流、会话存储，为 AI 应用提升性能
- **NestJS**：后端工业级框架，与 Next.js 组成完整业务系统
- **Docker / K8s**：容器化部署与集群编排，服务上线（若未完成）
- **AI 后端服务**：Ollama / RAG 服务化，让 Next.js 应用对接真实推理能力

各板块相互独立、顺序可调，可按需要跳读。