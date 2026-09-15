// Day08 - hooks_demo.js  Hook 行为模拟演示
// 用简单模拟说明 useState / useRef / useMemo 的关键差异。
// 离线可运行：node hooks_demo.js

function main() {
  console.log('【客户端 Hook 行为演示（模拟）】\n');

  console.log('① useState：状态变化 → 触发组件重渲染');
  console.log('   更新数组/对象要保持不可变，返回新引用：');
  console.log('   setTodos([...todos, newItem])   // ✅ 新数组');
  console.log('   todos.push(x); setTodos(todos)  // ❌ 原地修改不触发\n');

  console.log('② useRef：可变值变化 → 不触发重渲染');
  console.log('   用途：DOM 引用、计时器 id、保存上一次渲染的值');
  console.log('   区别：useState 变→重渲染；useRef 变→不重渲染\n');

  console.log('③ useMemo：缓存计算结果');
  const items = ['apple', 'banana', 'Avocado', 'cherry'];
  const q = 'a';

  // 模拟 useMemo：仅当 items 或 q 变化时才重算过滤
  const filtered = items.filter((i) =>
    i.toLowerCase().includes(q.toLowerCase())
  );
  console.log(`   输入：[${items}]，关键词="${q}" → [${filtered}]`);
  console.log('   useMemo 会在依赖(items/q)不变时复用上次结果，避免重复昂贵计算\n');

  console.log('④ useEffect：副作用 + 清理');
  console.log('   setTimeout 等需在组件卸载时清理，避免内存泄漏:');
  console.log('   useEffect(() => {\n     const id = setTimeout(...);\n     return () => clearTimeout(id);\n   }, [deps]);\n');

  console.log('tips: 需要交互的逻辑才放客户端组件(use client)。');
}

main();