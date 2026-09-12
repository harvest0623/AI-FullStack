// Day01 - hello-page.tsx  第一个页面（复制到 app/page.tsx 使用）
// Next.js App Router 中，app/page.tsx 对应根路径 /
// 运行：npm run dev 后访问 http://localhost:3000

export default function Home() {
  return (
    <main style={{ padding: '40px', maxWidth: 640, margin: '0 auto' }}>
      <h1>👋 Hello Next.js!</h1>
      <p>这是使用 App Router 渲染的第一个页面。</p>
      <ul>
        <li>文件位置：app/page.tsx 即根路由 /</li>
        <li>渲染方式：默认服务端渲染（SSR）</li>
        <li>根布局：app/layout.tsx 包裹所有页面</li>
      </ul>
    </main>
  );
}