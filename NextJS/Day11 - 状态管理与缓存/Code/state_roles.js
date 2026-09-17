// Day11 - state_roles.js  状态角色梳理演示
// 对比「服务端状态」与「客户端界面状态」，以及 Context / Zustand / Query 分工。
// 离线可运行：node state_roles.js

function main() {
  console.log('【状态分类与工具选型】\n');

  console.log('① 两类状态\n');
  const twoTypes = [
    ['服务端状态', '数据库/会话/Cookie/Headers', 'Server Component / Server Action'],
    ['客户端界面状态', '输入框/开关/临时UI数据', "'use client' 组件"],
  ];
  for (const [name, where, whereUse] of twoTypes) {
    console.log(` ${name}：`);
    console.log(`   来源    : ${where}`);
    console.log(`   读取位置: ${whereUse}\n`);
  }

  console.log('② 工具分工\n');
  const tools = [
    ['useState', '单个组件内局部状态'],
    ['Context', '组件树内共享低频全局状态（主题/登录态）'],
    ['Zustand', '复杂高频、跨模块全局状态（聊天消息）'],
    ['TanStack Query', '来自服务端的数据（缓存/重取/去重）'],
    ['Next Cache', '服务端数据缓存（revalidate/tags）'],
  ];
  for (const [name, use] of tools) {
    console.log(`  · ${name.padEnd(18)} ${use}`);
  }

  console.log('\n③ 服务端状态读取示例（泪滴示意）');
  console.log(`
  // app/dashboard/page.tsx (Server Component)
  import { cookies, headers } from 'next/headers';

  export default async function Dashboard() {
    const cookieStore = await cookies();
    const token = cookieStore.get('auth_token')?.value;
    const h = await headers();
    // ...读取 cookie/header 后会触发动态渲染
  }`);

  console.log('④ 缓存失效控制');
  console.log('  revalidatePath("/products")  // 路径失效');
  console.log('  revalidateTag("products")    // 标签失效');
  console.log('  fetch(url, { next: { tags: ["products"] } })  // 打标签');
}

main();