/**
 * Day07 - 数字枚举（Numeric Enum）
 *
 * 本文件演示：
 * 1. 数字枚举默认从 0 递增
 * 2. 自定义初始值（连续 / 不连续 / 位掩码）
 * 3. 反向映射：enum[key] = value 与 enum[value] = key
 * 4. 数字枚举的运行时对象结构（Object.keys 会包含双向键）
 */

export {};   // 将本文件标记为模块，避免与其他示例文件的顶层声明冲突

// ============================================================
// 1. 默认从 0 递增
// ============================================================

enum Direction {
  Up,      // 0
  Down,    // 1
  Left,    // 2
  Right,   // 3
}

console.log('--- 默认递增 ---');
console.log('Up    =', Direction.Up);     // 0
console.log('Down  =', Direction.Down);   // 1
console.log('Left  =', Direction.Left);   // 2
console.log('Right =', Direction.Right);  // 3


// ============================================================
// 2. 自定义初始值
// ============================================================

// 2.1 连续自定义初始值：后续成员从首成员 +1 递增
enum HttpStatus {
  Ok            = 200,
  Created       = 201,   // = Ok + 1
  BadRequest    = 400,
  Unauthorized  = 401,   // = BadRequest + 1
  NotFound      = 404,
  InternalError = 500,
}

console.log('\n--- 自定义初始值（HTTP 状态码）---');
console.log('Ok            =', HttpStatus.Ok);            // 200
console.log('Created       =', HttpStatus.Created);       // 201
console.log('NotFound      =', HttpStatus.NotFound);      // 404
console.log('InternalError =', HttpStatus.InternalError); // 500

// 2.2 不连续赋值：用于位掩码（bitmask）
enum Permission {
  Read    = 1,    // 0b0001
  Write   = 2,    // 0b0010
  Execute = 4,    // 0b0100
  Admin   = 8,    // 0b1000
}

// 位运算组合：读 + 写
const readWrite: Permission = Permission.Read | Permission.Write;
console.log('\n--- 位掩码组合 ---');
console.log('Read | Write =', readWrite);                    // 3
console.log('包含读权限？', (readWrite & Permission.Read) !== 0);    // true
console.log('包含执行权限？', (readWrite & Permission.Execute) !== 0); // false


// ============================================================
// 3. 反向映射：用值反查名字
// ============================================================

console.log('\n--- 反向映射 ---');

// 正向：enum[name] = value
console.log('Direction.Up      =>', Direction.Up);          // 0
console.log('Direction.Right   =>', Direction.Right);       // 3

// 反向：enum[value] = name   —— 数字枚举独有能力
console.log('Direction[0]      =>', Direction[0]);          // 'Up'
console.log('Direction[3]      =>', Direction[3]);          // 'Right'

// 实用：日志中把数字翻译回名字
function logDirection(d: Direction): void {
  const name = Direction[d];   // 反向映射
  console.log(`移动方向：${name}（值 ${d}）`);
}

logDirection(Direction.Up);     // 移动方向：Up（值 0）
logDirection(Direction.Right);  // 移动方向：Right（值 3）


// ============================================================
// 4. 数字枚举的运行时对象结构
// ============================================================

console.log('\n--- 数字枚举的运行时对象 ---');

// 数字枚举既有“名字 -> 值”键，也有“值 -> 名字”键
// Object.keys 会返回所有键（数字键以字符串形式出现）
const allKeys = Object.keys(Direction);
console.log('Object.keys(Direction) =', allKeys);
// ['0', '1', '2', '3', 'Up', 'Down', 'Left', 'Right']

const allValues = Object.values(Direction);
console.log('Object.values(Direction) =', allValues);
// [0, 1, 2, 3, 'Up', 'Down', 'Left', 'Right']

// 只取出“名字键”：过滤掉数字字符串
const nameKeys = Object.keys(Direction).filter((k) => isNaN(Number(k)));
console.log('只取名字键 =>', nameKeys);
// ['Up', 'Down', 'Left', 'Right']


// ============================================================
// 5. 反向映射的编译产物（注释展示）
// ============================================================

/*
TS 把上面的 Direction 编译为：

  var Direction;
  (function (Direction) {
    Direction[Direction['Up'] = 0] = 'Up';
    Direction[Direction['Down'] = 1] = 'Down';
    Direction[Direction['Left'] = 2] = 'Left';
    Direction[Direction['Right'] = 3] = 'Right';
  })(Direction || (Direction = {}));

关键点：
- (obj[k] = v) 整体返回 v，因此可以再用 v 作为键、k 作为值赋一次
- 这就是“反向映射”的实现原理
- 数字枚举独有；字符串枚举不会生成这种双向键
*/


console.log('\n--- numeric-enum.ts 执行完毕 ---');
