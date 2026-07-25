/**
 * Day01 练习一：hello.js
 * 第一个 Node.js 程序
 *
 * 学习要点：
 *   1. 使用 console.log 向标准输出打印信息
 *   2. 通过 process.version 读取当前 Node.js 版本
 *   3. 体会「.js 文件可直接被 node 运行」这一与浏览器的本质差异
 *
 * 运行方式：node hello.js
 */

// 1. 定义欢迎信息（可替换为你自己的名字）
const name = 'AI 全栈学习者';

// 2. 通过 process 全局对象获取 Node.js 版本号
const nodeVersion = process.version;

// 3. 用一段分隔线让输出更美观
const line = '====================================';

// 4. 依次输出三行内容：欢迎信息 / 版本号 / 学习期待
console.log(line);
console.log(`欢迎来到 Node.js Day01，我是 ${name}！`);
console.log(`当前 Node.js 版本：${nodeVersion}`);
console.log('期待用 Node.js 搭建第一个 AI 后端服务 🚀');
console.log(line);
