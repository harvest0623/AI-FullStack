// Day09 - route_handlers.js  Route Handler 逻辑演示
// 模拟 next/server 的请求参数、响应构造与 SSE 流式分片处理逻辑。
// 离线可运行：node route_handlers.js

// 模拟一个小型路由处理器的请求/响应
function simulateHandler({ method, path, query, body }) {
  console.log(`  请求：${method} ${path}` + (query ? `?${query}` : ''));

  // 解析查询参数
  const searchParams = new URLSearchParams(query || '');
  const q = searchParams.get('q');
  const pageStr = searchParams.get('page');

  if (method === 'GET') {
    return { status: 200, body: { q: q || null, page: Number(pageStr) || 1 } };
  }

  if (method === 'POST') {
    // 模拟解析 JSON 请求体
    const parsed = body || {};
    if (!parsed.text) return { status: 400, body: { error: '缺少 text 字段' } };
    return { status: 201, body: { ok: true, created: parsed.text } };
  }

  if (method === 'DELETE') {
    return { status: 200, body: { ok: true } };
  }

  return { status: 405, body: { error: 'Method Not Allowed' } };
}

// 模拟 SSE 流式分片
function simulateSSE(tokens) {
  console.log('\n【SSE 流式分片】\n  返回头: Content-Type: text/event-stream\n');
  for (const t of tokens) {
    const frame = `data: ${JSON.stringify({ token: t })}\n\n`;
    console.log(`  → 推送: ${frame.trim().replace('\n\n', ' ')}`);
  }
  console.log('  → 推送: data: [DONE]\n');
}

function main() {
  console.log('【Route Handler 逻辑演示】\n');

  console.log('① 查询参数与 JSON 响应');
  const r1 = simulateHandler({ method: 'GET', path: '/api/search', query: 'q=nexus&page=2' });
  console.log(`   → ${JSON.stringify({ status: r1.status, body: r1.body })}\n`);

  console.log('② 请求体校验与 201 响应');
  const r2 = simulateHandler({ method: 'POST', path: '/api/todos', body: { text: '学习 Route Handler' } });
  console.log(`   → ${JSON.stringify({ status: r2.status, body: r2.body })}`);
  const r2b = simulateHandler({ method: 'POST', path: '/api/todos', body: {} });
  console.log(`   → ${JSON.stringify({ status: r2b.status, body: r2b.body })}\n`);

  console.log('③ 动态段参数（路径中的 id）');
  console.log('   函数签名的 params 是 Promise，需 await：');
  console.log('   export async function GET(req, { params }) {\n     const { id } = await params;\n   }\n');

  simulateSSE(['你好', '，', '我是', 'AI', '助手']);

  console.log('【后端承载大模型调用】浏览器 → POST /api/chat → Route Handler → LLM(Key 在服务端)');
}

main();