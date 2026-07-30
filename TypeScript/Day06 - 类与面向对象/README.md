# Day06 - 类与面向对象

> TypeScript 的 `class` 在 ES6 class 的运行时能力之上，叠加了一套**类型系统**与**访问控制**机制：字段可以声明类型、成员可以加 `public` / `private` / `protected` / `readonly` 修饰符、构造函数参数可以自动升级为字段、还有 ECMAScript 私有字段 `#`、抽象类、泛型类等增强能力。这套机制不仅是组织业务逻辑的工具，更是 NestJS、TypeORM、Nest 工厂模式与依赖注入的类型基石——理解 class 的类型语义，是理解“容器如何按类型注入 Provider”的前提。本篇从字段声明一路讲到设计模式，把 OOP 在 TS 中该有的“形态”一次讲透。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解 - class 基础](#二理论知识讲解---class-基础)
  - [2.1 字段声明、构造函数与方法](#21-字段声明构造函数与方法)
  - [2.2 this 类型与多态this](#22-this-类型与多态this)
- [三、访问修饰符](#三访问修饰符)
  - [3.1 public / private / protected](#31-public--private--protected)
  - [3.2 ECMAScript 私有字段 #（运行时私有）](#32-ecmascript-私有字段--运行时私有)
  - [3.3 private 关键字 vs # 私有字段](#33-private-关键字-vs--私有字段)
- [四、readonly 修饰符](#四readonly-修饰符)
- [五、参数属性 Parameter Properties](#五参数属性-parameter-properties)
- [六、getter 与 setter 存取器](#六getter-与-setter-存取器)
- [七、静态成员 static](#七静态成员-static)
  - [7.1 静态属性与静态方法](#71-静态属性与静态方法)
  - [7.2 静态代码块 static block](#72-静态代码块-static-block)
- [八、抽象类 abstract](#八抽象类-abstract)
  - [8.1 抽象类与抽象方法](#81-抽象类与抽象方法)
  - [8.2 抽象类 vs 接口](#82-抽象类-vs-接口)
- [九、继承 extends 与 implements](#九继承-extends-与-implements)
  - [9.1 extends 单继承与 super](#91-extends-单继承与-super)
  - [9.2 方法覆盖与属性覆盖的兼容性](#92-方法覆盖与属性覆盖的兼容性)
  - [9.3 implements 实现接口](#93-implements-实现接口)
- [十、类类型与实例类型](#十类类型与实例类型)
- [十一、类与接口的取舍](#十一类与接口的取舍)
- [十二、类与泛型结合](#十二类与泛型结合)
- [十三、类与结构化类型](#十三类与结构化类型)
- [十四、设计模式速览（类型安全实现）](#十四设计模式速览类型安全实现)
- [十五、关键知识点总结（含修饰符对照表）](#十五关键知识点总结含修饰符对照表)
- [十六、实战练习](#十六实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 用 TS 的 `class` 声明字段、构造函数、方法，并理解 `this` 类型在链式调用与继承中的作用。
2. 准确区分 `public` / `private` / `protected` 三种访问修饰符的可见性范围，并解释 `private` 为何只是“编译期私有”。
3. 说明 ECMAScript 私有字段 `#` 与 `private` 关键字的本质差异（运行时私有 vs 编译期私有），并在二者间做出选择。
4. 用 `readonly` 控制字段不可变性，理解“只能在构造函数中赋值”的限制来源。
5. 用参数属性（`constructor(public name: string)`）简化样板代码，并指出它与手动赋值在运行时完全等价。
6. 编写 getter / setter 存取器，配合 `private` 字段实现受控的读写逻辑。
7. 使用 `static` 定义静态成员、`static {}` 代码块完成静态初始化，并用静态方法实现工厂与单例。
8. 定义抽象类与抽象方法，说明其与接口的区别，并在子类中用 `extends` 实现具体逻辑。
9. 区分 `extends`（单继承、复用实现）与 `implements`（多接口、只校验形状），并正确处理方法覆盖的类型兼容。
10. 解释 `typeof Class`（构造函数类型）与 `Class`（实例类型）的差异，理解类在类型空间与值空间的双重身份。
11. 编写泛型类 `Repository<T>`，并用泛型约束限定 `T` 的形状。
12. 说明 TS 的 class 是**结构化类型**而非 Java 的名义类型，并能预测 class 间的赋值兼容性。
13. 在 TS 中以类型安全的方式实现单例、工厂、策略三种设计模式，为后续 NestJS 依赖注入打基础。

---

## 二、理论知识讲解 - class 基础

### 2.1 字段声明、构造函数与方法

TS 的 `class` 在 ES6 class 之上做了两件事：**给字段加类型注解**、**给访问控制加修饰符**。一个最基本的类包含字段声明、构造函数、方法三部分。

```ts
class User {
  // 字段声明：必须显式声明类型（strict 模式下未初始化的字段需断言赋值）
  id: number;
  name: string;
  readonly createdAt: Date;          // readonly：只能读，初始化后不可改

  // 构造函数：用于初始化字段
  constructor(id: number, name: string) {
    this.id = id;
    this.name = name;
    this.createdAt = new Date();
  }

  // 方法
  greet(): string {
    return `Hello, I'm ${this.name}`;
  }
}

const u = new User(1, 'Alice');
console.log(u.greet());
```

几个关键点：

1. **字段必须先声明再使用**。在 strict 模式下，未初始化的字段（如上面的 `id`）若不通过构造函数赋值，TS 会报“未赋值”错误；可用 `!`（确定赋值断言）绕过，但应优先在构造函数中赋值。
2. **字段默认值**。可以直接在声明处给默认值，TS 会据此推断类型：

```ts
class Counter {
  count = 0;           // 推断为 number
  steps: number = 10;  // 显式标注 + 默认值
}
```

3. **方法就是挂在原型上的函数**。和 ES6 一样，TS class 方法不绑定 `this`，回调场景需要用箭头函数字段或在构造函数中 `bind`：

```ts
class Timer {
  seconds = 0;
  // 箭头函数字段：this 永远指向实例，适合做回调
  tick = () => {
    this.seconds++;
  };
}
const t = new Timer();
setInterval(t.tick, 1000);   // ✅ this 不会丢失
```

### 2.2 this 类型与多态 this

在 class 内部，`this` 的类型默认是“当前类的实例类型”。这在链式调用和继承场景下非常有用——TS 会把 `this` 推断为**最具体的子类类型**，这就是“多态 this（polymorphic this）”。

```ts
class StringBuilder {
  private parts: string[] = [];

  add(s: string): this {     // 返回 this 类型，支持链式
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
  .add('TS');                // 链式调用全程类型安全
```

多态 `this` 在继承时尤其重要——子类继承父类方法后，方法的返回类型仍是子类，而不是父类：

```ts
class Animal {
  clone(): this {
    // 简化示意，实际克隆需深拷贝
    return Object.create(this);
  }
}
class Dog extends Animal {
  bark(): void { console.log('woof'); }
}

const d = new Dog().clone();   // d: Dog，而不是 Animal
d.bark();                      // ✅ 仍可调用子类方法
```

---

## 三、访问修饰符

### 3.1 public / private / protected

TS 提供三个访问修饰符，**默认是 `public`**：

| 修饰符 | 类内部 | 子类 | 类外部 |
|--------|--------|------|--------|
| `public`（默认） | ✅ | ✅ | ✅ |
| `protected` | ✅ | ✅ | ❌ |
| `private` | ✅ | ❌ | ❌ |

```ts
class Account {
  public owner: string;        // 显式 public，等价于省略
  protected balance: number;   // 子类可见，外部不可见
  private pin: string;         // 仅本类可见

  constructor(owner: string, balance: number, pin: string) {
    this.owner = owner;
    this.balance = balance;
    this.pin = pin;
  }

  // 类内部可以访问所有成员
  describe(): string {
    return `${this.owner} 余额 ${this.balance}，PIN ${this.pin}`;
  }
}

class SavingsAccount extends Account {
  withdraw(amount: number): void {
    // ✅ 可以访问 protected balance
    if (amount <= this.balance) {
      this.balance -= amount;
    }
    // ❌ this.pin   // private，子类也不可访问
  }
}

const acc = new Account('Alice', 1000, '1234');
console.log(acc.owner);          // ✅ public
// console.log(acc.balance);     // ❌ protected
// console.log(acc.pin);         // ❌ private
```

**重要提醒**：TS 的 `private` / `protected` 是**编译期检查**，编译成 JS 后这些字段在运行时仍然可访问（普通属性）。换言之，它们是“给开发者和编译器看的契约”，不是真正的运行时隔离。要实现真正的运行时私有，需用 `#` 私有字段（见 3.2）。

### 3.2 ECMAScript 私有字段 #（运行时私有）

TS 4.3+ 完整支持 ECMAScript 提案的 `#` 私有字段。它和 `private` 关键字最大的区别是：**`#` 字段在运行时也是私有的**，外部代码、子类、甚至 `JSON.stringify` 都无法访问。

```ts
class SecureToken {
  #secret: string;            // 真正的运行时私有字段

  constructor(secret: string) {
    this.#secret = secret;
  }

  reveal(): string {
    return this.#secret;      // 类内部正常访问
  }
}

const t = new SecureToken('abc');
// console.log(t.#secret);    // ❌ 编译期就报错
// console.log(t['#secret']); // ❌ 运行时也无法访问
console.log(t.reveal());      // ✅ 只能通过暴露的方法访问
```

`#` 字段的几个特性：

1. **字段名以 `#` 开头**，每个字段独立声明，不能与同名的普通字段冲突。
2. **运行时私有**：编译产物用 WeakSet / 真正的私有字段语义实现，外部 JS 代码也读不到。
3. **不被 `in` 操作符发现**（针对子类）：

```ts
class Base {
  #hidden = 42;
  hasHidden(): boolean {
    return #hidden in this;   // 私有字段 brand check
  }
}
```

### 3.3 private 关键字 vs # 私有字段

| 维度 | `private` 关键字 | `#` 私有字段 |
|------|------------------|--------------|
| 检查时机 | 仅编译期 | 编译期 + 运行时 |
| 运行时是否可见 | ✅ 可见（普通属性） | ❌ 不可见 |
| 子类能否定义同名字段 | 不能 | ✅ 可以（独立作用域） |
| 兼容性 | TS 早期就有 | TS 4.3+ / ES2022 |
| `JSON.stringify` 是否包含 | ✅ 包含 | ❌ 不包含 |
| 适用场景 | 团队契约、纯 TS 工程 | 需要真运行时隔离、对外发布的库 |

> 📌 **选型建议**：纯 TS 项目用 `private` 足够，工具链与 IDE 跳转体验更好；对外发布的库、需要严格防篡改的代码（如安全相关）用 `#`。

---

## 四、readonly 修饰符

`readonly` 修饰符让字段成为“只在初始化时可写”的常量。它的限制是：**只能在声明处或构造函数中赋值**，之后任何赋值都会报错。

```ts
class Config {
  readonly version: string;
  readonly env: string = 'prod';     // 声明处赋值

  constructor(version: string) {
    this.version = version;          // ✅ 构造函数中可赋值
  }

  update(): void {
    // this.version = '2.0';         // ❌ 构造函数外不可赋值
  }
}

const cfg = new Config('1.0');
// cfg.version = '2.0';              // ❌ 外部也不可赋值
```

几个细节：

1. **`readonly` 只限制“赋值”，不限制“内部可变性”**。若字段是对象/数组，仍可修改其内部属性：

```ts
class Hub {
  readonly tags: string[] = [];
  addTag(t: string): void {
    this.tags.push(t);   // ✅ 修改数组内部，不触发 readonly 报错
    // this.tags = [];   // ❌ 重新赋值才报错
  }
}
```

2. **`readonly` 是浅层不可变**。要真正不可变，需配合 `Readonly<T>` 或 `as const`。
3. **`readonly` 可与参数属性联用**：`constructor(readonly id: number)` 一步到位。

---

## 五、参数属性 Parameter Properties

TS 提供了一种语法糖：在构造函数参数前直接加修饰符（`public` / `private` / `protected` / `readonly`，可组合），TS 会**自动声明同名字段并完成赋值**。这就是参数属性。

```ts
class User {
  // 等价于：声明字段 + 构造函数赋值
  constructor(
    public id: number,
    public name: string,
    private password: string,
    readonly createdAt: Date = new Date(),
  ) {}
}

const u = new User(1, 'Alice', 'pwd123');
console.log(u.id, u.name);     // ✅ public
// u.password;                  // ❌ private
// u.createdAt = new Date();    // ❌ readonly
```

参数属性与手动赋值**完全等价**，下面两段代码编译后的 JS 是一样的：

```ts
// 写法 A：参数属性
class A {
  constructor(public x: number) {}
}

// 写法 B：手动声明 + 赋值
class B {
  public x: number;
  constructor(x: number) {
    this.x = x;
  }
}
```

**何时用参数属性**：当字段只需要在构造函数中赋值、没有额外初始化逻辑时，用参数属性可大幅减少样板代码。如果构造函数内有校验、转换、副作用，则建议拆开写，逻辑更清晰。

---

## 六、getter 与 setter 存取器

TS 支持用 `get` / `set` 关键字定义存取器，把“字段访问”变成“方法调用”，从而实现校验、派生、日志等逻辑。存取器常与 `private` 字段配合——私有字段存真实数据，公开的 getter/setter 控制读写。

```ts
class Temperature {
  private _celsius: number = 0;

  get celsius(): number {
    return this._celsius;
  }

  set celsius(value: number) {
    if (value < -273.15) {
      throw new Error('温度不能低于绝对零度');
    }
    this._celsius = value;
  }

  // 只读 getter：派生属性，外部只读不可写
  get fahrenheit(): number {
    return this._celsius * 9 / 5 + 32;
  }
}

const t = new Temperature();
t.celsius = 25;
console.log(t.fahrenheit);     // 77
// t.fahrenheit = 100;         // ❌ 没有 setter，只读
// t.celsius = -300;           // ❌ 抛错
```

要点：

1. **只写 getter 不写 setter**，该属性就是只读的；只写 setter 不写 getter 较少见（写唯一属性）。
2. **getter / setter 的访问级别一致**：TS 不允许 getter 是 `public` 而 setter 是 `private`（4.3+ 已放宽，允许 setter 比 getter 更严格，但仍需谨慎）。
3. **存取器背后的字段命名约定**：常用 `_` 前缀（`_celsius`）作为私有后备字段，避免与存取器同名冲突。
4. **存取器不占实例字段位**：它们定义在原型上，访问时执行函数。

---

## 七、静态成员 static

### 7.1 静态属性与静态方法

`static` 修饰符把成员挂在**类本身**上，而非实例上。静态成员通过 `ClassName.member` 访问，所有实例共享一份。

```ts
class MathUtil {
  static PI = 3.14159;                       // 静态属性
  static readonly VERSION = '1.0.0';         // 静态只读

  static square(x: number): number {         // 静态方法
    return x * x;
  }

  static max<T>(a: T, b: T): T {             // 静态泛型方法
    return a > b ? a : b;
  }
}

console.log(MathUtil.PI);
console.log(MathUtil.square(5));
// const m = new MathUtil();
// m.PI;   // ❌ 静态成员只能通过类名访问
```

静态方法内 `this` 指向类本身（不是实例），因此**静态方法内不能访问实例字段**，只能访问其他静态成员：

```ts
class Counter {
  static instanceCount = 0;
  count = 0;

  constructor() {
    Counter.instanceCount++;        // ✅ 通过类名访问
  }

  static totalInstances(): number {
    // this.count;                  // ❌ 静态方法内没有实例 this
    return this.instanceCount;      // ✅ this 是类本身
  }
}
```

### 7.2 静态代码块 static block

ES2022 引入 `static {}` 代码块，用于执行**静态初始化逻辑**，比“立即执行表达式”更规范。它会在类定义被求值时执行一次。

```ts
class ConfigLoader {
  // 私有静态字段：在 static 块中赋值
  // （开启 useDefineForClassFields 时，static readonly 字段不能在 static 块中赋值，
  //   用“私有字段 + 只读 getter”可实现等价的只读语义，见 Code/static-members.ts）
  private static _settings: Record<string, string>;

  static {
    // 静态初始化块：可以访问私有静态字段，可以抛错
    const env = process.env.NODE_ENV ?? 'dev';
    ConfigLoader._settings = {
      env,
      apiKey: process.env.API_KEY ?? 'default-key',
    };
  }

  // 只读 getter：对外暴露不可变配置
  static get SETTINGS(): Record<string, string> {
    return ConfigLoader._settings;
  }
}

console.log(ConfigLoader.SETTINGS.env);
```

`static {}` 的用途：

1. **计算型静态字段**：需要多行逻辑才能确定的静态值。
2. **静态字段间依赖初始化**：A 依赖 B，需要按顺序执行。
3. **校验静态配置**：环境变量缺失时直接抛错，避免运行时延迟暴露问题。

每个类可以有多个 `static {}` 块，按出现顺序执行，且可以访问 `#` 私有静态字段。

---

## 八、抽象类 abstract

### 8.1 抽象类与抽象方法

`abstract` 修饰类表示“不能直接实例化”，只能作为父类被继承；`abstract` 修饰方法表示“只声明签名，不提供实现，必须由子类实现”。

```ts
abstract class Shape {
  abstract area(): number;          // 抽象方法：只有签名
  abstract readonly name: string;   // 抽象属性：子类必须实现

  // 普通方法：可以有默认实现，子类可直接复用
  describe(): string {
    return `${this.name} 的面积是 ${this.area().toFixed(2)}`;
  }
}

class Circle extends Shape {
  constructor(public radius: number) {
    super();                        // 即使父类没有字段，也要调用 super()
  }

  get name(): string {              // 实现抽象属性（用 getter 满足只读要求）
    return 'Circle';
  }

  area(): number {                  // 实现抽象方法
    return Math.PI * this.radius ** 2;
  }
}

// const s = new Shape();           // ❌ 抽象类不能实例化
const c = new Circle(2);
console.log(c.describe());          // 复用父类方法
```

要点：

1. **抽象类不能 `new`**，但可以有构造函数，供子类 `super()` 调用。
2. **抽象方法没有方法体**，只有签名；子类必须用 `override`（推荐）或同名方法实现。
3. **抽象类可以包含已实现的方法与字段**，这是它与“纯接口”的关键差异。
4. **抽象属性**（如 `abstract readonly name: string`）要求子类提供对应字段或 getter。

### 8.2 抽象类 vs 接口

| 维度 | 抽象类 `abstract class` | 接口 `interface` |
|------|-------------------------|------------------|
| 能否有实现 | ✅ 可以有字段、已实现方法 | ❌ 只能描述形状 |
| 多继承 | ❌ 单继承（一个子类只能 extends 一个） | ✅ 可 implements 多个 |
| 运行时存在 | ✅ 编译后是真实类，可用 `instanceof` | ❌ 类型擦除，运行时无 |
| 默认实现 | ✅ 可为子类提供公共逻辑 | ❌ 无（除非用抽象类） |
| 适用场景 | 共享实现 + 强约束子类形态 | 描述对象形状、跨类契约 |

> 📌 **经验法则**：当你需要“基类提供部分实现 + 子类强制实现某些方法”时用抽象类；当你只是想描述“这个对象长什么样”时用接口。NestJS 的 `@Injectable()` Provider、TypeORM 的 Repository 基类大量使用抽象类。

---

## 九、继承 extends 与 implements

### 9.1 extends 单继承与 super

TS 沿用 ES6 的**单继承**模型：一个类只能 `extends` 一个父类。子类构造函数必须先调用 `super()` 才能使用 `this`。

```ts
class Animal {
  constructor(public name: string) {}

  speak(): string {
    return `${this.name} 发出声音`;
  }
}

class Dog extends Animal {
  constructor(name: string, public breed: string) {
    super(name);                   // 必须先调用 super，再使用 this
  }

  speak(): string {
    return `${super.speak()}（${this.breed} 汪汪叫）`;
  }
}

const d = new Dog('Buddy', 'Labrador');
console.log(d.speak());
```

### 9.2 方法覆盖与属性覆盖的兼容性

子类覆盖父类方法时，签名必须**兼容**——参数不能比父类更宽（逆变），返回值不能比父类更窄（协变）。简单记忆：**子类方法要能“替代”父类方法被调用**。

```ts
class Base {
  greet(name: string): string {
    return `Hello, ${name}`;
  }
}

class OK extends Base {
  greet(name: string): string {        // ✅ 签名一致
    return `Hi, ${name}`;
  }
}

class Bad extends Base {
  // greet(name: string, extra: string): string {   // ❌ 多了必填参数
  //   return name + extra;
  // }
}
```

属性覆盖同理：子类属性类型必须是父类属性类型的子类型：

```ts
class P { animal: Animal = new Animal(); }
class C1 extends P { animal: Dog; }    // ✅ Dog 是 Animal 的子类型
// class C2 extends P { animal: object; }  // ❌ object 不是 Animal 的子类型
```

> 💡 TS 4.3+ 引入 `override` 关键字，显式标记覆盖方法。开启 `noImplicitOverride` 后，未加 `override` 的覆盖会报错，避免“父类改名了子类没跟上”的经典 bug：

```ts
class Base { speak(): void {} }
class Sub extends Base {
  override speak(): void { }   // ✅ 显式覆盖
  // override bark(): void {}  // ❌ 父类没有 bark，override 报错
}
```

### 9.3 implements 实现接口

`implements` 表示“类承诺满足某个接口的形状”，**不继承任何实现**。一个类可以 `implements` 多个接口。

```ts
interface Serializable {
  serialize(): string;
}
interface Loggable {
  log(msg: string): void;
}

class UserEntity implements Serializable, Loggable {
  constructor(public id: number, public name: string) {}

  serialize(): string {
    return JSON.stringify({ id: this.id, name: this.name });
  }

  log(msg: string): void {
    console.log(`[User:${this.id}] ${msg}`);
  }
}
```

注意：

1. **`implements` 只校验形状**，不提供字段、不调用 `super`、不继承方法。
2. **接口描述的是“类的实例类型”**，而非“类本身的静态类型”。要约束静态成员，需用构造函数签名。
3. **`extends` 和 `implements` 可同时使用**：`class D extends B implements I1, I2`。

---

## 十、类类型与实例类型

类在 TS 中有**双重身份**：

- **值空间**：类是一个真实的构造函数，可以 `new`，可以 `extends`。
- **类型空间**：类名作为类型用时，表示**实例类型**。

```ts
class Point {
  constructor(public x: number, public y: number) {}
  static origin(): Point {
    return new Point(0, 0);
  }
}

// 1. 作为类型用：实例类型
const p: Point = new Point(1, 2);     // p 拥有实例字段 x / y

// 2. 作为值用：构造函数
const P: typeof Point = Point;        // P 是“类本身”的类型
const p2 = new P(3, 4);               // ✅ 可 new
// p2.origin();                       // ❌ origin 是静态方法，实例上没有
P.origin();                           // ✅ 静态方法通过类本身调用
```

`typeof Point` 得到的是“Point 这个构造函数对象”的类型，它包含静态方法、构造签名，但不包含实例字段。这是工厂模式、依赖注入中“按构造函数注入”的类型基础。

```ts
function create<T>(Ctor: new (...args: any[]) => T, ...args: any[]): T {
  return new Ctor(...args);
}
const p3 = create(Point, 5, 6);       // p3: Point
```

---

## 十一、类与接口的取舍

`class` 与 `interface` 都能描述对象的形状，但定位完全不同：

| 维度 | `class` | `interface` |
|------|---------|-------------|
| 是否有实现 | ✅ 字段、方法都有实现 | ❌ 只描述形状 |
| 运行时存在 | ✅ 真实存在的值 | ❌ 编译期擦除 |
| `instanceof` | ✅ 可用 | ❌ 不可用 |
| 描述对象形状 | 可以（当作类型用） | ✅ 推荐方式 |
| 描述函数/构造函数 | 可定义 | ✅ 更灵活（call/construct 签名） |
| 跨类共享契约 | 需继承，受限 | ✅ 任意类 implements |
| 树摇友好 | ❌ 有运行时开销 | ✅ 纯类型，零开销 |

**选型建议**：

- **描述数据形状**（DTO、Props、Config）→ 用 `interface` 或 `type`，零运行时开销。
- **封装行为 + 状态**（Service、Repository、Controller）→ 用 `class`。
- **定义可被多种类实现的契约**（如 NestJS 的 `ILogger` 接口）→ 用 `interface` + `class implements`。
- **需要 `instanceof` 区分类型** → 必须用 `class`（接口无运行时存在）。

NestJS 的典型组合是：用 `interface` 定义 Provider 的能力契约，用 `class` 实现该契约，再用 DI 容器按接口注入——这正是“接口描述形状、类提供实现”的最佳实践。

---

## 十二、类与泛型结合

类可以是泛型的：`class Repository<T>`。泛型参数 `T` 在类的所有成员（字段、方法、构造函数）中都可用，实例化时确定具体类型。

```ts
class Repository<T extends { id: number }> {
  private items: T[] = [];

  add(item: T): void {
    this.items.push(item);
  }

  findById(id: number): T | undefined {
    return this.items.find((x) => x.id === id);
  }

  remove(id: number): boolean {
    const idx = this.items.findIndex((x) => x.id === id);
    if (idx === -1) return false;
    this.items.splice(idx, 1);
    return true;
  }

  list(): readonly T[] {
    return this.items;
  }
}

interface User { id: number; name: string; }
interface Post { id: number; title: string; }

const userRepo = new Repository<User>();     // T = User
userRepo.add({ id: 1, name: 'Alice' });
const u = userRepo.findById(1);              // u: User | undefined

const postRepo = new Repository<Post>();     // T = Post
// postRepo.add({ id: 1, name: 'x' });       // ❌ 不是 Post 形状
```

泛型约束在类上的应用：`T extends { id: number }` 限定 `T` 必须有 `id` 字段，这样 `findById` 才能合法地访问 `x.id`。这是 TypeORM、Prisma 等 ORM 的核心模式——Repository 只接受带主键的实体类型。

```ts
// 经典：栈数据结构
class Stack<T> {
  private data: T[] = [];
  push(item: T): void { this.data.push(item); }
  pop(): T | undefined { return this.data.pop(); }
  peek(): T | undefined { return this.data[this.data.length - 1]; }
  get size(): number { return this.data.length; }
}

const numStack = new Stack<number>();
numStack.push(1);
numStack.push(2);
const top = numStack.pop();   // top: number | undefined
```

---

## 十三、类与结构化类型

**TS 的 class 是结构化类型，不是名义类型**。这是与 Java / C# 最本质的差异——TS 判断“一个值是否属于某 class 类型”时，看的是**结构是否匹配**，而不是“是否真的由该构造函数创建”。

```ts
class Point {
  constructor(public x: number, public y: number) {}
}

// 字面量对象，结构完全相同
const p1: Point = { x: 1, y: 2 };     // ✅ 结构匹配，可以赋值
const p2 = new Point(1, 2);
console.log(p1 instanceof Point);     // ❌ false（p1 不是 Point 实例）
console.log(p2 instanceof Point);     // ✅ true
```

也就是说：

- **类型兼容看结构**：`{ x, y }` 能赋给 `Point` 类型，因为字段一致。
- **`instanceof` 看原型链**：只有 `new Point(...)` 出来的对象才 `instanceof Point`。

这带来一些反直觉但合理的兼容性：

```ts
class A { x = 1; }
class B { x = 1; }
const a: A = new B();                 // ✅ 结构相同，B 可赋给 A 类型

class User { constructor(public name: string) {} }
const u: User = { name: 'Alice' };    // ✅ 字面量也能赋值
```

**实践影响**：

1. 不要依赖“只有通过我的 class 构造的对象才能进入我的函数”——TS 不强制这一点。若需要，可在 class 里加 `#` 私有字段或 `brand` symbol 做名义标记：

```ts
class UserId {
  readonly #brand: unique symbol;     // 名义标记
  constructor(public value: number) {}
}
// const id: UserId = { value: 1 };   // ❌ 缺 #brand，结构不匹配
```

2. **结构化类型让 class 与 interface 高度互通**：一个 `class` 类型可以被等结构的 `interface` 替换，反之亦然。这也是为什么 NestJS 中“用 interface 描述 Provider、用 class 实现”能无缝替换。

---

## 十四、设计模式速览（类型安全实现）

这三种模式是理解 NestJS 依赖注入、TypeORM 工厂、策略路由的基础。我们用 TS 的类型系统把它们写得“编译期安全”。

### 模式 1：单例模式

确保一个类只有一个实例，提供全局访问点。TS 中常用“懒加载 + 静态访问器”实现：

```ts
class Logger {
  private static instance: Logger;

  private constructor() {            // 私有构造函数，禁止外部 new
    if (Logger.instance) {
      throw new Error('请用 Logger.getInstance()');
    }
  }

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  log(msg: string): void {
    console.log(`[LOG] ${msg}`);
  }
}

const a = Logger.getInstance();
const b = Logger.getInstance();
console.log(a === b);                 // true，同一实例
// new Logger();                      // ❌ 构造函数私有
```

NestJS 的 Provider 默认就是单例作用域，但理解手写单例有助于看清 DI 容器的内部机制。

### 模式 2：工厂模式

把“创建对象”的逻辑封装起来，调用方不关心具体怎么 new。TS 中用**泛型 + 构造函数类型**让工厂类型安全：

```ts
interface Animal {
  speak(): string;
}
class Dog implements Animal {
  speak(): string { return '汪汪'; }
}
class Cat implements Animal {
  speak(): string { return '喵喵'; }
}

type AnimalCtor = new () => Animal;

class AnimalFactory {
  private registry = new Map<string, AnimalCtor>([
    ['dog', Dog],
    ['cat', Cat],
  ]);

  create(kind: string): Animal {
    const Ctor = this.registry.get(kind);
    if (!Ctor) throw new Error(`未知动物：${kind}`);
    return new Ctor();
  }
}

const factory = new AnimalFactory();
console.log(factory.create('dog').speak());   // 汪汪
console.log(factory.create('cat').speak());   // 喵喵
```

`new () => Animal` 这种构造函数签名是 NestJS DI 容器“按 token 解析 Provider 并 new 出实例”的类型基础。

### 模式 3：策略模式

把“可替换的算法”抽象成接口，运行时注入不同实现。TS 中用 `interface` 定义策略契约，类实现具体策略：

```ts
interface DiscountStrategy {
  calculate(price: number): number;
}

class NoDiscount implements DiscountStrategy {
  calculate(price: number): number { return price; }
}
class TenPercentOff implements DiscountStrategy {
  calculate(price: number): number { return price * 0.9; }
}
class FullReduction implements DiscountStrategy {
  constructor(private threshold: number, private off: number) {}
  calculate(price: number): number {
    return price >= this.threshold ? price - this.off : price;
  }
}

class ShoppingCart {
  constructor(private discount: DiscountStrategy = new NoDiscount()) {}

  setDiscount(strategy: DiscountStrategy): void {
    this.discount = strategy;
  }

  checkout(price: number): number {
    return this.discount.calculate(price);
  }
}

const cart = new ShoppingCart();
console.log(cart.checkout(100));                       // 100（无折扣）
cart.setDiscount(new TenPercentOff());
console.log(cart.checkout(100));                       // 90
cart.setDiscount(new FullReduction(100, 20));
console.log(cart.checkout(100));                       // 80
```

策略模式的精髓是“面向接口编程”——`ShoppingCart` 依赖的是 `DiscountStrategy` 接口，而不是任何具体类。这正是 NestJS 依赖注入的核心思想：**消费方依赖抽象（接口/Token），容器在运行时注入具体实现**。理解这一段，再看 NestJS 的 `useClass` / `useValue` / `useFactory` Provider 就会非常自然。

---

## 十五、关键知识点总结（含修饰符对照表）

### 修饰符对照表

| 修饰符 | 作用域 | 类内部 | 子类 | 类外部 | 备注 |
|--------|--------|--------|------|--------|------|
| `public` | 实例/静态 | ✅ | ✅ | ✅ | 默认，可省略 |
| `protected` | 实例/静态 | ✅ | ✅ | ❌ | 常用于“模板方法”的钩子 |
| `private` | 实例/静态 | ✅ | ❌ | ❌ | 仅编译期检查 |
| `#field` | 实例/静态 | ✅ | ❌ | ❌ | 运行时也私有 |
| `readonly` | 实例/静态 | 只读 | 只读 | 只读 | 仅声明处/构造函数可写 |
| `static` | 类本身 | — | — | 类名访问 | 不属于实例 |
| `abstract` | 类/方法 | 不实例化 | 必须实现 | 不实例化 | 只能被继承 |
| `override` | 方法 | 标记覆盖 | — | — | 配合 noImplicitOverride |

### 核心要点

1. **class = ES6 class + 类型注解 + 访问修饰符**，运行时仍是原型链继承。
2. **`private` 是编译期私有，`#` 是运行时私有**——选型看是否需要真隔离。
3. **`readonly` 浅层不可变**：只限制赋值，不限制对象内部修改；与参数属性联用可一步声明只读字段。
4. **参数属性是语法糖**：`constructor(public x: number)` 等价于“声明字段 + 构造函数赋值”。
5. **getter/setter** 把字段访问变成方法调用，常与 `private` 后备字段配合实现受控读写。
6. **`static`** 成员属于类本身，`static {}` 块用于静态初始化，所有实例共享一份。
7. **抽象类**有实现可继承，不能实例化；**接口**只描述形状，可多实现。前者用于“共享实现 + 强约束”，后者用于“跨类契约”。
8. **`extends` 单继承复用实现**，子类构造函数必须先 `super()`；**`implements` 多接口只校验形状**，不继承实现。
9. **方法/属性覆盖要兼容**：子类签名要能替代父类，推荐用 `override` 显式标记。
10. **类有双重身份**：作为值是构造函数（`typeof Class`），作为类型是实例类型（`Class`）。
11. **TS class 是结构化类型**：`{x,y}` 能赋给 `Point` 类型；`instanceof` 才看原型链。
12. **泛型类**让类型在实例化时确定，泛型约束（`T extends {id: number}`）可限定实体形状。
13. **设计模式**：单例（私有构造 + 静态访问）、工厂（构造函数签名 + 注册表）、策略（接口 + 注入实现）——都是 NestJS DI 的类型前置知识。

---

## 十六、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：用参数属性 + readonly 设计不可变 User（对应 `parameter-properties.ts` 与 `class-basic.ts`）

设计一个 `User` 类，要求：

1. 用参数属性一步声明 `id`（`readonly`）、`name`（`public`）、`password`（`private`）。
2. 提供 `verify(input: string): boolean` 方法，比对 `password`，但不暴露 `password` 字段。
3. 提供 `withName(newName: string): User` 方法，返回一个**新**的 `User` 实例（保持 `id` 与 `password` 不变），体现不可变模式。
4. 思考：如果 `password` 用 `#` 私有字段而不是 `private` 关键字，`withName` 的实现会有什么不同？

**进阶**：把 `User` 改成泛型 `User<R extends string = string>`，让 `role` 字段的类型由调用方决定（如 `User<'admin' | 'user'>`）。

### 练习 2：抽象类 + 继承实现支付方式（对应 `abstract-class.ts` 与 `inheritance-implements.ts`）

1. 定义抽象类 `PaymentMethod`，包含：
   - 抽象属性 `readonly name: string`。
   - 抽象方法 `pay(amount: number): boolean`。
   - 已实现方法 `describe(): string`，返回 `${this.name}：${this.pay(0) ? '可用' : '不可用'}`。
2. 实现 `CreditCard` 与 `Alipay` 两个子类，各自实现抽象成员。
3. 写一个 `Checkout` 类，依赖 `PaymentMethod`（构造函数注入），调用 `pay` 完成支付。
4. 用 `override` 关键字标记覆盖方法，开启 `noImplicitOverride` 验证。
5. 思考：如果把 `PaymentMethod` 改成 `interface`，`describe()` 这个已实现的方法该怎么处理？为什么这里用抽象类更合适？

### 练习 3：泛型 Repository + 策略模式（对应 `generic-class.ts` 与 `static-members.ts`）

1. 实现泛型类 `Repository<T extends { id: number }>`，提供 `add` / `findById` / `remove` / `list` 方法。
2. 定义接口 `SortStrategy<T>`，包含 `sort(items: T[]): T[]`。实现 `ByIdAscSort` 和 `ByIdDescSort` 两个策略。
3. 给 `Repository` 增加 `setSort(strategy: SortStrategy<T>)` 方法，`list()` 时应用当前策略。
4. 用单例模式实现一个 `RepositoryRegistry`，集中管理多个 `Repository` 实例（`Map<string, Repository<unknown>>`）。
5. 思考：`Repository<unknown>` 在 `Map` 中是否类型安全？如何用泛型方法 `getRepository<T>(name: string): Repository<T>` 让调用方拿到正确类型的 Repository？

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/class-basic.ts` | class 字段声明、构造函数、方法、this 类型与多态 this |
| `Code/access-modifiers.ts` | public / private / protected 对比、# 私有字段运行时私有演示 |
| `Code/parameter-properties.ts` | 参数属性简写、与手动赋值等价性对比 |
| `Code/getters-setters.ts` | 存取器、只读 getter、与 private 后备字段配合 |
| `Code/abstract-class.ts` | 抽象类、抽象方法、子类实现、与接口对比 |
| `Code/inheritance-implements.ts` | extends 单继承、implements 多接口、方法覆盖、override |
| `Code/static-members.ts` | 静态属性/方法、static 代码块、单例模式 |
| `Code/generic-class.ts` | 泛型类 Repository<T>、Stack<T>、泛型约束 |

运行方式（需先在 `Code/` 目录执行 `npm install`）：

```bash
cd Code
npm install
npx ts-node class-basic.ts
npx ts-node access-modifiers.ts
npx ts-node parameter-properties.ts
npx ts-node getters-setters.ts
npx ts-node abstract-class.ts
npx ts-node inheritance-implements.ts
npx ts-node static-members.ts
npx ts-node generic-class.ts
```

或使用 `package.json` 中预置的脚本：

```bash
npm run basic        # 等价于 ts-node class-basic.ts
npm run access
npm run param
npm run accessor
npm run abstract
npm run inherit
npm run static
npm run generic
npm run type-check   # 全量类型检查（不输出文件）
```

---

> 📚 **延伸阅读**
> - TS 官方手册：[Classes](https://www.typescriptlang.org/docs/handbook/2/classes.html)
> - TS 官方手册：[Type Modifiers](https://www.typescriptlang.org/docs/handbook/2/classes.html#member-visibility)
> - ECMAScript 提案：[Private class fields](https://github.com/tc39/proposal-class-fields)
> - TS 4.3 Release Notes：私有字段与静态代码块增强
> - NestJS 官方文档：[Providers](https://docs.nestjs.com/providers)（理解 class 如何成为 DI 的基本单位）
