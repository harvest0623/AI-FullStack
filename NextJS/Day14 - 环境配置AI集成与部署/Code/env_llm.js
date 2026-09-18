// Day14 - env_llm.js  环境变量与 LLM 集成逻辑演示
// 展示 NEXT_PUBLIC_ 前缀对变量可见性的影响，以及本地 Ollama 与云端 LLM 对接。
// 离线可运行：node env_llm.js

// 模拟 .env 加载
const env = {
  OPENAI_API_KEY: 'sk-xxx-secret',        // 无前缀 → 仅服务端
  DATABASE_URL: 'postgres://...',          // 无前缀 → 仅服务端
  NEXT_PUBLIC_SITE_NAME: '我的 AI 应用',   // NEXT_PUBLIC_ → 暴露浏览器
};

function isPublic(key) {
  return key.startsWith('NEXT_PUBLIC_');
}

// 模拟 Route Handler 调用大模型（流式/非流式）
async function callLLM(messages, { stream }) {
  const apiKey = env.OPENAI_API_KEY; // 服务端可读到密钥
  console.log(`  服务端使用密钥（仅服务端可见）: ${apiKey.slice(0, 8)}...`);
  const reply = `你好，我是 AI，已收到：${messages[messages.length - 1].content}`;
  return stream ? { stream: true, reply: `逐 Token：${reply.split('').join(' | ')}` } : { reply };
}

async function main() {
  console.log('【环境变量可见性】\n');
  for (const [k, v] of Object.entries(env)) {
    const publicVisible = isPublic(k);
    console.log(`  ${k.padEnd(28)} 暴露到浏览器: ${publicVisible ? '✅ 是' : '❌ 否(仅服务端)'}`);
  }
  console.log('\n  铁律：密钥不要用 NEXT_PUBLIC_ 前缀，否则会打包进前端源码。\n');

  console.log('【LLM 集成（Route Handler 内安全调用）】\n');

  console.log('① 云端 OpenAI 兼容接口（非流式）');
  const r1 = await callLLM([{ role: 'user', content: '你好' }], { stream: false });
  console.log(`   → ${JSON.stringify(r1)}\n`);

  console.log('② 本地 Ollama 对接（OpenAI 兼容端点）');
  const base = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
  console.log(`   baseUrl: ${base}/v1/chat/completions`);
  console.log('   请求体：{ model: "qwen2.5:7b", messages, stream: true }');
  console.log('   返回：透传 upstream.body 给前端做 SSE 流式\n');

  console.log('【SSE 流式要点】');
  console.log('  · 上游 stream:true，后端透传/重组成 text/event-stream');
  console.log('  · 前端用 fetch reader 逐 Token 渲染 → 打字机效果');
  console.log('  · 本地方案免 Key、离线、私密，适合本地开发与演示');
}

main();