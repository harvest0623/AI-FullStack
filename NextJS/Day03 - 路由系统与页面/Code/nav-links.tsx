// Day03 - nav-links.tsx  客户端导航导航栏（Link 预取 + 编程式跳转）
// 可放到 app/components/NavLinks.tsx，在布局中引入使用。

'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function NavLinks() {
  const router = useRouter();
  const [path, setPath] = useState('/about');

  return (
    <nav style={{ display: 'flex', gap: 16, alignItems: 'center', padding: 12 }}>
      {/* Link 客户端导航，自动预取目标路由 */}
      <Link href="/">首页</Link>
      <Link href="/about">关于</Link>
      <Link href="/blog">博客</Link>
      <Link href="/blog/posts">文章列表</Link>

      {/* 编程式导航（表单提交后跳转等场景） */}
      <span style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
        <input
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="/about"
          style={{ padding: 6 }}
        />
        <button onClick={() => router.push(path)}>跳转</button>
      </span>
    </nav>
  );
}