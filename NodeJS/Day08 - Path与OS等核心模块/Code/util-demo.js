// Day08 - util 模块演示
// 主题：util.promisify 把 fs.readFile 转 Promise、util.inspect 深度打印、util.types 类型判断、format / deprecate
// 运行：node Code/util-demo.js
//
// 说明：现代项目可直接用 require('fs/promises')，这里演示 util.promisify 是为了理解其原理；
// inspect 是调试大对象的标准姿势，types 是跨 realm 严格判断的依据。

const util = require('util');
const fs = require('fs');
const path = require('path');
const os = require('os');

console.log('========================================');
console.log(' Day08 - util 模块演示');
console.log('========================================\n');

// ---------------------------------------------------------------
// 1. util.promisify：把错误优先回调风格的函数转成 Promise 版
// ---------------------------------------------------------------
console.log('--- 1. util.promisify：fs.readFile → Promise ---');

const readFile = util.promisify(fs.readFile);
const stat = util.promisify(fs.stat);

// 准备一个临时文件用于演示
const tmpFile = path.join(os.tmpdir(), `day08-demo-${Date.now()}.txt`);
fs.writeFileSync(tmpFile, 'Hello from util.promisify!\nLine 2 here.');

// 顶层用 async IIFE 包裹（CommonJS 不支持顶层 await）
(async () => {
  try {
    // 现在 readFile 返回 Promise，可以 await
    const content = await readFile(tmpFile, 'utf8');
    console.log('  读取内容：');
    console.log(content.split('\n').map(l => `    | ${l}`).join('\n'));

    const info = await stat(tmpFile);
    console.log(`  文件大小：${info.size} 字节`);
    console.log(`  修改时间：${info.mtime.toISOString()}`);
  } catch (err) {
    console.error('  发生错误：', err.message);
  } finally {
    fs.unlinkSync(tmpFile);   // 清理临时文件
  }

  // ---------------------------------------------------------------
  // 2. util.inspect：自定义深度打印对象
  // ---------------------------------------------------------------
  console.log('\n--- 2. util.inspect：深度打印嵌套对象 ---');

  const deep = {
    name: 'worker',
    config: {
      model: { type: 'gpt-4', params: { temperature: 0.7, top_p: 0.9 } },
      hooks: ['pre', 'post', 'error'],
    },
    nested: { a: { b: { c: { d: { e: '深不见底' } } } } },
  };

  console.log('  默认 console.log（只能看到 2 层）：');
  console.log('   ', deep);

  console.log('\n  util.inspect 深度全开：');
  console.log('  ' + util.inspect(deep, {
    depth: null,           // 不限层级
    colors: true,          // 带颜色（终端有效）
    compact: false,        // 每个属性换行
    maxArrayLength: null,  // 数组不限长度
    breakLength: 80,       // 超过 80 字符换行
  }));

  // console.dir 是 inspect 的便捷封装
  console.log('\n  console.dir 深度版本：');
  console.dir(deep, { depth: 3, colors: true });

  // ---------------------------------------------------------------
  // 3. util.format：格式化字符串
  // ---------------------------------------------------------------
  console.log('\n--- 3. util.format：printf 风格 ---');
  console.log('  ' + util.format('Name: %s, Age: %d', 'Tom', 18));
  console.log('  ' + util.format('JSON: %j', { a: 1, b: [2, 3] }));
  console.log('  ' + util.format('Object: %o', { x: 1, y: { z: 2 } }));
  console.log('  ' + util.format('Percent: 100%%'));
  // 参数多于占位符时追加空格连接
  console.log('  ' + util.format('%s is great', 'Node', 'and', 'fast'));

  // ---------------------------------------------------------------
  // 4. util.types：跨 realm 严格类型判断
  // ---------------------------------------------------------------
  console.log('\n--- 4. util.types：精确类型判断 ---');
  console.log(`  isPromise(Promise.resolve())     = ${util.types.isPromise(Promise.resolve())}`);
  console.log(`  isPromise({then:()=>{}})          = ${util.types.isPromise({ then: () => {} })}    ← thenable 不算`);
  console.log(`  isMap(new Map())                  = ${util.types.isMap(new Map())}`);
  console.log(`  isSet(new Set())                  = ${util.types.isSet(new Set())}`);
  console.log(`  isArrayBuffer(new ArrayBuffer(8)) = ${util.types.isArrayBuffer(new ArrayBuffer(8))}`);
  console.log(`  isAsyncFunction(async()=>{})      = ${util.types.isAsyncFunction(async () => {})}`);
  console.log(`  isProxy(new Proxy({},{}))         = ${util.types.isProxy(new Proxy({}, {}))}`);

  // 对比 instanceof 在跨 realm 时的盲区
  const vm = require('vm');
  const otherRealmPromise = vm.runInNewContext('Promise.resolve(42)');
  console.log(`\n  跨 realm 对比：`);
  console.log(`    otherRealmPromise instanceof Promise = ${otherRealmPromise instanceof Promise}    ← vm 沙箱中的 Promise 实例`);
  console.log(`    util.types.isPromise(otherRealmPromise) = ${util.types.isPromise(otherRealmPromise)}    ← 但它是原生 Promise`);

  // ---------------------------------------------------------------
  // 5. util.deprecate 与 callbackify
  // ---------------------------------------------------------------
  console.log('\n--- 5. util.deprecate：标记废弃 ---');

  // 用 process.on 抓 DeprecationWarning，避免污染输出
  process.on('warning', () => {});   // 静默
  const oldFn = util.deprecate(
    (x) => `result:${x}`,
    'oldFn 已废弃，请改用 newFn'
  );
  // 把 deprecate 触发的 warning 重定向，避免破坏演示输出
  const origEmit = process.emitWarning;
  process.emitWarning = (msg, opts) => {
    if (typeof msg === 'string' && msg.includes('已废弃')) {
      console.log(`  [DeprecationWarning 被捕获] ${msg}`);
    }
  };
  console.log(`  oldFn(42) 返回：${oldFn(42)}`);
  process.emitWarning = origEmit;    // 恢复

  // util.callbackify：async 函数 → 回调风格（promisify 的逆操作）
  console.log('\n  util.callbackify：把 async 函数转回回调风格 ---');
  const asyncFn = async (x) => x * 2;
  const cbFn = util.callbackify(asyncFn);
  // callback 是异步触发的，用 Promise 包一层以便 await，保证输出顺序
  await new Promise((resolve) => {
    cbFn(21, (err, result) => {
      if (err) console.error('  callback 出错：', err);
      else console.log(`  callbackify(asyncFn)(21, cb) → ${result}`);
      resolve();
    });
  });

  // ---------------------------------------------------------------
  console.log('\n=== 要点回顾 ===');
  console.log('  1. util.promisify 把错误优先回调转 Promise，但现代项目优先用 fs/promises；');
  console.log('  2. util.inspect({depth:null,colors:true}) 是调试大对象的标准姿势；');
  console.log('  3. console.dir 是 inspect 的便捷封装；');
  console.log('  4. util.types 跨 realm 严格判断，比 instanceof 更可靠；');
  console.log('  5. util.deprecate 标记废弃，callbackify 是 promisify 的逆操作。');
})();
