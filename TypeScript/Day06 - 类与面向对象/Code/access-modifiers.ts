/**
 * Day06 - 访问修饰符：public / private / protected / # 私有字段
 *
 * 本文件演示：
 * 1. public（默认）/ protected / private 的可见性范围
 * 2. private 关键字是“编译期私有”，运行时仍可访问
 * 3. # 私有字段是“运行时私有”，外部 JS 也读不到
 * 4. # 私有字段的 brand check（#field in this）
 */

// ============================================================
// 1. public / protected / private 可见性对比
// ============================================================

class Account {
  public owner: string;        // 显式 public，等价于省略
  protected balance: number;   // 子类可见，外部不可见
  private pin: string;         // 仅本类可见

  constructor(owner: string, balance: number, pin: string) {
    this.owner = owner;
    this.balance = balance;
    this.pin = pin;
  }

  // 类内部可以访问所有成员（包括 private）
  describe(): string {
    return `${this.owner} 余额 ${this.balance}，PIN ${this.pin}`;
  }
}

class SavingsAccount extends Account {
  withdraw(amount: number): void {
    // ✅ protected 成员：子类可访问
    if (amount <= this.balance) {
      this.balance -= amount;
      console.log(`取款成功，剩余 ${this.balance}`);
    } else {
      console.log('余额不足');
    }
    // ❌ this.pin        // private：子类也不可访问
  }

  showOwner(): string {
    // ✅ public 成员：到处可访问
    return this.owner;
  }
}

const acc = new Account('Alice', 1000, '1234');

// ✅ public：外部可访问
console.log('owner:', acc.owner);

// ❌ protected / private：外部不可访问
// console.log(acc.balance);   // 编译报错
// console.log(acc.pin);       // 编译报错

console.log(acc.describe());   // ✅ 通过公开方法间接访问

const sa = new SavingsAccount('Bob', 500, '5678');
sa.withdraw(200);
console.log('savings owner:', sa.showOwner());


// ============================================================
// 2. private 关键字是“编译期私有”——运行时仍可访问
// ============================================================

class SecretBox {
  private secret = 'top-secret';

  reveal(): string {
    return this.secret;
  }
}

const box = new SecretBox();

// ❌ 编译期：TS 会拦截
// console.log(box.secret);

// ⚠️ 但编译成 JS 后，secret 就是普通属性，运行时可访问
// 这演示了 private 只是“开发契约”，不是运行时隔离
console.log('runtime peek (private):', (box as any).secret);   // top-secret
console.log('JSON.stringify 包含 private:', JSON.stringify(box));  // {"secret":"top-secret"}


// ============================================================
// 3. # 私有字段：真正的运行时私有
// ============================================================

class SecureToken {
  #secret: string;              // 真正的运行时私有字段

  constructor(secret: string) {
    this.#secret = secret;
  }

  reveal(): string {
    return this.#secret;        // 类内部正常访问
  }

  // 用 #field in 做品牌检查（brand check）
  static isSecureToken(x: unknown): boolean {
    return typeof x === 'object' && x !== null && #secret in x;
  }
}

const token = new SecureToken('abc-123');

// ✅ 通过暴露的方法访问
console.log('token reveal:', token.reveal());

// ❌ 编译期：#secret 无法在类外访问
// console.log(token.#secret);

// ❌ 运行时：用方括号语法也读不到（这是 # 私有字段的关键特性）
console.log('runtime peek (#):', (token as any)['#secret']);   // undefined
console.log('JSON.stringify 不含 #:', JSON.stringify(token));   // {}

// ✅ 静态方法用 brand check 验证
console.log('isSecureToken(token):', SecureToken.isSecureToken(token));    // true
console.log('isSecureToken({}):', SecureToken.isSecureToken({}));          // false


// ============================================================
// 4. # 私有字段子类可定义同名字段（独立作用域）
// ============================================================

class Base {
  #value = 'base';

  baseValue(): string {
    return this.#value;
  }
}

class Derived extends Base {
  #value = 'derived';   // ✅ 与父类的 #value 互不冲突，独立作用域

  derivedValue(): string {
    return this.#value;
  }
}

const d = new Derived();
console.log('base value:', d.baseValue());       // base
console.log('derived value:', d.derivedValue()); // derived
// 同一个实例上，父类和子类各自维护一份 #value，互不干扰


// ============================================================
// 5. protected 的常见用法：模板方法模式的钩子
// ============================================================

abstract class Processor {
  // 模板方法：定义流程骨架，调用 protected 钩子让子类填空
  run(): void {
    this.before();
    this.doWork();
    this.after();
  }

  protected before(): void {
    console.log('  [默认 before] 准备资源');
  }

  // 抽象方法：强制子类实现
  protected abstract doWork(): void;

  protected after(): void {
    console.log('  [默认 after] 清理资源');
  }
}

class CsvProcessor extends Processor {
  protected doWork(): void {
    console.log('  [CsvProcessor] 解析 CSV');
  }

  // 覆盖钩子，复用其余流程
  protected override before(): void {
    console.log('  [CsvProcessor] 打开 CSV 文件');
  }
}

console.log('\n运行 CsvProcessor:');
new CsvProcessor().run();


console.log('\n--- access-modifiers.ts 执行完毕 ---');

export {};
