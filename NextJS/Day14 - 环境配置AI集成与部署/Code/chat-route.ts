// Day14 - chat-route-stream.ts  AI 流式对话 Route Handler 完整示例
// 落位：app/api/chat/route.ts
// 对接本地 Ollama（OpenAI 兼容端点）做 SSE 流式对话。可换云端 LLM。

import { NextRequest } from 'next/server';

export const runtime = 'nodejs'; // 需要 Node 运行时以透传流

export async function POST(req: NextRequest) {
  const { messages } = await req.json();

  // 本地 Ollama 的 OpenAI 兼容端点（默认 http://localhost:11434/v1）
  const base = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
  const model = process.env.OLLAMA_MODEL || 'qwen2.5:7b';

  // 请求本地模型，开启流式
  const upstream = await fetch(`${base}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, messages, stream: true }),
  });

  if (!upstream.ok || !upstream.body) {
    return Response.json({ error: `模型调用失败: ${upstream.status}` }, { status: 502 });
  }

  // 直接把上游 SSE 流转回给浏览器（打字机效果）
  return new Response(upstream.body, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
    },
  });
}

/*
  前端读取示例（客户端组件中）：
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: [{ role: 'user', content: '你好' }] }),
  });
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    // 解析 SSE data: {...} 行，提取 token 追加到 UI
  }
*/