/**
 * Day05 - 类型收窄：typeof / in / instanceof / 等值收窄 / truthy
 *
 * 本文件演示 TS 控制流分析下的几种“类型守卫”：
 * 1. typeof 守卫
 * 2. in 守卫（属性存在判断）
 * 3. instanceof 守卫（类实例判断）
 * 4. 等值收窄（=== 字面量）
 * 5. truthy 收窄（过滤 falsy 值）
 */

// ============================================================
// 1. typeof 守卫
// ============================================================

// typeof 返回的字符串集合是有限的：
// 'string' | 'number' | 'boolean' | 'undefined' | 'object' | 'function'
// | 'symbol' | 'bigint'
function padLeft(value: string | number, padding: string | number): string {
  // 用 typeof 把联合类型“切成”单一类型
  if (typeof padding === 'number') {
    // 此处 padding 收窄为 number
    return ' '.repeat(padding) + value;
  }
  // 此处 padding 收窄为 string
  return padding + value;
}

console.log(padLeft('hi', 4));
console.log(padLeft('hi', '>>>'));

// typeof 的坑：null 的 typeof 是 'object'，不是 'null'
function inspect(x: string | number | null | object): void {
  if (typeof x === 'object') {
    // 注意：null 也会进入这里！
    if (x === null) {
      console.log('是 null');
    } else {
      console.log('是对象：', (x as Record<string, unknown>).constructor?.name);
    }
  } else if (typeof x === 'string') {
    console.log('是字符串：', x.toUpperCase());
  } else if (typeof x === 'number') {
    console.log('是数字：', x.toFixed(2));
  }
}

inspect('abc');
inspect(123);
inspect(null);
inspect({ key: 'value' });

// typeof 对 bigint 和 symbol 的支持
function detectSpecial(x: symbol | bigint | string): string {
  if (typeof x === 'symbol') return 'symbol';
  if (typeof x === 'bigint') return 'bigint';
  return 'string';
}
console.log('特殊类型 =>', detectSpecial(Symbol('s')), detectSpecial(10n), detectSpecial('x'));


// ============================================================
// 2. in 守卫：属性存在判断
// ============================================================

interface Fish {
  swim(): void;
}
interface Bird {
  fly(): void;
}
type Animal = Fish | Bird;

function move(a: Animal): void {
  if ('swim' in a) {
    // 此处 a 收窄为 Fish
    a.swim();
  } else {
    // 此处 a 收窄为 Bird（else 分支自动收窄）
    a.fly();
  }
}

move({ swim() { console.log('游'); } });
move({ fly() { console.log('飞'); } });

// in 守卫也可用于可选属性判断
interface Config {
  host: string;
  port?: number;
  timeout?: number;
}
function readConfig(c: Config): void {
  console.log('host =>', c.host);
  if ('port' in c) console.log('port =>', c.port);
  if ('timeout' in c) console.log('timeout =>', c.timeout);
}

readConfig({ host: 'localhost', port: 3000 });


// ============================================================
// 3. instanceof 守卫：类实例判断
// ============================================================

class ValidationError extends Error {
  constructor(public field: string, message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

class NetworkError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

function reportError(err: ValidationError | NetworkError): string {
  // instanceof 让 TS 把类型收窄到对应类
  if (err instanceof ValidationError) {
    return `[校验错误] 字段 ${err.field}：${err.message}`;
  }
  if (err instanceof NetworkError) {
    return `[网络错误] HTTP ${err.statusCode}：${err.message}`;
  }
  return '未知错误';
}

console.log(reportError(new ValidationError('email', '格式不正确')));
console.log(reportError(new NetworkError(503, '服务不可用')));

// instanceof 也可用于内置类型；Array.isArray 是更地道的写法
function first<T>(arr: T[] | T): T | undefined {
  if (Array.isArray(arr)) {
    return arr[0];   // arr 收窄为 T[]
  }
  return undefined;
}
console.log('first =>', first([10, 20]));


// ============================================================
// 4. 等值收窄：用 === / !== 收窄到字面量
// ============================================================

type TriState = 'on' | 'off' | 'standby';

function describe(s: TriState): string {
  if (s === 'on') return '开启';         // s 收窄为 'on'
  if (s === 'off') return '关闭';        // s 收窄为 'off'
  return '待机';                          // s 自动收窄为 'standby'
}

console.log(describe('on'), describe('off'), describe('standby'));

// 用 === null / !== undefined 过滤可空类型
function safeLength(s: string | null | undefined): number {
  if (s === null || s === undefined) {
    return 0;
  }
  // 此处 s 收窄为 string
  return s.length;
}

console.log('safeLength =>', safeLength('abc'), safeLength(null), safeLength(undefined));


// ============================================================
// 5. truthy 收窄：过滤 falsy 值
// ============================================================

// falsy 值：false / 0 / '' / null / undefined / NaN
function printName(name: string | null | undefined): void {
  // truthy 收窄：if 内 name 不能为 null/undefined/'' （空字符串也排除）
  if (name) {
    console.log('名字是 =>', name.toUpperCase());
  } else {
    console.log('名字为空或缺失');
  }
}

printName('TypeScript');
printName(null);
printName('');

// 用 truthy 收窄过滤“可能为空”的列表
function firstItem<T>(arr: T[] | null | undefined): T | undefined {
  // arr 为 null/undefined 时为 falsy，进入 else
  if (arr && arr.length > 0) {
    return arr[0];
  }
  return undefined;
}

console.log('firstItem =>', firstItem([1, 2, 3]), firstItem(null), firstItem([]));

// 注意 truthy 收窄的盲区：0 / '' 会被当作 falsy 排除
function processValue(v: number | string | null): void {
  if (v) {
    // 这里 v 是 number | string，但 0 和 '' 不会进入
    console.log('有值 =>', v);
  } else {
    // 这里 v 是 number | '' | null
    console.log('falsy =>', v);
  }
}

processValue(0);   // 进入 falsy 分支
processValue('');  // 进入 falsy 分支


// ============================================================
// 6. 控制流分析：if/else、三目、return 提前退出都会收窄
// ============================================================

function pickValue(v: string | number | null): string {
  // return 提前退出：之后 v 不再是 null
  if (v === null) return '空';

  // 三目表达式同样会收窄
  return typeof v === 'string' ? `S:${v}` : `N:${v.toFixed(0)}`;
}

console.log(pickValue(null), pickValue('hi'), pickValue(3.14));


console.log('\n--- typeof-narrowing.ts 执行完毕 ---');
