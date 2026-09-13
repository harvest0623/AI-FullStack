# Day06 - 导航与数据获取

> 本章节落实「页面之间如何跳转」与「数据如何加载」两大主干。掌握 `Link` 预取与客户端导航、`useRouter`/`usePathname` 编程式导航，以及服务端组件中 `fetch` 的缓存、去重与并行请求模式，构建高效的数据加载链路。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 导航方式总览](#21-导航方式总览)
  - [2.2 Link 组件与预取](#22-link-组件与预取)
  - [2.3 useRouter 编程式导航](#23-userouter-编程式导航)
  - [2.4 usePathname 与 useSearchParams](#24-usepathname-与-usesearchparams)
  - [2.5 服务端数据获取](#25-服务端数据获取)
  - [2.6 fetch 缓存与去重](#26-fetch-缓存与去重)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 并行数据请求](#31-并行数据请求)
  - [3.2 顺序数据依赖](#32-顺序数据依赖)
  - [3.3 从服务端到客户端的传值](#33-从服务端到客户端的传值)
  - [3.4 错误与加载态配合](#34-错误与加载态配合)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **用 Link 做客户端导航**：理解预取机制带来的丝滑体验。
2. **编程式导航**：用 `useRouter` 处理跳转时机。
3. **读取当前路径与参数**：用 `usePathname`/`useSearchParams` 实现高亮等。
4. **服务端获取数据**：在 Server Component 中直接 `await fetch`。
5. **管理缓存与去重**：掌握 `revalidate`/`cache`/`tags` 与请求合并。

---

## 二、理论知识

### 2.1 导航方式总览

Next.js 中页面跳转有两种模式：

| 方式 | 组件/API | 适用 |
| --- | --- | --- |
| `<Link>` | 声明式 | 导航链接、菜单 |
| `useRouter().push()` | 编程式 | 表单提交后、条件跳转 |

两者都是**客户端导航**：切换视图不整页刷新，且自动**预取/预加载**目标数据，体验接近原生 App。

### 2.2 Link 组件与预取

`Link` 是导航首选。当链接元素进入**视口**，Next.js 自动**预取（Prefetch）**目标页面的数据与代码：

```tsx
import Link from 'next/link';

export default function Nav() {
  return (
    <nav>
      <Link href="/">首页</Link>
      <Link href="/about?from=nav">关于</Link>
      <Link href="/blog/hello-world">文章</Link>
    </nav>
  );
}
```

要点：
- 预取让点击后几乎**瞬时**切换。
- 静态页面预取完整内容；动态页面预取可共享的布局部分。
- 可用 `prefetch={false}` 关闭某链接的预取（低频入口）。

### 2.3 useRouter 编程式导航

```tsx
'use client';
import { useRouter } from 'next/navigation';

export default function SubmitButton() {
  const router = useRouter();

  const handleSubmit = () => {
    // ... 提交逻辑
    router.push('/success');   // 跳转
    // router.replace('/x');   // 替换历史（不留下返回记录）
    // router.back();          // 回退
    // router.refresh();       // 刷新当前路由
  };

  return <button onClick={handleSubmit}>提交</button>;
}
```

常用方法：`router.push` / `router.replace` / `router.back` / `router.forward` / `router.refresh` / `router.prefetch`。

### 2.4 usePathname 与 useSearchParams

```tsx
'use client';
import { usePathname, useSearchParams } from 'next/navigation';

export default function NavHighlight() {
  const pathname = usePathname();         // 如 /about
  const search = useSearchParams();       // 查询参数

  return <p>当前路径：{pathname}，query: {search.get('from')}</p>;
}
```

> `useSearchParams` 会触发动态渲染（依赖运行时 URL）。仅对需要实时读取 query 的客户端组件用。

### 2.5 服务端数据获取

**最佳实践**是直接用 **Server Component** `await` 数据——避免客户端 loading 与额外请求：

```tsx
// app/dashboard/page.tsx  （默认 Server Component）
export default async function Dashboard() {
  const user = await getUser();            // 假想数据函数
  const stats = await getStats();

  return (
    <main>
      <h1>欢迎，{user.name}</h1>
      <p>本月调用次数：{stats.count}</p>
    </main>
  );
}
```

好处：数据在服务端取完再渲染，返回的已是最终 HTML，无客户端猜心思。

### 2.6 fetch 缓存与去重

Next.js 让 `fetch` 默认优先做**静态渲染**，并自动**去重**——同一请求在多次渲染间结果共享：

```tsx
// 默认：静态化优先，自动去重缓存
await fetch('https://api.example.com/items');

// 定时重新验证（ISR）
await fetch('https://api.example.com/items', { next: { revalidate: 60 } });

// 完全动态（每次实时）
await fetch('https://api.example.com/items', { cache: 'no-store' });

// 标签缓存，配合按需刷新
await fetch('https://api.example.com/items', { next: { tags: ['items'] } });
```

**去重**：若两处用相同 URL 请求，Next.js 只发一次，复用结果，避免重复网络开销。

---

## 三、核心概念解析

### 3.1 并行数据请求

多个**互不依赖**的请求应并行发起，避免串行等待：

```tsx
// ✅ 并行：同时发起，总时长 = 最慢那个
export default async function Page() {
  const [user, posts, stats] = await Promise.all([
    getUser(),
    getPosts(),
    getStats(),
  ]);
  return <Dashboard user={user} posts={posts} stats={stats} />;
}

// ❌ 串行：一个等一个，总时长累加
// const user = await getUser();
// const posts = await getPosts(user);   // 依赖 user 才必须串行
```

### 3.2 顺序数据依赖

若后一个请求需要前一个结果，只能串行（顺序 await）或借助 Suspense 按需渲染（Day07 会优化）：

```tsx
export default async function Profile() {
  const user = await getUser(session.userId); // 先取用户
  const orders = await getOrders(user.id);    // 依赖 user.id
  return <Orders orders={orders} />;
}
```

### 3.3 从服务端到客户端的传值

Server Component 产出的数据要交给客户端组件，Props 是唯一通道。注意**可序列化**才可传递（函数、Date 等不能直接传）：

```tsx
// Server Component
export default async function Page() {
  const data = await getData();
  return <ClientTable data={data} />; // data 需可序列化
}
```

```tsx
'use client';
export default function ClientTable({ data }) {
  return <table>{data.map((r) => <tr key={r.id}><td>{r.name}</td></tr>)}</table>;
}
```

### 3.4 错误与加载态配合

即便数据在服务端取，首次请求仍有网络耗时。用 `loading.tsx`（全段）或 `Suspense` 包裹局部异步组件实现流式呈现（Day07 深入）：

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return <p>加载中...</p>;
}
```

---

## 四、关键知识点总结

- **Link 客户端导航 + 自动预取**：视口内链接预加载目标数据。
- **useRouter**：`push`/`replace`/`back`/`refresh` 等编程式导航。
- **usePathname / useSearchParams**：读当前路径与查询参数。
- **服务端取数优先**：Server Component 中 `await fetch`，返回完整 HTML。
- **缓存控制**：`revalidate`（定时）/ `cache:'no-store'`（实时）/ `tags`（按需）。
- **请求去重**：相同 URL 自动合并，避免重复网络开销。
- **并行请求**：`Promise.all` 减少串行等待。
- **序列化传值**：Server → Client 只能传可序列化数据（Props）。

---

## 五、实战练习

### 练习一：nav_data.js —— 导航与缓存逻辑演示

**任务描述**：运行脚本，演示 Link/编程式导航 API 集合、fetch 缓存选项差异，以及 Promise.all 并行 vs 串行的耗时对比。

**运行方式**

```bash
cd Code
node nav_data.js
```

### 练习二：实现带高亮的导航

用 `usePathname` 在导航栏高亮当前激活项，并用 `Link` 搭建几组页面链接，实时观察高亮变化。

### 练习三：服务端渲染数据页

创建 `app/products/page.tsx`，用 Server Component `await` 一个模拟数据源（或 fetch 真实 API），渲染商品列表，并对比 `revalidate: 60` 与 `cache:'no-store'` 的不同表现。

---

## 下节预告

下一节 **Day07** 将进入 **流式渲染与加载状态**：掌握 `Suspense`、`loading.tsx`、`error.tsx`、`not-found.tsx` 与流式 SSR，用骨架屏与渐进式渲染大幅提升首屏体验与页面健壮性。