/**
 * Day06 - class 基础：字段声明、构造函数、方法、this 类型
 *
 * 本文件演示：
 * 1. 字段声明与类型注解、默认值、确定赋值断言
 * 2. 构造函数与方法
 * 3. 箭头函数字段解决 this 丢失问题
 * 4. this 类型与链式调用
 * 5. 多态 this（polymorphic this）在继承中的表现
 */

// ============================================================
// 1. 字段声明：类型注解、默认值、确定赋值断言
// ============================================================

class User {
  // 显式声明类型，在构造函数中赋值
  id: number;
  name: string;

  // 声明时给默认值，TS 据此推断类型
  role: string = 'member';

  // 确定赋值断言：告诉 TS“我知道这个字段稍后会被赋值”
  // 通常更推荐在构造函数里直接赋值，这里仅为演示
  email!: string;

  constructor(id: number, name: string) {
    this.id = id;
    this.name = name;
  }

  describe(): string {
    return `User #${this.id}：${this.name}（${this.role}）`;
  }
}

const u = new User(1, 'Alice');
console.log(u.describe());
// 输出：User #1：Alice（member）


// ============================================================
// 2. 方法就是原型上的函数
// ============================================================

class Counter {
  count = 0;

  // 普通方法：this 默认不绑定，回调场景会丢失
  increment(): void {
    this.count++;
  }

  // 箭头函数字段：this 永远指向实例，适合做回调
  decrement = (): void => {
    this.count--;
  };
}

const c = new Counter();
c.increment();
c.increment();
console.log('count after increment:', c.count);   // 2

// 模拟“把方法解构出来当回调”的场景
const { increment } = c;
try {
  increment();
} catch (e) {
  // 运行时 this 为 undefined（strict 模式下），TS 的 transpileOnly 不报错
  console.log('increment 解构调用失败：', (e as Error).message);
}

// 箭头函数字段不会有这个问题
const { decrement } = c;
decrement();
console.log('count after decrement:', c.count);    // 1


// ============================================================
// 3. this 类型与链式调用
// ============================================================

class StringBuilder {
  private parts: string[] = [];

  // 返回 this 类型，支持链式调用，类型安全
  add(s: string): this {
    this.parts.push(s);
    return this;
  }

  build(): string {
    return this.parts.join('');
  }
}

const sb = new StringBuilder()
  .add('Hello')
  .add(', ')
  .add('TypeScript')
  .add('!');

console.log('builder result:', sb.build());        // Hello, TypeScript!


// ============================================================
// 4. 多态 this（polymorphic this）：继承时返回类型仍是子类
// ============================================================

class Animal {
  name: string;

  constructor(name: string) {
    this.name = name;
  }

  // 返回 this 类型，子类继承后，返回类型自动变为子类
  clone(): this {
    // 简化示意：浅拷贝原型链
    return Object.create(this) as this;
  }

  speak(): string {
    return `${this.name} 发出声音`;
  }
}

class Dog extends Animal {
  breed: string;

  constructor(name: string, breed: string) {
    super(name);
    this.breed = breed;
  }

  bark(): string {
    return `${this.name}（${this.breed}）汪汪叫`;
  }
}

const d = new Dog('Buddy', 'Labrador');
const dClone = d.clone();   // dClone 的类型是 Dog，而不是 Animal

// 因为多态 this，clone() 返回 Dog，所以能访问子类方法
console.log('clone speak:', dClone.speak());
console.log('clone bark:', dClone.bark());
console.log('clone is Dog:', dClone instanceof Dog);   // true


// ============================================================
// 5. 字段声明顺序与严格模式
// ============================================================

// strict 模式下，未初始化且未断言的字段会报错
class StrictDemo {
  // ok: 有默认值
  version: string = '1.0';

  // ok: 在构造函数中赋值
  createdAt: Date;

  // ok: 确定赋值断言
  data!: unknown;

  constructor() {
    this.createdAt = new Date();
    // data 假设由外部框架注入，用 ! 告诉 TS 稍后会有
  }
}

const demo = new StrictDemo();
console.log('StrictDemo:', demo.version, demo.createdAt.toISOString());


console.log('\n--- class-basic.ts 执行完毕 ---');

export {};
