# Day05 - 渲染策略（CSR/SSR/SSG/ISR）

> 本章节是 Next.js 全栈能力的核心。理解四种渲染方式——客户端渲染（CSR）、服务端渲染（SSR）、静态生成（SSG）、增量静态再生成（ISR）的原理与取舍，掌握服务端组件与客户端组件的边界，学会按业务场景选择正确策略。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 渲染时机全景](#21-渲染时机全景)
  - [2.2 客户端渲染 CSR](#22-客户端渲染-csr)
  - [2.3 服务端渲染 SSR](#23-服务端渲染-ssr)
  - [2.4 静态生成 SSG](#24-静态生成-ssg)
  - [2.5 增量静态再生成 ISR](#25-增量静态再生成-isr)
  - [2.6 四种策略对比](#26-四种策略对比)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 Server Component vs Client Component](#31-server-component-vs-client-component)
  - [3.2 'use client' 边界](#32-use-client-边界)
  - [3.3 fetch 与缓存](#33-fetch-与缓存)
  - [3.4 动态渲染的触发](#34-动态渲染的触发)
  - [3.5 如何选择渲染策略](#35-如何选择渲染策略)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **清晰描述四种渲染策略**：能说出各自的渲染时机与优劣势。
2. **理解 Server 与 Client 组件边界**：知道什么逻辑放服务端、什么放客户端。
3. **掌握 `'use client'` 的用法**：准确判断组件是否需要标记。
4. **理解 fetch 缓存与 revalidate**：会配置 ISR 的刷新策略。
5. **按场景选型**：面对一个业务需求能判断用哪种渲染策略。

---

## 二、理论知识

### 2.1 渲染时机全景

页面 HTML 在**何时、何地**被生成，决定了渲染策略：

| 策略 | 渲染位置 | 渲染时机 |
| --- | --- | --- |
| CSR | 浏览器 | 浏览器下载 JS 后实时渲染 |
| SSR | 服务器 | 每次请求时实时渲染 |
| SSG | 构建时 | 构建阶段一次生成，部署后静态提供 |
| ISR | 混合 | 构建时生成 + 后台定时间隔再生成 |

同样一份 React 组件，取决于**是否启用缓存、何时请求数据**，Next.js 会选择不同策略。

### 2.2 客户端渲染 CSR

**原理**：浏览器加载包含空的或最小 HTML 与全部 JS，JS 执行后在客户端调用 API、渲染真实内容。等同传统 React SPA。

```
浏览器请求 → 返回空壳HTML+JS → JS加载 → 前端调API → 客户端渲染内容
```

**特点**：
- ✅ 交互丰富，客户端逻辑灵活
- ✅ 避免服务端计算压力
- ❌ 首屏白屏较长、SEO 差（爬虫难抓取）

**适用**：完全依赖客户端交互、且无需 SEO 的内部工具页。

在 Next.js 中，需求数据且想用客户端渲染，可用 `'use client'` 组件 + `useEffect`，或用 React 库（如 React Query）fetch。

### 2.3 服务端渲染 SSR

**原理**：每次用户请求时，服务器执行组件、获取数据、渲染出完整 HTML 返回，浏览器再做「水合（Hydration）」（绑定事件、变成可交互 SPA）。

```
请求 → 服务器执行组件+取数据 → 返回完整HTML → 浏览器水合接管交互
```

**特点**：
- ✅ 首屏有完整内容，SEO 友好
- ✅ 数据始终最新（每次请求重新获取）
- ❌ 每次请求都跑服务端，响应比 SSG 慢；服务器压力大

**适用**：数据高度实时、个性化、需 SEO 的页面（如登录后主页、实时数据面板）。

### 2.4 静态生成 SSG

**原理**：**构建时**一次性把页面渲染成静态 HTML + 对应用的数据，部署到 CDN 后直接提供，速度最快。

```
构建 → 服务器渲染所有页面为静态HTML → 部署CDN → 直接返回（不跑服务端）
```

**触发静态化的条件**：
- 页面是纯静态（无动态数据）+ 无 `cookies()`/`headers()`/动态请求
- 用 `generateStaticParams` 预定义了动态路径集合
- `fetch` 数据被标记为 `force-static` / 默认缓存

**特点**：
- ✅ 极快（静态文件/CDN），零服务器运行时消耗
- ✅ SEO 极佳
- ❌ 内容构建后就固定，需重新构建才能更新

**适用**：文档、营销页、博客文章、产品介绍等**更新不频繁**页面。

### 2.5 增量静态再生成 ISR

**原理**：SSG 的基础上，允许页面在**后台定时**（或按需）重新生成静态版本。旧版本先提供（Cache First），新版本生成后切换（Cache Miss in Background），且首次访问未生成页面可即时生成。

```
构建 → 生成静态页面 → 访问 → 达到 revalidate 间隔 → 后台重新生成 → 提供新版本
```

```tsx
// app/data.ts —— 示例：设置 revalidate 间隔 60 秒
export const revalidate = 60;
```

```tsx
// 或对单个 fetch 设置
const res = await fetch('https://api.example.com/data', {
  next: { revalidate: 60 }, // 60 秒后重新验证
});
```

**三种触发更新的方式**：

```tsx
// 1. 基于时间的重新验证
export const revalidate = 60;

// 2. 按需重新验证（Webhook / Server Action 调用）
// import { revalidatePath, revalidateTag } from 'next/cache';
// revalidatePath('/blog/hello');
// revalidateTag('products');

// 3. 每次请求都动态（context 内有 cookies/headers 时）
```

**特点**：
- ✅ 静态化的速度 + 可更新的内容
- ✅ 兼顾 SEO、性能与新鲜度
- 🔧 复杂度略高，需规划 revalidate 间隔

**适用**：商品库存、新闻列表、博客列表等**定期更新**内容。

### 2.6 四种策略对比

| 维度 | CSR | SSR | SSG | ISR |
| --- | --- | --- | --- | --- |
| 渲染位置 | 浏览器 | 服务器 | 构建时 | 构建时+后台 |
| 首屏速度 | 慢 | 中 | 最快 | 快 |
| SEO | 差 | 好 | 最好 | 好 |
| 数据新鲜度 | 实时 | 实时 | 固定 | 定时更新 |
| 服务器压力 | 低 | 高 | 无 | 定时少量 |
| 更新机制 | 天然实时 | 天然实时 | 需重建 | revalidate/按需 |
| 适用 | 内部工具 | 实时个性化 | 固定内容 | 定期更新 |

---

## 三、核心概念解析

### 3.1 Server Component vs Client Component

**Server Component（服务端组件）** —— Next.js 的**默认**组件：

- 只在服务端渲染，**不携带 JS 到浏览器**（小、快）
- 可 `await` 异步数据、直读数据库/文件系统、访问私密环境变量
- **不能用** `useState`/`useEffect`/`useRouter` 等客户端 Hook

```tsx
// 默认是 Server Component
export default async function BlogList() {
  const posts = await db.post.findMany(); // 可直读数据库！
  return (
    <ul>
      {posts.map((p) => <li key={p.id}>{p.title}</li>)}
    </ul>
  );
}
```

**Client Component（客户端组件）** —— 需要交互的组件：

- 以 `'use client'` 标记，会打包 JS 到浏览器
- 可在客户端水合，使用事件、状态、副作用
- 配置、密钥等**不要**放在客户端组件

选用原则：**默认服务端，需要交互才加 `'use client'`**。

### 3.2 'use client' 边界

`'use client'` 标注在一个组件文件的**顶部**，其**整个子树**（它import的组件）都会成为客户端组件链：

```tsx
'use client';   // 文件顶部指令

import { useState } from 'react';

export default function SearchBox() {
  const [q, setQ] = useState('');
  return <input value={q} onChange={(e) => setQ(e.target.value)} />;
}
```

**注意**：
- `'use client'` 是「组件边界」标记，一旦标记，子组件都按客户端处理。
- 若客户端组件 import 了一个 Server Component 作为 children，children 仍可在服务端渲染（组合模式，性能友好）。
- **不要把密钥放客户端组件**（会被打包进浏览器）。

### 3.3 fetch 与缓存

Next.js 扩展了原生 `fetch`，默认行为随场景自适应：

```tsx
// 静态化优先的默认行为（GET fetch 默认缓存）
const data = await fetch(url); // 会尝试静态化

// 不想缓存，实时获取：
const data = await fetch(url, { next: { revalidate: 0 } }); // 动态
// 或每次请求动态：
const data = await fetch(url, { cache: 'no-store' });

// 分时间间隔刷新（ISR）
const data = await fetch(url, { next: { revalidate: 30 } });

// 标签化缓存，配合 revalidateTag 按需刷新
const data = await fetch(url, { next: { tags: ['products'] } });
```

### 3.4 动态渲染的触发

当页面**读取了以下任何一个**，Next.js 会将其判定为**动态渲染**（SSR，每次请求实时）：

- `cookies()` —— 读取 Cookie
- `headers()` —— 读取请求头
- `searchParams` —— 读取查询参数
- 使用 `fetch` 且标记为动态（`cache:'no-store'`、`revalidate:0`）

```tsx
// 判断页面是静态还是动态：看看有没有用到动态 API
import { cookies, headers } from 'next/headers';

export default async function Page() {
  const token = (await cookies()).get('auth'); // 触发动态渲染
  const ua = await headers(); // 触发动态渲染
  return <p>{token?.value}</p>;
}
```

### 3.5 如何选择渲染策略

决策流程：

1. 内容**完全固定**、很少变 → **SSG**
2. 内容**定期更新**、又希望快 → **ISR**
3. 内容**实时、个性化**、且要 SEO → **SSR**
4. 仅内部工具、无需 SEO → **CSR**
5. **同一页面混用**：公共部分静态 + 个性化部分动态（Next.js 天然支持组件级混合）

经验法则：**能静态就静态，不能静态就 ISR，再不行 SSR，最后才考虑纯 CSR**。

---

## 四、关键知识点总结

- **四种策略**：CSR（浏览器）、SSR（每次请求服务端）、SSG（构建时静态）、ISR（静态+定时再生成）。
- **SSG 最快速**：静态文件/CDN，适合更新少的页面。
- **ISR 最均衡**：静态速度 + 定时/按需更新。
- **SSR 最实时**：每次请求重新渲染，适合个性化数据。
- **默认服务端组件**：可 `await`、读库、访问私密变量，不打包 JS。
- **`'use client'` 边界**：需要交互才标记，子树继承客户端。
- **fetch 扩展**：`revalidate`/`cache`/`tags` 控制缓存与静态化。
- **动态渲染触发器**：`cookies()`/`headers()`/`searchParams`/动态 fetch。

---

## 五、实战练习

### 练习一：render_strategies.js —— 四种策略原理演示

**任务描述**：运行脚本，模拟四种渲染方式在「请求→响应」过程中的时序差异，并用对比表帮助记忆。

**运行方式**

```bash
cd Code
node render_strategies.js
```

### 练习二：静态与动态混合页面

在 `app/data/` 下分别实现：
- 一个无 `cookies()`/动态 fetch 的**静态页面（SSG）**
- 段级别设置 `export const revalidate = 30` 的 **ISR 页面**
- 读取 `searchParams` 的 **动态页面（SSR）**

运行 dev 访问，观察构建日志中的 ™（静态）与 ƒ（动态）标记差异。

### 练习三：'use client' 边界判断

分析现有页面：哪些需要 `'use client'`（有交互状态的），哪些保持服务端（只是展示数据）。动手给需要交互的组件加标记。

---

## 下节预告

下一节 **Day06** 将进入 **导航与数据获取**：掌握 `Link` 预取、`useRouter`、`usePathname` 等客户端导航 API，以及 Server Component 中 `fetch` 的缓存、去重与并行请求模式，构建高效的数据加载链路。