// Day01 - nextjs_check.js  环境检测与概念速记
// 检测本机 Node.js / npm 环境，并打印 Next.js 核心概念清单。
// 离线可运行：node nextjs_check.js

const { execSync } = require('child_process');

function run(cmd) {
  try {
    return execSync(cmd, { timeout: 10000, encoding: 'utf-8' }).trim();
  } catch {
    return null;
  }
}

function checkEnv() {
  console.log('【Next.js 环境检测】\n');
  const node = run('node -v');
  const npm = run('npm -v');
  console.log(`  Node.js 版本 : ${node || '未安装'}`);
  console.log(`  npm 版本     : ${npm || '未安装'}`);
  console.log('  建议 Node    : >= 18.17');
  console.log(`  是否可用 npm : ${npm ? '是' : '否'}`);
}

function concepts() {
  console.log('\n【Next.js 一句话速记】\n');
  const rows = [
    ['约定式路由', '文件放 app/ 目录，路径即 URL，无需配路由表'],
    ['默认 SSR', '服务端先渲染出完整 HTML，提升 SEO 与首屏'],
    ['App Router', '新版默认路由体系，app/ 目录 + 嵌套布局'],
    ['Server Component', '默认在服务端渲染的组件，可直读数据库'],
    ['Client Component', "用 'use client' 标记，在浏览器交互的组件"],
    ['Route Handlers', 'route.ts 提供后端 API 接口能力'],
    ['Server Actions', "'use server' 定义服务端函数，表单直接调用"],
    ['渲染策略', 'SSG / SSR / ISR / CSR 四种按需选择'],
    ['流式输出', 'Suspense + loading.tsx 实现渐进式渲染'],
    ['AI 集成', '服务端调用大模型，SSE 流式返回前端'],
  ];
  for (const [k, v] of rows) {
    console.log(`  · ${k.padEnd(16)}  ${v}`);
  }
}

function roadmap() {
  console.log('\n【14 天学习路线】');
  const days = [
    'Day01 简介与项目搭建',
    'Day02 React 组件模型与 JSX',
    'Day03 路由系统与页面',
    'Day04 动态路由与嵌套布局',
    'Day05 渲染策略(CSR/SSR/SSG/ISR)',
    'Day06 导航与数据获取',
    'Day07 流式渲染与加载状态',
    'Day08 客户端 Hook 与交互',
    'Day09 Route Handlers / API 路由',
    'Day10 Server Actions 服务端操作',
    'Day11 状态管理与缓存',
    'Day12 样式方案与 UI',
    'Day13 认证授权与中间件',
    'Day14 环境配置、AI 集成与部署',
  ];
  for (const d of days) console.log(`  ${d}`);
}

function main() {
  checkEnv();
  concepts();
  roadmap();
  console.log('\n  tips: 安装了 Node.js/npm 即可实战。');
  console.log('        运行 npx create-next-app@latest my-app 建项目。');
}

main();