/**
 * use-npx-demo.js
 * ------------------------------------------------------------------
 * Day03 示例：演示 npx 的常见用法。
 * 本文件本身只是"注释脚本 + require 自检"，并不真的去下载 cowsay。
 * 真正运行 npx 命令请在本文件所在目录的终端里手动敲：
 *
 *   npx cowsay "Hello, AI FullStack!"
 *   npx create-react-app demo-react-app
 *   npx tsc --version
 *   npx tsx use-npx-demo.ts
 *
 * npm start 会执行本文件，先做 require 自检，再打印一段说明。
 * ------------------------------------------------------------------
 */

'use strict';

// 演示：从 package.json 的 main 字段（math-util.js）导入工具
const math = require('./math-util.js');

// npx 常用命令汇总（仅打印说明，不真正执行）
const npxCommands = [
  {
    cmd: 'npx cowsay "Hello"',
    purpose: '运行一次性的小工具（cowsay 装完即用，不污染全局）'
  },
  {
    cmd: 'npx create-react-app my-app',
    purpose: '脚手架命令（npm init react-app 的等价写法）'
  },
  {
    cmd: 'npx prettier --write .',
    purpose: '运行项目内已装的工具（优先复用 node_modules/.bin/prettier）'
  },
  {
    cmd: 'npx eslint --init',
    purpose: '交互式生成 eslint 配置文件'
  },
  {
    cmd: 'npx tsx script.ts',
    purpose: '直接运行 TypeScript，无需 tsc 预编译'
  },
  {
    cmd: 'npx -p pkg-a -p pkg-b some-cmd',
    purpose: '临时同时安装多个包再运行命令'
  },
  {
    cmd: 'npx --no-install cowsay',
    purpose: '强制只使用本地已装包，找不到就报错（CI 友好）'
  }
];

console.log('========================================');
console.log('  Day03 - npx 用法演示');
console.log('========================================\n');

console.log('【1】先做一次 require 自检：');
console.log('  math.add(2, 3)         =', math.add(2, 3));
console.log('  math.factorial(5)      =', math.factorial(5));
console.log('  math.primesInRange(1, 20) =', math.primesInRange(1, 20));
console.log('');

console.log('【2】常用 npx 命令清单（请自行在终端执行）：\n');
npxCommands.forEach((item, i) => {
  console.log(`  ${i + 1}) ${item.cmd}`);
  console.log(`     → ${item.purpose}\n`);
});

console.log('【3】npx 执行原理一句话总结：');
console.log('  本地 node_modules/.bin 有 → 直接用；');
console.log('  没有 → 临时下载到 ~/.npm/_npx/ 缓存，执行完不污染全局。');
console.log('');
