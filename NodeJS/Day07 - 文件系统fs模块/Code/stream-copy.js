'use strict';

/**
 * Day07 - 大文件流式复制（stream/promises.pipeline）
 * 主题：createReadStream + createWriteStream + pipeline 实现大文件复制
 * 运行：node stream-copy.js
 *
 * 演示要点：
 *   1. 用循环写入生成一个测试用大文件（约 50MB）
 *   2. 用 pipeline 串联 ReadStream -> WriteStream 完成复制
 *   3. 对比源文件与目标文件 stat().size 是否一致
 *   4. 打印复制耗时，体现流式处理的优势
 *
 * 为什么不用 readFile + writeFile？
 *   - readFile 会把整个文件载入内存，50MB 还行，2GB 直接 OOM
 *   - createReadStream 按块（默认 64KB）读取，内存占用恒定
 *   - pipeline 自动处理“背压（backpressure）”，比 .pipe() 更安全：
 *     源出错时自动关闭下游流，避免内存泄漏
 */

const fs = require('fs');
const fsp = require('fs/promises');
const { pipeline } = require('stream/promises');
const path = require('path');

const workDir = path.join(__dirname, 'stream-workspace');
const srcFile = path.join(workDir, 'big.bin');
const destFile = path.join(workDir, 'big-copy.bin');

// 测试文件大小（字节）。50MB 足够展示流式处理；可调小以加快演示
const TARGET_SIZE = 50 * 1024 * 1024;

// ---------------------------------------------------------------
// 步骤 1：生成测试大文件
// 思路：准备一个 1MB 的 Buffer 块，循环写入 TARGET_SIZE/1MB 次
// 用 createWriteStream 流式写入，避免一次性占内存
// ---------------------------------------------------------------
async function generateBigFile() {
  console.log('[1] 生成测试大文件');
  await fsp.mkdir(workDir, { recursive: true });

  const chunkSize = 1024 * 1024; // 1MB
  // 用随机字节填充，避免被文件系统压缩或去重影响
  const chunk = Buffer.allocUnsafe(chunkSize);
  // 若想更“随机”，可取消下一行注释（会慢一些）
  // crypto.randomFillSync(chunk);

  const repeats = Math.ceil(TARGET_SIZE / chunkSize);
  const ws = fs.createWriteStream(srcFile);
  const t0 = Date.now();
  for (let i = 0; i < repeats; i++) {
    // write 返回 false 表示内部缓冲已满，需等待 'drain' 事件
    // 这里用 await + once('drain') 简单处理背压
    if (!ws.write(chunk)) {
      await new Promise(resolve => ws.once('drain', resolve));
    }
  }
  await new Promise(resolve => ws.end(resolve));
  const cost = Date.now() - t0;

  const st = await fsp.stat(srcFile);
  console.log(`  已生成: ${path.basename(srcFile)}`);
  console.log(`  大小  : ${(st.size / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  耗时  : ${cost} ms\n`);
}

// ---------------------------------------------------------------
// 步骤 2：用 pipeline 流式复制
// pipeline 比 src.pipe(dest) 更安全：
//   - 任一流出错时，自动销毁所有流，避免内存泄漏与未处理错误
//   - 自动处理背压，不会因为写入慢导致读端缓冲堆积
// ---------------------------------------------------------------
async function copyWithPipeline() {
  console.log('[2] pipeline 流式复制');
  const rs = fs.createReadStream(srcFile, { highWaterMark: 64 * 1024 }); // 64KB 块
  const ws = fs.createWriteStream(destFile);

  const t0 = Date.now();
  try {
    // pipeline 返回 Promise，出错时 reject
    await pipeline(rs, ws);
  } catch (err) {
    console.error('  pipeline 出错:', err.code, '-', err.message);
    throw err;
  }
  const cost = Date.now() - t0;
  console.log(`  复制完成，耗时: ${cost} ms\n`);
}

// ---------------------------------------------------------------
// 步骤 3：对比源/目标文件 stat().size，校验完整性
// ---------------------------------------------------------------
async function verify() {
  console.log('[3] 校验复制结果');
  const [srcStat, destStat] = await Promise.all([
    fsp.stat(srcFile),
    fsp.stat(destFile)
  ]);
  console.log(`  源文件 size : ${srcStat.size} bytes`);
  console.log(`  目标 size   : ${destStat.size} bytes`);
  console.log(`  一致?       : ${srcStat.size === destStat.size ? '是 ✅' : '否 ❌'}`);
  console.log('');
}

// ---------------------------------------------------------------
// 步骤 4（附加）：演示“中途插入转换流”统计字节数
// 这是 pipeline 的真正威力：可在 ReadStream 与 WriteStream 之间插入任意 Transform
// 例如：解压、加密、按行处理等
// ---------------------------------------------------------------
async function copyWithCounter() {
  console.log('[4] pipeline 中间插入 Transform 流，统计通过的字节数');
  const { Transform } = require('stream');

  let total = 0;
  const counter = new Transform({
    // 每来一块数据累加 size，原样透传给下游
    transform(chunk, encoding, callback) {
      total += chunk.length;
      callback(null, chunk);
    }
  });

  const destFile2 = path.join(workDir, 'big-copy-2.bin');
  await pipeline(
    fs.createReadStream(srcFile),
    counter,
    fs.createWriteStream(destFile2)
  );
  console.log(`  通过中间流的总字节数: ${total}`);
  const st = await fsp.stat(destFile2);
  console.log(`  目标文件 size       : ${st.size}`);
  console.log(`  两者一致?           : ${total === st.size ? '是 ✅' : '否 ❌'}\n`);

  // 清理第二个副本
  await fsp.unlink(destFile2);
}

// ---------------------------------------------------------------
// 清理：删除整个工作目录
// ---------------------------------------------------------------
async function cleanup() {
  console.log('[清理] 删除工作目录');
  await fsp.rm(workDir, { recursive: true, force: true });
  console.log('  已清理:', workDir, '\n');
}

// ---------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------
(async () => {
  try {
    await generateBigFile();
    await copyWithPipeline();
    await verify();
    await copyWithCounter();
  } catch (err) {
    console.error('主流程出错:', err);
  } finally {
    await cleanup();
    console.log('=== 结论 ===');
    console.log('1. 大文件复制用 createReadStream + createWriteStream + pipeline，');
    console.log('   内存占用恒定（默认 64KB highWaterMark），不会撑爆堆。');
    console.log('2. pipeline 比 .pipe() 更安全：自动处理背压与错误传播，');
    console.log('   任一流出错时自动销毁所有流。');
    console.log('3. pipeline 可在中间插入 Transform 流，构成处理流水线：');
    console.log('   解压、加密、统计、按行处理等都能挂在中间。');
    console.log('4. AI 场景：大模型权重/向量索引复制、日志流式处理、');
    console.log('   训练数据 ETL 都用这一套模式。');
  }
})();
