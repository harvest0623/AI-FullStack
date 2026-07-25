/**
 * Day01 练习二：system-info.js
 * 系统信息探针
 *
 * 学习要点：
 *   1. 认识 process 全局对象的常用属性（platform / arch / version / cwd / env）
 *   2. 理解「当前工作目录」与「脚本所在目录」的区别
 *   3. 对可能不存在的环境变量做容错处理，避免进程崩溃
 *
 * 运行方式：node system-info.js
 */

// 标题
console.log('【系统信息探针】');

// 1. 操作系统平台：win32 / linux / darwin(macOS)
console.log(`操作系统平台：${process.platform}`);

// 2. CPU 架构：x64 / arm64 等
console.log(`CPU 架构：    ${process.arch}`);

// 3. Node.js 版本号，如 v20.11.0
console.log(`Node 版本：   ${process.version}`);

// 4. 当前工作目录（进程启动时所在的目录，受 cd 影响，并非脚本自身目录）
console.log(`工作目录：    ${process.cwd()}`);

// 5. 读取环境变量 PATH，并做容错处理
//    process.env.PATH 在 Windows 上存在；极少数受限环境下可能为 undefined
const pathValue = process.env.PATH;
if (pathValue) {
  // 截取前 80 个字符，过长部分用省略号表示
  const preview = pathValue.length > 80 ? pathValue.slice(0, 80) + '...' : pathValue;
  console.log(`PATH 前 80 字符：${preview}`);
} else {
  // 友好提示，而不是抛出 ReferenceError
  console.log('PATH 前 80 字符：（当前环境未设置 PATH 变量）');
}
