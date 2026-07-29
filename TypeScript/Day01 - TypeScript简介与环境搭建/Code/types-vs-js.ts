/**
 * types-vs-js.ts
 * ------------------------------------------------------------------
 * Day01 示例：对比 JavaScript 与 TypeScript 写法，展示类型系统
 * 如何把「运行时才暴露的错误」前移到「编译时」。
 *
 * 文件中包含两组代码：
 *   - 「JS 风格」片段：展示动态类型的典型坑（注释形式）
 *   - 「TS 风格」片段：展示同一段逻辑在类型系统下的安全写法
 *
 * 运行方式：
 *   npx tsx types-vs-js.ts
 *
 * 类型检查：
 *   npx tsc --noEmit types-vs-js.ts
 * ------------------------------------------------------------------
 */

console.log('=== TypeScript Day01 - types-vs-js.ts ===\n');

// ==================================================================
// 第一组：函数参数 —— 动态类型 vs 静态类型
// ==================================================================
console.log('--- 第一组：函数参数 ---\n');

/*
 * ❌ JavaScript 风格：参数没有类型约束，调用方传什么都行，
 *    错误要等到运行到那一行才暴露。
 *
 *    function calculateArea(rect) {
 *      return rect.width * rect.height;
 *    }
 *
 *    calculateArea(undefined);            // TypeError: Cannot read properties of undefined
 *    calculateArea({ width: '10', height: 5 });  // '105' 字符串拼接，悄悄传播
 *    calculateArea({ width: 10 });        // NaN，难以追踪
 */

// ✅ TypeScript 风格：用 interface 描述形状，调用方必须传对
interface Rectangle {
  width: number;
  height: number;
}

function calculateArea(rect: Rectangle): number {
  return rect.width * rect.height;
}

const r: Rectangle = { width: 10, height: 5 };
console.log(`  Rectangle { width: 10, height: 5 } 的面积 = ${calculateArea(r)}`);

// 下列调用在 TS 中会直接红线报错，编译期拦截：
// calculateArea(undefined);                            // Error: Argument of type 'undefined' is not assignable to parameter of type 'Rectangle'.
// calculateArea({ width: '10', height: 5 });           // Error: Type 'string' is not assignable to type 'number'.
// calculateArea({ width: 10 });                        // Error: Property 'height' is missing in type '{ width: number; }'.

// ==================================================================
// 第二组：API 返回值 —— 字段拼错的重构灾难
// ==================================================================
console.log('\n--- 第二组：API 返回值字段拼错 ---\n');

/*
 * ❌ JavaScript 风格：后端把 userName 改成 fullName，前端代码继续用 userName，
 *    运行时拿到 undefined，页面渲染空白，QA 才能发现。
 *
 *    function fetchUser() {
 *      return { fullName: 'Alice', age: 28 };
 *    }
 *    const u = fetchUser();
 *    console.log(u.userName.toUpperCase());  // undefined.toUpperCase → TypeError
 */

// ✅ TypeScript 风格：用 interface 作为契约，字段改名后所有调用处立刻报错
interface UserDTO {
  fullName: string;
  age: number;
}

function fetchUser(): UserDTO {
  return { fullName: 'Alice', age: 28 };
}

const u: UserDTO = fetchUser();
console.log(`  fetchUser().fullName = "${u.fullName}"`);
// console.log(u.userName.toUpperCase());  // Error: Property 'userName' does not exist on type 'UserDTO'. Did you mean 'fullName'?

// ==================================================================
// 第三组：数组元素类型 —— 混入异类元素
// ==================================================================
console.log('\n--- 第三组：数组元素类型 ---\n');

/*
 * ❌ JavaScript 风格：数组里什么都能塞，遍历时调用 .toUpperCase 直接炸
 *
 *    const names = ['Alice', 'Bob', 123, null];
 *    names.forEach(n => console.log(n.toUpperCase()));  // 123.toUpperCase → TypeError
 */

// ✅ TypeScript 风格：数组类型注解 number[] / string[] 限定元素类型
const names: string[] = ['Alice', 'Bob', 'Charlie'];
console.log(`  names = ${JSON.stringify(names)}`);
console.log(`  大写: ${names.map((n) => n.toUpperCase()).join(', ')}`);
// const mixed: string[] = ['Alice', 123];  // Error: Type 'number' is not assignable to type 'string'.

// ==================================================================
// 第四组：可选链 + strictNullChecks —— null 安全
// ==================================================================
console.log('\n--- 第四组：null 安全（strictNullChecks 的价值）---\n');

/*
 * ❌ JavaScript 风格：访问深层属性随时可能崩
 *
 *    const data = { user: null };
 *    console.log(data.user.profile.name);  // TypeError
 */

// ✅ TypeScript 风格：strictNullChecks 下，null/undefined 不能赋给非空类型
interface Profile {
  name: string;
  age?: number;
}
interface Data {
  user: Profile | null;  // 显式标注可能为 null
}

const data: Data = { user: null };

// 在 strict 模式下，下面这行会报错：
// console.log(data.user.profile.name);
// Error: 'data.user' is possibly null.

// 正确写法：用可选链 ?. 与空值合并 ??
const userName: string = data.user?.name ?? '匿名';
console.log(`  data.user 为 null 时安全取值: "${userName}"`);

data.user = { name: 'Bob' };
console.log(`  data.user 不为空时取值: "${data.user?.name ?? '匿名'}"`);

// ==================================================================
// 第五组：联合类型 + 字面量类型 —— 限制取值范围
// ==================================================================
console.log('\n--- 第五组：联合类型 + 字面量类型 ---\n');

/*
 * ❌ JavaScript 风格：传入字符串拼错运行时才发现
 *
 *    function setRole(role) { ... }
 *    setRole('amdin');  // 拼错，运行时若不校验就静默生效
 */

// ✅ TypeScript 风格：字面量联合类型直接限制取值
type Role = 'admin' | 'editor' | 'viewer';

function setRole(role: Role): string {
  return `已设置角色: ${role}`;
}

console.log(`  ${setRole('admin')}`);
console.log(`  ${setRole('viewer')}`);
// setRole('amdin');  // Error: Argument of type '"amdin"' is not assignable to parameter of type 'Role'.

// ==================================================================
// 第六组：向量数据结构 —— AI 全栈中的真实场景
// ==================================================================
console.log('\n--- 第六组：AI 场景 —— 向量数据结构约束 ---\n');

/*
 * ❌ JavaScript 风格：embedding 维度写错没人发现
 *
 *    const doc = { id: 1, embedding: [0.1, 0.2], metadata: { source: 'a' } };
 *    // 模型期望 1536 维，实际只有 2 维，写入向量库时才报错
 */

// ✅ TypeScript 风格：interface 约束字段，类型不匹配编译期拦截
interface DocumentChunk {
  id: string;
  content: string;
  embedding: number[];
  metadata: {
    source: string;
    page: number;
  };
}

const chunk: DocumentChunk = {
  id: 'doc-001',
  content: 'TypeScript 让向量数据结构稳定可靠',
  embedding: [0.12, 0.34, 0.56, 0.78],
  metadata: { source: 'day01.md', page: 1 },
};

console.log(`  文档 ID: ${chunk.id}`);
console.log(`  向量维度: ${chunk.embedding.length}`);
console.log(`  来源: ${chunk.metadata.source}#p${chunk.metadata.page}`);

// const bad: DocumentChunk = {
//   id: 1,                              // Error: Type 'number' is not assignable to type 'string'.
//   content: 'x',
//   embedding: [0.1, '0.2'],            // Error: Type 'string' is not assignable to type 'number'.
//   metadata: { source: 'a' },          // Error: Property 'page' is missing.
// };

console.log('\n=== 演示结束 ===');
