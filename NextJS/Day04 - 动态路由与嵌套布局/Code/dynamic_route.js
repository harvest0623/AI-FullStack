// Day04 - dynamic_route.js  动态路由原理演示
// 模拟 [slug] 单段与 [...slug] 多段匹配，以及 generateStaticParams 思路。
// 离线可运行：node dynamic_route.js

// 模拟路由匹配器
function match(patterns, url) {
  const segs = url.replace(/^\//, '').split('/').filter(Boolean);
  const ret = [];
  for (const pattern of patterns) {
    const pSegs = pattern.split('/').filter(Boolean);
    const params = {};
    let ok = true;

    // [...param] 默认贪婪，先尝试按等长匹配再看是否多段
    if (pattern.includes('[...]')) {
      // 简化：只要前缀段相等就匹配，剩余全并入数组
      const listIdx = pSegs.findIndex((s) => s.startsWith('[...'));
      const name = pSegs[listIdx].slice(4, -1);
      const prefix = pSegs.slice(0, listIdx);
      if (segs.length < prefix.length) ok = false;
      else {
        for (let i = 0; i < prefix.length; i++) {
          if (!(prefix[i] === segs[i])) ok = false;
        }
        params[name || 'slug'] = segs.slice(prefix.length);
      }
    } else {
      if (pSegs.length !== segs.length) ok = false;
      else {
        for (let i = 0; i < pSegs.length; i++) {
          const p = pSegs[i];
          if (p.startsWith('[') && p.endsWith(']')) {
            params[p.slice(1, -1)] = segs[i];
          } else if (p === segs[i]) {
            // 静态段匹配
          } else {
            ok = false;
          }
        }
      }
    }

    if (ok) ret.push({ pattern, params });
  }
  return ret;
}

function main() {
  console.log('【动态路由匹配演示】\n');

  const patterns = [
    'blog/[slug]',           // 单动态段
    'docs/[...slug]',        // 捕获全部段
    'user/[id]/profile',     // 静态+动态混合
  ];

  const urls = [
    '/blog/hello-world',
    '/blog/2026/intro',
    '/docs/getting-started/quickstart',
    '/docs/a/b/c',
    '/user/42/profile',
    '/user/42/posts',
  ];

  for (const url of urls) {
    const hits = match(patterns, url);
    if (hits.length === 0) {
      console.log(`${url.padEnd(34)}  ✗ 无匹配`);
    } else {
      for (const h of hits) {
        console.log(`${url.padEnd(34)}  [${h.pattern}]  params=${JSON.stringify(h.params)}`);
      }
    }
  }

  console.log('\n【generateStaticParams 思路】');
  console.log(`
  步骤：
    1. 从数据源获取所有路径清单（如商品 id 数组）
    2. 返回 [{ id: '1' }, { id: '2' }, ...]
    3. 构建期对每个生成静态页面快照
    4. 未枚举但被请求的路径 → 按需动态渲染 + 缓存
  `);

  console.log('【优先级】静态段优先于动态段：');
  console.log('   请求 /blog/sale 时，静态段 sale 优先于动态段 [slug]');
}

main();