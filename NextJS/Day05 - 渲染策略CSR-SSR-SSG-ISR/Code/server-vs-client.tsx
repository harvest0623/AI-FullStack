// Day05 - server-vs-client.tsx  服务端与客户端组件边界示例
// ServerComponent 默认（可直读数据），ClientComponent 需交互则加 'use client'

// ============ Server Component（默认，服务端渲染） ============
// 落位：app/blog-list.tsx  或作为页面使用
// 可 await 数据、读库、访问私密变量，不携带 JS 到浏览器
async function BlogList() {
  // 示意：从数据源取文章（在真实项目中可直查数据库/调用 API）
  const posts = [
    { id: 1, title: '渲染策略详解' },
    { id: 2, title: '服务端组件实战' },
    { id: 3, title: 'AI 全栈之路' },
  ];

  return (
    <ul>
      {posts.map((p) => (
        <li key={p.id}>{p.title}</li>
      ))}
    </ul>
  );
}

// ============ Client Component（客户端组件，需标记） ============
// 落位：app/search-box.tsx
// 文件顶部需要 'use client' 指令（下面注释示意，实际是文件级导入）
const clientComponentNote = `
  要使用 useState/useEffect 等交互能力的组件，需在文件顶部：
  'use client';

  import { useState } from 'react';

  export default function SearchBox() {
    const [q, setQ] = useState('');
    return <input value={q} onChange={(e) => setQ(e.target.value)} />;
  }
`;

function main() {
  console.log('【Server vs Client Component 边界】\n');
  console.log('Server Component（默认）：');
  console.log('  · 只在服务端渲染，不打包 JS → 体积小、快');
  console.log('  · 可 await 异步数据 / 直读数据库 / 访问私密环境变量');
  console.log('  · 不能用 useState / useEffect / useRouter 等客户端 Hook');
  console.log('  · 示例：展示文章列表、读取数据库内容\n');

  console.log('Client Component（\'use client\' 标记）：');
  console.log('  · 会打包 JS 到浏览器，可在客户端水合交互');
  console.log('  · 可用状态、事件、副作用 Hook');
  console.log('  · 不要放密钥/私密配置（会暴露到浏览器）');
  console.log('  · 示例：搜索框、计数器、表单交互\n');

  console.log(clientComponentNote);

  console.log('【选用原则】默认服务端组件，需要交互才加 \'use client\'。');
  console.log('注意：\'use client\' 会使其 import 的子组件也变为客户端组件链。');
}

// 导出组件示例给真实项目用，本脚本以讲解为主
export { BlogList };
main();