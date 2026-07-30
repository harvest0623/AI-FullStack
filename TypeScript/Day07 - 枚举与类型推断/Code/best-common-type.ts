/**
 * Day07 - 最佳通用类型（Best Common Type）
 *
 * 本文件演示：
 * 1. 同类型元素数组推断为 T[]
 * 2. 不同基础类型元素推断为联合数组
 * 3. 子类元素数组：TS 取联合而非公共父类
 * 4. 显式标注父类型让数组“统一”
 * 5. 函数返回值中的最佳通用类型
 */

// ============================================================
// 1. 同类型元素 -> T[]
// ============================================================

console.log('--- 同类型元素 ---');

const nums = [1, 2, 3];                  // number[]
const strs = ['a', 'b', 'c'];            // string[]
const bools = [true, false, true];       // boolean[]

console.log('nums   =>', nums);
console.log('strs   =>', strs);
console.log('bools  =>', bools);


// ============================================================
// 2. 不同基础类型 -> 联合数组
// ============================================================

console.log('\n--- 不同基础类型联合 ---');

const mixed1 = [1, 'two', true];         // (number | string | boolean)[]
const mixed2 = [1, 2, 'three'];          // (number | string)[]

console.log('mixed1 =>', mixed1);
console.log('mixed2 =>', mixed2);

// 访问元素时得到的是联合类型，必须收窄才能用特有方法
mixed1.forEach((item) => {
  if (typeof item === 'number') {
    console.log('  number  =>', item.toFixed(2));
  } else if (typeof item === 'string') {
    console.log('  string  =>', item.toUpperCase());
  } else {
    console.log('  boolean =>', item);
  }
});


// ============================================================
// 3. 子类元素数组：取联合而非公共父类
// ============================================================

console.log('\n--- 子类元素取联合 ---');

class Animal {
  constructor(public name: string) {}
  speak(): string {
    return `${this.name} 发出声音`;
  }
}

class Dog extends Animal {
  speak(): string {
    return `${this.name} 汪汪`;
  }
  bark(): string {
    return `${this.name}：汪！`;
  }
}

class Cat extends Animal {
  speak(): string {
    return `${this.name} 喵喵`;
  }
  meow(): string {
    return `${this.name}：喵～`;
  }
}

class Bird extends Animal {
  speak(): string {
    return `${this.name} 啾啾`;
  }
  fly(): string {
    return `${this.name} 起飞！`;
  }
}

// 不显式标注：TS 推断为 (Dog | Cat)[]
const pets1 = [new Dog('旺财'), new Cat('咪咪')];
console.log('pets1 推断为 (Dog | Cat)[]');
pets1.forEach((p) => console.log('  ', p.speak()));

// 每个元素是联合类型，只能访问 Dog 和 Cat 的公共成员
// 公共成员 = Animal 上的 speak（被两者重写）
// p.bark()  // ❌ Cat 没有 bark
// p.meow()  // ❌ Dog 没有 meow


// ============================================================
// 4. 显式标注父类型让数组统一
// ============================================================

console.log('\n--- 显式标注父类型 ---');

// 标注为 Animal[]，元素被收窄到 Animal 视角
const pets2: Animal[] = [new Dog('旺财'), new Cat('咪咪'), new Bird('小绿')];
pets2.forEach((p) => {
  console.log('  ', p.speak());   // ✅ Animal 有 speak（多态调用）
  // p.bark();   // ❌ Animal 没有 bark
  // p.fly();    // ❌ Animal 没有 fly
});

// 如果想用各自特有方法，仍需类型收窄
pets2.forEach((p) => {
  if (p instanceof Dog) {
    console.log('  Dog 特有 =>', p.bark());
  } else if (p instanceof Cat) {
    console.log('  Cat 特有 =>', p.meow());
  } else if (p instanceof Bird) {
    console.log('  Bird 特有 =>', p.fly());
  }
});


// ============================================================
// 5. 函数返回值中的最佳通用类型
// ============================================================

console.log('\n--- 函数返回值 ---');

// 不同分支返回不同子类 -> 推断为联合
function makePet(kind: 'dog' | 'cat'): Dog | Cat {
  if (kind === 'dog') return new Dog('旺财');
  return new Cat('咪咪');
}
const pet = makePet('dog');
console.log('makePet 返回 =>', pet.speak());

// 想让返回类型是 Animal，需要显式标注
function makeAnimal(kind: 'dog' | 'cat' | 'bird'): Animal {
  if (kind === 'dog')  return new Dog('旺财');
  if (kind === 'cat')  return new Cat('咪咪');
  return new Bird('小绿');
}
const a = makeAnimal('bird');
console.log('makeAnimal 返回 =>', a.speak());


// ============================================================
// 6. 联合数组 vs 父类数组的取舍
// ============================================================

/*
| 场景                               | 选择
|------------------------------------|---------------------
| 只用公共方法（多态）               | 显式标注 Animal[]
| 需要按子类分别处理                 | 推断为联合，再 instanceof 收窄
| 后续会再 push 不同子类实例         | 显式标注父类数组
| 元素类型彼此完全无关               | 联合数组，必须收窄访问

注意：父类数组推断“丢失子类信息”，联合数组保留子类但访问受限。
最佳通用类型不会“向上找父类”，所以混合子类时默认得到联合数组。
*/


// ============================================================
// 7. 接口（非类）的混合元素数组
// ============================================================

console.log('\n--- 接口混合数组 ---');

interface HasId   { id: number; }
interface HasName { name: string; }
interface HasAge  { age: number; }

const a1: HasId   = { id: 1 };
const a2: HasName = { name: 'Alice' };
const a3: HasAge  = { age: 30 };

// TS 推断为 (HasId | HasName | HasAge)[]
const items = [a1, a2, a3];
console.log('items 推断为联合数组 =>', items);

// 显式标注为更宽的类型
type FullRecord = HasId & HasName & HasAge;
// const full: FullRecord[] = [a1, a2, a3];   // ❌ 缺字段，结构不兼容

// 要混合存储，常见做法是定义一个“联合接口”
type AnyItem = HasId | HasName | HasAge;
const list: AnyItem[] = [a1, a2, a3];
list.forEach((item) => {
  if ('id' in item)   console.log('  HasId   =>', item.id);
  if ('name' in item) console.log('  HasName =>', item.name);
  if ('age' in item)  console.log('  HasAge  =>', item.age);
});


console.log('\n--- best-common-type.ts 执行完毕 ---');
