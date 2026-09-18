// Day12 - styles_tour.js  样式方案对比演示
// 介绍全局 CSS / CSS Modules / Tailwind / CSS-in-JS / Sass 的写法与选型。
// 离线可运行：node styles_tour.js

function main() {
  console.log('【Next.js 样式方案一览】\n');

  const schemes = [
    ['全局 CSS', 'app/globals.css', '在根 layout.tsx 引入', 'CSS变量/reset/基础'],
    ['CSS Modules', 'xxx.module.css', 'styles.xxx 引用', '组件局部样式'],
    ['Tailwind CSS', 'className 工具类', '无需单独 CSS 文件', '快速布局/规范'],
    ['CSS-in-JS', '写在 .tsx/.jsx', '内联 style / 库', '动态主题化'],
    ['Sass', 'xxx.module.scss', 'npm install sass', '变量/嵌套/宏'],
  ];

  for (const [name, file, usage, use] of schemes) {
    console.log(` 【${name}】`);
    console.log(`   文件/载体: ${file}`);
    console.log(`   使用方式 : ${usage}`);
    console.log(`   适用场景 : ${use}\n`);
  }

  console.log('【CSS Modules 写法】\n');
  console.log(`  /* button.module.css */
  .button { padding: 10px 16px; border-radius: 8px; background: #7c3aed; color: #fff; }

  /* button.tsx */
  import styles from './button.module.css';
  export default function Button() { return <button className={styles.button}>OK</button>; }`);

  console.log('\n【Tailwind 写法】\n');
  console.log(`  <div className="flex items-center justify-between p-6 max-w-3xl mx-auto">
    <h1 className="text-2xl font-bold">标题</h1>
    <button className="px-4 py-2 rounded-lg bg-purple-600 text-white">提交</button>
  </div>`);

  console.log('\n【响应式与主题要点】');
  console.log('  · 响应式: grid-cols-1  md:grid-cols-2  lg:grid-cols-3');
  console.log('  · 主题  : CSS 变量 :root / [data-theme="dark"]');
  console.log('  · 图片  : next/image 自动优化；外部域名需配置 remotePatterns');
  console.log('  · 字体  : next/font 自托管优化，避免 CLS');
}

main();