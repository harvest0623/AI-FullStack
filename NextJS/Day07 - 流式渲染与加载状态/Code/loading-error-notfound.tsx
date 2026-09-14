// Day07 - loading-error-notfound.tsx  加载/错误/404 三态配置示例
// 分别展示 loading.tsx、error.tsx、not-found.tsx 的写法与用途。

// ============ app/blog/loading.tsx（加载骨架屏） ============
export function BlogLoading() {
  return (
    <div style={{ padding: 20 }}>
      <p>正在加载文章列表...</p>
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          style={{
            height: 60,
            margin: 8,
            borderRadius: 8,
            background: 'linear-gradient(90deg,#eee 25%,#f5f5f5 37%,#eee 63%)',
            backgroundSize: '400% 100%',
          }}
        />
      ))}
    </div>
  );
}

// ============ app/blog/error.tsx（错误边界，必须 'use client'） ============
// 'use client' 实际需写在文件顶部
export function BlogError({ reset }: { reset: () => void }) {
  return (
    <div role="alert" style={{ padding: 20, color: '#c00' }}>
      <h2>文章加载出错了</h2>
      <p>可能是网络异常或数据源故障。</p>
      <button onClick={reset}>点击重试</button>
    </div>
  );
}

// ============ app/blog/[slug]/not-found.tsx（404 页面） ============
export function PostNotFound() {
  return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <h2 style={{ fontSize: 60 }}>404</h2>
      <p>您访问的文章不存在或已被删除。</p>
      <a href="/blog">返回文章列表</a>
    </div>
  );
}

// ============ app/blog/[slug]/page.tsx（使用 notFound 触发） ============
export function useNotFoundDemo() {
  // 伪代码示意（真实组件中）：
  // import { notFound } from 'next/navigation';
  // const post = await getPost(slug);
  // if (!post) notFound();
  return 'if (!post) { notFound(); }  // 渲染最近的 not-found.tsx';
}

function main() {
  console.log('【加载 / 错误 / 404 三态】\n');
  console.log('loading.tsx：路由段的默认加载 UI，数据未就绪先展示（骨架屏）');
  console.log("error.tsx  ：错误边界，必须是 'use client'，可 reset 重试");
  console.log('not-found.tsx：404 页面，配合 notFound() 主动触发');
  console.log('\n一个健壮的路由段通常四件套齐备：');
  console.log('  app/page.tsx        页面内容');
  console.log('  app/loading.tsx     加载态');
  console.log('  app/error.tsx       出错态');
  console.log('  app/not-found.tsx   404 态');
}

main();