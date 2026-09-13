# Day04 - 动态路由与嵌套布局

> 本章节掌握 App Router 的进阶路由能力：动态路由 `[param]` 匹配任意路径、`generateStaticParams` 静态参数化、`generateMetadata` 动态元数据，以及嵌套布局的纵深组合，并了解并行路由与拦截路由等高级用法。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 动态路由 [param]](#21-动态路由-param)
  - [2.2 捕获动态参数 params](#22-捕获动态参数-params)
  - [2.3 动态段的读取](#23-动态段的读取)
  - [2.4 generateStaticParams](#24-generatestaticparams)
  - [2.5 generateMetadata](#25-generatemetadata)
  - [2.6 捕获全部段 […param]](#26-捕获全部段-param)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 动态段的嵌套组合](#31-动态段的嵌套组合)
  - [3.2 动态布局与参数](#32-动态布局与参数)
  - [3.3 并行路由 Parallel Routes](#33-并行路由-parallel-routes)
  - [3.4 拦截路由 Intercepting Routes](#34-拦截路由-intercepting-routes)
  - [3.5 动态段与静态页权衡](#35-动态段与静态页权衡)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **使用动态路由**：用 `[param]` 文件夹匹配任意动态路径。
2. **读取路由参数**：通过组件的 `params` prop 拿到动态值。
3. **实现静态参数化**：用 `generateStaticParams` 预生成常见路径，兼具静态与动态优势。
4. **动态生成元数据**：用 `generateMetadata` 为每个页面生成独立标题/描述（利于 SEO）。
5. **掌握嵌套布局组合**：把动态段融入多级布局。
6. **了解并行路由与拦截路由**：认识其适用场景（可以进阶再深入）。

---

## 二、理论知识

### 2.1 动态路由 [param]

当页面的某段 URL 是**不固定**的（如文章 id、商品 id、用户名），用动态段。做法：文件夹名用**方括号**包裹参数名 `[param]`。

```
app/
└── blog/
    └── [slug]/          # 动态段，参数名 slug
        └── page.tsx     # 匹配 /blog/任意值
```

匹配示例：

| 请求 URL | 匹配文件 | slug 值 |
| --- | --- | --- |
| `/blog/hello-world` | `app/blog/[slug]/page.tsx` | `hello-world` |
| `/blog/intro` | 同上 | `intro` |
| `/blog/2026/roadmap` | 不匹配（只有一段） | — |

文件夹名 `[slug]` 中的 `slug` 是**参数名**，可以是任意合法标识符。

### 2.2 捕获动态参数 params

动态段的值通过组件的 `params` **prop** 注入。页面与布局都能接收：

```tsx
// app/blog/[slug]/page.tsx
export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;      // App Router 中 params 是异步的
  return <h1>文章：{slug}</h1>;
}
```

> 注意（Next.js 15+）：`params` 以 Promise 形式传入，需用 `await` 解包。这在异步组件中很自然。

### 2.3 动态段的读取

若动态段位于更深层级，其它层级也可通过 `params` 拿到完整路径参数对象。例如：

```
app/
└── blog/
    ├── [slug]/
    │   └── page.tsx         # params: { slug }
```

嵌套时的 `params` 会**合并所有父级动态段**：

```
app/
├── [lang]/                  # 语言段
│   └── products/
│       └── [id]/page.tsx    # params: { lang, id }
```

```tsx
// app/[lang]/products/[id]/page.tsx
export default async function Product({
  params,
}: {
  params: Promise<{ lang: string; id: string }>;
}) {
  const { lang, id } = await params;
  return <p>语言={lang}，商品ID={id}</p>;
}
```

### 2.4 generateStaticParams

动态路由默认是**服务端渲染**（请求时生成）。若内容相对固定、且希望预生成部分路径，用 `generateStaticParams` **运行时静态化**：

```tsx
// app/products/[id]/page.tsx
type Params = { id: string };

// 告知 Next.js 需要预渲染哪些路径
export async function generateStaticParams(): Promise<Params[]> {
  const products = await fetchProducts(); // 从数据源取全部 id
  // 为了减小体积，也可以只取热门一部分
  return products.map((p) => ({ id: String(p.id) }));
}

export default async function Product({
  params,
}: {
  params: Promise<Params>;
}) {
  const { id } = await params;
  const p = await fetchProduct(id);
  return <h1>{p.name}</h1>;
}
```

效果：
- `generateStaticParams` 指定的路径在**构建时**生成静态 HTML（快、利于 SEO）。
- 未指定但被请求的动态路径，会**按需动态渲染**并缓存（on-demand）。
- 配合 `revalidate` 可实现 ISR（Day05 会讲）。

### 2.5 generateMetadata

为不同动态页面生成独立的 `<title>` 与 `<meta>`，对 SEO 极关键：

```tsx
import type { Metadata } from 'next';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const title = slug.replace(/-/g, ' '); // "hello-world" → "hello world"
  return {
    title: `${title} - 我的博客`,
    description: `${title} 的详细介绍。`,
  };
}

export default async function BlogPost({ params }) {
  const { slug } = await params;
  return <article>文章 {slug} 的正文...</article>;
}
```

浏览器标签页标题、搜索引擎描述都会随之改变。

### 2.6 捕获全部段 […param]

用 `[...param]` 可捕获**一个或多个**段（贪婪匹配），返回数组。适用于文档目录、层级资源等。

```
app/
└── docs/
    └── [...slug]/page.tsx   # 匹配 /docs/a、/docs/a/b、/docs/a/b/c...
```

```tsx
// app/docs/[...slug]/page.tsx
export default async function Docs({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const { slug } = await params;
  return <p>文档路径段：{slug.join(' / ')}</p>;
}
```

`/docs/getting-started/quickstart` → `slug = ['getting-started','quickstart']`。

> 可选捕获 `[[...param]]`：匹配 0 个或多个段，常用于首页与子页共享组件。

---

## 三、核心概念解析

### 3.1 动态段的嵌套组合

动态段可以与静态段、分组混合嵌套，构建任意 URL 结构：

```
app/
├── products/
│   ├── [category]/            # /products/电子
│   │   ├── page.tsx
│   │   └── [id]/page.tsx      # /products/电子/101
│   └── sale/page.tsx          # /products/sale  (静态优先于动态)
└── [lang]/home/page.tsx       # 多语言
```

**优先级**：静态段**优先于**动态段匹配（`sale` 优先于 `[category]`），这符合直觉。

### 3.2 动态布局与参数

`layout.tsx` 同样能接收 `params`，可使用动态段内容定制布局（如根据用户显示侧边栏）：

```tsx
// app/[user]/layout.tsx
export default async function UserLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ user: string }>;
}) {
  const { user } = await params;
  return (
    <div>
      <header>用户空间：{user}</header>
      {children}
    </div>
  );
}
```

### 3.3 并行路由 Parallel Routes

用槽位（`@slot`）在同一布局内**同时渲染多个相对独立的页面区域**，实现 Dashboard 多面板：

```
app/
├── layout.tsx
├── page.tsx                  # 需要显式定义（或重定向）
├── @analytics/page.tsx       # 槽位 analytics
└── @payments/page.tsx        # 槽位 payments
```

```tsx
// app/layout.tsx
export default function Layout({
  children,
  analytics,
  payments,
}: {
  children: React.ReactNode;
  analytics: React.ReactNode;
  payments: React.ReactNode;
}) {
  return (
    <div>
      {children}
      <div>{analytics}</div>
      <div>{payments}</div>
    </div>
  );
}
```

适合「分析面板」「社媒卡片」等多独立模块并存场景。

### 3.4 拦截路由 Intercepting Routes

用 `(.)`、`(..)` 等前缀**在当前布局内弹出**目标路由的局部视图，常用于「点开照片/帖子 → 弹窗查看，刷新则跳完整页面」：

```
app/
├── photos/
│   ├── page.tsx
│   ├── [id]/page.tsx
│   └── (.)[id]/page.tsx      # 拦截 /photos/:id，在列表内弹窗展示
```

### 3.5 动态段与静态页权衡

| 场景 | 推荐 |
| --- | --- |
| 内容固定、量大需预生成 | `generateStaticParams` 静态化 + ISR |
| 实时数据、个性化 | 动态渲染（默认） |
| SEO 敏感 | 服务端/静态渲染 + generateMetadata |

---

## 四、关键知识点总结

- **动态段 `[param]`**：文件夹方括号命名，匹配任意单段 URL。
- **params 异步**：Next 15+ 以 Promise 传入，需 `await` 解包。
- **generateStaticParams**：预生成路径，构建期静态化 + 请求时按需补充。
- **generateMetadata**：按动态参数生成独立标题/描述，利于 SEO。
- **[…param] 捕获全部段**：返回数组，支持任意层级资源路径。
- **优先级**：静态段优先于动态段匹配。
- **布局也可用 params**：按动态值定制共享外壳。
- **并行路由 `@slot`** 与 **拦截路由 `(.)`**：Dashboard 多面板与局部弹窗场景。

---

## 五、实战练习

### 练习一：dynamic_route.js —— 动态路由原理演示

**任务描述**：运行脚本，模拟 `[slug]`、`[...slug]` 对一组 URL 的匹配结果，并展示 `generateStaticParams` 的预生成思路。

**运行方式**

```bash
cd Code
node dynamic_route.js
```

### 练习二：博客动态文章页

在 `app/blog/[slug]/page.tsx` 实现动态文章页，读取 `params.slug` 显示文章名，并实现 `generateMetadata` 动态标题。访问 `/blog/hello-world`、`/blog/quickstart` 验证不同内容。

### 练习三：嵌套动态布局

创建 `app/[lang]/` 多语言结构：根有 `[lang]` 段，内含 `about/page.tsx`、`products/[id]/page.tsx`，用嵌套布局展示语言环境标题。可先从 `generateStaticParams` 固定 `['zh','en']` 两种语言。

---

## 下节预告

下一节 **Day05** 将进入 **渲染策略（CSR/SSR/SSG/ISR）**：深入理解客户端渲染、服务端渲染、静态生成与增量静态再生成的原理与取舍，掌握 Server Component 与 Client Component 的边界，学会按场景选择正确渲染方式。