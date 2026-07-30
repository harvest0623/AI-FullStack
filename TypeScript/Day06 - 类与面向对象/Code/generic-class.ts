/**
 * Day06 - 泛型类：Repository<T>、Stack<T>、泛型约束
 *
 * 本文件演示：
 * 1. 泛型类 class Repository<T> 的定义与实例化
 * 2. 泛型约束 T extends { id: number } 限定实体形状
 * 3. 泛型类的静态成员不能引用实例类型参数 T
 * 4. 经典数据结构 Stack<T>
 * 5. 多类型参数的泛型类 KeyValueStore<K, V>
 * 6. 泛型类与策略模式结合
 */

// ============================================================
// 1. 泛型类 Repository<T>：实例化时确定 T
// ============================================================

class Repository<T extends { id: number }> {
  // T 在所有实例成员中可用
  private items: T[] = [];

  constructor(private entityName: string = 'entity') {}

  add(item: T): void {
    this.items.push(item);
  }

  // 因为有 T extends { id: number } 约束，可以安全访问 x.id
  findById(id: number): T | undefined {
    return this.items.find((x) => x.id === id);
  }

  update(id: number, patch: Partial<Omit<T, 'id'>>): T | undefined {
    const item = this.findById(id);
    if (!item) return undefined;
    Object.assign(item, patch);
    return item;
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

  count(): number {
    return this.items.length;
  }

  describe(): string {
    return `Repository<${this.entityName}>（${this.count()} 条）`;
  }
}

// 不同实体类型，得到类型安全的 Repository
interface User { id: number; name: string; email: string; }
interface Post { id: number; title: string; views: number; }

const userRepo = new Repository<User>('user');
const postRepo = new Repository<Post>('post');

userRepo.add({ id: 1, name: 'Alice', email: 'alice@test.com' });
userRepo.add({ id: 2, name: 'Bob', email: 'bob@test.com' });

// ✅ findById 返回 User | undefined，能安全访问 name
const u = userRepo.findById(1);
if (u) {
  console.log('找到用户:', u.name, u.email);
}

// ✅ update 的 patch 类型受约束：不能改 id，其他字段可选
userRepo.update(1, { name: 'Alice Smith' });
console.log('更新后:', userRepo.findById(1)?.name);

// ❌ 类型错误演示（注释掉）：
// userRepo.add({ id: 3, title: 'xxx' });   // 不是 User 形状
// userRepo.update(1, { id: 99 });          // 不能改 id

console.log(userRepo.describe());

// 不同 T 完全隔离，postRepo 无法塞入 User
postRepo.add({ id: 101, title: 'Hello TS', views: 0 });
// postRepo.add({ id: 102, name: 'x' });   // ❌ Post 没有 name


// ============================================================
// 2. 静态成员不能引用实例类型参数 T
// ============================================================

class Container<T> {
  // ✅ 实例字段可以用 T
  private value: T;

  constructor(value: T) {
    this.value = value;
  }

  get(): T {
    return this.value;
  }

  // ❌ 静态成员不能引用实例类型参数 T
  // static wrap(v: T): Container<T> { return new Container(v); }

  // ✅ 静态方法可以有自己的泛型参数
  static create<U>(value: U): Container<U> {
    return new Container(value);
  }
}

const c = Container.create(42);    // c: Container<number>
console.log('Container value:', c.get());


// ============================================================
// 3. 经典数据结构：Stack<T>
// ============================================================

class Stack<T> {
  private data: T[] = [];

  push(item: T): void {
    this.data.push(item);
  }

  pop(): T | undefined {
    return this.data.pop();
  }

  peek(): T | undefined {
    return this.data[this.data.length - 1];
  }

  get size(): number {
    return this.data.length;
  }

  get isEmpty(): boolean {
    return this.data.length === 0;
  }

  toArray(): T[] {
    return [...this.data];
  }
}

// 数字栈
const numStack = new Stack<number>();
numStack.push(1);
numStack.push(2);
numStack.push(3);
console.log('size:', numStack.size);          // 3
console.log('peek:', numStack.peek());        // 3
console.log('pop:', numStack.pop());          // 3
console.log('pop:', numStack.pop());          // 2

// 字符串栈
const strStack = new Stack<string>();
strStack.push('a');
strStack.push('b');
console.log('str pop:', strStack.pop());      // b


// ============================================================
// 4. 多类型参数泛型类：KeyValueStore<K, V>
// ============================================================

class KeyValueStore<K extends string | number, V> {
  private store = new Map<K, V>();

  set(key: K, value: V): void {
    this.store.set(key, value);
  }

  get(key: K): V | undefined {
    return this.store.get(key);
  }

  has(key: K): boolean {
    return this.store.has(key);
  }

  delete(key: K): boolean {
    return this.store.delete(key);
  }

  keys(): K[] {
    return [...this.store.keys()];
  }

  values(): V[] {
    return [...this.store.values()];
  }

  entries(): Array<[K, V]> {
    return [...this.store.entries()];
  }
}

const userCache = new KeyValueStore<number, { name: string }>();
userCache.set(1, { name: 'Alice' });
userCache.set(2, { name: 'Bob' });
console.log('cache keys:', userCache.keys());
console.log('get 1:', userCache.get(1));

const configStore = new KeyValueStore<string, boolean>();
configStore.set('debug', true);
configStore.set('verbose', false);
console.log('config entries:', configStore.entries());


// ============================================================
// 5. 泛型约束在类上的高级应用：new() 约束做工厂
// ============================================================

// T extends new () => InstanceType<T>：T 必须是“可无参 new 的构造函数”
class Factory<T extends new () => InstanceType<T>> {
  constructor(private Ctor: T) {}

  create(): InstanceType<T> {
    return new this.Ctor();
  }
}

class Greeting {
  hello(): string { return 'hello'; }
}

const factory = new Factory(Greeting);
const g = factory.create();   // g: Greeting
console.log('factory result:', g.hello());


// ============================================================
// 6. 泛型类 + 策略模式：类型安全的排序仓库
// ============================================================

interface SortStrategy<T> {
  sort(items: T[]): T[];
}

class ByIdAscSort<T extends { id: number }> implements SortStrategy<T> {
  sort(items: T[]): T[] {
    return [...items].sort((a, b) => a.id - b.id);
  }
}

class ByIdDescSort<T extends { id: number }> implements SortStrategy<T> {
  sort(items: T[]): T[] {
    return [...items].sort((a, b) => b.id - a.id);
  }
}

// 给 Repository 扩展排序能力
class SortedRepository<T extends { id: number }> {
  private items: T[] = [];
  private sortStrategy: SortStrategy<T> = new ByIdAscSort<T>();

  add(item: T): void {
    this.items.push(item);
  }

  setSort(strategy: SortStrategy<T>): void {
    this.sortStrategy = strategy;
  }

  list(): T[] {
    return this.sortStrategy.sort(this.items);
  }
}

const repo = new SortedRepository<Post>();
repo.add({ id: 3, title: 'C', views: 30 });
repo.add({ id: 1, title: 'A', views: 10 });
repo.add({ id: 2, title: 'B', views: 20 });

console.log('默认（id 升序）:', repo.list().map((p) => p.id));   // [1, 2, 3]
repo.setSort(new ByIdDescSort());
console.log('id 降序:', repo.list().map((p) => p.id));          // [3, 2, 1]


// ============================================================
// 7. 泛型类的默认类型参数
// ============================================================

class Box<T = string> {     // T 默认为 string
  constructor(public value: T) {}

  unwrap(): T {
    return this.value;
  }
}

const strBox = new Box('hello');        // Box<string>
const numBox = new Box<number>(42);     // 显式指定为 number
console.log('strBox:', strBox.unwrap());
console.log('numBox:', numBox.unwrap());


console.log('\n--- generic-class.ts 执行完毕 ---');

export {};
