# Day07 - 流式渲染与加载状态

> 本章节让页面「不仅快，而且显得快」。掌握 `Suspense` 流式渲染、`loading.tsx` 骨架屏、`error.tsx` 错误兜底与 `not-found.tsx` 404 体验，把复杂的异步 UI 拆成渐进呈现的片段，大幅提升首屏体验与健壮性。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 为什么需要流式渲染](#21-为什么需要流式渲染)
  - [2.2 Suspense 基础](#22-suspense-基础)
  - [2.3 loading.tsx 骨架屏](#23-loadingtsx-骨架屏)
  - [2.4 error.tsx 错误边界](#24-errortsx-错误边界)
  - [2.5 not-found.tsx 404 体验](#25-not-foundtsx-404-体验)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 流式尽早呈现](#31-流式尽早呈现)
  - [3.2 Suspense 边界的粒度](#32-suspense-边界的粒度)
  - [3.3 错误边界的作用域](#33-错误边界的作用域)
  - [3.4 组合：loading + error + not-found](#34-组合loading--error--not-found)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **理解流式渲染价值**：为何能「尽快让用户看到内容」。
2. **使用 Suspense**：用流式边界包裹异步组件，独立呈现加载态。
3. **制作 loading.tsx 骨架屏**：为整段路由提供统一的加载 UI。
4. **配置 error.tsx / not-found.tsx**：优雅处理异常与 404，避免白屏。
5. **综合运用**：为真实页面搭好「加载 + 出错 + 未找到」三态。

---

## 二、理论知识

### 2.1 为什么需要流式渲染

传统 SSR 需等**整页**数据齐备才一次性返回 HTML。若某个数据很慢，整页都在等（阻塞首屏，出现「白屏」或占位）。

**流式渲染（Streaming SSR）**：把页面拆成多个片段，哪个数据先好就先渲染返回哪个。用户能**渐进**看到内容——先看到外壳/骨架，再逐块填充真实数据。

```
传统 SSR：        [-------等待所有数据-------]整页返回
流式 SSR：  [外壳/骨架][数据A][数据B][数据C] 逐块返回
```

对慢数据（如 AI 请求）尤为关键。这也是 AI 对话「打字机」体验背后的机制。

### 2.2 Suspense 基础

**`Suspense`** 是 React 提供的流式边界组件。用它包裹**异步子组件**，在子组件数据未就绪时渲染一个 `fallback`：

```tsx
import { Suspense } from 'react';

export default function Page() {
  return (
    <main>
      <Header />                 {/* 立即可渲染，不阻塞 */}

      {/* 数据未就绪时显示 loading，就绪后渲染真实内容 */}
      <Suspense fallback={<LoadingSpinner />}>
        <SlowComponent />
      </Suspense>

      <Footer />
    </main>
  );
}
```

行为：`Header`/`Footer` 先渲染返回；`SlowComponent` 的数据还在取时，先展示 `fallback`（骨架/菊花），取完再替换为真实组件。

### 2.3 loading.tsx 骨架屏

`loading.tsx` 是**文件约定**：放在某路由目录下，即为该段**默认的 Suspense 边界 + fallback**，无需手写 `<Suspense>`：

```
app/
├── blog/
│   ├── layout.tsx
│   ├── page.tsx        # /blog
│   ├── loading.tsx     # 访问 /blog 时的加载 UI
│   └── [slug]/page.tsx
```

```tsx
// app/blog/loading.tsx
export default function Loading() {
  return (
    <div className="skeleton">
      <p>正在加载文章列表...</p>
      {/* 可以放骨架屏：灰色色块占位 */}
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} style={{ height: 60, background: '#eee', margin: 8 }} />
      ))}
    </div>
  );
}
```

一个目录下既有 `page.tsx` 又有 `loading.tsx` 时，页面数据未就绪会先展示 `loading.tsx`，就绪后替换。

> `loading.tsx` 本质上等价于「包住整个 page 的 Suspense fallback」，是最简洁的整段加载方案。

### 2.4 error.tsx 错误边界

**`error.tsx`** 是该路由段内的**错误边界**：当该段渲染或数据请求抛错时展示，避免整页白屏/崩溃。

```tsx
// app/blog/error.tsx
'use client';     // error 组件必须是 Client Component
import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // 这里可上报错误日志
    console.error(error);
  }, [error]);

  return (
    <div role="alert">
      <h2>出错了</h2>
      <p>{error.message}</p>
      <button onClick={reset}>重试</button>  {/* reset 重新渲染该段 */}
    </div>
  );
}
```

要点：
- `error.tsx` **必须是 Client Component**（`'use client'`）。
- 通过 `reset` 让用户重试；通过 `error` 拿错误信息并上报。
- 错误边界**不会**捕获布局自身错误（布局错误需用根 layout 的 `global-error.tsx`）。

### 2.5 not-found.tsx 404 体验

**`not-found.tsx`** 展示「未找到」页面，可用 `notFound()` 主动触发：

```tsx
// app/blog/[slug]/page.tsx —— 主动触发 404
import { notFound } from 'next/navigation';

export default async function BlogPost({ params }) {
  const { slug } = await params;
  const post = await getPost(slug);

  if (!post) {
    notFound(); // 渲染最近的 not-found.tsx
  }
  return <article>{post.content}</article>;
}
```

```tsx
// app/blog/[slug]/not-found.tsx —— 局部的 404 UI
export default function NotFound() {
  return (
    <div>
      <h2>文章不存在</h2>
      <p>404 - 您访问的文章不存在或已被删除。</p>
    </div>
  );
}
```

未命中任何路由（如 `/xxxxx`）时，渲染 `app/not-found.tsx`（全局 404）。

---

## 三、核心概念解析

### 3.1 流式尽早呈现

何时用流式：
- 页面含**一个或多个慢数据**片段，不希望整页等待时
- 既有「立即可见」的部分，又有「需等待」的部分时

实现方式：
- 用 `<Suspense>` 包裹慢的异步子组件
- 或直接用 `loading.tsx` 覆盖整段

### 3.2 Suspense 边界的粒度

**粒度越小，流式越细、体验越好，但代码越碎**。平衡取舍：

```tsx
// 粗粒度：整个数据区一个边界（简单，但一起等待）
<Suspense fallback={<Skeleton />}>
  <AllData />
</Suspense>

// 细粒度：分开边界，各自独立加载（更好）
<Suspense fallback={<PostsSkeleton />}>
  <LatestPosts />
</Suspense>
<Suspense fallback={<ChartSkeleton />}>
  <StatsChart />
</Suspense>
```

### 3.3 错误边界的作用域

`error.tsx` 的捕获范围是**同目录及其子树**，向上传播（若无更近边界则逐级向上）。因此可按模块粒度精细化设计错误 UI：

```
app/
├── error.tsx               # 全局错误
├── blog/
│   └── error.tsx           # 博客模块错误
└── dashboard/error.tsx     # 看板错误
```

### 3.4 组合：loading + error + not-found

一个健壮的路由段通常四件套齐备：

```
app/
├── page.tsx           # 页面内容
├── loading.tsx        # 加载态（骨架屏）
├── error.tsx          # 出错态（可重试）
└── not-found.tsx      # 数据未找到（404）
```

四者配合实现「加载中 → 内容 / 出错 / 404」的完整用户旅程。

---

## 四、关键知识点总结

- **流式渲染**：分段返回，数据好的先展示，提升感知性能。
- **Suspense**：流式边界，`fallback` 渲染加载占位。
- **loading.tsx**：路由段的默认加载骨架屏（等效整段 Suspense fallback）。
- **error.tsx**：错误边界，必须 `'use client'`，可用 `reset` 重试。
- **not-found.tsx**：404 页面，配合 `notFound()` 主动触发。
- **global-error.tsx**：根布局错误兜底（布局自身出错）。
- **粒度权衡**：Suspense 边界越小流式越细，但代码更碎片。

---

## 五、实战练习

### 练习一：streaming.js —— 流式渲染时序演示

**任务描述**：运行脚本，展示传统 SSR（整页等待）与流式 SSR（逐块呈现）的时间线差异，帮助理解为何流式更友好。

**运行方式**

```bash
cd Code
node streaming.js
```

### 练习二：为博客加 loading 骨架屏

给 `app/blog/` 目录创建 `loading.tsx`（骨架屏占位），并给 `app/blog/[slug]/` 加上 `error.tsx`（可重试）与 `not-found.tsx`。用 `notFound()` 处理不存在的文章。

### 练习三：细粒度 Suspense

在 Dashboard 页面用多个 `<Suspense>` 分别包裹「文章列表」与「统计图表」两个异步区，观察各自独立出现加载态。

---

## 下节预告

下一节 **Day08** 将进入 **客户端 Hook 与交互**：系统梳理 `useState`、`useEffect`、`useCallback`、`useMemo` 及自定义 Hook，掌握受控组件、事件交互与客户端状态管理，把「展示型页面」升级为「可交互应用」。