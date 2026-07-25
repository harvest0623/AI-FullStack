/**
 * 模块系统：CommonJS（.js 默认即为 CJS）
 *
 * 演示点：
 * 1. 在 CommonJS 中使用动态 import() 加载 ESM 模块（.mjs）
 * 2. 观察 import() 返回的命名空间对象：命名导出与 default 的形态
 * 3. 对比 require() 与 import() 的差异：require 同步、不能加载 ESM；import() 异步、可跨系统
 *
 * 关键结论：CJS 不能同步 require(ESM)，但可以用 await import() 异步加载。
 */

async function main() {
  console.log('=== 1. 使用 await import() 加载 ESM 模块 ===');
  // import() 返回 Promise<Module Namespace Object>
  const circleModule = await import('./circle-area.mjs');

  console.log('circleModule 的所有 key =', Object.keys(circleModule));
  // 预期：[ 'default', 'area', 'circumference', 'PI' ]

  console.log('\n=== 2. 调用 ESM 的命名导出 ===');
  console.log('circleModule.area(2)          =', circleModule.area(2));
  console.log('circleModule.circumference(2) =', circleModule.circumference(2));
  console.log('circleModule.PI               =', circleModule.PI);

  console.log('\n=== 3. 观察 default ===');
  console.log('circleModule.default =', circleModule.default);
  // default 就是 circle-area.mjs 里 export default 的对象

  console.log('\n=== 4. 动态按变量加载（import() 支持变量路径） ===');
  const moduleName = './circle-area.mjs';
  const dynamicLoaded = await import(moduleName);
  console.log('动态加载后调用 area(5) =', dynamicLoaded.area(5));

  console.log('\n=== 5. 对比：require() 无法加载 ESM ===');
  console.log('如果取消下面这行的注释，会报 ERR_REQUIRE_ESM：');
  console.log('// const broken = require("./circle-area.mjs"); // ❌ 不支持');
}

main().catch((err) => {
  console.error('运行出错：', err);
  process.exit(1);
});
