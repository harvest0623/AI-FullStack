/**
 * Day08 - 类型查询与索引（keyof / typeof / T[K] / T[number]）
 *
 * 本文件演示：
 * 1. keyof T：获取类型的所有键的联合类型
 * 2. typeof T：获取值的类型（值空间 → 类型空间）
 * 3. 索引访问类型 T[K]：获取对象某属性的类型
 * 4. T[number]：获取数组/元组的元素类型
 * 5. 综合实战：类型安全的属性访问器
 */

export {};

// ============================================================
// 1. keyof T：获取类型的所有键的联合类型
// ============================================================

interface User {
  id: number;
  name: string;
  email: string;
  age?: number;          // 可选属性的键也会进入 keyof 结果
  readonly role: string; // readonly 修饰不影响 keyof
}

// keyof 把“键的集合”提到类型空间
type UserKeys = keyof User;
// 等价于：'id' | 'name' | 'email' | 'age' | 'role'

// 用 keyof 约束泛型参数，实现“键必须是对象真实存在的属性”
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const alice: User = { id: 1, name: 'Alice', email: 'a@x.com', role: 'admin' };

const aliceId   = getProperty(alice, 'id');    // number
const aliceName = getProperty(alice, 'name');  // string
// getProperty(alice, 'phone');                // ❌ 'phone' 不是 User 的键

console.log('[keyof] getProperty =>', aliceId, aliceName);


// keyof 对索引签名同样有效
interface StringMap {
  [key: string]: string;
}
type StringMapKeys = keyof StringMap;   // string | number（JS 对象 key 会自动转字符串）

// keyof 对数组/元组返回数字索引 + 数组原型方法名
type ArrKeys = keyof string[];          // number | 'length' | 'push' | 'pop' | ...
type TupleKeys = keyof [string, number]; // number | '0' | '1' | 'length' | ...

// 用 keyof 检查“某属性是否存在”
type HasEmail = 'email' extends keyof User ? true : false;   // true
type HasPhone = 'phone' extends keyof User ? true : false;   // false
console.log('[keyof] HasEmail =', true as HasEmail, '| HasPhone =', false as HasPhone);


// ============================================================
// 2. typeof T：从值推导类型（值空间 → 类型空间）
// ============================================================

// typeof 是把“变量/常量/表达式”的类型提取到类型空间
const config = {
  host: 'localhost',
  port: 3000,
  retries: 3,
  debug: true,
};

type AppConfig = typeof config;
// 等价于：{ host: string; port: number; retries: number; debug: boolean }

// 常见用法：以对象字面量为“单一数据源”同时提供值与类型
const HTTP_STATUS = {
  OK: 200,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
} as const;          // as const 让值成为字面量类型

type HttpStatus = typeof HTTP_STATUS;
// { readonly OK: 200; readonly NOT_FOUND: 404; readonly SERVER_ERROR: 500 }

type OkValue = HttpStatus['OK'];   // 200（字面量类型，而非宽泛的 number）
console.log('[typeof] HTTP_STATUS.OK =', HTTP_STATUS.OK, '| 类型字面量 =', 200 as OkValue);


// typeof 与函数：获取函数签名类型
function greet(name: string, age?: number): string {
  return age ? `Hi ${name}(${age})` : `Hi ${name}`;
}
type GreetFn = typeof greet;   // (name: string, age?: number) => string

const greeter: GreetFn = greet;
console.log('[typeof] greet =>', greeter('Bob', 25));


// typeof 与 class：获取“构造函数类型”（实例类型用 ClassName 直接拿）
class Point {
  constructor(public x: number, public y: number) {}
  distance() { return Math.hypot(this.x, this.y); }
}
type PointCtor = typeof Point;   // 构造函数类型，可 new
const P: PointCtor = Point;
const p = new P(3, 4);
console.log('[typeof] Point instance =>', p.x, p.y, 'distance =', p.distance().toFixed(2));


// typeof 配合 as const 推导字面量元组
const directions = ['up', 'down', 'left', 'right'] as const;
type Direction = typeof directions;          // readonly ['up', 'down', 'left', 'right']
type DirectionTupleElem = Direction[number]; // 'up' | 'down' | 'left' | 'right'
console.log('[typeof] directions =>', directions.join(', '));


// ============================================================
// 3. 索引访问类型 T[K]：获取对象某属性的类型
// ============================================================

interface Article {
  title: string;
  author: { name: string; email: string };   // 嵌套结构
  tags: string[];
  publishedAt: Date | null;
}

// 单个键：取出对应属性的类型
type TitleType   = Article['title'];         // string
type AuthorType  = Article['author'];        // { name: string; email: string }
type TagsType    = Article['tags'];          // string[]
type PublishedAt = Article['publishedAt'];   // Date | null

// 多个键联合：返回这些属性类型的联合
type StringFields = Article['title' | 'tags'];   // string | string[] = string[]

// 嵌套索引：链式访问
type AuthorName = Article['author']['name'];     // string
type TagsElem   = Article['tags'][number];       // string

console.log('[T[K]] 嵌套索引 =>',
  'title:', 'Hello',
  'author.name:', 'Alice',
  'tags[0]:', 'ts',
  'publishedAt:', new Date().toISOString());


// 用 keyof + T[K] 做“属性取值器”的返回类型推断
function pickField<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const article: Article = {
  title: 'TS 进阶',
  author: { name: 'Bob', email: 'b@x.com' },
  tags: ['ts', 'type'],
  publishedAt: new Date(),
};

const pickedTitle = pickField(article, 'title');   // string
const pickedTags  = pickField(article, 'tags');    // string[]
console.log('[T[K]] pickField =>', pickedTitle, '| tags:', pickedTags.join('/'));


// 用索引访问实现“类型同态映射”的前置知识
type OptionalKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? K : never;   // 见 mapped-types.ts
}[keyof T];

// ============================================================
// 4. T[number]：获取数组/元组的元素类型
// ============================================================

// 对数组类型用 [number]：返回元素类型
type StrArr = string[];
type StrArrElem = StrArr[number];   // string

type NumArr = number[];
type NumArrElem = NumArr[number];   // number

// 对元组用 [number]：返回所有元素类型的联合
type Tuple3 = [string, number, boolean];
type TupleElem = Tuple3[number];    // string | number | boolean

// 对 readonly 元组（as const 推导出的字面量元组）用 [number]：返回字面量联合
const PALETTE = ['red', 'green', 'blue'] as const;
type Palette = typeof PALETTE;          // readonly ['red', 'green', 'blue']
type Color = Palette[number];           // 'red' | 'green' | 'blue'

const c: Color = 'green';
console.log('[T[number]] Color =', c, '| 全部:', PALETTE.join(','));


// 应用：从运行时常量数组反推联合类型（替代手写 enum）
const ROLES = ['admin', 'editor', 'viewer'] as const;
type Role = typeof ROLES[number];   // 'admin' | 'editor' | 'viewer'

function grant(role: Role) {
  return `已授权：${role}`;
}
console.log('[T[number]] grant =>', grant('admin'));
// grant('owner');   // ❌ 'owner' 不在联合中


// 应用：把元组每个位置的元素类型提取出来
type FirstElem = Tuple3[0];    // string
type SecondElem = Tuple3[1];   // number
type ThirdElem = Tuple3[2];    // boolean
console.log('[T[number]] 元组位置 =>',
  'first:', 's' as FirstElem,
  '| second:', 1 as SecondElem,
  '| third:', true as ThirdElem);


// ============================================================
// 5. 综合实战：类型安全的属性访问器
// ============================================================

// 一个常见的模式：用 keyof + typeof 实现强类型的 get/set 辅助函数

// 用显式类型标注（而非 as const），让 fontSize 为 number，便于 setter 修改
const settings: {
  theme: 'dark' | 'light';
  fontSize: number;
  sidebar: boolean;
} = {
  theme: 'dark',
  fontSize: 14,
  sidebar: true,
};

type Settings = typeof settings;          // { theme: 'dark'|'light'; fontSize: number; sidebar: boolean }
type SettingKey = keyof Settings;         // 'theme' | 'fontSize' | 'sidebar'

// 强类型 getter：返回值类型与 key 严格对应
function getSetting<K extends SettingKey>(key: K): Settings[K] {
  return settings[key];
}

// 强类型 setter：新值必须匹配该 key 的字段类型
function setSetting<K extends SettingKey>(key: K, value: Settings[K]): void {
  // 实际项目里这里会触发更新逻辑，下面只是演示类型
  console.log(`[实战] setSetting(${String(key)}, ${JSON.stringify(value)})`);
}

const theme    = getSetting('theme');     // 'dark' | 'light'
const fontSize = getSetting('fontSize');  // number
const sidebar  = getSetting('sidebar');   // boolean
console.log('[实战] 当前 settings =>',
  'theme:', theme,
  '| fontSize:', fontSize,
  '| sidebar:', sidebar);

setSetting('theme', 'light');     // ✅
setSetting('fontSize', 16);       // ✅
// setSetting('theme', 'blue');   // ❌ 'blue' 不在 'dark' | 'light' 中
// setSetting('fontSize', '16');  // ❌ 字符串不能赋给 number


console.log('\n--- keyof-typeof.ts 执行完毕 ---');
