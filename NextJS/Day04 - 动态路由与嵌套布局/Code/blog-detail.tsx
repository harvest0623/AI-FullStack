// Day04 - blog-detail.tsx  动态文章页 + 静态参数化 + 元数据
// 落位：app/blog/[slug]/page.tsx（需自建 app/blog/[slug]/ 目录）

import type { Metadata } from 'next';

// 说明书名文章：静态参数化，构建期预生成这些路径
const posts = ['hello-world', 'quickstart', 'ai-roadmap'];

export async function generateStaticParams() {
  return posts.map((slug) => ({ slug }));
}

// 为每个动态路径生成独立元数据（利于 SEO）
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const title = slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  return {
    title: `${title} - 我的博客`,
    description: `${title} 的详细文章内容。`,
  };
}

export default async function BlogDetail({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  return (
    <article style={{ padding: 40, maxWidth: 700, margin: '0 auto' }}>
      <h1>文章：{slug}</h1>
      <p>
        这是动态路由 /blog/{slug} 的页面。
        参数 (params.slug) 由 Next.js 自动从 URL 注入。
      </p>
      <p>
        通过 generateStaticParams 静态化的路径在构建期预生成为静态 HTML，
        访问速度与 SEO 俱佳；其它路径按需动态渲染。
      </p>
    </article>
  );
}