// Day06 - nav_data.js  导航与数据获取逻辑演示
// 展示导航 API、fetch 缓存选项、并行 vs 串行数据获取的耗时差异。
// 离线可运行：node nav_data.js

// 模拟异步数据函数
function api(label, ms) {
  return new Promise((resolve) =>
    setTimeout(() => resolve(`${label} 数据`), ms)
  );
}

async function main() {
  console.log('【导航 API 一览】\n');
  const nav = [
    ['<Link>', '声明式链接，进视口自动预取，客户端跳转'],
    ['router.push', '编程式跳转'],
    ['router.replace', '替换当前历史记录'],
    ['router.back/forward', '前进后退'],
    ['router.refresh', '刷新当前路由（重新请求服务端组件）'],
    ['router.prefetch', '手动预取目标路由'],
  ];
  for (const [name, desc] of nav) console.log(`  · ${name.padEnd(20)} ${desc}`);

  console.log('\n【fetch 缓存选项】\n');
  const fetchOpts = [
    ['默认', '静态化优先，自动去重缓存'],
    ['{ next: { revalidate: 60 } }', 'ISR，60 秒后重新验证'],
    ["{ cache: 'no-store' }", '每次请求实时（动态）'],
    ["{ next: { tags: ['x'] } }", '标签缓存，可 revalidateTag 按需刷新'],
  ];
  for (const [opt, desc] of fetchOpts) console.log(`  · ${opt.padEnd(32)} ${desc}`);

  console.log('\n【并行 vs 串行请求耗时】\n');
  // 串行：总耗时累加
  const t0 = Date.now();
  await api('A', 300);
  await api('B', 300);
  await api('C', 300);
  const serialMs = Date.now() - t0;

  // 并行：总耗时 = 最慢那个
  const t1 = Date.now();
  await Promise.all([api('A', 300), api('B', 300), api('C', 300)]);
  const parallelMs = Date.now() - t1;

  console.log('  串行（一个等一个）：约 ' + serialMs + ' ms');
  console.log('  并行（Promise.all）：约 ' + parallelMs + ' ms');
  console.log('  结论：互不依赖的请求建议并行发起，避免串行等待。\n');

  console.log('【服务端取数原则】');
  console.log('  Server Component 中 await fetch → 返回完整 HTML，优先于此法。');
}

main();