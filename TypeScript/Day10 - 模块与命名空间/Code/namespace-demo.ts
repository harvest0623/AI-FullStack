/**
 * Day10 - namespace-demo.ts
 *
 * 演示命名空间（namespace）的定义、嵌套与跨文件引用。
 *
 * ⚠️ namespace 是 TS 早期的全局代码组织方式，现代项目优先使用 ES Modules。
 *    仅在 .d.ts 全局声明、旧库迁移等场景仍有价值。
 *
 * ⚠️ 本文件是「模块」（含 import），namespace 位于模块作用域。
 *    在 isolatedModules 下，全局脚本文件不允许定义 namespace（TS1280），
 *    因此现代项目把 namespace 放在模块里，用 import/export 跨文件共享。
 */

// ============================================================
// 0. 跨文件命名空间引用：现代方式 vs 旧式三斜线指令
// ============================================================

// ✅ 现代方式：用 import 引入其他模块 export 的 namespace
//    Validation 既是值（含 isEmail / isPhone 等运行时成员），
//    又携带类型成员（Validation.Rule），可直接在类型位置使用。
import { Validation } from './declaration-merging';

// ❌ 旧式三斜线指令（已废弃，仅作语法展示）：
// /// <reference path="./declaration-merging.ts" />
//
// 三斜线指令是 TS 早期的依赖声明方式，把目标文件的全局声明引入编译上下文。
// 在 isolatedModules + 模块化项目里它已不适用：
//   1. 全局脚本文件不允许定义 namespace（TS1280）；
//   2. CommonJS 每文件独立作用域，跨文件全局 namespace 运行时不可达。
// 因此现代代码统一用上面的 import 替代三斜线指令。


// ============================================================
// 1. 命名空间基本定义
// ============================================================

namespace App {
  /** 应用版本 */
  export const VERSION = '1.0.0';

  /** 应用配置 */
  export interface Config {
    name: string;
    port: number;
  }

  /** 启动应用 */
  export function bootstrap(cfg: Config): string {
    return `[App:${VERSION}] 启动 ${cfg.name} @ ${cfg.port}`;
  }
}


// ============================================================
// 2. 命名空间嵌套
// ============================================================

namespace App {
  // 同名 namespace 会声明合并，这里新增子命名空间
  // ⚠️ 避免命名为 App.Math，会遮蔽全局 Math 对象
  export namespace Calc {
    export function add(a: number, b: number): number {
      return a + b;
    }

    export function factorial(n: number): number {
      return n <= 1 ? 1 : n * factorial(n - 1);
    }

    // 更深层嵌套
    export namespace Geometry {
      export interface Circle {
        radius: number;
      }

      export function area(c: Circle): number {
        return Math.PI * c.radius ** 2;   // 此处 Math 是全局对象，未被遮蔽
      }
    }
  }

  export namespace UI {
    export function render(name: string): string {
      return `<div>${name}</div>`;
    }
  }
}


// ============================================================
// 3. 跨文件命名空间引用（通过 import 拿到的 Validation）
// ============================================================

// Validation.Rule 类型来自 declaration-merging.ts，import 让类型与值都可用
function applyRule(value: string, rule: Validation.Rule): boolean {
  return rule.test(value);
}

const emailRule: Validation.Rule = {
  name: 'email',
  message: '邮箱格式不正确',
  test: Validation.isEmail,   // 直接使用跨文件 namespace 的运行时方法
};

const phoneRule: Validation.Rule = {
  name: 'phone',
  message: '手机号格式不正确',
  test: Validation.isPhone,
};


// ============================================================
// 4. 运行时演示
// ============================================================

console.log(App.bootstrap({ name: 'Demo', port: 3000 }));
console.log('App.Calc.add(2, 3) =', App.Calc.add(2, 3));
console.log('App.Calc.factorial(5) =', App.Calc.factorial(5));
console.log('App.Calc.Geometry.area =', App.Calc.Geometry.area({ radius: 2 }).toFixed(2));
console.log('App.UI.render =', App.UI.render('hello'));
console.log('applyRule(email) =>', applyRule('a@b.com', emailRule), applyRule('bad', emailRule));
console.log('applyRule(phone) =>', applyRule('13800138000', phoneRule), applyRule('12345', phoneRule));

console.log('\n--- namespace-demo.ts 执行完毕 ---');

export {};
