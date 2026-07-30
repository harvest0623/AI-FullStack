/**
 * Day05 - 穷尽检查（Exhaustive Check）
 *
 * 本文件演示：
 * 1. never 类型的本质：不可能出现的值
 * 2. 用 never 做 exhaustive check：忘记处理分支时编译报错
 * 3. 在 switch 与 if 链中的用法
 * 4. 新增成员时编译期“提醒”的实现
 */

// ============================================================
// 1. never 类型回顾
// ============================================================

// never 表示“永远不会出现的值”：
// - 函数抛异常或无限循环，返回值类型是 never
// - 联合类型收窄到“空集”时，剩余分支是 never
// - 任何类型与 never 的联合都退化为该类型本身（never 被吸收）

function fail(message: string): never {
  throw new Error(message);
}

function infiniteLoop(): never {
  while (true) {
    // 永不返回
  }
}

// never 被联合吸收
type T1 = never | string;   // 等价于 string
type T2 = never | number | string;  // 等价于 number | string
const t1: T1 = 'hello';
const t2: T2 = 1;
console.log('never 被吸收 =>', t1, t2);


// ============================================================
// 2. 经典模式：assertNever 守卫
// ============================================================

// 在 switch 的 default 分支，把当前值赋给 never：
// - 若所有分支都已处理，则 default 不可达，s 的类型被收窄为 never
// - 若遗漏某个分支，s 的类型仍是某个具体类型，赋给 never 会编译报错
function assertNever(x: never): never {
  throw new Error(`未处理的分支：${JSON.stringify(x)}`);
}


// ============================================================
// 3. 在 Shape 联合上的应用
// ============================================================

interface Circle {
  type: 'circle';
  radius: number;
}
interface Square {
  type: 'square';
  side: number;
}
interface Triangle {
  type: 'triangle';
  base: number;
  height: number;
}

type Shape = Circle | Square | Triangle;

function area(s: Shape): number {
  switch (s.type) {
    case 'circle':
      return Math.PI * s.radius ** 2;
    case 'square':
      return s.side ** 2;
    case 'triangle':
      return 0.5 * s.base * s.height;
    default:
      // 此时 s 必须是 never；若忘记加 triangle 分支，这里会报错
      return assertNever(s);
  }
}

const shapes: Shape[] = [
  { type: 'circle', radius: 2 },
  { type: 'square', side: 3 },
  { type: 'triangle', base: 4, height: 5 },
];
shapes.forEach((s) => console.log(`${s.type} 面积 = ${area(s).toFixed(2)}`));


// ============================================================
// 4. 演示“忘记处理分支”时的编译报错
// ============================================================

// 试着删掉上面 area 函数中的 'triangle' case，
// 你会看到 default 分支里 assertNever(s) 报错：
//   Argument of type 'Triangle' is not assignable to parameter of type 'never'.
// 这正是穷尽检查的价值：新增成员时，编译器强制你补全处理逻辑。

// 我们再写一个故意不处理的版本，演示思路（保持注释以避免编译失败）：
//
// function areaBroken(s: Shape): number {
//   switch (s.type) {
//     case 'circle':
//       return Math.PI * s.radius ** 2;
//     case 'square':
//       return s.side ** 2;
//     default:
//       // ❌ 若取消 'triangle' case，此行报错：
//       // Argument of type 'Triangle' is not assignable to parameter of type 'never'.
//       return assertNever(s);
//   }
// }


// ============================================================
// 5. 在 if 链中做穷尽检查
// ============================================================

type Color = 'red' | 'green' | 'blue';

function toHex(c: Color): string {
  if (c === 'red') return '#ff0000';
  if (c === 'green') return '#00ff00';
  if (c === 'blue') return '#0000ff';

  // 走到此处 c 必为 never，若新增了 'yellow' 但没处理，此行编译报错
  return assertNever(c);
}

console.log(toHex('red'), toHex('green'), toHex('blue'));


// ============================================================
// 6. 用 never 检查函数参数穷尽性
// ============================================================

// 另一种写法：把 default 分支的值赋给 never 类型变量
function describe(s: Shape): string {
  switch (s.type) {
    case 'circle':
      return `半径 ${s.radius} 的圆`;
    case 'square':
      return `边长 ${s.side} 的正方形`;
    case 'triangle':
      return `底 ${s.base} 高 ${s.height} 的三角形`;
    default: {
      // 同样原理：s 应被收窄为 never
      const _exhaustive: never = s;
      return `未知形状：${_exhaustive}`;
    }
  }
}

console.log(describe({ type: 'circle', radius: 5 }));


// ============================================================
// 7. 实战：新增成员时的“强制提醒”
// ============================================================

// 假设我们要为 Shape 新增一个 'hexagon' 成员
interface Hexagon {
  type: 'hexagon';
  side: number;
}

type ShapeV2 = Circle | Square | Triangle | Hexagon;

// 下面这个函数忘了处理 hexagon，编译器会立刻在 assertNever 处报错
// 提示你需要补上对应的 case —— 这就是穷尽检查的“防呆”效果
function areaV2(s: ShapeV2): number {
  switch (s.type) {
    case 'circle':
      return Math.PI * s.radius ** 2;
    case 'square':
      return s.side ** 2;
    case 'triangle':
      return 0.5 * s.base * s.height;
    case 'hexagon':
      return (3 * Math.sqrt(3) / 2) * s.side ** 2;
    default:
      return assertNever(s);
  }
}

const hex: ShapeV2 = { type: 'hexagon', side: 2 };
console.log(`hexagon 面积 = ${areaV2(hex).toFixed(2)}`);


console.log('\n--- exhaustive-check.ts 执行完毕 ---');
