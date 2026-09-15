# Day08 - 客户端 Hook 与交互

> 本章节系统梳理客户端交互能力。掌握 `'use client'` 组件中的核心 Hook——`useState`、`useEffect`、`useCallback`、`useMemo`、`useRef`，理解受控组件、事件交互与自定义 Hook 的实战用法，把「展示型页面」升级为「可交互应用」。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 客户端组件与交互前提](#21-客户端组件与交互前提)
  - [2.2 useState 与状态设计](#22-usestate-与状态设计)
  - [2.3 useEffect 与副作用](#23-useeffect-与副作用)
  - [2.4 useRef 与生命周期](#24-useref-与生命周期)
  - [2.5 useCallback 与 useMemo](#25-usecallback-与-usememo)
  - [2.6 自定义 Hook](#26-自定义-hook)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 受控组件与事件](#31-受控组件与事件)
  - [3.2 状态提升与共享](#32-状态提升与共享)
  - [3.3 与 Server Component 组合](#33-与-server-component-组合)
  - [3.4 交互性能提醒](#34-交互性能提醒)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **判断交互组件**：知道哪些逻辑需要客户端组件（`'use client'`）。
2. **熟练 useState/useEffect**：管理数据状态与副作用。
3. **掌握 useRef**：引用 DOM 与保持可变值。
4. **优化性能**：用 `useCallback`/`useMemo` 避免不必要重算与重渲染。
5. **封装自定义 Hook**：抽取可复用的交互逻辑。
6. **管理受控表单**：实现受控输入与事件交互。

---

## 二、理论知识

### 2.1 客户端组件与交互前提

需要**用户交互、状态、副作用、浏览器 API** 的组件，必须在文件顶部标记 `'use client'`：

```tsx
'use client';

import { useState } from 'react';

export default function Interactive() {
  return /** 可用的交互 UI */;
}
```

标记后，Next.js 会把它（连同其 import 的依赖）打包成浏览器可执行的 JS，并执行水合（Hydration）使事件生效。

> 判断口诀：**有没有 `on*` 事件 / `useState` 等 Hook / `window` 等浏览器 API？有，就需要 `'use client'`。**

### 2.2 useState 与状态设计

`useState` 管理组件内的可变数据，更新触发重渲染：

```tsx
'use client';
import { useState } from 'react';

export default function Todo() {
  const [todos, setTodos] = useState<string[]>([]);
  const [input, setInput] = useState('');

  const addTodo = () => {
    if (!input.trim()) return;
    setTodos([...todos, input.trim()]); // 不可变更新：返回新数组
    setInput('');
  };

  return (
    <div>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={addTodo}>添加</button>
      <ul>{todos.map((t, i) => <li key={i}>{t}</li>)}</ul>
    </div>
  );
}
```

状态设计要点：
- 状态**不可变更新**：数组用 `[...arr, item]`、对象用 `{...obj, key: val}`。
- **依赖旧值**用函数式更新：`setCount(c => c + 1)`，避免闭包陈旧值。
- 无关状态拆分为多个 `useState`，避免"大且全"的对象，减少无关重渲染。

### 2.3 useEffect 与副作用

`useEffect` 处理组件渲染后的外部副作用（请求、订阅、定时器、DOM 监听）：

```tsx
'use client';
import { useEffect, useState } from 'react';

export default function Countdown() {
  const [seconds, setSeconds] = useState(10);

  useEffect(() => {
    if (seconds <= 0) return;
    const id = setTimeout(() => setSeconds((s) => s - 1), 1000);
    return () => clearTimeout(id); // 清理，避免内存泄漏
  }, [seconds]);

  return <p>剩余 {seconds} 秒</p>;
}
```

依赖数组语义：
- 缺省：每次渲染后执行（慎用，易死循环）
- `[]`：仅挂载后执行一次（如首次拉取数据）
- `[a]`：a 变化后执行（并清理上一次）

### 2.4 useRef 与生命周期

`useRef` 返回一个可变的 `{ current }` 对象，可用于：

1. **引用 DOM**：操作输入框、聚焦、测量尺寸。
2. **保存可变值**：跨渲染保持，但不触发重渲染（区别于 useState）。

```tsx
'use client';
import { useRef } from 'react';

export default function Focus() {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <div>
      <input ref={inputRef} placeholder="点按钮聚焦" />
      <button onClick={() => inputRef.current?.focus()}>聚焦</button>
    </div>
  );
}
```

> 区别：`useState` 变→重渲染；`useRef` 变→不重渲染（适合定时器 id、上一次值等）。

### 2.5 useCallback 与 useMemo

**useCallback**：缓存**函数引用**，避免每次渲染都创建新函数，减少子组件因引用变化重复渲染。

```tsx
const memoAdd = useCallback((id: number) => {
  // 处理逻辑
}, [deps]);   // 依赖变化时才重新创建
```

**useMemo**：缓存**计算结果**，避免昂贵计算的重复执行。

```tsx
const filtered = useMemo(() => {
  return items.filter((i) => i.keyword.includes(q));
}, [items, q]); // 仅当 items 或 q 变化时重算
```

两者都是**性能优化**手段，不要让复杂逻辑因简单渲染而每次重算/重建。

> 提醒：滥用 useCallback/useMemo 反而增加开销。只在「子组件频繁重渲染 / 昂贵计算」时使用。

### 2.6 自定义 Hook

把可复用的交互逻辑抽成**以 `use` 开头的函数**，内部可调用其它 Hook：

```tsx
'use client';
import { useState, useCallback } from 'react';

// 自定义 Hook：受控输入，返回值 + 变更函数
function useInput(initial = '') {
  const [value, setValue] = useState(initial);
  const onChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value),
    []
  );
  const reset = useCallback(() => setValue(''), []);

  return { value, onChange, reset };
}

export default function LoginForm() {
  const email = useInput('');
  const pwd = useInput('');

  const submit = () => console.log(email.value, pwd.value);

  return (
    <div>
      <input placeholder="邮箱" value={email.value} onChange={email.onChange} />
      <input placeholder="密码" type="password" value={pwd.value} onChange={pwd.onChange} />
      <button onClick={submit}>登录</button>
    </div>
  );
}
```

自定义 Hook 让逻辑在多处复用，保持组件简洁。

---

## 三、核心概念解析

### 3.1 受控组件与事件

**受控组件**：`value` 由 React 状态控制，值始终在 React 掌控中（便于校验、联动、重置）：

```tsx
<input
  value={text}
  onChange={(e) => setText(e.target.value)}
/>
```

表单可用 `onSubmit` 阻止默认刷新；交互可用 `onClick`/`onKeyDown` 等。事件对象为 React 合成事件，跨浏览器行为一致。

### 3.2 状态提升与共享

多个组件需要同一状态时，把状态**提升**到最近的公共父组件，通过 Props 下发：

```tsx
'use client';
function Parent() {
  const [q, setQ] = useState('');
  return <><SearchBox q={q} setQ={setQ} /><ResultList q={q} /></>;
}
```

若共享层级很深，考虑 Context（Day11 深入）或状态库（Zustand）。

### 3.3 与 Server Component 组合

最佳实践是**最小化客户端边界**：尽量用 Server Component 渲染静态数据，只在需要交互的叶子节点用 `'use client'` 组件，数据通过 Props 传入（可序列化）：

```
Server Page
  └─ render 静态部分（服务端）
  └─ <ClientInteraction data={serializable} />   ← 交互部分标 'use client'
```

Server Component 可作为 children 传入客户端组件，保持性能刚度。

### 3.4 交互性能提醒

- **稳const / 函数**：交互尽量轻量，避免阻塞 UI（复杂计算用 useMemo）。
- **事件节流**：连续触发的事件（滚动、输入）用 `throttle`/`debounce`。
- **避免内存泄漏**：useEffect 记得清理订阅/定时器。

---

## 四、关键知识点总结

- **交互前提**：有事件/状态/Hook/浏览器 API 的组件需 `'use client'`。
- **useState**：管理可变数据，不可变更新，旧值用函数式更新。
- **useEffect**：处理副作用，用依赖数组控制时机，返回清理函数。
- **useRef**：引用 DOM、保存跨渲染可变值（不触发重渲染）。
- **useCallback**：缓存函数引用；**useMemo**：缓存计算结果（适时可优化）。
- **自定义 Hook**：以 `use` 开头的纯逻辑复用函数。
- **受控组件**：`value` + `onChange`，值归 React 管理。
- **组合策略**：静态数据走服务端，交互叶子标客户端，Props 传值。

---

## 五、实战练习

### 练习一：hooks_demo.js —— Hook 行为模拟演示

**任务描述**：运行脚本，模拟 useState/useRef/useMemo 的关键行为差异（重渲染 vs 不重渲染、缓存计算），帮助建立直觉。

**运行方式**

```bash
cd Code
node hooks_demo.js
```

### 练习二：Todo 组件

用 `useState` 实现一个 todo 清单（添加、删除、勾选完成），注意不可变更新与稳定 key。

### 练习三：倒计时 + 自定义 Hook

用 `useInput` 自定义 Hook 构建一个登录表单，并用 `useEffect` 实现倒计时按钮（60 秒内禁止重复点击）。

---

## 下节预告

下一节 **Day09** 将进入 **Route Handlers（API 路由）**：用 `route.ts` 在应用内定义后端接口，掌握 GET/POST、参数解析、响应构造、流式响应（SSE），并安全承载大模型 API 调用。