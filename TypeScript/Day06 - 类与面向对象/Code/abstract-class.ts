/**
 * Day06 - 抽象类 abstract：抽象方法、子类实现、与接口对比
 *
 * 本文件演示：
 * 1. 抽象类不能实例化，只能被继承
 * 2. 抽象方法只有签名，子类必须实现
 * 3. 抽象类可包含已实现方法，子类直接复用
 * 4. 抽象属性：子类必须提供对应字段或 getter
 * 5. 抽象类 vs 接口：何时用哪个
 */

// ============================================================
// 1. 抽象类基础：不能实例化、可含已实现方法
// ============================================================

abstract class Shape {
  // 抽象属性：子类必须实现（用字段或 getter 满足只读要求）
  abstract readonly name: string;

  // 抽象方法：只有签名，没有方法体
  abstract area(): number;

  // 已实现方法：子类可直接复用，无需重写
  describe(): string {
    return `${this.name} 的面积是 ${this.area().toFixed(2)}`;
  }
}

// ❌ 抽象类不能直接实例化
// const s = new Shape();

// ============================================================
// 2. 子类实现抽象成员
// ============================================================

class Circle extends Shape {
  constructor(public radius: number) {
    super();                  // 即使父类没有显式构造函数，也要调用 super()
  }

  // 实现抽象属性：用 getter 满足 readonly
  get name(): string {
    return 'Circle';
  }

  // 实现抽象方法
  area(): number {
    return Math.PI * this.radius ** 2;
  }
}

class Rectangle extends Shape {
  constructor(public width: number, public height: number) {
    super();
  }

  get name(): string {
    return 'Rectangle';
  }

  area(): number {
    return this.width * this.height;
  }
}

const circle = new Circle(2);
const rect = new Rectangle(4, 5);

// 复用父类已实现的 describe()
console.log(circle.describe());   // Circle 的面积是 12.57
console.log(rect.describe());     // Rectangle 的面积是 20.00

// 抽象类可作为类型用，引用任意子类实例
const shapes: Shape[] = [circle, rect];
shapes.forEach((s) => console.log('  -', s.describe()));


// ============================================================
// 3. 抽象类作为多态容器：统一接口、各自实现
// ============================================================

abstract class Animal {
  constructor(public name: string) {}

  abstract speak(): string;        // 子类各自实现

  // 模板方法：定义流程，调用抽象方法让子类填空
  introduce(): string {
    return `我是 ${this.name}，${this.speak()}`;
  }
}

class Dog extends Animal {
  speak(): string { return '汪汪！'; }
}

class Cat extends Animal {
  speak(): string { return '喵~'; }
}

class Duck extends Animal {
  speak(): string { return '嘎嘎！'; }
}

const animals: Animal[] = [
  new Dog('Buddy'),
  new Cat('Kitty'),
  new Duck('Donald'),
];
animals.forEach((a) => console.log(a.introduce()));


// ============================================================
// 4. 抽象类可以有构造函数与受保护字段
// ============================================================

abstract class RepositoryBase<T extends { id: number }> {
  protected items: T[] = [];          // protected：子类可访问

  constructor(protected entityName: string) {}

  abstract create(data: Omit<T, 'id'>): T;   // 子类决定如何生成 id

  add(item: T): void {
    this.items.push(item);
  }

  findById(id: number): T | undefined {
    return this.items.find((x) => x.id === id);
  }

  count(): number {
    return this.items.length;
  }

  protected nextId(): number {
    return this.items.length + 1;
  }
}

interface User { id: number; name: string; }
interface Post { id: number; title: string; }

class UserRepository extends RepositoryBase<User> {
  constructor() {
    super('user');
  }

  // 实现抽象方法：用 nextId 生成 id
  create(data: Omit<User, 'id'>): User {
    const user: User = { id: this.nextId(), ...data };
    this.add(user);
    return user;
  }
}

const userRepo = new UserRepository();
userRepo.create({ name: 'Alice' });
userRepo.create({ name: 'Bob' });
console.log(`仓库 [${userRepo['entityName']}] 有 ${userRepo.count()} 条记录`);
console.log('查找 id=1:', userRepo.findById(1));


// ============================================================
// 5. 抽象类 vs 接口：何时用哪个
// ============================================================

// 场景 A：有公共实现 + 强约束子类 → 用抽象类
abstract class HttpHandler {
  // 公共流程：所有子类共享
  async handle(req: unknown): Promise<string> {
    this.validate(req);
    const result = await this.process(req);
    return this.format(result);
  }

  protected validate(req: unknown): void {
    if (req == null) throw new Error('请求不能为空');
  }

  protected abstract process(req: unknown): Promise<unknown>;

  protected format(result: unknown): string {
    return JSON.stringify(result);
  }
}

class UserHandler extends HttpHandler {
  protected async process(req: unknown): Promise<unknown> {
    return { ok: true, data: req };
  }
}

// 场景 B：只描述形状、跨类契约 → 用接口
interface Loggable {
  log(msg: string): void;
}
interface Serializable {
  serialize(): string;
}

// 一个类可以 implements 多个接口，但只能 extends 一个抽象类
class Service implements Loggable, Serializable {
  log(msg: string): void {
    console.log('[Service]', msg);
  }
  serialize(): string {
    return '{}';
  }
}

console.log('\n--- 抽象类 vs 接口 ---');
console.log('抽象类：有实现、单继承、可用 instanceof');
console.log('接口：只描述形状、多实现、类型擦除');

const handler = new UserHandler();
handler.handle({ id: 1 }).then((r) => console.log('handler 结果:', r));


// ============================================================
// 6. abstract 也可修饰访问器（getter/setter）
// ============================================================

abstract class ConfigBase {
  // 抽象 getter：子类必须实现
  abstract get apiBase(): string;

  describe(): string {
    return `API 地址：${this.apiBase}`;
  }
}

class ProdConfig extends ConfigBase {
  get apiBase(): string {
    return 'https://api.example.com';
  }
}

console.log(new ProdConfig().describe());


console.log('\n--- abstract-class.ts 执行完毕 ---');

export {};
