'use strict';

/**
 * Day07 - 文件操作全流程（fs/promises）
 * 主题：writeFile / appendFile / stat / rename / unlink 完整生命周期 + 原子写入
 * 运行：node file-ops.js
 *
 * 演示要点：
 *   1. 用 fs/promises 完成文件从创建到删除的完整流程
 *   2. 每步都加 try/catch，捕获并打印 err.code
 *   3. 实现 atomicWrite（先写临时文件再 rename）
 */

const fsp = require('fs/promises');
const path = require('path');

// 所有测试文件都放在自己的工作目录下，避免误操作系统文件
const workDir = path.join(__dirname, 'file-ops-workspace');

// ---------------------------------------------------------------
// 工具：把错误转成可读字符串（含 err.code）
// ---------------------------------------------------------------
function describeErr(err) {
  return `${err.code || 'UNKNOWN'} - ${err.message}`;
}

// ---------------------------------------------------------------
// 步骤 1：准备工作目录（mkdir recursive）
// ---------------------------------------------------------------
async function prepare() {
  console.log('[步骤 1] 准备工作目录');
  // recursive: true 保证父目录不存在时自动创建，目录已存在也不报错（幂等）
  await fsp.mkdir(workDir, { recursive: true });
  console.log('  工作目录:', workDir, '\n');
}

// ---------------------------------------------------------------
// 步骤 2：writeFile 覆盖写入 + appendFile 追加
// ---------------------------------------------------------------
async function writeAndAppend() {
  console.log('[步骤 2] writeFile / appendFile');
  const file = path.join(workDir, 'note.txt');

  // writeFile：默认 flag='w'，会清空原文件后写入
  await fsp.writeFile(file, '第一行：初始内容\n', 'utf8');
  console.log('  writeFile 写入第一行');

  // appendFile：在文件末尾追加，等价于 writeFile 带 flag:'a'
  await fsp.appendFile(file, '第二行：追加内容 A\n');
  await fsp.appendFile(file, '第三行：追加内容 B\n');
  console.log('  appendFile 追加了两行');

  // 用 flag:'a' 实现等价追加
  await fsp.writeFile(file, '第四行：用 flag=a 追加\n', { flag: 'a' });
  console.log('  writeFile({flag:\'a\'}) 追加第四行');

  // 读回验证
  const content = await fsp.readFile(file, 'utf8');
  console.log('  当前文件内容:\n' + content.split('\n').map(l => '    ' + l).join('\n'));

  // 演示 flag='wx'：文件已存在则抛 EEXIST，常用于“原子创建/文件锁”
  try {
    await fsp.writeFile(file, '不该被写入', { flag: 'wx' });
  } catch (err) {
    console.log('  flag=wx 写已存在文件 -> 抛错:', err.code); // EEXIST
  }
  console.log('');
  return file;
}

// ---------------------------------------------------------------
// 步骤 3：stat 获取文件信息
// ---------------------------------------------------------------
async function showStat(file) {
  console.log('[步骤 3] stat 获取文件信息');
  try {
    const st = await fsp.stat(file);
    console.log('  size      :', st.size, 'bytes');
    console.log('  mtime     :', st.mtime.toISOString());
    console.log('  birthtime :', st.birthtime.toISOString());
    console.log('  isFile()  :', st.isFile());
    console.log('  isDirectory():', st.isDirectory());
    // mode 的低 12 位是权限位，用八进制更直观
    console.log('  mode      :', '0o' + (st.mode & 0o7777).toString(8));
  } catch (err) {
    console.error('  stat 出错:', describeErr(err));
  }
  console.log('');
}

// ---------------------------------------------------------------
// 步骤 4：rename 改名 + 再次 stat 验证
// ---------------------------------------------------------------
async function renameAndVerify(file) {
  console.log('[步骤 4] rename 改名');
  const newName = path.join(workDir, 'note-renamed.txt');
  try {
    await fsp.rename(file, newName);
    console.log('  已重命名:', path.basename(file), '->', path.basename(newName));

    // 验证旧路径已不存在
    try {
      await fsp.stat(file);
    } catch (err) {
      console.log('  旧路径 stat 报错（预期）:', err.code); // ENOENT
    }

    // 验证新路径可访问
    const st = await fsp.stat(newName);
    console.log('  新路径 size:', st.size, 'bytes（与原文件一致）');
  } catch (err) {
    console.error('  rename 出错:', describeErr(err));
  }
  console.log('');
  return newName;
}

// ---------------------------------------------------------------
// 步骤 5：原子写入（先写临时文件再 rename）
// 场景：写配置/缓存时，写到一半进程崩溃会留下截断的脏文件
// 解法：写到同目录临时文件，再 rename 原子替换；要么完整生效，要么完全不生效
// ---------------------------------------------------------------
async function atomicWrite(file, content) {
  // 注意：临时文件必须与目标在同一目录（同卷），否则 rename 不再原子
  const tmp = file + '.tmp.' + process.pid;
  await fsp.writeFile(tmp, content, 'utf8');
  await fsp.rename(tmp, file); // 同卷 rename 是原子操作
}

async function demoAtomicWrite() {
  console.log('[步骤 5] 原子写入 atomicWrite');
  const target = path.join(workDir, 'config.json');

  // 第一次：目标不存在，正常生成
  await atomicWrite(target, JSON.stringify({ version: 1, ok: true }, null, 2));
  console.log('  第一次写入:', await fsp.readFile(target, 'utf8'));

  // 第二次：目标已存在，原子替换为新内容（不会留下半截脏文件）
  await atomicWrite(target, JSON.stringify({ version: 2, ok: true, updated: true }, null, 2));
  console.log('  第二次写入:', await fsp.readFile(target, 'utf8'));

  // 验证临时文件已被 rename 带走
  try {
    await fsp.stat(target + '.tmp.' + process.pid);
    console.log('  临时文件还在（异常）');
  } catch (err) {
    console.log('  临时文件已不存在（预期）:', err.code);
  }
  console.log('');
  return target;
}

// ---------------------------------------------------------------
// 步骤 6：copyFile 复制 + unlink 删除
// ---------------------------------------------------------------
async function copyAndDelete(file) {
  console.log('[步骤 6] copyFile 复制 + unlink 删除');
  const copy = path.join(workDir, 'config-backup.json');
  try {
    await fsp.copyFile(file, copy);
    console.log('  已复制:', path.basename(file), '->', path.basename(copy));

    // 删除原文件
    await fsp.unlink(file);
    console.log('  已 unlink 原文件:', path.basename(file));

    // 验证原文件不存在
    try {
      await fsp.stat(file);
    } catch (err) {
      console.log('  原文件 stat 报错（预期）:', err.code); // ENOENT
    }

    // 删除备份
    await fsp.unlink(copy);
    console.log('  已 unlink 备份:', path.basename(copy));
  } catch (err) {
    console.error('  copyAndDelete 出错:', describeErr(err));
  }
  console.log('');
}

// ---------------------------------------------------------------
// 错误处理演示：故意制造 ENOENT / EISDIR
// ---------------------------------------------------------------
async function errorCases() {
  console.log('[附加] 错误码演示');

  // ENOENT：读不存在的文件
  try {
    await fsp.readFile(path.join(workDir, 'no-such.txt'), 'utf8');
  } catch (err) {
    console.log('  ENOENT ->', err.code);
  }

  // EISDIR：把目录当文件读
  try {
    await fsp.readFile(workDir, 'utf8'); // workDir 是目录
  } catch (err) {
    console.log('  EISDIR ->', err.code);
  }

  // ENOTDIR：把文件当目录读（直接对文件路径调用 readdir）
  try {
    const fakeFile = path.join(workDir, 'fake.txt');
    await fsp.writeFile(fakeFile, 'x', 'utf8');
    await fsp.readdir(fakeFile); // fake.txt 是文件不是目录
  } catch (err) {
    console.log('  ENOTDIR ->', err.code);
  }
  console.log('');
}

// ---------------------------------------------------------------
// 清理：删除整个工作目录
// ---------------------------------------------------------------
async function cleanup() {
  console.log('[清理] rm recursive 删除工作目录');
  // recursive: 递归删子内容；force: 不存在不抛错
  await fsp.rm(workDir, { recursive: true, force: true });
  console.log('  已清理:', workDir);
}

// ---------------------------------------------------------------
// 主流程：完整生命周期
// ---------------------------------------------------------------
(async () => {
  try {
    await prepare();
    const file = await writeAndAppend();
    await showStat(file);
    const renamed = await renameAndVerify(file);
    const target = await demoAtomicWrite();
    await copyAndDelete(target);
    await errorCases();
  } catch (err) {
    // 顶层兜底：任何未在子函数内捕获的错误都会到这里
    console.error('顶层捕获错误:', describeErr(err));
  } finally {
    await cleanup();
    console.log('\n=== 结论 ===');
    console.log('1. fs/promises 配合 async/await 让文件操作像同步代码一样直观。');
    console.log('2. 每一步都应 try/catch，按 err.code 分支处理常见错误。');
    console.log('3. 原子写入（tmp + rename）是写配置/缓存的标准姿势，');
    console.log('   能避免“写到一半崩溃留下脏文件”。');
    console.log('4. 临时文件必须与目标在同一目录，保证 rename 在同卷上原子。');
  }
})();
