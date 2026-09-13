// Day05 - render_strategies.js  四种渲染策略原理演示
// 用时间线模拟 CSR / SSR / SSG / ISR 在「请求→响应」中的差异。
// 离线可运行：node render_strategies.js

// 模拟各类策略的处理时序
function renderStrategy(name, steps) {
  console.log(`【${name}】`);
  steps.forEach((s, i) => {
    const indent = '    '.repeat(s.indent || 0);
    const arrow = i === 0 ? '请求 ' : '     ';
    console.log(`  ${arrow}→ ${indent}${s.text}`);
  });
  console.log();
}

function main() {
  console.log('======== 四种渲染策略时序演示 ========\n');

  renderStrategy('CSR（客户端渲染）', [
    { text: '浏览器请求页面' },
    { text: '返回【空壳 HTML + 全部 JS】', indent: 1 },
    { text: '浏览器加载并执行 JS' },
    { text: 'JS 调用 API 获取数据', indent: 1 },
    { text: '客户端实时渲染真实内容', indent: 1 },
  ]);

  renderStrategy('SSR（服务端渲染）', [
    { text: '浏览器请求页面' },
    { text: '服务器执行组件 + 取数据', indent: 1 },
    { text: '服务器渲染完整 HTML 返回', indent: 1 },
    { text: '浏览器显示完整内容', indent: 1 },
    { text: '浏览器水合(Hydration)接管交互', indent: 1 },
  ]);

  renderStrategy('SSG（静态生成）', [
    { text: '【构建时】渲染所有页面为静态 HTML' },
    { text: '部署到 CDN', indent: 1 },
    { text: '浏览器任意请求', indent: 0 },
    { text: 'CDN 直接返回静态文件（不执行服务端）', indent: 1 },
  ]);

  renderStrategy('ISR（增量静态再生成）', [
    { text: '【构建时】生成静态页面' },
    { text: '浏览器请求，命中缓存 → 立即返回', indent: 1 },
    { text: '达到 revalidate 间隔（如 60s）' },
    { text: '后台重新渲染生成新版本', indent: 1 },
    { text: '新版本替换，下次请求提供新内容', indent: 1 },
  ]);

  console.log('======== 选择建议 ========\n');
  const rows = [
    ['完全固定内容', 'SSG'],
    ['定期更新内容', 'ISR'],
    ['实时/个性化+SEO', 'SSR'],
    ['内部工具/无需SEO', 'CSR'],
  ];
  for (const [case_, choice] of rows) {
    console.log(`  ${case_.padEnd(22)} → ${choice}`);
  }
  console.log('\n  经验法则：能静态就静态 → 不能静态用 ISR → 再不行 SSR → 最后纯 CSR');
}

main();