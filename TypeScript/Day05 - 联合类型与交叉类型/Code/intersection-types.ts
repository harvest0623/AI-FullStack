/**
 * Day05 - 交叉类型（Intersection Types）
 *
 * 本文件演示：
 * 1. 交叉类型 & 的含义（与关系，同时具备所有类型属性）
 * 2. 交叉类型实现 mixin 模式
 * 3. 交叉类型的字段冲突：同名字段类型不兼容时退化为 never（或取交集）
 * 4. 交叉类型与 Object.assign 的对应关系
 */

// ============================================================
// 1. 交叉类型的基本含义：与关系
// ============================================================

interface HasName {
  name: string;
}

interface HasAge {
  age: number;
}

interface HasEmail {
  email: string;
}

// Person 同时具备 name / age / email 三个属性
type Person = HasName & HasAge & HasEmail;

const alice: Person = {
  name: 'Alice',
  age: 28,
  email: 'alice@example.com',
};

console.log('Person =>', alice);

// 任意一个属性缺失都会编译报错
// const bob: Person = { name: 'Bob', age: 30 };  // ❌ 缺少 email


// ============================================================
// 2. 交叉类型实现 mixin 模式
// ============================================================

// mixin：给一个对象“混入”额外能力，本质就是交叉类型
type Timestamped<T> = T & { createdAt: Date; updatedAt: Date };
type SoftDeletable<T> = T & { deletedAt: Date | null; isDeleted: boolean };
type Traceable<T> = T & { traceId: string };

// 业务实体本身只有核心字段
interface Article {
  id: number;
  title: string;
  content: string;
}

// 通过交叉叠加，得到一个“带时间戳 + 软删除 + 链路追踪”的文章类型
type ArticleEntity = Traceable<SoftDeletable<Timestamped<Article>>>;

const article: ArticleEntity = {
  id: 1,
  title: 'TS 进阶',
  content: '联合与交叉类型',
  createdAt: new Date(),
  updatedAt: new Date(),
  deletedAt: null,
  isDeleted: false,
  traceId: 'req-abc-123',
};

console.log('ArticleEntity =>', article);


// 函数式 mixin：把“混入能力”封装成函数
function withTimestamp<T extends object>(base: T): T & { createdAt: Date } {
  return { ...base, createdAt: new Date() };
}

function withLogger<T extends object>(base: T): T & { log(): void } {
  return {
    ...base,
    log() {
      console.log('[log]', JSON.stringify(base));
    },
  };
}

const raw = { host: 'localhost', port: 3000 };
const enriched = withLogger(withTimestamp(raw));
enriched.log();
console.log('enriched.createdAt =>', enriched.createdAt);


// ============================================================
// 3. 交叉类型的字段冲突
// ============================================================

// 情况 A：同名字段类型“兼容（可交集）”时，取交集
interface A {
  value: string | number;
}
interface B {
  value: string;
}
type AB = A & B;
// AB['value'] 等价于 (string | number) & string = string
const ab: AB = { value: 'hello' };
// const ab2: AB = { value: 123 };  // ❌ number 不能赋给 string
console.log('AB.value 取交集 =>', ab.value);


// 情况 B：同名字段类型“完全不兼容”时，退化为 never
interface X {
  flag: string;
}
interface Y {
  flag: number;
}
type XY = X & Y;
// XY['flag'] 等价于 string & number = never
// 意味着该字段实际上无法赋任何值，对象整体也无法构造
type XYFlag = XY['flag'];   // never

console.log('XY.flag 类型为 never，无法构造 XY 实例');
// 注意：以下赋值都会编译报错
// const xy: XY = { flag: 'x' };  // ❌ string 不能赋给 never
// const xy2: XY = { flag: 1 };   // ❌ number 不能赋给 never


// 情况 C：方法冲突（参数个数不同）会变成函数重载
interface Greetable {
  greet(name: string): string;
}
interface FormalGreetable {
  greet(name: string, title: string): string;
}
type Greeter = Greetable & FormalGreetable;
// greet 形成重载：可以 greet(name) 或 greet(name, title)

function greetSomeone(g: Greeter): void {
  // 调用时按重载匹配
  const a = g.greet('Alice');          // 走单参重载
  const b = g.greet('Bob', 'Dr.');     // 走双参重载
  console.log('重载结果 =>', a, '|', b);
}

greetSomeone({
  // 实现签名用可选参数兼容两个重载
  greet(name: string, title?: string): string {
    return title ? `Hello, ${title} ${name}` : `Hello, ${name}`;
  },
});


// ============================================================
// 4. 交叉类型与 Object.assign 的对应关系
// ============================================================

// Object.assign 把多个对象合并为一个，运行时行为正好对应交叉类型
const withName = { name: 'Carol' };
const withAge = { age: 30 };
const withRole = { role: 'admin' };

// 运行时合并
const merged = Object.assign({}, withName, withAge, withRole);

// 类型层面：交叉类型描述同样的结构
type MergedType = typeof withName & typeof withAge & typeof withRole;
const typedMerged: MergedType = merged;   // 结构兼容

console.log('Object.assign 结果 =>', typedMerged);


// 交叉类型用于“合并默认配置与用户配置”
interface DefaultConfig {
  timeout: number;
  retries: number;
  baseURL: string;
}
interface UserConfig {
  baseURL?: string;
  timeout?: number;
}
type FinalConfig = DefaultConfig & Required<UserConfig>;

function makeConfig(def: DefaultConfig, user: Required<UserConfig>): FinalConfig {
  return { ...def, ...user };   // 运行时合并，等价于交叉类型
}

const cfg = makeConfig(
  { timeout: 3000, retries: 3, baseURL: '/api' },
  { baseURL: '/api/v2', timeout: 5000 }
);
console.log('FinalConfig =>', cfg);


// ============================================================
// 5. 交叉 vs 联合：一个对比例子
// ============================================================

interface Cat {
  meow(): void;
}
interface Dog {
  bark(): void;
}

// 联合：要么是猫要么是狗，只能调用“共有”方法（这里没有共有方法）
type CatOrDog = Cat | Dog;

// 交叉：既是猫又是狗（同时拥有两种能力）
type CatDog = Cat & Dog;

const chimera: CatDog = {
  meow() { console.log('喵~'); },
  bark() { console.log('汪！'); },
};
chimera.meow();
chimera.bark();


console.log('\n--- intersection-types.ts 执行完毕 ---');
