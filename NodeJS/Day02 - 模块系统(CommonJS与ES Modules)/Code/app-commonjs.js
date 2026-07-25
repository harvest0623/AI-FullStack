/**
 * 模块系统：CommonJS
 *
 * 演示点：
 * 1. 使用 require 引入同目录的 math-commonjs.js
 * 2. 演示 __dirname / __filename 这两个模块包装函数注入的变量
 * 3. 演示 module 对象的常用属性（id / filename / loaded / children）
 * 4. 演示缓存机制：重复 require 同一模块只会执行一次模块代码
 */

const math = require('./math-commonjs'); // 扩展名可省略，Node 会自动补 .js

console.log('=== 1. 调用 math 模块导出的方法 ===');
console.log('1 + 2 =', math.add(1, 2));
console.log('5 - 3 =', math.subtract(5, 3));
console.log('4 * 6 =', math.multiply(4, 6));
console.log('PI =', math.PI);

console.log('\n=== 2. 模块包装函数注入的变量 ===');
console.log('__dirname  =', __dirname); // 当前模块所在目录的绝对路径
console.log('__filename =', __filename); // 当前模块文件的绝对路径

console.log('\n=== 3. module 对象常用属性 ===');
console.log('module.id       =', module.id); // 入口模块通常是 '.'
console.log('module.filename =', module.filename);
console.log('module.loaded   =', module.loaded); // 当前模块是否加载完毕（此处仍在执行，所以是 false）
console.log('module.children =', module.children.map((m) => m.filename));

console.log('\n=== 4. 缓存机制验证：再次 require 不会重新执行 ===');
const mathAgain = require('./math-commonjs');
console.log('math === mathAgain ?', math === mathAgain); // true，说明返回的是同一个缓存对象

// 缓存以「绝对路径」为 key，可通过 require.cache 查看
const resolvedPath = require.resolve('./math-commonjs');
console.log('require.resolve("./math-commonjs") =', resolvedPath);
console.log('该模块是否在 require.cache 中 ?', Object.keys(require.cache).includes(resolvedPath));
