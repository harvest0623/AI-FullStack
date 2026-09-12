# Day01 - Next.js 简介与项目搭建

> 本章节我们从「Next.js 到底是什么」出发，理解它如何让 React 从纯前端框架升级为全栈框架，并逐步搭建起开发环境与首个项目骨架，为后续 13 天奠定工程基础。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 Next.js 是什么](#21-nextjs-是什么)
  - [2.2 从 SPA 到全栈框架的演进](#22-从-spa-到全栈框架的演进)
  - [2.3 App Router 与 Pages Router](#23-app-router-与-pages-router)
  - [2.4 Next.js 的核心优势](#24-nextjs-的核心优势)
  - [2.5 对 AI 全栈开发的意义](#25-对-ai-全栈开发的意义)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 create-next-app 脚手架](#31-create-next-app-脚手架)
  - [3.2 项目目录结构](#32-项目目录结构)
  - [3.3 关键配置文件](#33-关键配置文件)
  - [3.4 首个页面与启动流程](#34-首个页面与启动流程)
- [四、环境搭建步骤](#四环境搭建步骤)
- [五、关键知识点总结](#五关键知识点总结)
- [六、实战练习](#六实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **准确描述 Next.js 的本质**：理解它是「基于 React 的全栈框架」，同时提供前端组件渲染与后端 API、服务端渲染能力，而非单纯的前端库。
2. **理解 SPA → 全栈框架的演进逻辑**：能说清传统 CSR 的痛点，以及 Next.js 如何通过服务端渲染与文件路由解决它们。
3. **区分 App Router 与 Pages Router**：清楚这是两代路由体系，新项目默认使用 App Router。
4. **独立完成 Next.js 项目搭建**：使用 `create-next-app` 初始化项目，掌握目录结构与关键配置。
5. **启动项目并理解运行机制**：能运行 `npm run dev`，并解释 `next start`、开发模式与生产构建的区别。

---

## 二、理论知识

### 2.1 Next.js 是什么

Next.js 是一个由 Vercel 开发的**开源的 React 全栈框架（Full-Stack React Framework）**。

它的核心定位可以用一句话概括：**在 React 之上，补齐了「路由、渲染、构建、部署、后端 API」等一套生产级解决方案**。

传统 React（如 Vite 脚手架）只负责「客户端渲染」（CSR），页面内容和路由、SEO、服务端能力都需要开发者自己引入一堆库（React Router、服务器框架、构建配置等）来组装。而 Next.js 把这些全部「约定成俗」地内置好了：

```
┌───────────────────────────────────────────────┐
│                Next.js 应用                     │
├───────────────────────────────────────────────┤
│   前端层：React 组件 + 路由 + 样式 + 状态        │
├───────────────────────────────────────────────┤
│   数据层：数据获取 fetch / 服务端渲染 SSR         │
├───────────────────────────────────────────────┤
│   接口层：Route Handlers / Server Actions       │
├───────────────────────────────────────────────┤
│   构建层：Webpack/Turbopack + 编译 + 代码分割     │
└───────────────────────────────────────────────┘
```

一句话：**React 负责「组件」，Next.js 负责「应用」**。

### 2.2 从 SPA 到全栈框架的演进

要理解 Next.js 的价值，先回顾前端架构的演进。

**阶段一：纯服务端渲染（传统）**
页面由服务器用 HTML 模板生成，每次跳转都重新加载整个页面。缺点：交互体验差；优点：SEO 好、首屏快。

**阶段二：SPA 客户端渲染（CSR）**
React / Vue 流行后，页面在浏览器中由 JS 渲染，路由切换不刷新页面，交互丝滑。但产生三个典型痛点：

| 痛点 | 表现 |
| --- | --- |
| **首屏慢** | 浏览器要下载全部 JS 并执行后白屏渲染，弱网下等待久 |
| **SEO 差** | 页面初始 HTML 为空，搜索引擎爬虫难以抓取内容 |
| **无服务端能力** | Promise、鉴权、数据库访问都要另起后端或额外库 |

**阶段三：同构 / 全栈框架**
Next.js 等框架解耦了「在服务端预渲染出初始 HTML」的问题，同时保留 SPA 的交互体验：

- 服务端先渲染出完整 HTML 返回浏览器（解决 SEO 与首屏）
- 浏览器加载 JS 后「水合」（Hydration），接管交互（保留 SPA 体验）
- 同一套 React 组件代码可同时在服务端与客户端运行（同构）

这才是「全栈」的真正含义：**一套代码，前后端共铸**。

### 2.3 App Router 与 Pages Router

Next.js 历史上存在两代路由体系：

| 维度 | Pages Router（旧） | App Router（新，13+ 默认） |
| --- | --- | --- |
| 路由目录 | `pages/` | `app/` |
| 页面文件 | `pages/about.tsx` | `app/about/page.tsx` |
| 布局支持 | 单一根布局，靠 `_app.tsx` | 每个页面可自定义嵌套 `layout.tsx` |
| 渲染机制 | 页面级 CSR/SSR | 组件级 Server Component + 布局 |
| 数据获取 | `getServerSideProps` 等 | 直接在组件内 `await fetch` |
| 路由拦截/并行 | 支持有限 | `@parallel` 并行路由、`(.)` 拦截路由 |

**结论**：新项目一律使用 **App Router**。本板块全部围绕 App Router 展开（从 Day03 开始深入）。

### 2.4 Next.js 的核心优势

1. **约定式文件路由**：把文件放到 `app/` 目录，路径即 URL，无需写路由配置。
2. **多渲染策略开箱即用**：静态生成（SSG）、服务端渲染（SSR）、增量静态再生成（ISR）、客户端渲染（CSR），按场景自由选择。
3. **内置后端能力**：Route Handlers（`route.ts`）与 Server Actions（`"use server"`）让前端项目自带 API。
4. **性能优化内置**：自动代码分割、图片优化、字体优化、预取预渲染。
5. **生态与部署无缝**：Vercel 一键部署，也支持 Docker、Node 服务器、Edge 等。
6. **全栈数据流统一**：同一文件里既能拿后端数据又能渲染 UI，减少上下文切换。

### 2.5 对 AI 全栈开发的意义

对 AI 全栈工程师，Next.js 是「AI 应用的前端与交付层」的最佳载体：

1. **打造对话式 AI 界面**：聊天框、流式输出、Markdown 渲染、代码高亮等，React 生态成熟，Next.js 组织良好。
2. **安全调用大模型**：在 Route Handler / Server Action（服务端）中调用 OpenAI / Ollama，把密钥藏在服务端，前端只接收结果。
3. **流式响应（SSE）**：Next.js 支持服务端流式返回 token，实现「打字机」式对话体验。
4. **Agent / RAG 的 Web 交互入口**：与后端服务（NestJS / Python）协作，成为 AI 能力的 Web 门户。
5. **快速原型与上云**：Vercel 一键部署，适合快速验证 AI 产品。

简言之：**Python 训模型，Next.js 让模型可交互**。

---

## 三、核心概念解析

### 3.1 create-next-app 脚手架

Next.js 官方提供一键初始化的脚手架命令：

```bash
npx create-next-app@latest my-app
```

运行后会交互式询问一系列配置项，可通过命令行参数跳过交互：

```bash
# 全参数版（一条命令完成初始化）
npx create-next-app@latest my-app \
  --ts \            # TypeScript
  --app \           # 使用 App Router
  --tailwind \      # 集成 Tailwind CSS
  --eslint \        # 启用 ESLint
  --src-dir \       # 源码放到 src/ 目录
  --import-alias "@/*" \
  --use-npm         # 使用 npm 作为包管理器
```

初始化的项目结构即「Hello World」骨架，可立即 `npm run dev` 启动。

### 3.2 项目目录结构

一个典型的 App Router 项目结构如下：

```
my-app/
├── app/                      # 应用根目录（App Router 核心）
│   ├── layout.tsx            # 根布局（必须存在）
│   ├── page.tsx              # 首页 /（根路径页面）
│   ├── globals.css           # 全局样式
│   ├── about/                # /about 路由
│   │   └── page.tsx
│   └── api/                  # API 路由目录
│       └── hello/
│           └── route.ts      # /api/hello 接口
├── public/                   # 静态资源（图片等）
├── src/                      # 若启用 src-dir，源码放这里
├── next.config.{js,mjs}     # Next.js 配置
├── package.json
├── tsconfig.json             # TypeScript 配置
└── next-env.d.ts             # Next 类型声明（勿手动修改）
```

### 3.3 关键配置文件

**`package.json`** 中的 scripts：

```json
{
  "scripts": {
    "dev": "next dev",        // 开发模式：热更新、带错误提示
    "build": "next build",    // 生产构建：产出优化后的静态/服务端产物
    "start": "next start",    // 启动生产服务器（需先 build）
    "lint": "next lint"       // 代码检查
  }
}
```

**`next.config.mjs`**：Next.js 的核心配置，可配置代理、图片域名、环境变量、实验特性等：

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**.example.com' },
    ],
  },
};

export default nextConfig;
```

### 3.4 首个页面与启动流程

`app/page.tsx` 是根路径 `/` 的页面组件：

```tsx
export default function Home() {
  return (
    <main>
      <h1>Hello Next.js!</h1>
    </main>
  );
}
```

`app/layout.tsx` 是根布局，包裹所有页面：

```tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

**启动流程**：

1. `npm run dev` 启动开发服务器（默认 3000 端口）
2. 访问 `http://localhost:3000`，Next.js 根据 `app/` 目录自动匹配 `/` 到 `app/page.tsx`
3. 开发模式下页面热更新，改动即时生效
4. `npm run build && npm start` 用于生产：先优化构建，再以生产模式运行

---

## 四、环境搭建步骤

前置：确保已安装 Node.js 18.17+（建议 20 LTS）。

### 4.1 创建项目

```bash
npx create-next-app@latest my-app
```

按提示选择：TypeScript = **Yes**、ESLint = Yes、Tailwind = Yes、`src/`目录 = **Yes**、App Router = Yes。

### 4.2 启动开发服务器

```bash
cd my-app
npm run dev
```

浏览器打开 `http://localhost:3000`，看到欢迎页即成功。

### 4.3 验证安装（运行附带检测脚本）

本 Day 的 `Code/nextjs_check.js` 会检测当前机器 Node/npm 环境，并打印 Next.js 相关说明：

```bash
cd Code
node nextjs_check.js
```

### 4.4 IDE 配置建议（VS Code）

- 安装扩展：**ESLint**、**Prettier**、**Tailwind CSS IntelliSense**、**ES7+ React/Redux snippets**
- 开启 `typescript.referencesCodeLens.enabled` 以更好定位类型
- 可配置 `.vscode/settings.json` 统一格式化：

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  }
}
```

---

## 五、关键知识点总结

- **Next.js = React 全栈框架**：在 React 之上补齐路由、渲染、构建、后端 API 等生产能力。
- **演进三阶段**：传统 SSR → SPA/CSR → 同构全栈框架，Next.js 属于后者。
- **两代路由**：Pages Router（旧）与 App Router（新，默认），本板块全用 App Router。
- **核心目录 `app/`**：`page.tsx` 即页面，`layout.tsx` 即布局，文件即路由。
- **渲染优势**：SSG/SSR/ISR/CSR 多策略，代码分割、图片优化内置。
- **开发命令**：`npm run dev`（开发）、`npm run build`（构建）、`npm start`（生产启动）。
- **对 AI 的价值**：对话界面、安全调用 LLM、SSE 流式、Agent/RAG 交互入口。

---

## 六、实战练习

以下练习对应 `Code/` 下的文件，讲解脚本可直接用 Node 运行，示例代码需在真实 Next.js 项目中体验。

### 练习一：nextjs_check.js —— 环境检测与理解

**任务描述**：运行 `node nextjs_check.js`，它会检测本机 Node.js / npm 版本，并逐一打印 Next.js 的核心概念清单。

**运行方式**

```bash
cd Code
node nextjs_check.js
```

**预期输出示例**

```
【Next.js 环境检测】
Node.js 版本：v20.13.0
npm 版本：   10.5.2
建议 Node 版本：>= 18.17

【Next.js 一句话速记】
约定式路由：文件放 app/ 目录，路径即 URL
...
```

### 练习二：hello-page.tsx —— 第一个页面

**任务描述**：把 `Code/hello-page.tsx` 的内容复制到 `app/page.tsx`，运行 `npm run dev` 访问首页。

**预期界面**：页面上显示标题与一行描述，验证了「文件即路由」与组件渲染。

### 练习三：架构说明 —— 概念自查

对照 README 第五节关键点，用一句话向他人解释「为什么说 Next.js 是全栈框架」。能让人听懂即达标。

---

## 下节预告

下一节 **Day02** 将进入 **React 组件模型与 JSX**：组件化思维、函数组件与 Props、状态与副作用 Hook、事件处理与列表渲染，夯实前端组件层，为服务端/客户端组件的划分打下基础。