/**
 * Day05 - 可辨识联合（Discriminated Unions）
 *
 * 本文件演示：
 * 1. 用字面量类型的公共字段（type/kind）做判别
 * 2. Shape 类型家族：circle / square / rectangle
 * 3. switch 收窄 + 穷尽检查
 * 4. 可辨识联合实现状态机
 */

// ============================================================
// 1. 为什么需要可辨识联合
// ============================================================

// 普通联合：成员之间没有“明显标识”，收窄时要靠 in 或 typeof
interface CircleRaw {
  radius: number;
}
interface SquareRaw {
  side: number;
}
type ShapeRaw = CircleRaw | SquareRaw;

function areaRaw(s: ShapeRaw): number {
  // 只能靠 in 判断属性是否存在
  if ('radius' in s) {
    return Math.PI * s.radius * s.radius;
  }
  return s.side * s.side;
}

// 可辨识联合：每个成员都有同名的“判别字段”（字面量类型），收窄更直观
interface Circle {
  type: 'circle';   // 字面量类型，是该成员的“身份证”
  radius: number;
}
interface Square {
  type: 'square';
  side: number;
}
interface Rectangle {
  type: 'rectangle';
  width: number;
  height: number;
}

type Shape = Circle | Square | Rectangle;


// ============================================================
// 2. switch 收窄：按判别字段分发
// ============================================================

function area(s: Shape): number {
  switch (s.type) {
    case 'circle':
      // 此处 s 被收窄为 Circle
      return Math.PI * s.radius ** 2;
    case 'square':
      // 此处 s 被收窄为 Square
      return s.side ** 2;
    case 'rectangle':
      // 此处 s 被收窄为 Rectangle
      return s.width * s.height;
  }
}

function describeShape(s: Shape): string {
  // switch 之外的等值收窄：用 === 也能让 TS 收窄
  if (s.type === 'circle') {
    return `圆形，半径 ${s.radius}`;
  }
  if (s.type === 'square') {
    return `正方形，边长 ${s.side}`;
  }
  return `矩形，${s.width} x ${s.height}`;
}

const shapes: Shape[] = [
  { type: 'circle', radius: 2 },
  { type: 'square', side: 3 },
  { type: 'rectangle', width: 4, height: 5 },
];

shapes.forEach((s) => {
  console.log(`${describeShape(s)}，面积 = ${area(s).toFixed(2)}`);
});


// ============================================================
// 3. 穷尽检查：保证每个分支都被处理
// ============================================================

// 见 exhaustive-check.ts，这里只演示基本思路：
// 在 default 分支把 s 赋给 never，若遗漏某个 case 编译器会报错。
function assertNever(x: never): never {
  throw new Error(`未处理的分支：${JSON.stringify(x)}`);
}

function getDimensions(s: Shape): { width: number; height: number } {
  switch (s.type) {
    case 'circle':
      return { width: s.radius * 2, height: s.radius * 2 };
    case 'square':
      return { width: s.side, height: s.side };
    case 'rectangle':
      return { width: s.width, height: s.height };
    default:
      // 若以后新增了 triangle 但忘了在这里加 case，
      // s 不会被收窄为 never，编译器立刻报错
      return assertNever(s);
  }
}

console.log('dimensions =>', getDimensions(shapes[0]));


// ============================================================
// 4. 可辨识联合实现状态机
// ============================================================

// 状态机的状态集合：每个状态自带 type 与各自的“负载”
type AppState =
  | { status: 'idle' }
  | { status: 'loading'; startedAt: number }
  | { status: 'success'; data: unknown }
  | { status: 'error'; message: string };

function render(state: AppState): string {
  switch (state.status) {
    case 'idle':
      return '点击开始';
    case 'loading':
      return `加载中（已耗时 ${Date.now() - state.startedAt}ms）`;
    case 'success':
      return `成功：${JSON.stringify(state.data)}`;
    case 'error':
      return `出错了：${state.message}`;
  }
}

// 模拟状态流转
const flow: AppState[] = [
  { status: 'idle' },
  { status: 'loading', startedAt: Date.now() - 200 },
  { status: 'success', data: { ok: true } },
  { status: 'error', message: '网络断开' },
];

flow.forEach((s) => console.log('[state]', render(s)));


// ============================================================
// 5. 判别字段命名约定：type / kind / _tag / discriminator
// ============================================================

// 实际项目中常见的命名：type（最常见）、kind（K8s、React Actions）、discriminator
interface Action<T extends string, P = unknown> {
  type: T;
  payload: P;
}

type FetchAction =
  | Action<'FETCH_START'>
  | Action<'FETCH_SUCCESS', { data: unknown }>
  | Action<'FETCH_FAIL', { error: string }>;

function reducer(action: FetchAction): string {
  switch (action.type) {
    case 'FETCH_START':
      return '开始请求';
    case 'FETCH_SUCCESS':
      return `成功：${JSON.stringify(action.payload.data)}`;
    case 'FETCH_FAIL':
      return `失败：${action.payload.error}`;
  }
}

console.log(reducer({ type: 'FETCH_START', payload: undefined }));
console.log(reducer({ type: 'FETCH_SUCCESS', payload: { data: [1, 2, 3] } }));
console.log(reducer({ type: 'FETCH_FAIL', payload: { error: 'timeout' } }));


console.log('\n--- discriminated-union.ts 执行完毕 ---');
