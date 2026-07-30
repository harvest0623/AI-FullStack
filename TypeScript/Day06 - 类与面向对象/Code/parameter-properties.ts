/**
 * Day06 - 参数属性（Parameter Properties）
 *
 * 本文件演示：
 * 1. 参数属性简写：构造函数参数前加修饰符自动声明并赋值
 * 2. 修饰符可组合：public/private/protected/readonly
 * 3. 参数属性与手动赋值在运行时完全等价
 * 4. 何时用参数属性、何时拆开写
 */

// ============================================================
// 1. 参数属性简写：一步声明 + 赋值
// ============================================================

class User {
  constructor(
    public id: number,                // 自动声明 public id 并赋值
    public name: string,              // 自动声明 public name 并赋值
    private password: string,         // 自动声明 private password 并赋值
    readonly createdAt: Date = new Date(),  // 默认值 + readonly 也可
  ) {}

  verify(input: string): boolean {
    return this.password === input;   // ✅ 类内部可访问 private
  }

  describe(): string {
    return `User #${this.id}：${this.name}，注册于 ${this.createdAt.toISOString().slice(0, 10)}`;
  }
}

const u = new User(1, 'Alice', 'pwd123');
console.log(u.describe());
console.log('verify right:', u.verify('pwd123'));    // true
console.log('verify wrong:', u.verify('xxx'));        // false

// ✅ public 成员外部可访问
console.log('id:', u.id, 'name:', u.name);
// ❌ private 成员外部不可访问
// console.log(u.password);
// ❌ readonly 成员不可重新赋值
// u.createdAt = new Date();


// ============================================================
// 2. 等价性对比：参数属性 vs 手动声明 + 赋值
// ============================================================

// 写法 A：参数属性
class WithParamProps {
  constructor(
    public x: number,
    private y: number,
    protected z: number,
    readonly w: number,
  ) {}
}

// 写法 B：手动声明字段 + 构造函数赋值
class WithManualFields {
  public x: number;
  private y: number;
  protected z: number;
  readonly w: number;

  constructor(x: number, y: number, z: number, w: number) {
    this.x = x;
    this.y = y;
    this.z = z;
    this.w = w;
  }
}

// 两者行为完全一致：字段可见性、运行时结构都相同
const a = new WithParamProps(1, 2, 3, 4);
const b = new WithManualFields(1, 2, 3, 4);
console.log('param props fields:', Object.keys(a));
console.log('manual fields:', Object.keys(b));
console.log('两者结构一致:', JSON.stringify(a) === JSON.stringify(b));


// ============================================================
// 3. 修饰符组合：readonly + private 等
// ============================================================

class Config {
  // readonly + private：只能在构造函数中赋值，且仅本类可见
  constructor(
    private readonly apiKey: string,
    public readonly env: string,
  ) {}

  getHeaders(): Record<string, string> {
    return { 'X-API-Key': this.apiKey, 'X-Env': this.env };
  }
}

const cfg = new Config('sk-123', 'prod');
console.log('env:', cfg.env);
// ❌ cfg.env = 'dev';        // readonly
// ❌ cfg.apiKey;             // private
console.log('headers:', cfg.getHeaders());


// ============================================================
// 4. 何时用参数属性、何时拆开写
// ============================================================

// ✅ 适合参数属性：纯赋值，无额外逻辑
class Point {
  constructor(public x: number, public y: number) {}
}
const p = new Point(3, 4);
console.log(`Point(${p.x}, ${p.y})`);

// ⚠️ 适合拆开写：构造函数内有校验/转换/副作用
class Email {
  public value: string;

  constructor(raw: string) {
    // 构造函数里有校验逻辑，参数属性无法表达，应当拆开写
    if (!raw.includes('@')) {
      throw new Error(`非法邮箱：${raw}`);
    }
    this.value = raw.trim().toLowerCase();
  }
}

const email = new Email('  Alice@Example.COM  ');
console.log('email value:', email.value);   // alice@example.com
// new Email('not-an-email');   // 抛错：非法邮箱


// ============================================================
// 5. 参数属性 + 默认值：可选配置
// ============================================================

class HttpClient {
  constructor(
    public baseURL: string,
    public timeout: number = 5000,           // 默认值
    public retries: number = 3,              // 默认值
    readonly userAgent: string = 'ts-client/1.0',
  ) {}

  info(): string {
    return `${this.userAgent} -> ${this.baseURL} (timeout=${this.timeout}, retries=${this.retries})`;
  }
}

console.log(new HttpClient('https://api.example.com').info());
console.log(new HttpClient('https://api.example.com', 10000).info());
console.log(new HttpClient('https://api.example.com', 10000, 5, 'my-agent').info());


console.log('\n--- parameter-properties.ts 执行完毕 ---');

export {};
