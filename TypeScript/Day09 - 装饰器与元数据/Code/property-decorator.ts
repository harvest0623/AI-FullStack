/**
 * Day09 - 属性装饰器（PropertyDecorator）
 *
 * 签名：(target, propertyKey) => void
 * - target：静态属性时为构造函数；实例属性时为原型对象
 * - propertyKey：属性名（string | symbol）
 * - 没有 descriptor！TS 不会为实例字段生成属性描述符
 * - 返回值被忽略
 *
 * 属性装饰器本身能做的事很少（拿不到值，也拿不到描述符），
 * 它的核心用法是"贴标签 + 配合 reflect-metadata 读取 design:type"。
 */

import 'reflect-metadata';

// ---------- 1. 记录属性类型（design:type） ----------
// 需要 tsconfig 开启 emitDecoratorMetadata，TS 才会自动注入 design:type
function TypeLog(target: any, propertyKey: string) {
  const t = Reflect.getMetadata('design:type', target, propertyKey);
  console.log(`[TypeLog] ${propertyKey} 的类型是 ${t?.name}`);
}

class UserDTO {
  @TypeLog
  id: number = 0;

  @TypeLog
  name: string = '';

  @TypeLog
  isAdmin: boolean = false;

  @TypeLog
  birthday: Date = new Date();
}

// ---------- 2. 用元数据"贴标签"，标记需要校验的属性 ----------
const VALIDATE_KEY = 'property:validate';

function Required(target: any, propertyKey: string) {
  // 在类的原型上为这个属性记录"必填"标记
  const list: string[] = Reflect.getOwnMetadata(VALIDATE_KEY, target) ?? [];
  list.push(propertyKey);
  Reflect.defineMetadata(VALIDATE_KEY, list, target);
}

function validate(instance: object): string[] {
  const errors: string[] = [];
  // 沿原型链查找所有贴了 Required 的属性
  const proto = Object.getPrototypeOf(instance);
  const fields: string[] = Reflect.getMetadata(VALIDATE_KEY, proto) ?? [];
  for (const f of fields) {
    if (instance[f as keyof object] === undefined || instance[f as keyof object] === null || instance[f as keyof object] === '') {
      errors.push(`${f} 不能为空`);
    }
  }
  return errors;
}

class LoginForm {
  @Required
  username: string;

  @Required
  password: string;

  remember?: boolean;

  constructor(username: string, password: string, remember?: boolean) {
    this.username = username;
    this.password = password;
    this.remember = remember;
  }
}

const ok = new LoginForm('alice', 'pwd123');
const bad = new LoginForm('', '');
console.log('校验 ok：', validate(ok));   // []
console.log('校验 bad：', validate(bad)); // ['username 不能为空', 'password 不能为空']

// ---------- 3. 用 getter/setter 实现"伪字段"装饰 ----------
// 属性装饰器拿不到 descriptor，但可以通过 Object.defineProperty 反向植入
function Trim(target: any, propertyKey: string) {
  const internalKey = `__${String(propertyKey)}`;

  Object.defineProperty(target, propertyKey, {
    get() {
      return this[internalKey];
    },
    set(value: string) {
      this[internalKey] = typeof value === 'string' ? value.trim() : value;
    },
    enumerable: true,
    configurable: true,
  });
}

class Profile {
  @Trim
  nickname: string = '';

  constructor(nickname: string) {
    this.nickname = nickname; // 走 setter，自动 trim
  }
}

const prof = new Profile('   alice   ');
console.log(`"${prof.nickname}"`); // "alice"

console.log('\n[property-decorator.ts] 运行结束');
