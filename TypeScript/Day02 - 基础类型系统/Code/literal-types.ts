// literal-types.ts
// 演示字面量类型（字符串 / 数字 / 布尔）与联合字面量模拟状态机

console.log('===== 1. 字符串字面量类型 =====');

// 把类型限定为若干个具体字符串之一，常用于枚举式的固定取值
type Direction = 'up' | 'down' | 'left' | 'right';
function move(d: Direction) {
  console.log('向', d, '移动');
}
move('up');
move('right');
// move('north'); // ❌ 报错：'north' 不能分配给类型 Direction

type Greeting = 'hello' | 'hi' | 'hey';
function greet(g: Greeting) {
  console.log(g, 'world');
}
greet('hello');

console.log('\n===== 2. 数字字面量类型 =====');

type Dice = 1 | 2 | 3 | 4 | 5 | 6;
function roll(d: Dice) {
  console.log('掷出：', d);
}
roll(3);
// roll(7); // ❌ 报错：7 不在联合类型 Dice 中

// 实际应用：限定 HTTP 状态码
type HttpStatus = 200 | 201 | 400 | 404 | 500;
function describeStatus(code: HttpStatus) {
  switch (code) {
    case 200: return 'OK';
    case 201: return 'Created';
    case 400: return 'Bad Request';
    case 404: return 'Not Found';
    case 500: return 'Internal Server Error';
  }
}
console.log('HTTP 200：', describeStatus(200));
console.log('HTTP 404：', describeStatus(404));

console.log('\n===== 3. 布尔字面量类型 =====');

// true / false 本身就是字面量类型，boolean = true | false
type AlwaysTrue = true;
const t: AlwaysTrue = true;
// const f: AlwaysTrue = false; // ❌ 报错：false 不能分配给类型 true
console.log('布尔字面量 true：', t);

// 实际应用：标记某个配置永远为某固定值
interface StrictConfig {
  readonly strict: true;  // 此属性只能是 true，不能是 false
  readonly mode: 'production';
}
const cfg: StrictConfig = { strict: true, mode: 'production' };
console.log('严格配置：', cfg);

console.log('\n===== 4. 联合字面量模拟状态机 =====');

// 用联合字面量代替枚举（enum），类型更精确且 tree-shaking 更友好
type RequestStatus = 'idle' | 'loading' | 'success' | 'error';

interface RequestState {
  status: RequestStatus;
  data?: string;
  error?: string;
}

function render(state: RequestState): string {
  switch (state.status) {
    case 'idle':
      return '等待发起请求...';
    case 'loading':
      return '加载中...';
    case 'success':
      return `成功：${state.data}`;
    case 'error':
      return `失败：${state.error}`;
  }
}

console.log(render({ status: 'idle' }));
console.log(render({ status: 'loading' }));
console.log(render({ status: 'success', data: '用户列表' }));
console.log(render({ status: 'error', error: '网络超时' }));

console.log('\n===== 5. 字面量类型与 const 推断的关系 =====');

// const 声明的原始值会被自动推断为字面量类型（详见 primitive-types.ts）
const COLOR = 'red';   // 推断为 'red'（字面量类型）
let color = 'red';     // 推断为 string（宽类型）
color = 'blue';        // ✅ OK：string 可重新赋值为任意字符串
console.log('let color 推断为 string →', color);

// 用 typeof 把 const 变量的字面量类型提取出来作为类型
type Color = typeof COLOR;   // 等价于 type Color = 'red'
const c: Color = 'red';
// const c2: Color = 'blue'; // ❌ 报错：'blue' 不能分配给 'red'
console.log('const COLOR 推断为字面量类型，typeof 取出 → c=', c);

console.log('\n===== 6. 字面量类型 vs 枚举 enum =====');

// 字面量联合 vs enum 的取舍：
//   - 字面量联合：值就是字符串本身，调试友好，tree-shaking 好，无需导入导出
//   - enum：会生成额外运行时代码，但提供「反向映射」（数字枚举）和命名空间
enum ColorEnum {
  Red = 'RED',
  Green = 'GREEN',
  Blue = 'BLUE',
}

type ColorLiteral = 'RED' | 'GREEN' | 'BLUE';

function paintEnum(c: ColorEnum) {
  console.log('[enum] 涂色：', c);
}
function paintLiteral(c: ColorLiteral) {
  console.log('[literal] 涂色：', c);
}

paintEnum(ColorEnum.Red);
paintLiteral('RED');  // 字面量联合无需导入，直接用字符串
