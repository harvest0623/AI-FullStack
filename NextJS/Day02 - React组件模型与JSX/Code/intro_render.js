// Day02 - intro_render.js  组件/JSX 核心逻辑演示（纯 JS 模拟）
// 用最小实现模拟 React 的 Props、状态重渲染、条件与列表渲染。
// 离线可运行：node intro_render.js

// ---------- 极简组件模拟器 ----------
// 维护一个组件状态，setState 后触发重渲染
function createComponent(initial) {
  let state = initial;
  const listeners = new Set();
  return {
    get value() {
      return state;
    },
    set(v) {
      state = v;
      listeners.forEach((fn) => fn());
    },
    subscribe(fn) {
      listeners.add(fn);
    },
  };
}

// Props 单向传递：父给子，子只读
function Child({ name }) {
  return () => `子组件收到 Props 名称为：${name}`;
}

// 列表渲染：map + key
const lessons = [
  { id: 1, title: '简介与搭建' },
  { id: 2, title: '组件与 JSX' },
  { id: 3, title: '路由与页面' },
];

// 条件渲染
function Conditional({ isLogged }) {
  return isLogged ? '✅ 已登录，显示欢迎语' : '⛔ 未登录，显示登录按钮';
}

function main() {
  console.log('【React 核心逻辑演示（模拟）】\n');

  console.log('① Props 单向数据流');
  console.log(`   ${Child({ name: 'AI 学习者' })()}`);
  console.log('   说明：Props 只读，子组件不能修改父组件数据\n');

  console.log('② 状态驱动重渲染（useState 原理）');
  const count = createComponent(0);
  const renders = [];
  count.subscribe(() => renders.push(`重渲染→ count=${count.value}`));
  count.set(1);
  count.set(2);
  console.log('   操作：setCount(1) → setCount(2)');
  renders.forEach((r) => console.log(`   ${r}`));
  console.log('   说明：状态变化触发组件函数重新执行\n');

  console.log('③ 列表渲染（map + key）');
  lessons.forEach((l) => console.log(`   <li key="${l.id}">${l.title}</li>`));
  console.log('   说明：key 用于 React 精确比对，列表项需稳定唯一\n');

  console.log('④ 条件渲染');
  console.log(`   isLogged=true  → ${Conditional({ isLogged: true })}`);
  console.log(`   isLogged=false → ${Conditional({ isLogged: false })}`);
  console.log('   说明：用三目 / 逻辑与短路控制渲染分支\n');

  console.log('tips: 状态要不可变更新（返回新引用），才会触发重渲染。');
}

main();