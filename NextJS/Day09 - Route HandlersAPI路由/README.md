# Day09 - Route Handlers（API 路由）

> 本章节让 Next.js 应用具备真正的后端接口能力。掌握 `route.ts` 定义各 HTTP 方法的接口、请求参数解析、统一响应构造、流式响应（SSE），并学会在后端安全承载大模型 API 调用——这是 AI 全栈的关键一环。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 Route Handler 是什么](#21-route-handler-是什么)
  - [2.2 定义 GET / POST 等接口](#22-定义-get--post-等接口)
  - [2.3 请求与响应](#23-请求与响应)
  - [2.4 动态段在手接口](#24-动态段在手接口)
  - [2.5 流式响应 SSE](#25-流式响应-sse)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 与 Page 的权限规划](#31-与-page-的权限规划)
  - [3.2 缓存行为](#32-缓存行为)
  - [3.3 后端承载大模型调用](#33-后端承载大模型调用)
  - [3.4 安全注意](#34-安全注意)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **定义 API 接口**：用 `route.ts` 实现 GET/POST/PUT/DELETE 等接口。
2. **解析请求**：读取查询参数、路径参数与 JSON 请求体。
3. **构造响应**：返回 JSON、设置状态码与头。
4. **实现流式响应**：用 SSE/流式返回 Token，做 AI 打字机交互。
5. **安全承接 LLM 调用**：在后端调用大模型并在服务端保护密钥。

---

## 二、理论知识

### 2.1 Route Handler 是什么

**Route Handler** 是 Next.js App Router 中定义**后端 API** 的方式。在某个路由目录下放一个 `route.ts`，导出对应 HTTP 方法命名的函数即可：

```
app/
└── api/
    └── hello/
        └── route.ts    # /api/hello
```

基础 GET 接口：

```tsx
// app/api/hello/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ message: 'Hello from API' });
}
```

访问 `GET /api/hello` 返回 `{ "message": "Hello from API" }`。

### 2.2 定义 GET / POST 等接口

导出以 HTTP 方法命名的异步函数即可，一个文件可定义多个方法：

```tsx
// app/api/todos/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET() {
  // 读取列表
  return NextResponse.json({ data: todoList });
}

export async function POST(req: NextRequest) {
  const body = await req.json();        // 解析请求体
  const newTodo = createTodo(body.text);
  return NextResponse.json({ ok: true, data: newTodo }, { status: 201 });
}

export async function DELETE(req: NextRequest) {
  // 处理删除
  return NextResponse.json({ ok: true });
}
```

支持的常见方法：`GET`、`POST`、`PUT`、`PATCH`、`DELETE`、`OPTIONS`、`HEAD`。

### 2.3 请求与响应

**解析请求 `NextRequest`**：

```tsx
import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const searchParams = req.nextUrl.searchParams;
  const q = searchParams.get('q');       // 查询参数 ?q=
  const page = Number(searchParams.get('page') ?? '1');

  return NextResponse.json({ q, page });
}
```

**构造响应 `NextResponse`**：

```tsx
// JSON + 自定义状态码
return NextResponse.json({ error: '未授权' }, { status: 401 });

// 设置响应头
const res = NextResponse.json({ data });
res.headers.set('X-Custom', 'value');
return res;

// 重定向
return NextResponse.redirect(new URL('/login', req.url));
```

### 2.4 动态段在手接口

在动态路由目录下的 `route.ts`，通过 `params` 获取路径参数：

```
app/api/users/[id]/route.ts   →  /api/users/42
```

```tsx
import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;   // params 是 Promise，需 await
  const user = await fetchUser(id);
  if (!user) return NextResponse.json({ error: '未找到' }, { status: 404 });
  return NextResponse.json({ data: user });
}
```

### 2.5 流式响应 SSE

为实现「AI 对话打字机」效果，Route Handler 可返回**流式响应**，把大模型的 Token 分片推送给前端：

```tsx
// app/api/chat/route.ts —— 大模型流式对话
import { NextRequest } from 'next/server';

export async function POST(req: NextRequest) {
  const { messages } = await req.json();

  // 生成一个 SSE（Server-Sent Events）流
  const stream = new ReadableStream({
    async start(controller) {
      // 伪代码：从某大模型 API 拿到流式增量
      const tokens = ['你好', '，', '我是', 'AI', '助手']; // 示意分片
      for (const t of tokens) {
        controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify({ token: t })}\n\n`));
        // 实际应 await 真实模型流
      }
      controller.enqueue(new TextEncoder().encode(`data: [DONE]\n\n`));
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',  // SSE 类型
      'Cache-Control': 'no-cache, no-transform',
    },
  });
}
```

前端用 `EventSource` 或 `fetch` 读流，逐 Token 更新 UI（Day14 会完整实现 AI 对话）。

---

## 三、核心概念解析

### 3.1 与 Page 的权限规划

- **Page**（`page.tsx`）：面向用户的可视化页面。
- **Route Handler**（`route.ts`）：面向程序的后端接口。

放置建议：

```
app/
├── chat/
│   └── page.tsx           # 聊天 UI 页面
└── api/
    └── chat/
        └── route.ts       # 聊天后端接口（供页面调用）
```

二者同属一个应用、可共享代码，职责分离清晰。

### 3.2 缓存行为

- `GET` 默认可能被缓存（静态化），需要动态数据可 `export const dynamic = 'force-dynamic'` 或用 `revalidate`。
- `POST`、`PUT` 等方法**默认不缓存**，每次实时执行。
- 大模型接口通常是 POST + 动态，天然每次实时。

```tsx
export const dynamic = 'force-dynamic';   // 强制每次动态渲染
```

### 3.3 后端承载大模型调用

Route Handler 的关键价值：**把大模型 API Key 藏在服务端**，前端只调用自己的 `/api/xxx`：

```
浏览器 ──POST /api/chat──▶ Next.js Route Handler
                                   │  调用大模型 API（Key 在此服务端持有）
                                   ▼
                             大模型 / Ollama / OpenAI
```

前端不会接触到 Key，也便于统一限流、日志、鉴权。这是 AI 应用的安全基线。

### 3.4 安全注意

- **密钥只放服务端**：`NEXT_PUBLIC_` 开头的变量会被暴露到浏览器，密钥/Secret 慎用该前缀。
- **校验输入**：处理 user 输入时防止注入与非预期内容。
- **鉴权**：业务接口加鉴权（Day13 深入）。
- **限流**：为公开接口考虑频率限制。
- **流式**：注意关闭流、处理客户端断开。

---

## 四、关键知识点总结

- **route.ts** 定义接口，按 HTTP 方法导出函数。
- **NextRequest**：读 query（`nextUrl.searchParams`）、JSON body（`req.json()`）、路径参数（`params`）。
- **NextResponse.json**：返回 JSON；可设状态码、头、重定向。
- **params 是 Promise**：动态段在手需 `await`。
- **SSE 流式**：`ReadableStream` + `text/event-stream`，做 AI 打字机。
- **页面/接口分离**：`page.tsx` 看渲染，`route.ts` 做后端。
- **安全**：Key 只留服务端，接口负责鉴权、限流、校验。

---

## 五、实战练习

### 练习一：route_handlers.js —— 接口逻辑演示

**任务描述**：运行脚本，演示请求参数、响应构造、SSE 流式分片的处理逻辑（用 Node 模拟 `next/server` 的响应行为）。

**运行方式**

```bash
cd Code
node route_handlers.js
```

### 练习二：实现 todo API

创建 `app/api/todos/route.ts` 实现 GET（列表）、POST（新增），并用浏览器或 curl 测试：

```bash
curl http://localhost:3000/api/todos
curl -X POST http://localhost:3000/api/todos -H "Content-Type: application/json" -d '{"text":"学习RouteHandler"}'
```

### 练习三：SSE 小对话

实现 `app/api/chat/route.ts` 返回一个简易 SSE 流（可用上面 2.5 的分片伪代码），在前端用 fetch 逐段读取并追加显示。

---

## 下节预告

下一节 **Day10** 将进入 **Server Actions（服务端操作）**：用 `'use server'` 定义服务端函数，表单与按钮直接调用，体验「HTML 增强」的渐进式提交、`revalidatePath` 刷新数据与乐观更新。