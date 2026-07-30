/**
 * Day05 - 自定义类型守卫（Custom Type Guards）
 *
 * 本文件演示：
 * 1. 谓词 x is Type 的语法
 * 2. 常用守卫函数：isString / isNumber / isError / isNonNull
 * 3. 用自定义守卫校验外部数据（API 返回、JSON.parse 结果）
 */

// ============================================================
// 1. 基本语法：parameterName is Type
// ============================================================

// 关键字 is 让函数的返回值不仅是 boolean，还“告诉”编译器
// 一旦返回 true，参数在调用处会被收窄为指定类型
function isString(x: unknown): x is string {
  return typeof x === 'string';
}

function isNumber(x: unknown): x is number {
  return typeof x === 'number' && !Number.isNaN(x);
}

function isBoolean(x: unknown): x is boolean {
  return typeof x === 'boolean';
}

// 例子：在联合类型上做精确收窄
function format(value: string | number | boolean | null): string {
  if (isString(value)) {
    return `字符串：${value.toUpperCase()}`;   // value 收窄为 string
  }
  if (isNumber(value)) {
    return `数字：${value.toFixed(2)}`;        // value 收窄为 number
  }
  if (isBoolean(value)) {
    return `布尔：${value ? '真' : '假'}`;
  }
  return '空';
}

console.log(format('abc'));
console.log(format(3.14));
console.log(format(true));
console.log(format(null));

// 注意 NaN 处理：typeof NaN === 'number'，所以 isNumber 单独过滤了 NaN
console.log('NaN 是数字吗？', isNumber(NaN));   // false


// ============================================================
// 2. 守卫函数：isError / isNonNull / isRecord
// ============================================================

function isError(x: unknown): x is Error {
  return x instanceof Error;
}

function isNonNull<T>(x: T | null | undefined): x is T {
  return x !== null && x !== undefined;
}

// 判断是否为“普通对象”，可进一步用于对象守卫
function isRecord(x: unknown): x is Record<string, unknown> {
  return typeof x === 'object' && x !== null && !Array.isArray(x);
}

const unknowns: unknown[] = [
  new Error('boom'),
  { a: 1 },
  [1, 2, 3],
  null,
  'text',
];

unknowns.forEach((u) => {
  if (isError(u)) {
    console.log('[Error]', u.message);
  } else if (isRecord(u)) {
    console.log('[Record] keys =', Object.keys(u));
  } else if (Array.isArray(u)) {
    console.log('[Array] length =', u.length);
  } else {
    console.log('[Other]', u);
  }
});


// ============================================================
// 3. 守卫组合：&& / ||
// ============================================================

// 多个守卫用 && 组合，会依次收窄
function isNonEmptyString(x: unknown): x is string {
  return isString(x) && x.length > 0;
}

console.log('isNonEmptyString("x") =>', isNonEmptyString('x'));
console.log('isNonEmptyString("") =>', isNonEmptyString(''));
console.log('isNonEmptyString(1) =>', isNonEmptyString(1));

// 过滤掉 null/undefined，保留有效项
const rawList: (string | null | undefined)[] = ['a', null, 'b', undefined, 'c'];
const cleaned = rawList.filter(isNonNull);
console.log('filter(isNonNull) =>', cleaned);   // ['a', 'b', 'c']


// ============================================================
// 4. 校验外部数据：API 响应、JSON.parse 结果
// ============================================================

// 外部数据通常是 unknown，必须用守卫“逐步证明”其结构
interface UserDTO {
  id: number;
  name: string;
  email?: string;
}

function isUserDTO(x: unknown): x is UserDTO {
  if (!isRecord(x)) return false;
  return (
    typeof x.id === 'number' &&
    typeof x.name === 'string' &&
    (x.email === undefined || typeof x.email === 'string')
  );
}

// 模拟一段从服务端拿到的未知 JSON
const json = `{"id": 1, "name": "Alice", "email": "alice@example.com"}`;
const parsed: unknown = JSON.parse(json);

if (isUserDTO(parsed)) {
  // 此处 parsed 收窄为 UserDTO
  console.log('校验通过 =>', parsed.id, parsed.name, parsed.email);
} else {
  console.log('校验失败：数据不符合 UserDTO 结构');
}

// 模拟一段恶意/损坏的 JSON
const bad = `{"id": "x", "name": 123}`;
const badParsed: unknown = JSON.parse(bad);
console.log('bad 是否为 UserDTO =>', isUserDTO(badParsed));   // false


// ============================================================
// 5. 嵌套对象的守卫校验
// ============================================================

interface Order {
  orderId: string;
  amount: number;
  user: UserDTO;
}

function isOrder(x: unknown): x is Order {
  if (!isRecord(x)) return false;
  if (typeof x.orderId !== 'string') return false;
  if (typeof x.amount !== 'number') return false;
  return isUserDTO(x.user);
}

const orderJson = `{
  "orderId": "ORD-001",
  "amount": 99.5,
  "user": { "id": 1, "name": "Bob" }
}`;

const order: unknown = JSON.parse(orderJson);
if (isOrder(order)) {
  console.log('订单校验通过 =>', order.orderId, order.user.name);
}


// ============================================================
// 6. 用守卫函数复用类型判断逻辑
// ============================================================

// 守卫最大的价值：把“判断逻辑 + 类型收窄”封装成可复用函数
function categorize(value: unknown): string {
  if (isString(value)) return `string(len=${value.length})`;
  if (isNumber(value)) return `number(${value})`;
  if (isBoolean(value)) return `boolean(${value})`;
  if (isError(value)) return `error(${value.message})`;
  if (isRecord(value)) return `object(keys=${Object.keys(value).length})`;
  if (Array.isArray(value)) return `array(len=${value.length})`;
  return String(value);
}

console.log(categorize('hello'));
console.log(categorize(42));
console.log(categorize(new Error('oops')));
console.log(categorize({ a: 1, b: 2 }));
console.log(categorize([1, 2, 3]));


console.log('\n--- custom-guard.ts 执行完毕 ---');
