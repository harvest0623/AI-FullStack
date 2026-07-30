/**
 * Day07 - 枚举 vs 联合字面量类型 vs as const 三种方式对比
 *
 * 本文件演示：用三种不同方式表达同一组“任务状态”常量，
 * 对比它们在
 *   - 类型安全性
 *   - 运行时对象可用性
 *   - 反向映射
 *   - 遍历能力
 *   - 新增成员成本
 * 上的差异。
 */

export {};   // 将本文件标记为模块，避免与其他示例文件的顶层声明冲突

// ============================================================
// 方式一：enum（字符串枚举）
// ============================================================

enum StatusEnum {
  Pending  = 'pending',
  Running  = 'running',
  Done     = 'done',
  Failed   = 'failed',
  Cancelled = 'cancelled',
}

function describeEnum(s: StatusEnum): string {
  switch (s) {
    case StatusEnum.Pending:   return '待处理';
    case StatusEnum.Running:   return '执行中';
    case StatusEnum.Done:      return '已完成';
    case StatusEnum.Failed:    return '失败';
    case StatusEnum.Cancelled: return '已取消';
  }
}

// ============================================================
// 方式二：字面量联合类型
// ============================================================

type StatusUnion =
  | 'pending'
  | 'running'
  | 'done'
  | 'failed'
  | 'cancelled';

function describeUnion(s: StatusUnion): string {
  switch (s) {
    case 'pending':   return '待处理';
    case 'running':   return '执行中';
    case 'done':      return '已完成';
    case 'failed':    return '失败';
    case 'cancelled': return '已取消';
  }
}

// ⚠️ 字面量联合是纯类型，运行时没有任何对象
// Object.values(StatusUnion);   // ❌ 报错：StatusUnion 只是类型，不能作为值
// 想在运行时列出所有状态？必须另写一个数组：
const ALL_STATUSES: StatusUnion[] = ['pending', 'running', 'done', 'failed', 'cancelled'];


// ============================================================
// 方式三：as const 对象
// ============================================================

const StatusObj = {
  Pending:   'pending',
  Running:   'running',
  Done:      'done',
  Failed:    'failed',
  Cancelled: 'cancelled',
} as const;

// 从对象导出联合类型
type StatusObjValue = typeof StatusObj[keyof typeof StatusObj];
// 'pending' | 'running' | 'done' | 'failed' | 'cancelled'

function describeObj(s: StatusObjValue): string {
  switch (s) {
    case StatusObj.Pending:   return '待处理';
    case StatusObj.Running:   return '执行中';
    case StatusObj.Done:      return '已完成';
    case StatusObj.Failed:    return '失败';
    case StatusObj.Cancelled: return '已取消';
  }
}


// ============================================================
// 三种方式调用对比
// ============================================================

console.log('--- 三种方式调用 ---');

// 都能让 describe(401) 在编译期报错：
// describeEnum(401);     // ❌ number 不能赋给 StatusEnum
// describeUnion(401);    // ❌ number 不能赋给 StatusUnion
// describeObj(401);      // ❌ number 不能赋给 StatusObjValue

// 三种合法调用：
console.log('enum   =>', describeEnum(StatusEnum.Pending));      // 待处理
console.log('enum   =>', describeEnum(StatusEnum.Done));         // 已完成
console.log('union  =>', describeUnion('running'));              // 执行中
console.log('union  =>', describeUnion('failed'));               // 失败
console.log('obj    =>', describeObj(StatusObj.Cancelled));      // 已取消


// ============================================================
// 运行时遍历对比
// ============================================================

console.log('\n--- 运行时遍历 ---');

// ① enum：字符串枚举直接 Object.values
console.log('enum Object.values   =>', Object.values(StatusEnum));
// ['pending', 'running', 'done', 'failed', 'cancelled']

// ② union：必须手写数组，类型与数组可能不同步
console.log('union 手写数组       =>', ALL_STATUSES);

// ③ as const：Object.values
console.log('obj  Object.values   =>', Object.values(StatusObj));
// ['pending', 'running', 'done', 'failed', 'cancelled']


// ============================================================
// 反向映射对比（数字枚举才支持）
// ============================================================

console.log('\n--- 反向映射（只有数字枚举支持）---');

enum NumStatus {
  Pending,    // 0
  Running,    // 1
  Done,       // 2
}

// 数字枚举可以反查名字
console.log('NumStatus[0] =>', NumStatus[0]);   // 'Pending'
console.log('NumStatus[2] =>', NumStatus[2]);   // 'Done'

// 字符串枚举、字面量联合、as const 对象都不支持自动反向映射
// 但 as const 对象可以手写反查：
const reverseObj: Record<string, string> = {};
(Object.keys(StatusObj) as (keyof typeof StatusObj)[]).forEach((k) => {
  reverseObj[StatusObj[k]] = k;
});
console.log('手写反向映射 =>', reverseObj['pending']);   // 'Pending'


// ============================================================
// 新增成员成本对比
// ============================================================

console.log('\n--- 新增成员成本 ---');

/*
假设要新增 'paused' 状态：

【enum】
  enum StatusEnum { Pending = 'pending', ..., Paused = 'paused' }
  - 1 处修改：枚举定义
  - describeEnum 需要补 case（switch 缺少 return 会编译报错）
  - Object.values 自动包含新值

【字面量联合】
  type StatusUnion = ... | 'paused';
  - 1 处修改：类型定义
  - describeUnion 需要补 case
  - 但 ALL_STATUSES 数组不会自动更新！需要手动加，否则运行时缺失

【as const 对象】
  const StatusObj = { ..., Paused: 'paused' } as const;
  - 1 处修改：对象定义
  - StatusObjValue 自动包含 'paused'（typeof 自动更新）
  - describeObj 需要补 case
  - Object.values 自动包含新值

结论：
- enum 与 as const 都能“一处修改，运行时自动同步”
- 字面量联合最易出现“类型与运行时数组脱节”问题
- as const 兼具类型与运行时，且兼容 isolatedModules，是新项目首选
*/


// ============================================================
// 树摇对比
// ============================================================

/*
【enum】
  - 整个对象会被打包保留，即使只用了 1 个成员
  - 字符串枚举打包体积可接受，但仍比纯类型大

【字面量联合】
  - 纯类型，编译后完全消失，零运行时
  - 树摇最彻底

【as const 对象】
  - 对象本身有运行时开销
  - 但若使用 import { StatusObj } 时只访问 Pending，现代打包工具
    能通过属性访问分析把对象内联消除
  - 接近 enum，但更易优化
*/


// ============================================================
// 三种方式选型建议（总结）
// ============================================================

/*
| 场景                                   | 推荐方式
|----------------------------------------|--------------------------
| 纯类型约束，无运行时遍历需求            | 字面量联合
| 需要运行时遍历 / 反查名字              | enum（数字枚举）或 as const 对象
| 跨文件复用 + isolatedModules 兼容      | as const 对象（首选）
| 老项目已大量使用 enum                  | 继续用 enum，新代码可逐步迁移
| 需要“位掩码 + 自增”语义                | 数字 enum（这是它的强项）
| 配置常量、环境变量、对外协议字段        | 字符串枚举或 as const 字符串对象
*/

console.log('\n--- enum-vs-union.ts 执行完毕 ---');
