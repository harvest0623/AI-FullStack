// Day08 - path 模块演示
// 主题：join / resolve / parse / format / dirname / basename / extname / sep / delimiter / isAbsolute / relative
// 运行：node Code/path-demo.js
//
// 说明：path 是纯字符串模块，不会检查文件是否存在；
// 不同平台下 sep / delimiter / resolve 行为不同，本文件会同时展示 POSIX 与 Windows 视角。

const path = require('path');
const os = require('os');

console.log('========================================');
console.log(' Day08 - path 模块演示');
console.log('========================================');
console.log(`当前平台：${os.platform()}    path.sep = ${JSON.stringify(path.sep)}    path.delimiter = ${JSON.stringify(path.delimiter)}\n`);

// ---------------------------------------------------------------
// 1. path.join vs path.resolve
// ---------------------------------------------------------------
console.log('--- 1. path.join vs path.resolve ---');

// join：只做拼接 + 规范化，不强行变成绝对路径
console.log("path.join('/foo', 'bar', 'baz')        =", path.join('/foo', 'bar', 'baz'));
console.log("path.join('foo', 'bar')                 =", path.join('foo', 'bar'));
console.log("path.join('foo', '..', 'bar', '.')      =", path.join('foo', '..', 'bar', '.'));
// 空字符串被忽略
console.log("path.join('foo', '', 'bar')             =", path.join('foo', '', 'bar'));

// resolve：一定返回绝对路径（找不到绝对片段就补 process.cwd）
console.log('\n--- resolve 必返回绝对路径 ---');
console.log("path.resolve('/foo/bar', './baz')        =", path.resolve('/foo/bar', './baz'));
console.log("path.resolve('foo', 'bar')              =", path.resolve('foo', 'bar'), '   ← 前缀是当前 cwd');
console.log("path.resolve()                          =", path.resolve(), '   ← 等价于 process.cwd()');
console.log("path.resolve('foo', '', 'bar')         =", path.resolve('foo', '', 'bar'));

// ---------------------------------------------------------------
// 2. 规范化 normalize
// ---------------------------------------------------------------
console.log('\n--- 2. path.normalize 清掉 . 与 .. 与多余分隔符 ---');
console.log("normalize('/foo/bar//baz/.././qux/')    =", path.normalize('/foo/bar//baz/.././qux/'));
console.log("normalize('foo/./bar/..')               =", path.normalize('foo/./bar/..'));

// ---------------------------------------------------------------
// 3. dirname / basename / extname
// ---------------------------------------------------------------
console.log('\n--- 3. dirname / basename / extname ---');
const file = '/data/models/chatglm-6b/model.bin';
console.log('原始路径：', file);
console.log('  dirname  =', path.dirname(file));      // /data/models/chatglm-6b
console.log('  basename =', path.basename(file));     // model.bin
console.log('  basename(.bin) =', path.basename(file, '.bin')); // model
console.log('  extname  =', path.extname(file));      // .bin

// extname 只取最后一个点
const archive = '/tmp/backup/report.tar.gz';
console.log('\n原始路径：', archive);
console.log('  extname  =', path.extname(archive), '   ⚠️ 只取最后一个点，不是 .tar.gz');
console.log('  basename =', path.basename(archive));

// ---------------------------------------------------------------
// 4. parse / format（拆解与重组）
// ---------------------------------------------------------------
console.log('\n--- 4. path.parse / path.format ---');
const parsed = path.parse(archive);
console.log('parse 结果：');
console.log(parsed);
// {
//   root: '/tmp'/'/' 等平台相关
//   dir: '/tmp/backup',
//   base: 'report.tar.gz',
//   name: 'report',
//   ext: '.gz'
// }

// format：把片段重新拼回路径
const reassembled = path.format({
  dir: '/data/output',
  name: 'result',
  ext: '.json',
});
console.log('format 重组：', reassembled);

// ---------------------------------------------------------------
// 5. 平台差异：posix vs win32
// ---------------------------------------------------------------
console.log('\n--- 5. 强制走 POSIX 规则（常用于生成容器内路径）---');
console.log("path.posix.join('/app', 'data', 'x.json') =", path.posix.join('/app', 'data', 'x.json'));
console.log("path.win32.join('C:\\\\app', 'data', 'x.json') =", path.win32.join('C:\\app', 'data', 'x.json'));
console.log("path.posix.sep =", JSON.stringify(path.posix.sep));
console.log("path.win32.sep =", JSON.stringify(path.win32.sep));

// ---------------------------------------------------------------
// 6. isAbsolute / relative
// ---------------------------------------------------------------
console.log('\n--- 6. isAbsolute / relative ---');
console.log("isAbsolute('/foo')      =", path.isAbsolute('/foo'));
console.log("isAbsolute('foo')       =", path.isAbsolute('foo'));
console.log("isAbsolute('C:\\\\foo')  =", path.isAbsolute('C:\\foo'), '   ← Windows 视角下 true');

console.log("relative('/data/a/b', '/data/a/c/d') =", path.relative('/data/a/b', '/data/a/c/d'));
console.log("relative('/x', '/x')                  =", JSON.stringify(path.relative('/x', '/x')), '   ← 同目录返回空字符串');

// ---------------------------------------------------------------
// 7. delimiter 拆 PATH
// ---------------------------------------------------------------
console.log('\n--- 7. 用 delimiter 拆 PATH 环境变量（前 3 项）---');
const paths = process.env.PATH ? process.env.PATH.split(path.delimiter) : [];
console.log(`PATH 共 ${paths.length} 项，前 3 项：`);
paths.slice(0, 3).forEach((p, i) => console.log(`  [${i}] ${p}`));

// ---------------------------------------------------------------
// 8. 实战：跨平台配置文件路径
// ---------------------------------------------------------------
console.log('\n--- 8. 实战：跨平台获取配置文件路径 ---');

function buildConfigPath(appName, fileName) {
  // 在用户家目录下找/创建隐藏目录
  let baseDir;
  if (os.platform() === 'win32') {
    // Windows 习惯用 %APPDATA%/<appName>
    baseDir = path.join(process.env.APPDATA || os.homedir(), appName);
  } else {
    // macOS / Linux 习惯用 ~/.<appName>
    baseDir = path.join(os.homedir(), `.${appName}`);
  }
  return path.join(baseDir, fileName);
}

const configPath = buildConfigPath('myapp', 'config.json');
console.log('配置文件路径：', configPath);

// 把它拆开看看
const info = path.parse(configPath);
console.log('parse 拆解：');
console.log(`  root : ${info.root}`);
console.log(`  dir  : ${info.dir}`);
console.log(`  base : ${info.base}`);
console.log(`  name : ${info.name}`);
console.log(`  ext  : ${info.ext}`);

// ---------------------------------------------------------------
console.log('\n=== 要点回顾 ===');
console.log('  1. join 只拼接、resolve 必返回绝对路径；');
console.log('  2. extname 只取最后一个点后的内容；');
console.log('  3. path.posix / path.win32 可强制平台规则；容器路径用 posix；');
console.log('  4. parse/format 互逆，可拆解也可重组；');
console.log('  5. isAbsolute/relative 跨平台行为不同，注意 Windows 的盘符场景。');
