/**
 * Day03 - interface 基础演示
 * 主题：定义对象形状、可选属性 ?、只读属性 readonly、多余属性检查
 * 运行：npx ts-node interface-basic.ts
 */

console.log('=== 1. interface 定义对象形状 ===\n');

// interface 描述对象的"形状"——它只关心有哪些字段、字段是什么类型
// 不关心字段顺序，也不参与运行时（编译后会被完全擦除）
interface User {
  id: number;
  name: string;
  email: string;
}

const alice: User = {
  id: 1,
  name: 'Alice',
  email: 'alice@example.com',
};
console.log('[User] alice =', alice);

console.log('\n=== 2. 可选属性 ? ===\n');

// 在属性名后加 ? 表示该字段可缺省
// 注意：可选属性读出来是 T | undefined，访问它要做 narrowing
interface Article {
  title: string;
  tags?: string[];      // 可选
  publishedAt?: Date;   // 可选
}

const a1: Article = { title: 'TS 入门' };              // 合法：tags/publishedAt 都可省
const a2: Article = { title: 'TS 进阶', tags: ['ts'] }; // 合法
console.log('[Article] a1 =', a1);
console.log('[Article] a2 =', a2);

// 读可选属性前必须判空，否则 .length 等访问会触发 possibly undefined
if (a2.tags) {
  console.log('[Article] a2.tags.length =', a2.tags.length);
}

console.log('\n=== 3. 只读属性 readonly ===\n');

// readonly 修饰的属性只能在对象初始化时赋值，之后不可改
// 注意：readonly 仅在【编译期】检查，运行时不变性需用 Object.freeze 等手段
interface Repo {
  readonly owner: string;
  readonly name: string;
  stars: number;
}

const repo: Repo = { owner: 'torvalds', name: 'linux', stars: 100000 };
console.log('[Repo] 初始 =', repo);

// repo.owner = 'linus';   // ❌ TS2540: Cannot assign to 'owner' because it is read-only
repo.stars++;               // ✅ stars 不是 readonly，可以改
console.log('[Repo] stars++ =', repo);

// readonly 的"浅层"陷阱：readonly 只锁属性本身，不递归到嵌套对象
interface Window {
  readonly size: { width: number; height: number };
}
const win: Window = { size: { width: 800, height: 600 } };
win.size.width = 1024;      // ✅ 通过！size 本身 readonly，但 size.width 不是
console.log('[Window] size.width 被改了 =', win.size);

console.log('\n=== 4. 多余属性检查 Excess Property Checking ===\n');

// 当【对象字面量】直接赋值给一个有明确类型的变量时，TS 会做"多余属性检查"
// 字面量里出现了目标类型里没有的字段 → 报错
interface LoginPayload {
  username: string;
  password: string;
}

// ✅ 字面量字段正好匹配
const ok: LoginPayload = { username: 'bob', password: '123456' };
console.log('[Login] ok =', ok);

// ❌ 多了 remember 字段（取消注释会看到 TS2322）
// const bad: LoginPayload = { username: 'bob', password: '123456', remember: true };

// 绕过方式 1：用变量中转——TS 只对【直接赋值的字面量】做多余属性检查
const raw = { username: 'bob', password: '123456', remember: true };
const bypassed: LoginPayload = raw;   // ✅ raw 不是字面量，走结构化类型兼容
console.log('[Login] 绕过(变量中转) =', bypassed);

// 绕过方式 2：类型断言
const asserted: LoginPayload = {
  username: 'bob',
  password: '123456',
  remember: true,           // 多余字段
} as LoginPayload;          // 通过断言绕过
console.log('[Login] 绕过(断言) =', asserted);

// 绕过方式 3：在目标类型上加索引签名（不推荐，丢失精确性）
// interface LoginPayload { username: string; password: string; [k: string]: unknown }
