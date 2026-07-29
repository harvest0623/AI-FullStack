// array-tuple.ts
// 演示数组类型、只读数组、元组、命名元组、可选元素、rest 元素

console.log('===== 1. 数组类型两种写法 =====');

// 写法一：T[]（推荐，更简洁）
const scores: number[] = [90, 85, 92];
const names: string[] = ['Alice', 'Bob', 'Carol'];

// 写法二：Array<T>（泛型写法，二者完全等价）
const temps: Array<number> = [36.5, 37.0, 36.8];
const flags: Array<boolean> = [true, false, true];

console.log('T[] 写法：scores=', scores, 'names=', names);
console.log('Array<T> 写法：temps=', temps, 'flags=', flags);

console.log('\n===== 2. 只读数组 =====');

// readonly T[] 与 ReadonlyArray<T> 等价，二者都禁止修改
const readonlyScores: readonly number[] = [90, 85, 92];
const frozenNames: ReadonlyArray<string> = ['Alice', 'Bob'];

// readonlyScores.push(100);  // ❌ 报错：类型 "readonly number[]" 上不存在属性 "push"
// readonlyScores[0] = 100;   // ❌ 报错：索引签名只允许读取
console.log('readonly number[]：', readonlyScores);
console.log('ReadonlyArray<string>：', frozenNames);

// 普通数组可以赋值给只读数组（可变 → 只读 是安全的）
const mutableArr: number[] = [1, 2, 3];
const immutableArr: readonly number[] = mutableArr; // ✅ OK
// const backToMutable: number[] = immutableArr; // ❌ 报错：只读数组不能赋回可变数组
console.log('可变 → 只读 OK：', immutableArr);

console.log('\n===== 3. 元组 Tuple：固定长度与类型 =====');

// 元组：每个位置的类型都明确，长度也固定（区别于「同类型若干个」的数组）
const point: [number, number] = [10, 20];
const httpStatus: [number, string] = [404, 'Not Found'];

console.log('元组 [number, number]：point=', point);
console.log('元组 [number, string]：httpStatus=', httpStatus);

// 访问越界会报错
// point[2]; // ❌ 报错：长度为 2 的元组在索引 "2" 处没有元素

console.log('\n===== 4. 命名元组（带标签） =====');

// 命名元组：在类型位置加标签，仅作为文档提示，运行时无影响
// 调用方在 IDE 悬浮时能看到每个位置的含义，比纯 [number, number] 可读性更好
const namedPoint: [x: number, y: number] = [10, 20];
const httpResponse: [status: number, body: string] = [200, 'OK'];

console.log('命名元组 [x: number, y: number]：', namedPoint);
console.log('命名元组 [status: number, body: string]：', httpResponse);

console.log('\n===== 5. 可选元素的元组 =====');

// 末尾元素可用 ? 标记为可选
const optTuple1: [number, string?] = [1];
const optTuple2: [number, string?] = [1, 'two'];

console.log('可选元素元组 [1]：', optTuple1);
console.log('可选元素元组 [1, "two"]：', optTuple2);

console.log('\n===== 6. rest 元素（剩余元素） =====');

// rest 元素：表示「若干个同类型元素」，常用在前缀固定 + 后续任意数量的场景
const stringNumberPairs: [string, ...number[]] = ['scores', 90, 85, 92];
const leading: [number, number, ...string[]] = [1, 2, 'a', 'b', 'c'];

console.log('rest 元素 [string, ...number[]]：', stringNumberPairs);
console.log('rest 元素 [number, number, ...string[]]：', leading);

// 实际应用：函数参数中固定前缀 + 任意数量同类型后续
function logCall(id: string, ...rest: [timestamp: number, ...args: string[]]) {
  console.log(`[${id}] 时间戳=${rest[0]}，附加参数=${rest.slice(1)}`);
}
logCall('req-001', 1700000000, 'GET', '/api/users', '200');

console.log('\n===== 7. 数组与元组的对比 =====');

// 数组：所有元素同类型，长度任意
const arr: number[] = [1, 2, 3, 4, 5];
arr.push(6); // OK

// 元组：每个位置类型独立，长度固定
const tuple: [number, string, boolean] = [1, 'two', true];
// tuple.push(2); // ⚠️ 注意：TS 允许 push 但会破坏元组语义，应避免

console.log('数组 number[] 长度可变：', arr);
console.log('元组 [number, string, boolean]：', tuple);
