# Day02 - React 组件模型与 JSX

> 本章节夯实 Next.js 的「前端组件层」基础。组件是 React 的核心，也是 Next.js App Router 的基本单元；我们将掌握函数组件、JSX、状态与副作用、事件与列表渲染，为区分服务端/客户端组件打基础。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 组件化思维](#21-组件化思维)
  - [2.2 JSX 语法](#22-jsx-语法)
  - [2.3 Props 属性传递](#23-props-属性传递)
  - [2.4 状态 useState](#24-状态-usestate)
  - [2.5 副作用 useEffect](#25-副作用-useeffect)
  - [2.6 事件处理](#26-事件处理)
  - [2.7 条件与列表渲染](#27-条件与列表渲染)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 Hooks 规则](#31-hooks-规则)
  - [3.2 受控与非受控组件](#32-受控与非受控组件)
  - [3.3 组件的拆分与组合](#33-组件的拆分与组合)
  - [3.4 与 Next.js 的衔接](#34-与-nextjs-的衔接)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **用组件化思维组织界面**：把 UI 拆分为可复用、可组合的独立组件。
2. **熟练编写 JSX**：理解 JSX 是 JS 的语法扩展，能在其中嵌入表达式与逻辑。
3. **掌握 Props 单向数据流**：父组件通过 Props 给子组件传值。
4. **使用状态与副作用 Hook**：用 `useState` 管理数据、`useEffect` 处理副作用。
5. **掌握事件与列表渲染**：处理用户交互，动态渲染数据列表。
6. **理解 Hooks 使用规则**：避免条件调用等常见错误。

---

## 二、理论知识

### 2.1 组件化思维

**组件（Component）** 是 React 中可复用的、独立的一段 UI 片段，它把界面、逻辑、样式封装在一起，以函数/类的形式存在。现代 React 使用**函数组件**。

组件让开发像「搭积木」：

```
        ┌───────────── App ─────────────┐
        │                               │
   ┌────┴─────┐                    ┌────┴─────┐
   │ Header    │                    │ ChatPanel│
   └───────────┘                    └──────────┘
        │
   ┌────┴────────────────┐
   │ Nav  │   UserCard   │   (可复用子组件)
   └──────┴──────────────┘
```

**组件化带来三大好处**：可复用（写一次用多处）、可维护（改动隔离局部）、可测试（独立验证组件行为）。

### 2.2 JSX 语法

JSX（JavaScript XML）是一种**语法扩展**，看起来像 HTML，本质上编译为 `React.createElement()` 调用。它让你在 JS 代码中「写界面」。

```tsx
// 这不是普通的 HTML，而是 JSX（TSX 是支持 TS 类型的 JSX）
const greeting = (
  <div className="card">
    <h2>Hello</h2>
    <p>Welcome to Next.js</p>
  </div>
);
```

JSX 核心规则：

| 规则 | 示例 |
| --- | --- |
| **嵌入表达式** | `{name}`、`{1 + 2}`、`{condition && <p/>}` |
| **使用 className** | 用 `className` 而非 `class`（因为是 JS 关键字） |
| **表达式必须返回单一根元素** | 可用 `<Fragment>` 或 `<>...</>` 包裹 |
| **属性用驼峰命名** | `onClick`、`maxLength`（DOM 属性驼峰化） |
| **所有标签必须闭合** | `<img />`、`<br />` |

JSX 中「`{}` 大括号」可嵌入任意 JS 表达式，这是 JSX 与 HTML 最关键的区别：

```tsx
const name = 'AI 学习者';
const isLogged = true;

export default function Greeting() {
  return (
    <div>
      <h1>{isLogged ? `您好，${name}` : '请登录'}</h1>
      <p>本次渲染时间：{new Date().toLocaleTimeString()}</p>
    </div>
  );
}
```

### 2.3 Props 属性传递

**Props（属性）** 是父组件向子组件传递数据的单向通道，子组件不可修改 Props（只读）。

```tsx
// 子组件：声明接收的 Props 类型
type UserCardProps = {
  name: string;
  age?: number; // 可选
  role: 'admin' | 'user';
};

function UserCard({ name, age, role }: UserCardProps) {
  return (
    <div>
      <strong>{name}</strong>
      <span>{role}</span>
      {age !== undefined && <em>{age} 岁</em>}
    </div>
  );
}

// 父组件：通过 JSX 属性传值
export default function Page() {
  return <UserCard name="Tom" role="admin" age={18} />;
}
```

要点：
- Props **只读**，单向流动，杜绝数据回流造成混乱。
- **children**：特殊 Props，用于把子元素插入组件内部某个位置。
- 受控组件中，Props 常与状态配合，父传数据、回调传事件。

### 2.4 状态 useState

**State（状态）** 是组件内部可变的数据。修改状态会触发组件**重新渲染**。`useState` 返回 `[值, 更新函数]`：

```tsx
'use client'; // 使用状态即为客户端组件
import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0); // 初始值 0

  return (
    <div>
      <p>当前计数：{count}</p>
      <button onClick={() => setCount(count + 1)}>+1</button>
    </div>
  );
}
```

关键认知：
- `setCount` 更新，React 重新执行组件函数，生成新 UI。
- **状态不可变（immutable）**：要更新数组/对象，应返回新引用：

```tsx
const [items, setItems] = useState<number[]>([]);
// 正确：返回新数组
setItems([...items, items.length]);

// 错误：原地 push 不触发重渲染
// items.push(items.length); setItems(items);
```

- 性能优化：多个无关状态应拆成多个 `useState` 而非一个大对象。

### 2.5 副作用 useEffect

**Effect（副作用）** 指组件渲染后需要执行的外部操作：发请求、订阅事件、操作 DOM、设置定时器。`useEffect` 在渲染提交后执行：

```tsx
'use client';
import { useEffect, useState } from 'react';

export default function Users() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    // 依赖数组为空：组件挂载后执行一次
    fetch('/api/users')
      .then((r) => r.json())
      .then(setUsers);
  }, []); // [] 表示仅挂载时执行

  return <ul>{users.map((u) => <li key={u.id}>{u.name}</li>)}</ul>;
}
```

`useEffect` 的依赖数组决定何时执行：

| 依赖 | 执行时机 |
| --- | --- |
| 缺省 | 每次渲染后都执行 |
| `[]` | 仅挂载后执行一次 |
| `[a, b]` | a 或 b 变化时执行 |

**清理函数**：需要在卸载时清理定时器/订阅，返回清理函数：

```tsx
useEffect(() => {
  const id = setInterval(() => setTime(new Date()), 1000);
  return () => clearInterval(id); // 组件卸载时清理
}, []);
```

> 提示：在 Next.js 的**Server Component** 中不能使用 useEffect（那是在客户端才有的能力）；这类交互逻辑要放到 `'use client'` 组件里。Day05/Day08 会深入。

### 2.6 事件处理

React 使用**合成事件**（SyntheticEvent），命名采用驼峰，语义与原生 DOM 事件对齐但不完全相同：

```tsx
'use client';
import { useState } from 'react';

export default function Form() {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault(); // 阻止表单默认提交刷新
    console.log('提交内容：', text);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="输入内容"
      />
      <button type="submit">提交</button>
    </form>
  );
}
```

常用事件：`onClick`、`onChange`、`onSubmit`、`onKeyDown`、`onFocus` 等。事件处理器可接收事件对象参数 `(e)`，并用 `e.preventDefault()` / `e.stopPropagation()` 控制行为。

### 2.7 条件与列表渲染

**条件渲染**：用 JS 逻辑表达式控制是否渲染：

```tsx
{isLogged ? <Welcome /> : <LoginButton />}  // 条件三目
{users.length === 0 && <p>暂无数据</p>}      // 逻辑与短路
{isLoading ? '加载中...' : <Data />}          // 三元
```

**列表渲染**：用 `map()` 生成列表，每个子元素必须提供唯一的 `key`，用于精确比对更新：

```tsx
const lessons = [
  { id: 1, title: '简介与搭建' },
  { id: 2, title: '组件与 JSX' },
];

export default () => (
  <ul>
    {lessons.map((l) => (
      <li key={l.id}>{l.title}</li>
    ))}
  </ul>
);
```

`key` 必须是稳定、唯一的标识（常用 id），不要用数组索引（顺序变化会导致状态错乱）。

---

## 三、核心概念解析

### 3.1 Hooks 规则

Hooks（`useState`、`useEffect` 等）必须遵守两条铁律：

1. **只能在顶层调用**：不能放在 `if`、循环、嵌套函数里，否则每次渲染调用顺序不一致，React 无法对应状态。
2. **只能在 React 函数中调用**：函数组件或自定义 Hook 内部，不能在普通 JS 函数中使用。

```tsx
// 错误示例：条件中调用 Hook（不合法）
function Bad({ cond }) {
  if (cond) {
    const [x, setX] = useState(0); // ❌ 违反调用铁律
  }
}
```

### 3.2 受控与非受控组件

- **受控组件**：表单值由 React 状态控制，`value` + `onChange` 双向绑定，值始终在 React 掌控中（推荐，便于校验）。
- **非受控组件**：值由 DOM 自身维护，用 `ref` 读取，代码少但难协作。

### 3.3 组件的拆分与组合

- **拆分的时机**：一段 UI 复用多次、逻辑变复杂、为可测试性时拆分。
- **组合模式**：通过 `children` 与具名 Props 组合，而非大量 Props 透传：

```tsx
// 容器组件用 children 接收内部内容
function Card({ title, children }) {
  return (
    <section>
      <h3>{title}</h3>
      {children}
    </section>
  );
}

// 使用：把任意 JSX 作为 children 传入
<Card title="AI 对话">
  <ChatInput />
  <ChatMessages />
</Card>
```

### 3.4 与 Next.js 的衔接

- React 组件是 Next.js 页面的基础，`app/page.tsx` 本身就是一个 React 组件。
- Next.js 引入 **服务端组件（RSC）**：默认组件在服务端渲染，不能用 Hooks；需要交互时加 `'use client'` 变成客户端组件。
- 因此 Day02 学到的 `useState` / `useEffect` 属于**客户端组件**范畴，与 `'use client'` 强相关（Day05 详述）。

---

## 四、关键知识点总结

- **组件**是 React 的基本单元，函数组件是现代主流写法。
- **JSX** 是 JS 语法扩展，`{}` 内嵌表达式，`className` 代替 `class`。
- **Props** 单向只读传递数据，`children` 实现组合。
- **useState** 管理可变状态，更新状态触发重渲染，修改要保持不可变。
- **useEffect** 处理副作用，用依赖数组控制时机，可返回清理函数。
- **事件**用驼峰命名与合成事件对象，表单常用受控组件。
- **渲染**支持条件渲染（三目/短路）与列表渲染（map + 稳定 key）。
- **Hooks 铁律**：顶层调用、函数组件内调用。
- **衔接 Next.js**：交互状态是客户端能力，对应 `'use client'` 组件。

---

## 五、实战练习

以下练习对应 `Code/` 下的文件，讲解可运行，示例需放入真实项目中。

### 练习一：intro_render.js —— 组件/JSX 核心逻辑演示

**任务描述**：运行 Node 脚本，模拟展示 Props 单向传递、状态更新触发重渲染、条件与列表渲染等核心逻辑（用纯 JS 模拟 React 行为，便于离线理解）。

**运行方式**

```bash
cd Code
node intro_render.js
```

### 练习二：counter.tsx —— 计数器组件

**任务描述**：把 `Code/counter.tsx` 放入 `app/` 下（建议创建 `app/counter/page.tsx`），运行 dev 测试点击 +1 观察状态更新。验证了 useState 与事件处理。

### 练习三：用户列表组件

结合条件渲染、`map()`、Props 与 None 数据，动手实现一个展示用户列表的小组件（可参考 README 2.5/2.7 的写法自建）。

---

## 下节预告

下一节 **Day03** 将进入 **路由系统与页面**：深入 App Router 的约定式路由，掌握 `page.tsx`、`layout.tsx`、`Link` 导航、嵌套路由与分组路由，让组件真正组织成可访问的多页面应用。