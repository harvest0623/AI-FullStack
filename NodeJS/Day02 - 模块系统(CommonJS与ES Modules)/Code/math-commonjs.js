/**
 * 模块系统：CommonJS（.js 默认即为 CJS，未声明 package.json "type": "module"）
 *
 * 演示点：
 * 1. 通过 module.exports 整体导出一个对象
 * 2. 顺便演示 exports 与 module.exports 的等价挂载方式
 * 3. 模块顶层代码只在首次 require 时执行一次（缓存机制）
 */

// 模块加载时执行一次：可用于验证缓存机制
console.log('[math-commonjs] 模块被加载并执行了一次');

// 工具函数定义
function add(a, b) {
  return a + b;
}

function subtract(a, b) {
  return a - b;
}

function multiply(a, b) {
  return a * b;
}

// 方式一：给 module.exports 挂属性（等价于 exports.add = add）
// exports.add = add;
// exports.subtract = subtract;
// exports.multiply = multiply;

// 方式二：整体替换 module.exports（推荐写法，语义更清晰）
module.exports = {
  add,
  subtract,
  multiply,
  // 顺便导出常量，便于在 app-commonjs.js 中观察缓存带来的「同引用」现象
  PI: 3.14159,
};

// ❌ 反面教材：下面这行不会生效，因为上面已经整体替换了 module.exports
// exports.foo = () => 'foo';
