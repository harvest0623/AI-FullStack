/**
 * Day03 - 结构化类型 Structural Typing
 * 主题：鸭式辩型 duck typing、类型兼容性赋值、函数参数双变量检查
 * 运行：npx ts-node structural-typing.ts
 */

console.log('=== 1. 结构化类型：看"形状"不看"名字" ===\n');

// TS 是结构化类型系统：只要字段形状匹配，就认为类型兼容——这就是"鸭式辩型"
// "走起来像鸭子、叫起来像鸭子，那就是鸭子"
interface User {
  name: string;
  age: number;
}

// 一个独立的 interface，名字不同但形状相同
interface Person {
  name: string;
  age: number;
}

const u: User = { name: 'Alice', age: 30 };
const p: Person = u;        // ✅ 形状一致，互相赋值合法
const u2: User = p;         // ✅ 反向也合法
console.log('[结构化] User ↔ Person 互赋值 OK:', u, p);

console.log('\n=== 2. 超集可赋给子集（结构化兼容规则）===\n');

// 拥有更多字段的对象可以赋给字段更少的目标（多出来的字段不影响兼容性）
interface Employee {
  name: string;
  age: number;
  salary: number;
}
const emp: Employee = { name: 'Bob', age: 25, salary: 8000 };

// Employee 有 User 的全部字段 → 可以赋值给 User（超集 → 子集）
const u3: User = emp;       // ✅
console.log('[超集→子集] Employee → User OK:', u3);

// ❌ 反向不行：User 缺少 salary
// const emp2: Employee = u;   // ❌ Property 'salary' is missing

console.log('\n=== 3. 多余属性检查 vs 结构化类型 ===\n');

// 注意区别：
// - 多余属性检查：仅在【对象字面量直接赋值】时触发，挡掉"字面量里多了字段"
// - 结构化类型：在【变量中转 / 函数传参】时起作用，只看形状是否兼容

interface Point2D { x: number; y: number }

// ❌ 字面量直接赋值，多了 z → 多余属性检查报错
// const pt: Point2D = { x: 1, y: 2, z: 3 };

// ✅ 通过变量中转，多余属性检查不触发，结构化兼容 OK
const raw = { x: 1, y: 2, z: 3 };
const pt: Point2D = raw;
console.log('[多余属性 vs 结构化] 变量中转后 =', pt);

console.log('\n=== 4. 函数参数：结构化兼容 ===\n');

// 函数参数类型兼容：参数列表也要结构匹配
interface Named { name: string }
function greet(n: Named): string {
  return `Hello, ${n.name}`;
}

// 传一个有 name 字段的对象字面量 → OK
console.log('[greet] 字面量 =', greet({ name: 'Alice' }));

// 传一个变量，多出来字段也 OK（结构化兼容）
const dog = { name: 'Rex', bark: () => 'woof' };
console.log('[greet] 变量中转 =', greet(dog));

// ❌ 字面量直接传多了字段 → 多余属性检查触发
// greet({ name: 'Bob', x: 1 });

console.log('\n=== 5. 函数兼容性：返回值协变、参数逆变 ===\n');

// 函数赋值时的兼容规则：
// - 返回值：源函数返回的类型必须是目标返回类型的【子类型】（协变 covariant）
// - 参数：  源函数参数类型必须是目标参数类型的【超类型】（逆变 contravariant）
//    通俗记忆：能接收更"宽"参数的函数，可以赋给要求更"窄"参数的位置

type Sub = { name: string; age: number };   // 更具体（窄）
type Sup = { name: string };                // 更宽泛（宽）

// 返回值协变：返回 Sub 的函数可赋给"返回 Sup"的函数类型
type ReturnSup = () => Sup;
type ReturnSub = () => Sub;
const returnSub: ReturnSub = () => ({ name: 'A', age: 1 });
const returnSuper: ReturnSup = returnSub;   // ✅ 协变
console.log('[协变] returnSuper() =', returnSuper());

// 参数逆变：参数为 Sup 的函数可赋给"参数为 Sub"的函数类型
// 反过来想：要求 (x: Sub) => void 的位置，给一个 (x: Sup) => void 是安全的——
// 它能处理任何 Sub（因为 Sub 也是 Sup，子类型可以传给超类型参数）
type TakesSub = (x: Sub) => void;
type TakesSup = (x: Sup) => void;

const takesSup: TakesSup = (x) => console.log('[逆变] name =', x.name);
const takesSub: TakesSub = takesSup;        // ✅ 逆变：宽参数函数赋给窄参数位置
takesSub({ name: 'Alice', age: 30 });

// ❌ 反过来不安全：要求 (x: Sup) 但给 (x: Sub)——传一个 { name } 进去会缺 age
// const takesSubOnly: TakesSub = (x: Sub) => console.log(x.age);
// const bad: TakesSup = takesSubOnly;   // ❌ strictFunctionTypes 下报错

console.log('\n=== 6. 鸭式辩型实战：第三方对象复用 ===\n');

// 实际场景：你定义了一个 Logger 接口，任何符合该形状的对象都能用
interface Logger {
  log(msg: string): void;
  error(msg: string): void;
}

const myLogger: Logger = {
  log: (msg) => console.log('[myLogger]', msg),
  error: (msg) => console.error('[myLogger]', msg),
};

function runTask(logger: Logger) {
  logger.log('开始任务');
  logger.error('模拟一个错误');
}
runTask(myLogger);

// 鸭式辩型：只要形状对，多出来的字段不影响兼容
interface VerboseLogger extends Logger {
  debug(msg: string): void;
}
const verbose: VerboseLogger = {
  log: (m) => console.log('[v]', m),
  error: (m) => console.error('[v]', m),
  debug: (m) => console.log('[v:debug]', m),
};
// VerboseLogger 是 Logger 的超集 → 可赋给 Logger 参数
runTask(verbose);

console.log('\n=== 7. 类的实例同样走结构化兼容 ===\n');

class Cat {
  constructor(public name: string, public age: number) {}
  meow() {
    return `${this.name}: meow`;
  }
}

// Cat 实例的形状是 { name: string; age: number; meow(): string }
// 它满足 User 的 { name; age } 形状 → 可赋值给 User
const cat = new Cat('Tom', 5);
const u4: User = cat;       // ✅ 结构化兼容
console.log('[类实例] Cat → User =', u4);
console.log('[类实例] 原方法仍可用 =', cat.meow());
