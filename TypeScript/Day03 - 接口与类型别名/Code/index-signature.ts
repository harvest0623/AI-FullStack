/**
 * Day03 - 索引签名 Index Signature
 * 主题：[key: string]: T、Record<string, T> 等价、字符串/数字索引共存规则、局限性
 * 运行：npx ts-node index-signature.ts
 */

console.log('=== 1. 索引签名基础 ===\n');

// 当对象的 key 是动态的、且所有 key 对应的 value 类型一致时，用索引签名
interface Scores {
  [subject: string]: number;   // 任意 string key，value 必须是 number
}

const s1: Scores = {
  math: 90,
  english: 85,
  physics: 78,
};
console.log('[Scores] s1 =', s1);

console.log('\n=== 2. 索引签名 + 已知属性 ===\n');

// 可以同时声明已知属性和索引签名
// 但约束：已知属性的类型必须【兼容】索引签名的 value 类型
interface Locale {
  lang: string;           // 已知属性，string
  [key: string]: string;  // 索引签名也是 string → 兼容
}

const zh: Locale = { lang: 'zh-CN', region: 'CN' };
console.log('[Locale] zh =', zh);

// ❌ 这种会报错：已知属性 number 与索引签名 string 不兼容
// interface Bad {
//   count: number;
//   [key: string]: string;   // ❌ Property 'count' of type 'number' is not assignable to string index type 'string'
// }

console.log('\n=== 3. 字符串索引与数字索引共存规则 ===\n');

// 规则：数字索引的 value 类型必须是字符串索引 value 类型的【子类型】
// 原因：JS 中 obj[0] 实际上是用 '0' 这个字符串 key 查的，
// 所以数字索引的值必须能放进字符串索引里
interface Dictionary {
  [key: string]: string;     // 字符串索引
  [key: number]: string;     // 数字索引（与字符串索引同类型，兼容）
}

const dict: Dictionary = { a: 'A', b: 'B' };
dict[0] = 'zero';            // 数字 key 实际存为字符串 '0'
console.log('[Dictionary] dict =', dict);
console.log('[Dictionary] dict[0] =', dict[0]);

// ❌ 数字索引值类型不能比字符串索引"更宽"
// interface BadDict {
//   [key: string]: string;
//   [key: number]: number;   // ❌ number 不是 string 的子类型
// }

console.log('\n=== 4. 索引签名 vs Record<string, T> ===\n');

// Record<K, V> 是 TS 内置工具类型，本质就是索引签名的语法糖
// 以下两种写法几乎等价
interface IScores { [k: string]: number }
type RScores = Record<string, number>;

const is1: IScores = { math: 90 };
const rs1: RScores = { math: 90 };
console.log('[等价] IScores =', is1, ', Record =', rs1);

// Record 的优势：可以用【联合类型】作为 key，比索引签名更精确
type HttpStatus = 200 | 404 | 500;
type StatusText = Record<HttpStatus, string>;

const statusText: StatusText = {
  200: 'OK',
  404: 'Not Found',
  500: 'Internal Server Error',
};
console.log('[Record 联合 key] statusText =', statusText);
// 索引签名做不到这一点：[k: 200 | 404 | 500] 非法

console.log('\n=== 5. 索引签名的局限性 ===\n');

// 局限 1：value 类型只能统一一个 T，无法区分不同 key
interface Config { [k: string]: string | number | boolean }
const c: Config = { host: '0.0.0.0', port: 8080, debug: true };
// 读取后类型被"抹平"为联合类型，丢失了"port 一定是 number"的信息
const portValue: string | number | boolean = c.port;
console.log('[局限1] c.port 类型被抹平 =', portValue);
// const portNum: number = c.port;   // ❌ 不能直接当 number 用

// 局限 2：value 类型如果是对象，需要写完整形状
interface RouteMap { [path: string]: { handler: () => void } }
const routes: RouteMap = {
  '/home': { handler: () => console.log('  → 命中 /home') },
  '/about': { handler: () => console.log('  → 命中 /about') },
};
routes['/home'].handler();

// 局限 3：无法表达"key 必须是某些值之一"——这一点 Record<联合, V> 解决了

console.log('\n=== 6. 替代方案：精确的对象类型 ===\n');

// 当需要"精确的若干 key + 各自的 value 类型"时，
// 直接写 interface / 对象 type 才最精确——每个字段类型都保留
interface PreciseConfig {
  host: string;
  port: number;     // 这里 port 一定是 number，不会丢失
  debug: boolean;
}

const pc: PreciseConfig = { host: '0.0.0.0', port: 8080, debug: true };
const port: number = pc.port;   // ✅ 类型精确
console.log('[PreciseConfig] port =', port);

// 配合 keyof + 映射类型，可以把精确对象转成 Record 形式
type ConfigKeys = keyof PreciseConfig;           // 'host' | 'port' | 'debug'
type ConfigValues = PreciseConfig[keyof PreciseConfig];  // string | number | boolean
console.log('[keyof] ConfigKeys 类型 = "host" | "port" | "debug"');
console.log('[索引访问] ConfigValues 类型 = string | number | boolean');
