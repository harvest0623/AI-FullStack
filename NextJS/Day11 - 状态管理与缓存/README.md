# Day11 - 状态管理与缓存

> 本章节厘清 Next.js 中「状态」的层次。区分服务端状态（`cookies()`/`headers()`/Next Cache）与客户端界面状态（Context / Zustand / TanStack Query），掌握服务端数据缓存与按需失效，学会为不同状态选择正确的管理工具。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 状态的两种类别](#21-状态的两种类别)
  - [2.2 服务端状态读取](#22-服务端状态读取)
  - [2.3 Next Cache 缓存体系](#23-next-cache-缓存体系)
  - [2.4 客户端界面状态 Context](#24-客户端界面状态-context)
  - [2.5 状态库 Zustand](#25-状态库-zustand)
  - [2.6 服务端状态 TanStack Query](#26-服务端状态-tanstack-query)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 Context vs 状态库](#31-context-vs-状态库)
  - [3.2 服务端状态 vs 客户端状态](#32-服务端状态-vs-客户端状态)
  - [3.3 选型决策](#33-选型决策)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **区分状态类别**：明白「服务端状态」与「客户端界面状态」的区别与处理方式。
2. **读取服务端状态**：在 Server Component 中用 `cookies()`/`headers()`。
3. **理解 Next Cache**：掌握 request/segment/full route 多层缓存与失效。
4. **用 Context / Zustand 管界面状态**：为客户端组件提供全局状态。
5. **用 TanStack Query 管服务端数据**：管理获取、缓存与重取。

---

## 二、理论知识

### 2.1 状态的两种类别

Next.js 应用中的「状态」可归为两类，处理方式截然不同：

```
┌──────────────────────────────────────────────────┐
│  ① 服务端状态（Server State）                    │
│     数据库、会话、Cookie、Headers、文件/系统      │
│     → 在 .tsx(Server) 或 Server Action 读取       │
├──────────────────────────────────────────────────┤
│  ② 客户端界面状态（UI State）                    │
│     输入框、开关、预加载列表、用户交互临时数据     │
│     → 在 'use client' 中用 Context/Zustand 管理   │
└──────────────────────────────────────────────────┘
```

### 2.2 服务端状态读取

**Server Component** 可直接读取服务端状态：

```tsx
// app/dashboard/page.tsx （Server Component）
import { cookies, headers } from 'next/headers';

export default async function Dashboard() {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth_token')?.value;

  const h = await headers();
  const ua = h.get('user-agent');

  // 也可直读数据库
  // const user = await db.user.findUnique(...);

  return <p>已读取 cookie 与 header（这会触发动态渲染）</p>;
}
```

读取 `cookies()`/`headers()` 会把页面**标记为动态渲染**（SSR，不缓存为静态）。

### 2.3 Next Cache 缓存体系

Next.js 有多层缓存，需理解其层次：

| 缓存 | 位置 | 失效方式 |
| --- | --- | --- |
| **Request Memoization** | 单次请求内去重（fetch 去重） | 随请求结束自动 |
| **Data Cache** | 持久化数据缓存 | `revalidate` / `revalidateTag` / no-store |
| **Full Route Cache** | 静态 HTML 缓存 | 重新构建 / revalidate / 动态API触发 |
| **Router Cache** | 客户端导航缓存 | 导航过期 / revalidate / refresh() |

常用控制：

```tsx
// 数据缓存（Data Cache）
await fetch(url, { next: { revalidate: 60 } });         // 定时
await fetch(url, { cache: 'no-store' });                // 每次实时
await fetch(url, { next: { tags: ['products'] } });     // 标签化

// 按需失效
import { revalidatePath, revalidateTag } from 'next/cache';
revalidatePath('/products');        // 使路径缓存失效
revalidateTag('products');          // 使标签缓存失效
```

### 2.4 客户端界面状态 Context

**Context** 用于在组件树中向下传递共享数据，无需逐层 Props 透传：

```tsx
'use client';
import { createContext, useContext, useState } from 'react';

// 1. 创建 Context
const ThemeContext = createContext<{ theme: string; toggle: () => void } | null>(null);

// 2. 提供者 Provider
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState('light');
  const toggle = () => setTheme((t) => (t === 'light' ? 'dark' : 'light'));
  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

// 3. 消费步骤
```

```tsx
'use client';
import { useContext } from 'react';

export function ThemeButton() {
  const ctx = useContext(ThemeContext);   // 在子树中直接取
  return <button onClick={ctx?.toggle}>当前：{ctx?.theme}</button>;
}
```

> 注意：使用 Context 的组件仍需要 `'use client'`（State 是客户端能力）。Context 更新会引起整个 Provider 子树重渲染，价值传导频繁时用拆分/useMemo 优化。

### 2.5 状态库 Zustand

当状态较复杂、被很多组件或跨越长路径共享时，用 **Zustand**（轻量、直观）。它在 Provider 外创建 store，在任何组件直接取用：

```bash
npm install zustand
```

```tsx
// store.ts
'use client';
import { create } from 'zustand';

type ChatState = {
  messages: string[];
  isStreaming: boolean;
  addMessage: (m: string) => void;
  setStreaming: (v: boolean) => void;
};

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  setStreaming: (v) => set({ isStreaming: v }),
}));
```

```tsx
'use client';
import { useChatStore } from './store';

export function ChatBox() {
  const messages = useChatStore((s) => s.messages);  // 只取用到的，避免多余重渲染
  const addMessage = useChatStore((s) => s.addMessage);
  return <div>{messages.map((m, i) => <p key={i}>{m}</p>)}</div>;
}
```

特点：无需 Provider 包裹、selector 精确订阅、支持持久化中间件等。

### 2.6 服务端状态 TanStack Query

管理「从服务端获取、需要缓存/重取」的数据，用 **TanStack Query**（原 React Query）最合适：

```bash
npm install @tanstack/react-query
```

```tsx
'use client';
import { useQuery, useMutation, QueryClientProvider, QueryClient } from '@tanstack/react-query';

function useTodos() {
  return useQuery({
    queryKey: ['todos'],               // 缓存标识
    queryFn: () => fetch('/api/todos').then((r) => r.json()),
  });
}

function AddTodo() {
  const qc = useQueryClient();
  const mutation = useMutation({
    mutationFn: (text: string) =>
      fetch('/api/todos', { method: 'POST', body: JSON.stringify({ text }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['todos'] }), // 使列表缓存失效重取
  });
  return <button onClick={() => mutation.mutate('新事项')}>添加</button>;
}
```

价值：自动缓存、后台刷新、请求去重、错误重试、loading 状态管理，极大简化服务端数据交互。

---

## 三、核心概念解析

### 3.1 Context vs 状态库

| 维度 | Context | Zustand |
| --- | --- | --- |
| 额外依赖 | 无（内置） | 需安装 |
| 架构 | Provider 包裹 | 全局 store |
| 重渲染粒度 | 值变整棵子树重渲染 | 精确 selector 订阅 |
| 适用 | 低频全局主题/登录态 | 高频、复杂跨模块状态 |

**选型**：
- 简单、低频、层级结构清晰 → **Context** 轻量够用
- 复杂、高频、跨模块共享、需要持久化 → **Zustand**

### 3.2 服务端状态 vs 客户端状态

| 维度 | 服务端状态 | 客户端界面状态 |
| --- | --- | --- |
| 所在 | 数据库/会话/Cookie/Headers | 组件内变量/输入/开关 |
| 读取位置 | Server Component / Server Action | `'use client'` 组件 |
| 持久性 | 服务端持久化 | 客户端临时，刷新即失 |
| 管理工具 | 数据库/ORM + Next Cache | Context / Zustand |
| 时效 | 依赖服务端刷新 | 即时交互 |

### 3.3 选型决策

1. 数据来自**服务端、需缓存/重取** → **TanStack Query**
2. 组件树内**共享低频全局状态** → **Context**
3. **复杂跨模块、高频更新** → **Zustand**
4. 只要**单个组件内部**状态 → 原生 `useState`

---

## 四、关键知识点总结

- **两类状态**：服务端状态（Server State）与客户端界面状态（UI State）分开治理。
- **服务端读取**：Server Component 中用 `cookies()`/`headers()`/数据库，读取会触发动态渲染。
- **缓存分层**：Request Memoization / Data Cache / Full Route Cache / Router Cache。
- **失效控制**：`revalidate`/`revalidateTag`/`revalidatePath`/`no-store`/`refresh()`。
- **Context**：Provider 包裹向下传，适合低频全局状态。
- **Zustand**：全局 store 直接取用，精确订阅，适合复杂高频状态。
- **TanStack Query**：管理服务端数据缓存、重取、去重。
- **选型**：Query(服务端数据) / Context(树内低频) / Zustand(全局复杂) / useState(局部)。

---

## 五、实战练习

### 练习一：use_state_context.js —— 状态角色梳理

**任务描述**：运行脚本，用对比示例梳理「服务端状态」与「客户端界面状态」，并演示 Context / Zustand / Query 的角色分工。

**运行方式**

```bash
cd Code
node use_state_context.js
```

### 练习二：Context 主题切换

用 Context + `useState` 实现主题 ThemeProvider，让多个组件读取并切换主题。

### 练习三：Zustand 聊天 store

安装 Zustand，创建聊天消息 store，实现多个组件共享 messages 并选择性子订阅更新。

---

## 下节预告

下一节 **Day12** 将进入 **样式方案与 UI**：掌握全局 CSS、CSS Modules、Tailwind CSS、CSS-in-JS 等方案，配合响应式设计、主题与图片字体优化，构建专业美观的界面。