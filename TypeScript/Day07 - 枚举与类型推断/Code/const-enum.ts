/**
 * Day07 - const enum：编译时内联
 *
 * 本文件演示：
 * 1. const enum 的基本用法：编译时把引用替换为字面量
 * 2. const enum 与普通 enum 的编译产物对比
 * 3. isolatedModules 下的限制（vite/esbuild/swc/babel 等工具链）
 * 4. 用 as const 对象作为 const enum 的替代方案
 */

export {};   // 将本文件标记为模块，避免与其他示例文件的顶层声明冲突

// ============================================================
// 1. const enum：编译时完全内联
// ============================================================

const enum Color {
  Red,
  Green,
  Blue,
}

const enum Direction {
  Up    = 'UP',
  Down  = 'DOWN',
  Left  = 'LEFT',
  Right = 'RIGHT',
}

// 这些访问在编译时会被直接替换为字面量
const c1: Color = Color.Red;          // 编译后：const c1 = 0;
const c2: Color = Color.Green;        // 编译后：const c2 = 1;
const d1: Direction = Direction.Up;   // 编译后：const d1 = 'UP';

console.log('--- const enum 内联 ---');
console.log('Color.Red        =>', c1);   // 0
console.log('Color.Green      =>', c2);   // 1
console.log('Direction.Up     =>', d1);   // 'UP'

// const enum 也可以参与类型推断：c1 的类型是字面量 0，而非 Color
// 注意：在 transpileOnly 模式下，运行时仍可看到值，但类型层面是字面量


// ============================================================
// 2. const enum 不生成运行时对象
// ============================================================

// 普通枚举是真实存在的对象，可以 Object.keys
enum NormalRole {
  Guest = 'guest',
  User  = 'user',
  Admin = 'admin',
}
console.log('\n--- 普通 enum 是运行时对象 ---');
console.log('Object.keys(NormalRole) =', Object.keys(NormalRole));
// ['Guest', 'User', 'Admin']

// const enum 是纯类型层概念，运行时没有任何对象
const enum ConstRole {
  Guest = 'guest',
  User  = 'user',
  Admin = 'admin',
}
// Object.keys(ConstRole);   // ❌ 编译报错：const enum 不能作为值使用
// typeof ConstRole;         // ❌ 同上

// 但作为值类型仍可正常使用：
const role: ConstRole = ConstRole.Admin;
console.log('\n--- const enum 仅作值类型 ---');
console.log('const role =', role);   // 'admin'


// ============================================================
// 3. 编译产物对比（注释展示）
// ============================================================

/*
【普通 enum】编译产物：

  enum NormalRole {
    Guest = 'guest',
    User  = 'user',
    Admin = 'admin',
  }

  var NormalRole;
  (function (NormalRole) {
    NormalRole['Guest'] = 'guest';
    NormalRole['User']  = 'user';
    NormalRole['Admin'] = 'admin';
  })(NormalRole || (NormalRole = {}));

  —— 生成了一个真实的 IIFE 对象。


【const enum】编译产物：

  const enum ConstRole {
    Guest = 'guest',
    User  = 'user',
    Admin = 'admin',
  }
  const role = ConstRole.Admin;

  —— 完全内联后：
  const role = 'admin';

  —— 没有任何 ConstRole 对象，零运行时开销。
*/


// ============================================================
// 4. isolatedModules 下的限制
// ============================================================

/*
现代前端工具链（vite/esbuild/swc/babel）默认开启 isolatedModules：true，
它们逐文件编译，不读取其他文件的类型信息。

这会导致跨文件使用 const enum 出问题：

  // file-a.ts
  export const enum Mode { Read, Write }

  // file-b.ts
  import { Mode } from './file-a';
  const m = Mode.Read;

  // 在 isolatedModules 下：
  // - esbuild/swc 无法假设 Mode 真的存在
  // - 它们要么报错，要么退化为保留 import（导致运行时崩溃）

TS 5.0 起，官方甚至推荐开启 isolatedModules 时不要使用 const enum，
或使用 preserveConstEnums 选项保留运行时对象。

更稳的做法：用 as const 对象替代 const enum（见下节）。
*/


// ============================================================
// 5. 用 as const 对象替代 const enum（推荐）
// ============================================================

// 等价于 const enum Color { Red, Green, Blue }
const ColorConst = {
  Red: 0,
  Green: 1,
  Blue: 2,
} as const;

// 提取联合类型
type ColorValue = typeof ColorConst[keyof typeof ColorConst];
// 0 | 1 | 2

console.log('\n--- as const 替代方案 ---');

const paint: ColorValue = ColorConst.Red;
console.log('paint =', paint);   // 0

// 优势：
// 1. 有运行时对象可用（可 Object.keys / values 遍历）
// 2. 完全兼容 isolatedModules
// 3. 类型推断仍为最窄字面量
// 4. 可以被打包工具正常树摇

// 字符串版本（更可读）
const DirectionConst = {
  Up:    'UP',
  Down:  'DOWN',
  Left:  'LEFT',
  Right: 'RIGHT',
} as const;

type DirectionValue = typeof DirectionConst[keyof typeof DirectionConst];
// 'UP' | 'DOWN' | 'LEFT' | 'RIGHT'

function turn(d: DirectionValue): string {
  return `向 ${d} 转`;
}

console.log(turn(DirectionConst.Up));   // 向 UP 转

// 列出所有方向（const enum 做不到这一点！）
console.log('所有方向 =>', Object.values(DirectionConst));
// ['UP', 'DOWN', 'LEFT', 'RIGHT']


console.log('\n--- const-enum.ts 执行完毕 ---');
