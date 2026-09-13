// Day06 - products-page.tsx  服务端数据获取 + 缓存控制示例
// 落位：app/products/page.tsx（Server Component）

// 模拟异步取数（真实场景可用 fetch / ORM）
async function getProducts() {
  return [
    { id: 1, name: 'AI 对话助手', price: 99 },
    { id: 2, name: 'RAG 知识库', price: 199 },
    { id: 3, name: 'Agent 编排平台', price: 299 },
  ];
}

export default async function Products() {
  // 在 Server Component 中直接 await 数据
  const products = await getProducts();

  return (
    <main style={{ padding: 40, maxWidth: 700, margin: '0 auto' }}>
      <h1>商品列表（服务端渲染）</h1>
      <p>数据在服务端获取后随完整 HTML 一并返回，首屏即时可见、利于 SEO。</p>

      <ul style={{ listStyle: 'none', padding: 0 }}>
        {products.map((p) => (
          <li
            key={p.id}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: 12,
              borderBottom: '1px solid #eee',
            }}
          >
            <span>{p.name}</span>
            <b>${p.price}</b>
          </li>
        ))}
      </ul>

      <p style={{ color: '#888', fontSize: 13 }}>
        缓存：本页面默认静态缓存，如需定期刷新可在文件顶部加
        <code style={{ background: '#f0f0f0', padding: '2px 4px' }}>
          export const revalidate = 60;
        </code>
      </p>
    </main>
  );
}