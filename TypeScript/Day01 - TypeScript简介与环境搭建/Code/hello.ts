/**
 * hello.ts
 * ------------------------------------------------------------------
 * Day01 第一个 TypeScript 程序：
 *   - 演示接口（interface）
 *   - 演示类型注解（参数、返回值、变量）
 *   - 演示可选属性与默认参数
 *
 * 运行方式：
 *   方式 A（看编译产物）: tsc hello.ts && node hello.js
 *   方式 B（ts-node）   : npx ts-node hello.ts
 *   方式 C（tsx 推荐）   : npx tsx hello.ts
 *
 * 编译目标：Node 18+ / TypeScript 5+
 * ------------------------------------------------------------------
 */

// 1. 接口：描述一个对象的「形状」，是 TS 最常用的类型构造
interface User {
  id: number;
  name: string;
  age: number;
  email?: string;        // 可选属性：调用方可不传
  readonly createdAt: Date;  // 只读属性：赋值后不可改
}

// 2. 带类型注解的函数：参数与返回值都标注
function formatUser(user: User): string {
  const emailPart = user.email ? ` <${user.email}>` : '';
  return `[${user.id}] ${user.name}, ${user.age} 岁${emailPart}`;
}

// 3. 带默认参数与可选参数的函数
function greet(name: string, greeting: string = '你好'): string {
  return `${greeting}, ${name}!`;
}

// 4. 数组类型与联合类型注解
function sumEven(numbers: number[]): number {
  return numbers
    .filter((n) => n % 2 === 0)
    .reduce((acc, n) => acc + n, 0);
}

// ------------------------------------------------------------------
// 主流程：构造数据、调用函数、输出结果
// ------------------------------------------------------------------
const alice: User = {
  id: 1,
  name: 'Alice',
  age: 28,
  email: 'alice@example.com',
  createdAt: new Date('2024-01-15'),
};

const bob: User = {
  id: 2,
  name: 'Bob',
  age: 35,
  createdAt: new Date('2024-03-22'),
};

console.log('=== TypeScript Day01 - hello.ts ===\n');

console.log('1) formatUser 演示');
console.log('  ' + formatUser(alice));
console.log('  ' + formatUser(bob));

console.log('\n2) greet 演示（默认参数 + 显式参数）');
console.log('  ' + greet('世界'));
console.log('  ' + greet('TypeScript', '欢迎来到'));

console.log('\n3) sumEven 演示（数组类型 + 联合类型）');
const nums: number[] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
console.log(`  输入: ${nums.join(', ')}`);
console.log(`  偶数之和: ${sumEven(nums)}`);

console.log('\n4) 只读属性与可选属性演示');
console.log(`  Alice 创建于: ${alice.createdAt.toISOString()}`);
console.log(`  Alice 邮箱: ${alice.email ?? '（未填写）'}`);
console.log(`  Bob  邮箱: ${bob.email ?? '（未填写）'}`);

// alice.createdAt = new Date();  // 取消注释会报错：readonly 属性不可重新赋值

console.log('\n=== 程序运行结束 ===');
