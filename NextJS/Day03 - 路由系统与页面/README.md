# Day03 - 路由系统与页面

> 本章节进入 Next.js 的核心——App Router 路由系统。理解「文件即路由」的约定式路由，掌握 `page.tsx`、`layout.tsx`、`Link` 导航、嵌套路由与分组路由，把组件组织成可访问的多页面应用。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 约定式路由的本质](#21-约定式路由的本质)
  - [2.2 文件夹映射 URL](#22-文件夹映射-url)
  - [2.3 page.tsx 与 layout.tsx](#23-pagetsx-与-layouttsx)
  - [2.4 Link 导航](#24-link-导航)
  - [2.5 嵌套路由与布局](#25-嵌套路由与布局)
  - [2.6 分组路由 Route Groups](#26-分组路由-route-groups)
  - [2.7 特殊文件一览](#27-特殊文件一览)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 静态路由 vs 动态路由](#31-静态路由-vs-动态路由)
  - [3.2 布局的复用与嵌套](#32-布局的复用与嵌套)
  - [3.3 链接预取 Prefetch](#33-链接预取-prefetch)
  - [3.4 绝对路径与导入别名](#34-绝对路径与导入别名)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **理解文件即路由**：通过文件系统结构定义应用路由，无需手写路由表。
2. **掌握路由映射规则**：知道 `app/` 下文件夹路径如何对应到 URL。
3. **熟练编写 page 与 layout**：用 `page.tsx` 定义页面、`layout.tsx` 定义布局并实现嵌套。
4. **使用 Link 进行客户端导航**：性能优化（客户端跳转 + 预取）。
5. **理解分组路由**：用 `(group)` 组织文件而不改变 URL 路径。

---

## 二、理论知识

### 2.1 约定式路由的本质

App Router 采用**约定式路由（Convention-based Routing）**：**你不需要写任何路由配置文件**，文件与文件夹在 `app/` 目录中的位置，直接决定了 URL 结构。

核心思想：**URL 的分段 = app/ 内的嵌套文件夹**。每个 URL 对应一个文件夹，其中放对应的页面、布局等文件。

例如：

```
app/
├── page.tsx            →  /                     （首页）
├── layout.tsx          →  （根布局）
├── about/
│   └── page.tsx        →  /about
├── blog/
│   ├── page.tsx        →  /blog
│   └── posts/
│       └── page.tsx    →  /blog/posts
└── settings/
    └── page.tsx        →  /settings
```

> 对比 Vue Router / React Router 等需要显式注册路由配置的库，Next.js 用「文件位置」自动生成路由，减少样板代码。

### 2.2 文件夹映射 URL

每个文件夹代表一个**路由段（Segment）**，URL 由各段拼接而成：

| app/ 下文件路径 | 对应 URL |
| --- | --- |
| `app/page.tsx` | `/`（根路径） |
| `app/about/page.tsx` | `/about` |
| `app/blog/posts/page.tsx` | `/blog/posts` |
| `app/dashboard/settings/page.tsx` | `/dashboard/settings` |

约定：
- `page.tsx` 是**页面文件**，一个文件夹有它才算一个可访问路由。
- 文件夹名 => 段名，多级文件夹 => 多级 URL 段。
- 文件名必须小写（除特殊约定外），URL 大小写敏感。

### 2.3 page.tsx 与 layout.tsx

**page（页面）**：定义路由的最终内容：

```tsx
// app/about/page.tsx
export default function About() {
  return (
    <div>
      <h1>关于我们</h1>
      <p>这里是 /about 页面的内容。</p>
    </div>
  );
}
```

**layout（布局）**：包裹某个段及其子路由的**共享外壳**，在多个页面间复用的 UI（导航栏、侧边栏、页脚等）。布局**不会**随着子页面切换而重新渲染（持久保持），因此可在布局中放共享状态。

```tsx
// app/dashboard/layout.tsx  —— 包裹 /dashboard 及其子路由
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div style={{ display: 'flex' }}>
      <aside>侧边导航（所有 /dashboard/* 共享）</aside>
      <main>{children}</main>
    </div>
  );
}
```

```tsx
// app/dashboard/page.tsx  —— 渲染到布局的 {children} 位置
export default function Dashboard() {
  return <h2>仪表盘主页</h2>;
}
```

**关键**：`{children}` 是被该布局包裹的子路由的渲染出口。布局可以层层嵌套，形成「布局树」。

### 2.4 Link 导航

页面之间跳转有两种方式：

**方式一：`<Link>` 组件（推荐，客户端导航）**

```tsx
import Link from 'next/link';

export default function Nav() {
  return (
    <nav>
      <Link href="/">首页</Link>
      <Link href="/about">关于</Link>
      <Link href="/blog/posts">文章</Link>
    </nav>
  );
}
```

`Link` 的特点是**客户端导航**：点击后由 JS 在前端切换视图，不整页刷新，并自动对目标路由**预取（Prefetch）**，体验如 SPA。

**方式二：`useRouter().push()` 编程式导航**

```tsx
'use client';
import { useRouter } from 'next/navigation';

export default function Button() {
  const router = useRouter();
  return <button onClick={() => router.push('/about')}>跳转</button>;
}
```

适合表单提交后跳转、条件跳转等场景。

### 2.5 嵌套路由与布局

路由文件夹可以无限嵌套，形成树状结构；每个段可有自己的 `layout.tsx`，层层包起来：

```
app/
├── layout.tsx           # 根布局（含 <html>）
├── page.tsx             # /
├── blog/
│   ├── layout.tsx       # blog 布局（如博客头部）
│   ├── page.tsx         # /blog
│   └── [slug]/
│       └── page.tsx     # /blog/...    （动态段，Day04）
```

渲染时，Next.js 会从外到内把布局套在页面外层：

```
<RootLayout>
  <BlogLayout>
    <BlogPostPage />
  </BlogLayout>
</RootLayout>
```

布局的复用带来明显好处：导航栏、页脚等只需在对应层级写一次，子页面共享。

### 2.6 分组路由 Route Groups

有时需要若干页面共用同一套布局，却**不希望它们拥有相同 URL 前缀**。这时可用**分组路由**——用 `(括号)` 包裹文件夹名，它**不会**成为 URL 的一部分，仅用于组织文件，且可以为组单独指定 `layout.tsx`。

```
app/
├── (marketing)/
│   ├── layout.tsx          # 营销页专用布局（大导航+页脚）
│   ├── about/page.tsx      # /about      （注意：没有 (marketing) 前缀）
│   └── pricing/page.tsx    # /pricing
├── (store)/
│   ├── layout.tsx          # 商店页专用布局（购物车栏）
│   ├── shop/page.tsx       # /shop
│   └── cart/page.tsx       # /cart
└── layout.tsx              # 根布局
```

要点：
- `(name)` 的文件夹名**不影响 URL**。
- 不同分组可各自携带 `layout.tsx`，实现不同 UI 骨架。
- 一个路由不能在多个组里同时存在（会冲突）。

### 2.7 特殊文件一览

在 `app/` 路由文件夹中，以下**约定文件名**各有专属职责：

| 特殊文件 | 作用 |
| --- | --- |
| `page.tsx` | 路由渲染的页面内容 |
| `layout.tsx` | 该段共享布局（包裹子路由） |
| `loading.tsx` | 该段加载中显示的 UI（配合 Suspense） |
| `error.tsx` | 该段出错时显示的 UI |
| `not-found.tsx` | 该段 404 时的 UI |
| `route.ts` | 定义该路径的后端 API 接口（Day09） |
| `template.tsx` | 类似 layout，但切换页面时重新挂载 |

`loading/error/not-found` 会在 Day07 深入；`route.ts` 在 Day09。

---

## 三、核心概念解析

### 3.1 静态路由 vs 动态路由

- **静态路由**：段名写死，如 `/about`、`/blog/posts`，URL 固定。
- **动态路由**：用 `[param]` 或 `[...param]` 命名文件夹，匹配任意值，如 `/blog/[slug]` 匹配 `/blog/hello`。这是 Day04 的重头戏。

### 3.2 布局的复用与嵌套

- 布局在路由切换时**保留**（不卸载），适合放导航栏、轮播持久状态。
- `template.tsx` 在每次子路由切换时**重新挂载**，适合需要重置状态的场景。
- 根 `layout.tsx` 必须包含 `<html>` 和 `<body>`，全局字体、主题可在此注入。

### 3.3 链接预取 Prefetch

`<Link>` 在视口内出现时，Next.js 会**预取**目标路由（静态页面直接预下载 HTML 与 JS，服务端组件的会预取数据）。用户点击时几乎瞬时跳转。这也是 SEO / 性能俱佳的原因。

### 3.4 绝对路径与导入别名

配置 `tsconfig.json` 的 `paths` 与 `next.config.js` 的 alias，可用 `@/` 引用项目根，避免深路径引用的地狱：

```ts
// 导入 app/lib/util.ts
import { helper } from '@/lib/util';
```

---

## 四、关键知识点总结

- **文件即路由**：`app/` 文件夹路径 = URL，无需写路由配置。
- **page.tsx** 定义页面，**layout.tsx** 定义共享外壳并层层嵌套。
- **Link 客户端导航** + 自动预取；`useRouter` 编程式跳转。
- **布局持久**：切换子页面布局不卸载，可放共享状态与导航。
- **分组路由 `(group)`**：组织文件不改 URL，可为组单独设布局。
- **特殊文件**：`page/layout/loading/error/not-found/route/template`。
- **模板 template.tsx**：每次切换重新挂载，与 layout 互补。

---

## 五、实战练习

### 练习一：file_route.js —— 文件路径→URL 映射演示

**任务描述**：运行 Node 脚本，输入/示例一组 `app/` 目录文件，展示它们各自映射成的 URL 路径，验证「文件即路由」。

**运行方式**

```bash
cd Code
node file_route.js
```

### 练习二：多页面导航结构

**任务描述**：在项目 `app/` 下创建 `about/page.tsx`、`blog/page.tsx`，并在根页面用 `Link` 搭建导航。运行 dev 点击跳转，观察客户端导航（页面不整刷）与预取行为。

**落位路径**：`app/page.tsx`（首页含导航）、`app/about/page.tsx`、`app/blog/page.tsx`。

### 练习三：嵌套布局

为 `blog/` 目录创建 `blog/layout.tsx`（如博客头部），并创建 `blog/posts/page.tsx`，体验布局复用与嵌套。

---

## 下节预告

下一节 **Day04** 将进入 **动态路由与嵌套布局**：用 `[param]` 匹配任意路径、用 `generateStaticParams` 做静态参数化、`generateMetadata` 动态元数据，以及并行路由、拦截路由等高级路由能力。