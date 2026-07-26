'use strict';

/**
 * Day07 - 目录操作（fs/promises）
 * 主题：mkdir recursive / readdir withFileTypes / 递归遍历 / rm recursive / mkdtemp
 * 运行：node dir-ops.js
 *
 * 演示要点：
 *   1. mkdir recursive 一次性创建多层目录
 *   2. readdir withFileTypes 直接拿到 isFile/isDirectory，省去额外 stat
 *   3. 递归遍历目录树（walk 函数）
 *   4. rm recursive 安全删除整个目录树
 *   5. mkdtemp 创建系统临时目录
 */

const fsp = require('fs/promises');
const fs = require('fs');
const os = require('os');
const path = require('path');

// ---------------------------------------------------------------
// 准备：在工作目录下构造测试目录树
//   sandbox/
//     a.txt
//     b.txt
//     sub1/
//       c.txt
//       deep/
//         d.txt
//     sub2/
//       e.txt
// ---------------------------------------------------------------
const sandbox = path.join(__dirname, 'dir-sandbox');

async function buildSandbox() {
  console.log('[1] 用 mkdir recursive 构建测试目录树');
  console.log('  根目录:', sandbox);

  // recursive: true 让多层路径一次性建好，已存在也不报错
  await fsp.mkdir(path.join(sandbox, 'sub1', 'deep'), { recursive: true });
  await fsp.mkdir(path.join(sandbox, 'sub2'), { recursive: true });

  // 在各层放几个文件，方便后续遍历
  await fsp.writeFile(path.join(sandbox, 'a.txt'), 'A\n', 'utf8');
  await fsp.writeFile(path.join(sandbox, 'b.txt'), 'BB\n', 'utf8');
  await fsp.writeFile(path.join(sandbox, 'sub1', 'c.txt'), 'CCC\n', 'utf8');
  await fsp.writeFile(path.join(sandbox, 'sub1', 'deep', 'd.txt'), 'DDDD\n', 'utf8');
  await fsp.writeFile(path.join(sandbox, 'sub2', 'e.txt'), 'EEEEE\n', 'utf8');

  console.log('  目录树已构建完毕\n');
}

// ---------------------------------------------------------------
// readdir withFileTypes：列出目录条目，无需对每个条目再 stat
// Dirent 对象提供 isFile() / isDirectory() / isSymbolicLink() 等方法
// ---------------------------------------------------------------
async function listWithFileTypes() {
  console.log('[2] readdir { withFileTypes: true } 列出 sandbox 顶层');
  const entries = await fsp.readdir(sandbox, { withFileTypes: true });
  for (const ent of entries) {
    let type = '未知';
    if (ent.isDirectory()) type = '目录';
    else if (ent.isFile()) type = '文件';
    else if (ent.isSymbolicLink()) type = '软链';
    console.log(`  [${type}] ${ent.name}`);
  }
  console.log('');
}

// ---------------------------------------------------------------
// 递归遍历：walk(dir) 返回所有文件的相对路径与大小
// 这是 AI 项目里“扫描数据集目录”的常见需求
// ---------------------------------------------------------------
async function walk(dir, base = dir) {
  const results = [];
  const entries = await fsp.readdir(dir, { withFileTypes: true });
  for (const ent of entries) {
    const full = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      // 递归进入子目录
      const sub = await walk(full, base);
      results.push(...sub);
    } else if (ent.isFile()) {
      // 取相对路径与大小，便于打印
      const rel = path.relative(base, full);
      const st = await fsp.stat(full);
      results.push({ path: rel, size: st.size });
    }
    // 软链等其他类型这里忽略；如需跟踪软链要用 lstat + 自行处理
  }
  return results;
}

async function demoWalk() {
  console.log('[3] 递归遍历目录树 walk()');
  const files = await walk(sandbox);
  for (const f of files) {
    console.log(`  ${f.path}  (${f.size} bytes)`);
  }
  console.log(`  共 ${files.length} 个文件\n`);
}

// ---------------------------------------------------------------
// mkdtemp：在系统临时目录下创建带随机后缀的目录
// 常用于单元测试、批处理中间产物
// ---------------------------------------------------------------
async function demoMkdtemp() {
  console.log('[4] mkdtemp 创建临时目录');
  // 注意：prefix 必须是路径前缀，建议用 path.join(os.tmpdir(), ...) 保证落在系统临时目录
  const prefix = path.join(os.tmpdir(), 'day07-job-');
  const tmp = await fsp.mkdtemp(prefix);
  console.log('  临时目录:', tmp);

  // 在临时目录里写点东西，演示一次性使用
  await fsp.writeFile(path.join(tmp, 'result.txt'), '中间结果', 'utf8');
  const content = await fsp.readFile(path.join(tmp, 'result.txt'), 'utf8');
  console.log('  写入并读回:', content);

  // 用完即删（递归）
  await fsp.rm(tmp, { recursive: true, force: true });
  console.log('  已清理临时目录\n');
}

// ---------------------------------------------------------------
// rm recursive：删除整个目录树
// ---------------------------------------------------------------
async function cleanup() {
  console.log('[5] rm recursive 清理 sandbox');
  // recursive: 递归删子内容；force: 不存在也不抛错
  await fsp.rm(sandbox, { recursive: true, force: true });
  console.log('  已清理:', sandbox);

  // 验证已删除
  try {
    await fsp.stat(sandbox);
  } catch (err) {
    console.log('  验证 stat 报错（预期）:', err.code); // ENOENT
  }
  console.log('');
}

// ---------------------------------------------------------------
// 对比：rmdir 已废弃，不要用 recursive 参数
// ---------------------------------------------------------------
async function warnAboutRmdir() {
  console.log('[附加] rmdir vs rm 注意事项');
  console.log('  - fs.rmdir 只能删空目录，recursive 参数在 Node 16+ 已废弃；');
  console.log('  - 删目录树统一用 fs.rm(path, { recursive: true, force: true })。');
  console.log('');
}

// ---------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------
(async () => {
  try {
    await buildSandbox();
    await listWithFileTypes();
    await demoWalk();
    await demoMkdtemp();
    await warnAboutRmdir();
  } catch (err) {
    console.error('出错:', err.code, '-', err.message);
  } finally {
    await cleanup();
    console.log('=== 结论 ===');
    console.log('1. mkdir recursive 是“一次性建多层目录”的标准姿势，幂等。');
    console.log('2. readdir { withFileTypes: true } 返回 Dirent，');
    console.log('   可直接 isFile/isDirectory，省去对每个条目额外 stat。');
    console.log('3. 递归遍历目录树用 walk(dir) 模式，AI 项目里常用于扫描数据集。');
    console.log('4. mkdtemp 落在 os.tmpdir()，配合 rm 做即用即清。');
    console.log('5. 删目录树统一用 rm recursive，不要再依赖 rmdir。');
  }
})();
