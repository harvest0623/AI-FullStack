/**
 * Day06 - 继承 extends 与 implements：单继承、多接口、方法覆盖
 *
 * 本文件演示：
 * 1. extends 单继承、super 调用顺序
 * 2. 方法覆盖：子类重新实现父类方法
 * 3. override 关键字（TS 4.3+）：显式标记覆盖
 * 4. 属性覆盖的兼容性：子类型才允许
 * 5. implements 实现接口：可多实现、不继承实现
 * 6. extends 与 implements 同时使用
 */

// ============================================================
// 1. extends 单继承与 super 调用
// ============================================================

class Animal {
  constructor(public name: string) {}

  speak(): string {
    return `${this.name} 发出声音`;
  }

  eat(): string {
    return `${this.name} 在吃东西`;
  }
}

class Dog extends Animal {
  public breed: string;

  constructor(name: string, breed: string) {
    // ⚠️ 子类构造函数必须先调用 super()，才能使用 this
    super(name);
    this.breed = breed;
  }

  // 覆盖父类方法，用 super.speak() 复用父类逻辑
  speak(): string {
    return `${super.speak()}（${this.breed} 汪汪叫）`;
  }
}

const dog = new Dog('Buddy', 'Labrador');
console.log(dog.speak());    // Buddy 发出声音（Labrador 汪汪叫）
console.log(dog.eat());      // 复用父类方法：Buddy 在吃东西
console.log('是 Animal 吗:', dog instanceof Animal);   // true
console.log('是 Dog 吗:', dog instanceof Dog);         // true


// ============================================================
// 2. 方法覆盖与 override 关键字
// ============================================================

class Base {
  greet(name: string): string {
    return `Hello, ${name}`;
  }

  // 故意拼错的方法名，演示 override 的保护作用
  process(): string {
    return 'base process';
  }
}

class Sub extends Base {
  // ✅ override 显式标记覆盖，配合 noImplicitOverride 最安全
  override greet(name: string): string {
    return `Hi, ${name}!`;
  }

  // ⚠️ 如果父类没有同名方法却标了 override，TS 会报错
  // override bark(): string { return 'woof'; }   // ❌ 父类没有 bark

  // 如果父类改名了（如 proces），子类未跟改，未标 override 会被忽略
  // 加 override 后，这种“名字不匹配”会立刻暴露为编译错误
}

console.log(new Sub().greet('Alice'));   // Hi, Alice!


// ============================================================
// 3. 方法覆盖的签名兼容性
// ============================================================

class Calculator {
  compute(x: number, y: number): number {
    return x + y;
  }
}

class OK extends Calculator {
  // ✅ 签名一致
  override compute(x: number, y: number): number {
    return x * y;
  }
}

// ❌ 子类方法不能比父类“更严格”——多了必填参数会报错
// class Bad extends Calculator {
//   override compute(x: number, y: number, extra: number): number {
//     return x + y + extra;
//   }
// }

// ✅ 可选参数是允许的（比父类更宽松）
class Flexible extends Calculator {
  override compute(x: number, y: number, extra?: number): number {
    return extra !== undefined ? x + y + extra : x + y;
  }
}

console.log(new OK().compute(2, 3));          // 6
console.log(new Flexible().compute(2, 3));    // 5
console.log(new Flexible().compute(2, 3, 4)); // 9


// ============================================================
// 4. 属性覆盖：子类属性类型必须是父类的子类型
// ============================================================

class Pet {
  name: string = 'pet';
}

class Puppy extends Pet {
  // ✅ string 是 string 的子类型
  name: string = 'puppy';
}

// class WrongPet extends Pet {
//   name: number = 1;   // ❌ number 不是 string 的子类型
// }


// ============================================================
// 5. implements 实现接口：可多实现、只校验形状
// ============================================================

interface Serializable {
  serialize(): string;
}

interface Loggable {
  log(msg: string): void;
}

interface Comparable<T> {
  compareTo(other: T): number;
}

// 一个类可同时 implements 多个接口
class Product implements Serializable, Loggable, Comparable<Product> {
  constructor(
    public id: number,
    public name: string,
    public price: number,
  ) {}

  // 必须实现所有接口声明的成员
  serialize(): string {
    return JSON.stringify({ id: this.id, name: this.name, price: this.price });
  }

  log(msg: string): void {
    console.log(`[Product:${this.id}] ${msg}`);
  }

  compareTo(other: Product): number {
    return this.price - other.price;
  }
}

const p1 = new Product(1, 'Apple', 5);
const p2 = new Product(2, 'Banana', 3);
p1.log(`价格对比：${p1.compareTo(p2) > 0 ? 'p1 更贵' : 'p2 更贵'}`);
console.log('序列化:', p1.serialize());

// 接口类型可作为变量类型用
const s: Serializable = p1;
const l: Loggable = p1;
console.log('接口类型引用:', s.serialize());


// ============================================================
// 6. extends 与 implements 同时使用
// ============================================================

interface Trackable {
  trackId: string;
}

class Entity {
  constructor(public id: number) {}

  toString(): string {
    return `Entity#${this.id}`;
  }
}

// 先继承复用实现，再实现接口补充契约
class Order extends Entity implements Trackable {
  constructor(
    id: number,
    public amount: number,
    public trackId: string,
  ) {
    super(id);
  }

  override toString(): string {
    return `Order#${this.id}（金额 ${this.amount}，追踪 ${this.trackId}）`;
  }
}

const order = new Order(1001, 99.5, 'TRK-001');
console.log(order.toString());                  // 复用并覆盖父类方法
console.log('是 Entity 吗:', order instanceof Entity);   // true
console.log('是 Trackable 吗:', typeof order.trackId === 'string');  // 接口无 instanceof


// ============================================================
// 7. implements 只校验形状，不继承实现
// ============================================================

interface HasName {
  name: string;
  greet(): string;
}

// implements 不继承任何字段或方法，只校验类是否满足形状
class Person implements HasName {
  name: string;          // 必须自己声明
  constructor(name: string) {
    this.name = name;
  }
  greet(): string {      // 必须自己实现
    return `Hi, I'm ${this.name}`;
  }
}

// 对比 extends：继承会复用父类的字段与方法实现
class Employee extends Person {
  constructor(name: string, public salary: number) {
    super(name);         // 复用父类构造逻辑
  }
  // 无需重新声明 name、无需重新实现 greet，直接复用
}

const emp = new Employee('Alice', 50000);
console.log(emp.greet(), `，薪资 ${emp.salary}`);


// ============================================================
// 8. 多层继承与 super 链
// ============================================================

class Vehicle {
  constructor(public wheels: number) {}
  describe(): string {
    return `Vehicle（${this.wheels} 轮）`;
  }
}

class Car extends Vehicle {
  constructor(public brand: string) {
    super(4);
  }
  describe(): string {
    return `${super.describe()}，品牌 ${this.brand}`;
  }
}

class ElectricCar extends Car {
  constructor(brand: string, public battery: number) {
    super(brand);
  }
  describe(): string {
    return `${super.describe()}，电量 ${this.battery}kWh`;
  }
}

const ec = new ElectricCar('Tesla', 75);
console.log(ec.describe());
// Vehicle（4 轮），品牌 Tesla，电量 75kWh
console.log('是 Vehicle 吗:', ec instanceof Vehicle);    // true
console.log('是 Car 吗:', ec instanceof Car);            // true
console.log('是 ElectricCar 吗:', ec instanceof ElectricCar);  // true


console.log('\n--- inheritance-implements.ts 执行完毕 ---');

export {};
