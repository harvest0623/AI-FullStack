/**
 * Day07 - 字符串枚举（String Enum）
 *
 * 本文件演示：
 * 1. 字符串枚举：每个成员必须显式给字符串字面量
 * 2. 字符串枚举没有反向映射
 * 3. 字符串枚举的运行时对象只有名字键（更干净）
 * 4. 联合枚举成员类型：枚举本身成为联合类型，每个成员成为字面量类型
 */

export {};   // 将本文件标记为模块，避免与其他示例文件的顶层声明冲突

// ============================================================
// 1. 字符串枚举：显式赋值，无自动递增
// ============================================================

enum Env {
  Dev  = 'development',
  Test = 'test',
  Stg  = 'staging',
  Prod = 'production',
}

console.log('--- 字符串枚举 ---');
console.log('Env.Dev  =', Env.Dev);    // 'development'
console.log('Env.Test =', Env.Test);   // 'test'
console.log('Env.Prod =', Env.Prod);   // 'production'

// 字符串枚举的值就是字符串字面量，序列化时直接看到 'production' 而非数字 3
const env: Env = Env.Prod;
console.log('当前环境（序列化友好）=>', JSON.stringify({ env }));
// {"env":"production"}   —— 日志可读性强


// ============================================================
// 2. 字符串枚举没有反向映射
// ============================================================

console.log('\n--- 字符串枚举无反向映射 ---');

// 正向访问 OK
console.log('Env.Prod            =>', Env.Prod);             // 'production'

// 反向访问会失败：用值作键查不到名字
const tryReverse = (Env as unknown as Record<string, string>)['production'];
console.log("Env['production']   =>", tryReverse);           // undefined

// 与数字枚举对比：
// - 数字枚举：enum[value] = name  ✅ 支持
// - 字符串枚举：enum[value] = name ❌ 不支持
// 原因：字符串值本身可能与某个成员名冲突，TS 干脆不为字符串枚举生成反向键


// ============================================================
// 3. 字符串枚举的运行时对象更干净
// ============================================================

console.log('\n--- 运行时对象 ---');

// 字符串枚举只有“名字键”，没有“值键”
console.log('Object.keys(Env)   =', Object.keys(Env));
// ['Dev', 'Test', 'Stg', 'Prod']

console.log('Object.values(Env) =', Object.values(Env));
// ['development', 'test', 'staging', 'production']

console.log('Object.entries(Env) =');
Object.entries(Env).forEach(([k, v]) => console.log(`  ${k} -> ${v}`));

// 字符串枚举可以直接 Object.values 拿到所有合法值，无需过滤
// 这让字符串枚举在“配置常量”场景下比数字枚举更好用


// ============================================================
// 4. 联合枚举成员类型：每个成员是它自己的字面量类型
// ============================================================

console.log('\n--- 联合枚举成员类型 ---');

enum TaskState {
  Pending = 'pending',
  Running = 'running',
  Done    = 'done',
  Failed  = 'failed',
}

// TaskState.Pending 的类型不只是 TaskState，而是字面量 'pending'（更窄）
// 这意味着可以把字段类型标注为某个具体成员
interface Task {
  id: number;
  state: TaskState.Pending;   // 只允许 Pending！
  title: string;
}

const onlyPending: Task = { id: 1, state: TaskState.Pending, title: 'demo' };
console.log('只接受 Pending 的任务 =>', onlyPending);

// const wrong: Task = { id: 2, state: TaskState.Done, title: 'x' };
// ❌ Type '"done"' is not assignable to type '"pending"'.

// 联合枚举作为判别字段，配合 switch 收窄
type Result =
  | { state: TaskState.Pending; createdAt: number }
  | { state: TaskState.Running; progress: number }
  | { state: TaskState.Done; tokens: number }
  | { state: TaskState.Failed; error: string };

function summarize(r: Result): string {
  switch (r.state) {
    case TaskState.Pending:
      // 此处 r.state 收窄为 'pending'，r 是第一支
      return `待处理（创建于 ${new Date(r.createdAt).toISOString()}）`;
    case TaskState.Running:
      return `执行中，进度 ${(r.progress * 100).toFixed(1)}%`;
    case TaskState.Done:
      return `完成，消耗 ${r.tokens} tokens`;
    case TaskState.Failed:
      return `失败：${r.error}`;
  }
}

const results: Result[] = [
  { state: TaskState.Pending, createdAt: Date.now() },
  { state: TaskState.Running, progress: 0.45 },
  { state: TaskState.Done, tokens: 1280 },
  { state: TaskState.Failed, error: '网络超时' },
];

results.forEach((r) => console.log(summarize(r)));


// ============================================================
// 5. 字符串枚举 vs 数字枚举：选择建议
// ============================================================

/*
| 维度          | 数字枚举                | 字符串枚举
|--------------|--------------------------|----------------------------|
| 自动递增      | ✅ 支持                  | ❌ 必须显式赋值
| 反向映射      | ✅ enum[value] = name    | ❌ 无
| 序列化可读性  | 差（看到 0/1/2）         | 好（看到 'production'）
| 运行时对象    | 双向键，需过滤           | 仅名字键，干净
| 持久化稳定性  | 易受新增成员插入影响      | 字符串值更稳定
| 适用场景      | 内部状态、位掩码         | 配置常量、环境、对外协议

经验：
- 涉及序列化 / 日志 / 持久化的枚举，优先字符串枚举
- 内部状态机、位掩码用数字枚举
- 不确定时，字符串枚举是更安全的默认选择
*/

console.log('\n--- string-enum.ts 执行完毕 ---');
