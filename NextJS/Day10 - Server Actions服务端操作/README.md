# Day10 - Server Actions（服务端操作）

> 本章节掌握 Next.js 的「HTML 增强」能力——Server Actions。用 `'use server'` 直接定义服务端函数，表单与按钮无需手动调用 API 即可安全执行后端逻辑，并结合 `revalidatePath` 刷新数据、表单校验与乐观更新，构建高效的变更操作。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 Server Actions 是什么](#21-server-actions-是什么)
  - [2.2 定义与调用方式](#22-定义与调用方式)
  - [2.3 表单中使用 form action](#23-表单中使用-form-action)
  - [2.4 绑定额外参数 bind](#24-绑定额外参数-bind)
  - [2.5 revalidatePath 刷新数据](#25-revalidatepath-刷新数据)
  - [2.6 返回新状态 useActionState](#26-返回新状态-useactionstate)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 表单校验与错误处理](#31-表单校验与错误处理)
  - [3.2 乐观更新](#32-乐观更新)
  - [3.3 与 Route Handler 的选择](#33-与-route-handler-的选择)
  - [3.4 安全注意](#34-安全注意)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **理解 Server Actions 理念**：为何能「渐进增强」地处理表单与变更。
2. **定义服务端函数**：用 `'use server'` 编写并在表单/按钮中调用。
3. **处理表单提交流程**：掌握 `formData`、绑定参数与错误返回。
4. **刷新页面数据**：用 `revalidatePath`/`revalidateTag` 使新数据生效。
5. **实现校验与乐观更新**：提升表单体验并保持状态一致。

---

## 二、理论知识

### 2.1 Server Actions 是什么

**Server Actions** 是 Next.js 提供的在**服务端执行的异步函数**。它们从客户端（表单、按钮）安全地发起，在服务端运行（可访问私密环境变量、数据库），完成后相关界面自动更新。

核心价值：
- **无 JS 也能提交**：基于原生 HTML 表单的 `action`，浏览器原生能力即可工作（渐进增强）。
- **免写 API 样板**：不用再为每个操作定义 `route.ts` + `fetch`，直接调函数。
- **自动更新**：配合 `revalidatePath`，提交后页面数据自动刷新。

```tsx
'use server';   // 声明此文件的导出都是 Server Action
```

### 2.2 定义与调用方式

**方式一：独立文件**（推荐，声明 `'use server'`）：

```tsx
// app/actions.ts
'use server';

import { revalidatePath } from 'next/cache';

export async function createTodo(formData: FormData) {
  const text = formData.get('text')?.toString() ?? '';
  // 服务端逻辑：写入数据库等
  await saveTodo({ text });
  revalidatePath('/todos'); // 让列表页面数据刷新
}
```

在组件中调用：

```tsx
// app/todos/page.tsx
import { createTodo } from '@/app/actions';

export default function Todos() {
  return (
    <form action={createTodo}>       {/* 直接当 action 用 */}
      <input name="text" placeholder="新事项" />
      <button type="submit">创建</button>
    </form>
  );
}
```

**方式二：客户端组件中手动调用**：

```tsx
'use client';
import { createTodo } from '@/app/actions';

export function Button() {
  const onClick = async () => {
    const formData = new FormData();
    formData.set('text', '手动触发');
    await createTodo(formData);   // 直接 await 调用
  };
  return <button onClick={onClick}>触发</button>;
}
```

### 2.3 表单中使用 form action

服务端组件中，原生 `<form action={serverAction}>` 即可在提交时把表单字段收集为 `FormData` 传给函数：

```tsx
export default function AddForm() {
  return (
    <form action={createTodo}>
      <input name="text" required placeholder="请输入" />
      <button>提交</button>
    </form>
  );
}
```

表单里每个带 `name` 的字段都会进入 `FormData`，服务端用 `formData.get('text')` 读取。

> 表单提交后 Next.js 自动**刷新**被 `revalidatePath` 标记的路由，展示最新数据。

### 2.4 绑定额外参数 bind

若 action 需要额外参数（如某个 id），用 `.bind` 预绑定（避免把 id 放进表单或依赖客户端状态）：

```tsx
// 定义接收 id 的 action
export async function deleteTodo(id: number, formData: FormData) {
  await removeTodo(id);
  revalidatePath('/todos');
}
```

```tsx
// 通过 bind 把 id 捆上去（id 在前，formData 在后）
<form action={deleteTodo.bind(null, todo.id)}>
  <button>删除</button>
</form>
```

### 2.5 revalidatePath 刷新数据

Server Action 修改数据后，用 `revalidatePath` / `revalidateTag` 让缓存失效并重新渲染：

```tsx
import { revalidatePath, revalidateTag } from 'next/cache';

export async function createTodo(formData: FormData) {
  const text = formData.get('text')?.toString() ?? '';
  await saveTodo({ text });

  revalidatePath('/todos');       // 按路径刷新（页面/接口）
  // revalidateTag('todos');      // 按数据标签刷新（配合 fetch 的 tags）
}
```

调用后，受影响页面会为**下次请求**重新获取最新数据。

### 2.6 返回新状态 useActionState

用 `useActionState`（React 19+）把 action 包装为「可返回表单状态」的函数，实现校验错误回显：

```tsx
'use client';
import { useActionState } from 'react';
import { submitForm } from '@/app/actions';

const [state, action, isPending] = useActionState(submitForm, {
  error: null,
});

// state 是 action 返回的结果，isPending 表示提交中
// 服务端 submitForm 返回 { error: string | null }
```

在服务端 action 中返回校验结果：

```tsx
'use server';
export async function submitForm(prev, formData) {
  const email = formData.get('email')?.toString() ?? '';
  if (!email.includes('@')) {
    return { error: '邮箱格式不正确' };
  }
  await saveUser({ email });
  return { error: null };
}
```

---

## 三、核心概念解析

### 3.1 表单校验与错误处理

体验良好的做法：**服务端校验** + 返回值回显错误，而不是只靠前端校验：

```tsx
'use server';
export async function submit(prev, formData) {
  const name = formData.get('name')?.toString() ?? '';
  if (name.trim().length < 2) {
    return { error: '名称至少 2 个字符', value: name };
  }
  await save();
  return { error: null, value: name };
}
```

并配合 `useActionState` 在客户端展示 `state.error`。

### 3.2 乐观更新

提交后不想等服务端刷新，可先用**乐观值**更新 UI，服务端成功后再校正。常用 `useOptimistic`（React 19+）：

```tsx
'use client';
import { useOptimistic } from 'react';

const [optimisticTodos, addOptimistic] = useOptimistic(todos,
  (state, newTodo) => [...state, newTodo]);
```

提交时先 `addOptimistic(newTodo)` 立即显示，服务端处理完再刷新校正。适合聊天、评论等即时反馈场景。

### 3.3 与 Route Handler 的选择

| 场景 | 推荐 |
| --- | --- |
| 表单提交 / 简单增删改 + 页面刷新 | **Server Action**（更简洁） |
| 需要被第三方/前端独立调用的公共 API | **Route Handler** |
| GET 数据、RESTful 语义、需要状态码精细控制 | **Route Handler** |
| AI 流式对话（SSE 长连接） | **Route Handler** |

一般规则：**内部 UI 变更用 Server Action，对外/流式接口用 Route Handler**。

### 3.4 安全注意

- Server Action 也是**可被直接调用的端点**，不能信任其输入，同样需要鉴权与校验。
- 危险操作（删除等）务必做**权限校验**（Day13 配合鉴权）。
- 密钥同样只在服务端 action 中使用。

---

## 四、关键知识点总结

- **Server Actions**：`'use server'` 声明的服务端函数，表单/按钮直接调用。
- **渐进增强**：原生 HTML 表单 `action` 即可工作，无 JS 也能提交。
- **formData.get()**：读取表单字段；`.bind` 绑定额外参数。
- **revalidatePath/revalidateTag**：提交后刷新页面缓存数据。
- **useActionState**：包装 action 返回结果，做表单错误回显。
- **useOptimistic**：乐观更新，即时反馈体验。
- **选择**：内部 UI 变更用 Server Action，流式/对外 API 用 Route Handler。
- **安全**：action 也是端点，需鉴权与输入校验。

---

## 五、实战练习

### 练习一：server_actions.js —— Server Action 流程演示

**任务描述**：运行脚本，模拟「表单提交 → 服务端函数 → 校验 → revalidate」的完整流程，展示 formData 解析、绑定参数、校验返回与数据刷新逻辑。

**运行方式**

```bash
cd Code
node server_actions.js
```

### 练习二：Todo 增删 + revalidate

实现 `app/actions.ts` 的 `createTodo`/`deleteTodo`，在 Todos 页用 `<form action>` 提交新增、用 `.bind` 删除，并 `revalidatePath` 刷新列表。

### 练习三：邮箱校验表单

用 `useActionState` + 服务端校验实现注册表单，输入非法邮箱时回显错误信息（不刷新整页）。

---

## 下节预告

下一节 **Day11** 将进入 **状态管理与缓存**：区分服务端状态（`cookies()`/`headers()`/Next Cache）与客户端状态，掌握 Zustand、Context 与 TanStack Query 的选型，构建应用级的数据与界面状态管理。