// Day03 - file_route.js  文件路径→URL 映射演示（模拟 App Router 约定）
// 输入一组 app/ 目录文件，计算其对应 URL，验证「文件即路由」。
// 离线可运行：node file_route.js

// 模拟一组实际项目中 app/ 下的文件（相对 app/ 的路径）
const files = [
  'page.tsx',                        // /
  'layout.tsx',                      // 根布局（不映射 URL）
  'about/page.tsx',                  // /about
  'blog/page.tsx',                   // /blog
  'blog/posts/page.tsx',             // /blog/posts
  'dashboard/settings/page.tsx',     // /dashboard/settings
  '(marketing)/pricing/page.tsx',    // /pricing （分组不影响 URL）
  '(store)/cart/page.tsx',           // /cart
];

// 计算 URL：取目录部分，剥离分组段 (xxx)，直到 page.tsx 所在目录
function toUrl(file) {
  // 只处理页面文件
  if (!file.endsWith('/page.tsx') && file !== 'page.tsx') return null;

  // 取目录段
  const segments = file.split('/'); // 例如 ['blog','posts','page.tsx']
  segments.pop();                  // 去掉 'page.tsx'

  // 去掉分组段 (xxx)
  const real = segments.filter((s) => !/^\(/.test(s));

  const path = real.join('/');
  return '/' + (path === '' ? '' : path).replace(/\/$/, '');
}

function main() {
  console.log('【App Router：文件路径 → URL 映射】\n');

  for (const f of files) {
    const url = toUrl(f);
    const label = f.endsWith('layout.tsx')
      ? '（布局文件，不产生 URL）'
      : url;
    console.log(`  ${f.padEnd(42)}  →  ${label}`);
  }

  console.log('\n  规则：');
  console.log('    · 文件夹路径 = URL 段，page.tsx 即路由页面');
  console.log("    · layout.tsx 只定义共享外壳，不单独映射 URL");
  console.log('    · 分组路由 (name) 不影响 URL，仅组织文件');
  console.log('    · 根 app/page.tsx 对应根路径 /');

  // 演示结构树
  console.log('\n【对应目录树】');
  console.log(`  app/
  ├── page.tsx
  ├── layout.tsx
  ├── about/page.tsx
  ├── blog/
  │   ├── page.tsx
  │   └── posts/page.tsx
  ├── dashboard/settings/page.tsx
  ├── (marketing)/pricing/page.tsx
  └── (store)/cart/page.tsx`);
}

main();