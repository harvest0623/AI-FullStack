# Day14 - 环境配置、AI 集成与生产部署

> 收官章节，把 Next.js 与「大模型」真正打通并上线。掌握 `.env` 环境变量管理，在 Route Handler / Server Action 中安全调用大模型（Ollama / OpenAI / DeepSeek 等）并做 SSE 流式对话，完成构建、Vercel 与 Docker 部署，最后做性能优化清单。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 环境变量管理 .env](#21-环境变量管理-env)
  - [2.2 服务端 vs 客户端变量](#22-服务端-vs-客户端变量)
  - [2.3 安全调用大模型](#23-安全调用大模型)
  - [2.4 SSE 流式对话实现](#24-sse-流式对话实现)
  - [2.5 对接 Ollama 本地模型](#25-对接-ollama-本地模型)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 构建与生产启动](#31-构建与生产启动)
  - [3.2 Vercel 部署](#32-vercel-部署)
  - [3.3 Docker 部署](#33-docker-部署)
  - [3.4 性能优化清单](#34-性能优化清单)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **管理工作环境变量**：分清 `NEXT_PUBLIC_` 前缀与密钥的存放。
2. **安全调用大模型**：在服务端调用 LLM，密钥不暴露前端。
3. **实现流式对话**：用 Route Handler + SSE 做出打字机体验。
4. **本地对接 Ollama**：在本地跑通「Next.js + 本地模型」。
5. **构建与部署**：掌握 build、Vercel、Docker 部署流程。
6. **性能优化**：用内置能力与最佳实践提升应用表现。

---

## 二、理论知识

### 2.1 环境变量管理 .env

Next.js 读取根目录的 `.env`、`.env.local`、`.env.production` 等文件：

```bash
# .env.local —— 本地/私密（勿提交仓库）
OPENAI_API_KEY=sk-xxx
OLLAMA_BASE_URL=http://localhost:11434

# 会用 NEXT_PUBLIC_ 前缀的才会暴露到浏览器
NEXT_PUBLIC_SITE_NAME=我的AI应用
```

读取方式：

```tsx
// 服务端组件 / Route Handler / Server Action（安全）
const apiKey = process.env.OPENAI_API_KEY;

// 客户端组件 —— 只能读到 NEXT_PUBLIC_ 前缀的变量
const siteName = process.env.NEXT_PUBLIC_SITE_NAME;
```

> **铁律**：密钥/Secret 不要用 `NEXT_PUBLIC_` 前缀（会打包进浏览器源码，等同泄露）。

### 2.2 服务端 vs 客户端变量

| 变量 | 前缀 | 可见范围 |
| --- | --- | --- |
| `OPENAI_API_KEY` | 无 | 仅服务端 |
| `DATABASE_URL` | 无 | 仅服务端 |
| `NEXT_PUBLIC_SITE_NAME` | `NEXT_PUBLIC_` | 构建时打进入浏览器代码 |

只有 `NEXT_PUBLIC_` 的变量能被客户端组件引用，密钥一律放服务端。

### 2.3 安全调用大模型

在 **Route Handler** 中调用大模型，前端只请求自己的 `/api/chat`：

```tsx
// app/api/chat/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  const apiKey = process.env.OPENAI_API_KEY; // 服务端密钥

  // 使用 OpenAI 兼容接口（也可换 DeepSeek / Ollama 的 baseUrl）
  const resp = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({ model: 'gpt-4o-mini', messages, stream: false }),
  });

  const data = await resp.json();
  return NextResponse.json({ reply: data.choices?.[0]?.message?.content });
}
```

前端：

```tsx
'use client';
const res = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ messages: [{ role: 'user', content: '你好' }] }),
});
const data = await res.json();
```

密钥始终在服务端，前端看不到。

### 2.4 SSE 流式对话实现

把上面的调用改为**流式**，后端分片返回 Token，前端逐 Token 渲染（打字机效果）：

```tsx
// app/api/chat/route.ts —— 流式版本
import { NextRequest } from 'next/server';

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  const apiKey = process.env.OPENAI_API_KEY;

  // 请求大模型的 stream 流
  const upstream = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({ model: 'gpt-4o-mini', messages, stream: true }),
  });

  // 直接把上游的 JSONL 事件流转回给浏览器
  return new Response(upstream.body, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
    },
  });
}
```

前端读取流：

```tsx
'use client';
async function streamChat(messages, onToken) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  });

  const reader = res.body?.getReader();
  const decoder = new TextDecoder();
  let text = '';

  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;
    // 解析 SSE data 行，累积渲染
    text += decoder.decode(value, { stream: true });
    onToken(extractText(text));  // 简化：提取已返回的文本部分渲染
  }
}
```

> 也可以让服务端用 ReadableStream 逐 token 组 SSE （见 Day09 2.5）。

### 2.5 对接 Ollama 本地模型

本地安装 Ollama 后可对接本地模型（免费、离线、私密）：

```tsx
// app/api/chat/route.ts —— 对接本地 Ollama（OpenAI 兼容端点）
export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  const base = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';

  const resp = await fetch(`${base}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'qwen2.5:7b',          // 已 pull 的模型
      messages,
      stream: true,
    }),
  });

  return new Response(resp.body, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
    },
  });
}
```

本地跑：`ollama run qwen2.5:7b` 启动，Next.js 应用即可调用本地模型做流式对话。这也是「AI 全栈」昔无联网限制的落地方式。

---

## 三、核心概念解析

### 3.1 构建与生产启动

```bash
npm run build    # 生产构建（会静态化能静态的页面 + 服务端打包）
npm start        # 启动生产服务器（默认 3000）
```

`next build` 时，日志会标注各页面是静态（[○]、[ƒ] 静态、[ƒ] 动态）：

- `●` / `(Static)`：静态生成
- `ƒ` / `(Dynamic)`：动态渲染
- `ISR`：增量静态再生成

### 3.2 Vercel 部署

1. 把项目推到 GitHub。
2. 在 Vercel 导入仓库，自动识别 Next.js 设置。
3. 配置环境变量（在 Vercel 控制台添加 `OPENAI_API_KEY` 等）。
4. 点击 Deploy，即可获得 `xxx.vercel.app` 可访问地址。

Vercel 会自动处理构建、Serverless 函数、CDN 与 HTTPS，几乎零配置。

### 3.3 Docker 部署

自建服务器可用 Docker 镜像部署：

```dockerfile
# Dockerfile
FROM node:20-alpine AS base

# 安装依赖
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# 构建
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# 运行
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

需在 `next.config.ts` 开启单文件输出：

```ts
const nextConfig = { output: 'standalone' };
```

本地构建运行：

```bash
docker build -t my-next-app .
docker run -p 3000:3000 -e OPENAI_API_KEY=xxx my-next-app
```

### 3.4 性能优化清单

- **渲染策略**：能用 SSG/ISR 就静态化，减少动态计算。
- **图片**：用 `next/image`，`priority` 标记首屏关键图。
- **字体**：用 `next/font`，避免布局偏移。
- **流式/骨架屏**：用 Suspense + loading.tsx 提升感知速度。
- **代码分割**：动态导入 `next/dynamic` 懒加载大组件。
- **缓存**：合理使用 `revalidate`/`tags` 与 TanStack Query。
- **日志与监控**：构建期与运行时日志，便于排查。
- **安全**：密钥服务端受限，中间件鉴权，接口校验与限流。

---

## 四、关键知识点总结

- **.env 管理**：密钥无前缀仅服务端，`NEXT_PUBLIC_` 才暴露浏览器。
- **安全调用 LLM**：在 Route Handler 调大模型，密钥留服务端，前端只调自己的 `/api/chat`。
- **SSE 流式**：`stream: true` + 透传 `upstream.body` / 自组 ReadableStream，flush 到前端。
- **对接 Ollama**：用其 OpenAI 兼容端点（`{base}/v1/chat/completions`）即可本地化。
- **构建部署**：`npm run build` → `npm start`；Vercel 零配置；Docker 用 standalone 输出。
- **性能**：SSG/ISR、next/image、next/font、next/dynamic、Suspense、缓存协同。

---

## 五、实战练习

### 练习一：env_llm.js —— 环境变量与 LLM 集成逻辑演示

**任务描述**：运行脚本，演示 `NEXT_PUBLIC_` 前缀对变量可见性的影响，以及本地 Ollama / 云端 LLM 的对接方式对比。

**运行方式**

```bash
cd Code
node env_llm.js
```

### 练习二：搭建 AI 对话页（完整闭环）

在 `app/chat/` 实现：聊天 UI（客户端组件）+ `app/api/chat/route.ts`（调用本地 Ollama 或云端 LLM，SSE 流式）+ 对话消息用 Zustand 管理。运行 dev 与模型对话，实现打字机输出。

**具备条件**：本地需 `ollama run <模型>` 或配置 API Key。

### 练习三：Dockerfile 部署

为本项目编写 Dockerfile 并在本地 `docker build/run` 跑通；或通过 Vercel 做一次线上部署。

---

## 下节预告

至此，Next.js 模块全部完成。你可以：

- 回头用「知识点速查」表自检各主题掌握情况。
- 把 AI 对话应用对接后端（NestJS / Python 模型服务）做真实产品。
- 继续学习更聚焦的主题（TypeScript 强化、NestJS、Redis 缓存、Docker/K8s 部署等）。