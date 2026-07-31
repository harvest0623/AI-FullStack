/**
 * Day10 - declaration-merging.ts
 *
 * 演示声明合并（Declaration Merging）：
 * 同名的 interface / function / namespace 会被编译器合并成一个声明。
 *
 * ⚠️ 本文件是「模块」（含 export），声明位于模块作用域，不污染全局。
 *    Validation 命名空间通过 export 暴露，可被 namespace-demo.ts 通过 import 引用
 *    （现代跨文件共享方式）；旧式 /// <reference path 见 namespace-demo.ts 注释。
 *
 * ⚠️ 为何不用全局脚本：在 isolatedModules 下，全局脚本文件不允许定义 namespace
 *    （TS1280），因此现代项目里 namespace 都放在模块中，配合 import/export 共享。
 */

// ============================================================
// 1. 接口声明合并：同名 interface 成员取并集
// ============================================================

interface Box {
  width: number;
  height: number;
}

// 同名 interface 会合并成员，而非覆盖
interface Box {
  depth: number;
  label?: string;
}

// 合并后的 Box 拥有 width / height / depth / label
function buildBox(): Box {
  return { width: 10, height: 20, depth: 30, label: '包裹' };
}


// ============================================================
// 2. 函数声明合并：形成重载集合
// ============================================================

function format(input: number): string;
function format(input: string): string;
function format(input: number | string): string {
  return typeof input === 'number'
    ? `数字：${input.toFixed(2)}`
    : `字符串：${input}`;
}


// ============================================================
// 3. 命名空间声明合并 + 内部 interface 合并
// ============================================================

// 第一片声明：基础校验。export 使其可被其他模块 import。
export namespace Validation {
  export interface Rule {
    name: string;
    test: (value: string) => boolean;
  }

  export const EMAIL_REGEX = /^[^@]+@[^@]+\.[^@]+$/;

  export function isEmail(value: string): boolean {
    return EMAIL_REGEX.test(value);
  }
}

// 同名 namespace 的第二片声明会合并成员（同名 interface Rule 也合并）
export namespace Validation {
  // Rule 接口在此处再次声明，会与上面的 Rule 合并成员
  export interface Rule {
    message: string;
  }

  export const PHONE_REGEX = /^1[3-9]\d{9}$/;

  export function isPhone(value: string): boolean {
    return PHONE_REGEX.test(value);
  }
}


// ============================================================
// 4. 运行时演示（仅在被直接 ts-node 执行时运行，被 import 时不运行）
// ============================================================

function runDemo(): void {
  // 接口合并
  console.log('Box 合并后 =>', buildBox());

  // 函数重载
  console.log(format(3.14159));   // 数字：3.14
  console.log(format('hello'));   // 字符串：hello
  // format(true);  // ❌ 没有匹配的重载

  // namespace 合并：Rule 类型同时含 name / test / message；
  // 命名空间值同时含 isEmail / isPhone / EMAIL_REGEX / PHONE_REGEX
  const emailRule: Validation.Rule = {
    name: 'email',
    message: '邮箱格式不正确',
    test: Validation.isEmail,
  };

  const phoneRule: Validation.Rule = {
    name: 'phone',
    message: '手机号格式不正确',
    test: Validation.isPhone,
  };

  console.log('emailRule 校验 =>', emailRule.test('a@b.com'), emailRule.test('bad'));
  console.log('phoneRule 校验 =>', phoneRule.test('13800138000'), phoneRule.test('12345'));
}

if (require.main === module) {
  runDemo();
  console.log('\n--- declaration-merging.ts 执行完毕 ---');
}
