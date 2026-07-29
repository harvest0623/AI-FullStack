// type-assertion.ts
// 演示 as 断言、尖括号语法、非空断言、双重断言，以及断言与转换的区别

console.log('===== 1. as 语法断言 =====');

// 场景：从 unknown / 联合类型中提取具体类型（最常见用法）
const value: unknown = 'hello, ts';
const strLen = (value as string).length;
console.log('as 断言后调用 .length：', strLen);

// 场景：将联合类型断言为更具体的分支
type Result = { ok: true; data: string } | { ok: false; error: string };
const result: Result = { ok: true, data: 'success payload' };
// 即使不通过 ok 字段判断，也可直接断言为成功分支（开发者负责正确性）
const data = (result as { ok: true; data: string }).data;
console.log('断言联合类型为成功分支 → data=', data);

console.log('\n===== 2. 尖括号语法 <T>value（仅 .ts 文件可用） =====');

// 与 as 等价，但在 .tsx 中会与 JSX 标签冲突，因此 React 项目必须用 as
const v: unknown = 100;
const num = <number>v;
console.log('尖括号语法断言 →', num);

console.log('\n===== 3. 非空断言 ! =====');

// 从 Map.get 取值，TS 推断为 string | undefined
const userCache = new Map<string, string>();
userCache.set('id', 'trae-001');

const id: string | undefined = userCache.get('id');
// 开发者确认一定有值，用 ! 断言为非空（避免显式 if 判断）
console.log('非空断言 id!.toUpperCase() →', id!.toUpperCase());

// 链式非空断言：连续访问可能为空的属性
interface LinkedNode { value: number; next?: LinkedNode; }
const list: LinkedNode = { value: 1, next: { value: 2 } };
console.log('链式非空断言 list.next!.value →', list.next!.value);

// 注意：非空断言只是「告诉编译器别管」，运行时若真为 null/undefined 仍会抛错
// const missing = userCache.get('not-exist')!.toUpperCase(); // 运行时抛错：Cannot read properties of undefined

console.log('\n===== 4. 双重断言 as unknown as T =====');

// 当两个类型之间「重叠不足」时，TS 会拒绝直接断言
const raw: string = 'raw-string';
// const fake: number = raw as number; // ❌ 报错：string 与 number 重叠不足
// 此时通过 unknown 中转：先断言为 unknown，再断言为目标类型
const fake: number = raw as unknown as number;  // ✅ OK：双重断言
console.log('双重断言通过 unknown 中转 → fake=', fake, '（运行时仍是', typeof fake, '）');

console.log('\n===== 5. 类型断言 vs 类型转换 =====');

// 5.1 断言：只在编译期生效，运行时完全不影响值
const input: unknown = '42';
const asserted = input as number;
console.log('断言后运行时类型仍是 →', typeof asserted);  // 'string'

// 5.2 转换：运行时真正改变值
const converted = Number(input);
console.log('类型转换后运行时类型 →', typeof converted, '值=', converted);  // 'number' 42

// 5.3 一个常见错误：以为断言会做转换
const jsonStr: unknown = '"42"';        // 这是一个 JSON 字符串，内容是 "42"
const assertedNum = jsonStr as number;  // 编译期假装是 number，运行时仍是 string
console.log('错误做法（断言）typeof →', typeof assertedNum);  // 'string'

const parsed = JSON.parse(jsonStr as string);  // 先断言为 string 再解析：得到字符串 "42"
const realNum = Number(parsed);         // 再转换为数字 42
console.log('正确做法（解析 + 转换）typeof →', typeof realNum, '值=', realNum);  // 'number' 42

console.log('\n===== 6. 断言的合理使用场景 =====');

// 合理场景一：处理 JSON.parse 的结果（返回 any，应先断言为 unknown 再收窄）
const apiResponse = JSON.parse('{"name":"Trae","age":28}') as unknown;
if (typeof apiResponse === 'object' && apiResponse !== null && 'name' in apiResponse) {
  console.log('合理断言 + 收窄：name=', (apiResponse as { name: string }).name);
}

// 合理场景二：DOM 查询（浏览器环境，仅作文档说明）
//   const btn = document.querySelector('#submit') as HTMLButtonElement;
//   开发者确认 #submit 一定是 <button>，比 TS 默认推断的 Element | null 更精确

// 不合理场景：用断言绕过类型检查，掩盖真正的类型不匹配
// const bad = 'hello' as unknown as number;  // 危险：运行时仍是字符串，调用数字方法会崩
console.log('原则：断言只用于「你比编译器更清楚类型」的场景，不要用于掩盖错误');
