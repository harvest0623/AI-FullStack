/**
 * Day05 - 联合类型（Union Types）
 *
 * 本文件演示：
 * 1. 联合类型 | 的基本含义（或关系，取值属于其中一个）
 * 2. 联合类型与字面量类型组合实现状态枚举
 * 3. 联合类型的公共属性：只能访问所有成员共有的属性/方法
 * 4. 联合类型在数组、函数参数中的常见用法
 */

// ============================================================
// 1. 联合类型的基本含义：或关系
// ============================================================

// id 可以是 number，也可以是 string —— 取值只需属于其中之一
type UserId = number | string;

function printUserId(id: UserId): void {
  console.log('用户 ID：', id);
}

printUserId(1001);        // number 分支
printUserId('U-1001');    // string 分支
// printUserId(true);     // ❌ 编译报错：boolean 不能赋给 number | string

// 联合类型可以扩展任意多个成员
type Mixed = number | string | boolean | null;
const m1: Mixed = 1;
const m2: Mixed = 'hello';
const m3: Mixed = true;
const m4: Mixed = null;
console.log('Mixed 示例：', m1, m2, m3, m4);


// ============================================================
// 2. 字面量联合：实现轻量级“状态枚举”
// ============================================================

// 不需要 enum，用字面量联合就能表达有限的状态集合
type TaskStatus = 'pending' | 'running' | 'success' | 'failed';

function describeStatus(status: TaskStatus): string {
  switch (status) {
    case 'pending':
      return '等待执行';
    case 'running':
      return '执行中';
    case 'success':
      return '已完成';
    case 'failed':
      return '执行失败';
  }
}

const statuses: TaskStatus[] = ['pending', 'running', 'success', 'failed'];
statuses.forEach((s) => console.log(`${s} -> ${describeStatus(s)}`));

// 字面量联合还能混合不同类型字面量
type Direction = 'up' | 'down' | 'left' | 'right';
type Answer = 'yes' | 'no' | 0 | 1;       // 字符串字面量与数字字面量混合
type Align = 'left' | 'center' | 'right';

const a: Answer = 'yes';
console.log('Answer =', a);


// ============================================================
// 3. 公共属性：只能访问所有成员共有的成员
// ============================================================

// string | number 的公共方法有哪些？
// - string 和 number 都继承了 valueOf / toString / constructor
// - 但 string 有 charAt，number 有 toFixed，这些不是公共的
function processValue(value: string | number): void {
  // ✅ toString 是 string 与 number 的公共方法，可以安全调用
  console.log('toString =>', value.toString());

  // ✅ valueOf 也是公共方法
  console.log('valueOf =>', value.valueOf());

  // ❌ 以下两行如果取消注释会编译报错：
  // value.toFixed(2);   // number 有，string 没有
  // value.toUpperCase(); // string 有，number 没有

  // ✅ 通过类型收窄后才能访问各自特有的成员
  if (typeof value === 'string') {
    console.log('字符串特有 =>', value.toUpperCase());
  } else {
    console.log('数字特有 =>', value.toFixed(2));
  }
}

processValue('abc');
processValue(3.14159);


// 对象类型的联合：公共属性访问限制更明显
interface Bird {
  kind: 'bird';
  fly(): void;
  layEgg(): void;
}

interface Fish {
  kind: 'fish';
  swim(): void;
  layEgg(): void;
}

type Pet = Bird | Fish;

function handlePet(pet: Pet): void {
  // ✅ layEgg 是两者的公共方法
  pet.layEgg();

  // ❌ pet.fly();    // Bird 有，Fish 没有
  // ❌ pet.swim();   // Fish 有，Bird 没有

  // 必须先收窄
  if (pet.kind === 'bird') {
    pet.fly();        // 此处 pet 被收窄为 Bird
  } else {
    pet.swim();       // 此处 pet 被收窄为 Fish
  }
}


// ============================================================
// 4. 联合类型在函数参数与数组中的用法
// ============================================================

// 可选参数 + undefined 联合
function greet(name: string | undefined): string {
  // name 在此处为 string | undefined，不能直接 .toUpperCase()
  if (name === undefined) {
    return 'Hello, anonymous';
  }
  return `Hello, ${name.toUpperCase()}`;
}

console.log(greet('TypeScript'));
console.log(greet(undefined));

// 数组元素为联合类型
const mixedArray: (number | string)[] = [1, 'two', 3, 'four'];
mixedArray.forEach((item) => {
  if (typeof item === 'number') {
    console.log('数字 =>', item * 2);
  } else {
    console.log('字符串 =>', item.length);
  }
});

// null 联合：模拟“可能没有值”
type Maybe<T> = T | null;
function findUser(id: number): Maybe<{ id: number; name: string }> {
  return id === 1 ? { id, name: 'Alice' } : null;
}

const found = findUser(1);
if (found !== null) {
  console.log('找到用户 =>', found.name);
} else {
  console.log('用户不存在');
}


// ============================================================
// 5. 联合类型的“分配律”：对联合使用类型别名会分配展开
// ============================================================

type Boxed<T> = { value: T };

// Boxed<number | string> 等价于 Boxed<number> | Boxed<string>
type BoxedUnion = Boxed<number | string>;

const b1: BoxedUnion = { value: 1 };       // 满足 Boxed<number>
const b2: BoxedUnion = { value: 'two' };   // 满足 Boxed<string>
console.log('Boxed 联合 =>', b1, b2);


console.log('\n--- union-types.ts 执行完毕 ---');
