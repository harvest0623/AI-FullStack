/**
 * Day06 - getter 与 setter 存取器
 *
 * 本文件演示：
 * 1. get / set 存取器的基本用法
 * 2. setter 中做校验
 * 3. 只读 getter（派生属性）
 * 4. 与 private 后备字段配合实现受控读写
 * 5. 存取器定义在原型上，不占实例字段位
 */

// ============================================================
// 1. 基础存取器：getter / setter
// ============================================================

class Temperature {
  // 私有后备字段，约定用 _ 前缀避免与存取器同名冲突
  private _celsius: number = 0;

  get celsius(): number {
    return this._celsius;
  }

  set celsius(value: number) {
    if (value < -273.15) {
      throw new Error(`温度不能低于绝对零度：${value}`);
    }
    this._celsius = value;
  }

  // 只读 getter：派生属性，外部只读
  get fahrenheit(): number {
    return this._celsius * 9 / 5 + 32;
  }

  // 另一个只读派生属性
  get kelvin(): number {
    return this._celsius + 273.15;
  }
}

const t = new Temperature();
t.celsius = 25;
console.log(`25℃ = ${t.fahrenheit}°F = ${t.kelvin}K`);
// 25℃ = 77°F = 298.15K

// ❌ 只读 getter：没有 setter，无法赋值
// t.fahrenheit = 100;

// ❌ setter 校验：低于绝对零度抛错
try {
  t.celsius = -300;
} catch (e) {
  console.log('校验拦截:', (e as Error).message);
}


// ============================================================
// 2. 懒计算 + 缓存：getter 的高级用法
// ============================================================

class ExpensiveComputation {
  private _cached: number | null = null;
  private _dirty = true;

  constructor(private input: number) {}

  // 输入变化时标记缓存失效
  set value(v: number) {
    this.input = v;
    this._dirty = true;
  }

  get value(): number {
    if (this._dirty) {
      console.log('  [计算] 执行耗时运算...');
      // 模拟耗时计算：平方 + 开方
      this._cached = Math.sqrt(this.input) * this.input;
      this._dirty = false;
    } else {
      console.log('  [缓存] 命中缓存');
    }
    return this._cached!;
  }
}

const calc = new ExpensiveComputation(16);
console.log('第一次访问:', calc.value);   // 触发计算
console.log('第二次访问:', calc.value);   // 命中缓存
calc.value = 25;                          // 标记失效
console.log('失效后访问:', calc.value);   // 重新计算


// ============================================================
// 3. 存取器配合 private 字段：受控读写
// ============================================================

class UserAccount {
  // 真实数据存在私有字段里
  private _email: string;
  private _loginCount: number = 0;

  constructor(email: string) {
    this._email = email;
  }

  // setter 做格式化 + 校验
  get email(): string {
    return this._email;
  }

  set email(value: string) {
    const trimmed = value.trim().toLowerCase();
    if (!trimmed.includes('@')) {
      throw new Error(`非法邮箱：${value}`);
    }
    this._email = trimmed;
  }

  // loginCount 只读：外部不能直接改，只能通过方法累加
  get loginCount(): number {
    return this._loginCount;
  }

  signIn(): void {
    this._loginCount++;
    console.log(`${this._email} 登录（第 ${this._loginCount} 次）`);
  }
}

const acc = new UserAccount('Alice@Example.com');
console.log('初始邮箱:', acc.email);       // alice@example.com（构造函数未走 setter，这里手动小写演示）
acc.email = '  BOB@Test.COM  ';
console.log('改后邮箱:', acc.email);        // bob@test.com

try {
  acc.email = 'not-an-email';
} catch (e) {
  console.log('邮箱校验:', (e as Error).message);
}

// ✅ 只读 getter：loginCount 只能通过 signIn 累加
acc.signIn();
acc.signIn();
console.log('登录次数:', acc.loginCount);
// acc.loginCount = 100;   // ❌ 没有 setter，只读


// ============================================================
// 4. 只读 getter 替代公开方法：API 设计更自然
// ============================================================

class Rectangle {
  constructor(public width: number, public height: number) {}

  // 用 getter 表达“派生属性”，比 getWidth() 更自然
  get area(): number {
    return this.width * this.height;
  }

  get perimeter(): number {
    return 2 * (this.width + this.height);
  }

  get isSquare(): boolean {
    return this.width === this.height;
  }
}

const r = new Rectangle(4, 5);
console.log(`矩形 ${r.width}x${r.height}：面积=${r.area}，周长=${r.perimeter}，正方形=${r.isSquare}`);

const sq = new Rectangle(3, 3);
console.log(`矩形 ${sq.width}x${sq.height}：正方形=${sq.isSquare}`);


// ============================================================
// 5. 存取器定义在原型上：不占实例字段位
// ============================================================

class Demo {
  get now(): number {
    return Date.now();
  }
}

const d1 = new Demo();
const d2 = new Demo();

// getter 定义在 Demo.prototype 上，每个实例共享同一个描述符
// 但每次访问都执行函数，所以返回值会变
console.log('d1.now:', d1.now);
console.log('d2.now:', d2.now);

// 验证：实例自身属性不含 now（它在原型上）
console.log('now 是否在实例上:', 'now' in d1 && d1.hasOwnProperty('now'));   // false
console.log('now 是否在原型上:', Object.getOwnPropertyDescriptor(Demo.prototype, 'now') !== undefined);  // true


console.log('\n--- getters-setters.ts 执行完毕 ---');

export {};
