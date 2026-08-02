/**
 * fs-typed.ts
 * 用 TypeScript 重写 fs/promises 常见操作：
 *   - 异步读写文件
 *   - 目录创建/读取
 *   - stat 元信息
 *   - Buffer 类型标注
 *
 * 运行：tsx fs-typed.ts
 */

import { promises as fs } from 'node:fs';
import * as path from 'node:path';

// ============================================================
// 1. 文本文件读写：返回 string
// ============================================================

async function writeText(filePath: string, content: string): Promise<void> {
  // encoding 传 'utf8' 时返回 string，TS 会自动收窄重载
  await fs.writeFile(filePath, content, 'utf8');
  console.log(`[writeText] 已写入 ${content.length} 字符到 ${filePath}`);
}

async function readText(filePath: string): Promise<string> {
  // 注意：不传 encoding 时返回 Buffer；传 encoding 收窄为 string
  const text: string = await fs.readFile(filePath, 'utf8');
  return text;
}

// ============================================================
// 2. Buffer 类型标注：二进制读写
// ============================================================

async function writeBuffer(filePath: string, buf: Buffer): Promise<void> {
  await fs.writeFile(filePath, buf);
  console.log(`[writeBuffer] 已写入 ${buf.byteLength} 字节到 ${filePath}`);
}

async function readBuffer(filePath: string): Promise<Buffer> {
  // 不传 encoding，返回 Buffer
  const buf: Buffer = await fs.readFile(filePath);
  return buf;
}

// ============================================================
// 3. 目录操作：mkdir 递归、readdir 读取
// ============================================================

async function ensureDir(dir: string): Promise<void> {
  // recursive: true 等价于 mkdir -p，已存在不会抛错
  await fs.mkdir(dir, { recursive: true });
  console.log(`[ensureDir] 目录就绪: ${dir}`);
}

async function listFiles(dir: string): Promise<string[]> {
  // withFileTypes: true 返回 Dirent[]，这里只要名字
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files: string[] = entries
    .filter((entry) => entry.isFile())
    .map((entry) => entry.name);
  return files;
}

// ============================================================
// 4. stat 元信息：Stats 类型
// ============================================================

interface FileMeta {
  size: number;
  isFile: boolean;
  isDirectory: boolean;
  mtime: Date;
}

async function getMeta(filePath: string): Promise<FileMeta> {
  const stats = await fs.stat(filePath);
  return {
    size: stats.size,
    isFile: stats.isFile(),
    isDirectory: stats.isDirectory(),
    mtime: stats.mtime,
  };
}

// ============================================================
// 5. 顶层入口：使用 Node 18+ 的顶层 await 不在 CommonJS 中支持
//    因此包一层 main()
// ============================================================

async function main(): Promise<void> {
  const tmpDir: string = path.join(process.cwd(), '.day14-tmp');
  await ensureDir(tmpDir);

  const textFile: string = path.join(tmpDir, 'hello.txt');
  const binFile: string = path.join(tmpDir, 'data.bin');

  // 文本读写
  await writeText(textFile, 'Hello, TypeScript + Node.js!');
  const text: string = await readText(textFile);
  console.log('[readText]', text);

  // Buffer 读写：从字符串构造 Buffer
  const input: Buffer = Buffer.from('二进制内容 🚀', 'utf8');
  await writeBuffer(binFile, input);
  const output: Buffer = await readBuffer(binFile);
  console.log('[readBuffer] bytes =', output.byteLength, 'toString =', output.toString('utf8'));

  // 目录列表
  const files: string[] = await listFiles(tmpDir);
  console.log('[listFiles]', files);

  // 元信息
  const meta: FileMeta = await getMeta(textFile);
  console.log('[getMeta]', meta);

  // 清理
  await fs.rm(tmpDir, { recursive: true, force: true });
  console.log('[cleanup] 已删除临时目录');
}

main().catch((err: unknown) => {
  console.error('主流程异常:', err);
  process.exit(1);
});
