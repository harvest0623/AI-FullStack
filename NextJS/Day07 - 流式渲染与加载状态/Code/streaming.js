// Day07 - streaming.js  流式渲染时序演示
// 对比传统 SSR（整页等待）与流式 SSR（逐块呈现）的时间线。
// 离线可运行：node streaming.js

// 模拟异步片段
function segment(label, ms) {
  return new Promise((resolve) =>
    setTimeout(() => resolve(label), ms)
  );
}

async function traditionalSSR() {
  console.log('【传统 SSR（整页等待）】\n');
  console.log('  服务器开始处理请求');
  console.log('  · 等待 页头数据(200ms) ...');
  await segment('页头', 200);
  console.log('  · 等待 主内容数据(500ms) ...');
  await segment('主内容', 500);
  console.log('  · 等待 侧栏数据(300ms) ...');
  await segment('侧栏', 300);
  console.log('  → 全部数据就绪，一次性返回完整 HTML');
  console.log('  缺点：最慢的片段拖累整页，之前屏幕一直空白\n');
}

async function streamingSSR() {
  console.log('【流式 SSR（逐块呈现）】\n');
  console.log('  服务器开始处理请求，立即返回可用的外壳片段');
  console.log('  · 页头数据(200ms) 完成 → 立即返回该片段');
  await segment('页头', 200);
  console.log('  · 主内容数据(500ms) 完成 → 立即返回');
  await segment('主内容', 500);
  console.log('  · 侧栏数据(300ms) 完成 → 立即返回');
  await segment('侧栏', 300);
  console.log('  优点：页头先出现，主内容还在加载时用户已能浏览外壳\n');
}

async function main() {
  await traditionalSSR();
  await streamingSSR();

  console.log('【对应 Next.js 实现】');
  console.log('  · <Suspense fallback={...}> 包裹慢的异步子组件');
  console.log('  · loading.tsx 作为整段路由的默认加载 UI（骨架屏）');
  console.log('  · 先渲染外壳/骨架，数据就绪后流式替换为真实内容');
}

main();