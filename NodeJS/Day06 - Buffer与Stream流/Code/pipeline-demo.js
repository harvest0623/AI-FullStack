'use strict';

/**
 * Day06 - stream.pipeline 演示
 * 主题：大文件读取 → 转换 → 写入，对比 pipe 的错误处理优势
 * 运行：node pipeline-demo.js
 *
 * 流程：
 *   1. 生成一个临时大文件
 *   2. 用 pipeline 读 → 转大写 → 写，演示正常流程与完成回调
 *   3. 用 pipeline + 故意出错，演示错误自动传播与资源清理
 *   4. 对比 pipe 的错误处理痛点
 *   5. 清理临时文件
 */

const fs = require('fs');
const path = require('path');
const { Transform, Writable } = require('stream');
const pipeline = require('stream').pipeline;
const pipelinePromise = require('stream/promises').pipeline;

// ---------------------------------------------------------------
// 工具：自定义 Transform —— 行首加行号
// ---------------------------------------------------------------
class LineNumberTransform extends Transform {
  constructor(options) {
    super(options);
    this.lineNo = 0;
    this.remainder = ''; // 累积不完整的最后一行
  }
  _transform(chunk, encoding, callback) {
    const text = this.remainder + chunk.toString('utf8');
    const lines = text.split('\n');
    // 最后一段可能是不完整的行，留到下次
    this.remainder = lines.pop();
    const out = lines.map(l => `${++this.lineNo}: ${l}`).join('\n') + '\n';
    callback(null, Buffer.from(out, 'utf8'));
  }
  _flush(callback) {
    if (this.remainder) {
      callback(null, Buffer.from(`${++this.lineNo}: ${this.remainder}\n`, 'utf8'));
    } else {
      callback();
    }
  }
}

// 工具：故意随机出错的 Transform
class UnstableTransform extends Transform {
  constructor(failAt, options) {
    super(options);
    this.failAt = failAt; // 第几次 transform 时抛错
    this.count = 0;
  }
  _transform(chunk, encoding, callback) {
    this.count++;
    if (this.count >= this.failAt) {
      callback(new Error(`💥 第 ${this.count} 块时故意抛错`));
      return;
    }
    callback(null, chunk); // 原样转发
  }
}

// ---------------------------------------------------------------
// 1. 生成临时大文件
// ---------------------------------------------------------------
function createTempFile(filePath, lines) {
  const content = Array.from({ length: lines }, (_, i) => `这是第 ${i + 1} 行数据`).join('\n') + '\n';
  fs.writeFileSync(filePath, content, 'utf8');
  const sizeKB = (Buffer.byteLength(content) / 1024).toFixed(1);
  console.log(`已生成临时文件: ${path.basename(filePath)} (${lines} 行, ${sizeKB} KB)`);
}

// ---------------------------------------------------------------
// 2. 正常流程：pipeline 读 → 加行号 → 写
// ---------------------------------------------------------------
function normalPipelineDemo(srcPath, destPath) {
  console.log('\n=== 演示 1：pipeline 正常流程 ===');
  const rs = fs.createReadStream(srcPath);
  const ws = fs.createWriteStream(destPath);
  const addLineNo = new LineNumberTransform();

  pipeline(
    rs,
    addLineNo,
    ws,
    (err) => {
      if (err) {
        console.error('  pipeline 失败:', err.message);
        return;
      }
      console.log('  ✅ pipeline 完成（callback 触发）');
      // 打印目标文件前 3 行验证
      const head = fs.readFileSync(destPath, 'utf8').split('\n').slice(0, 3).join('\n');
      console.log('  目标文件前 3 行:\n' + head.split('\n').map(l => '    ' + l).join('\n'));
      errorPipelineDemo(srcPath, destPath);
    }
  );
}

// ---------------------------------------------------------------
// 3. 错误流程：pipeline 中间出错，自动销毁所有流
// ---------------------------------------------------------------
function errorPipelineDemo(srcPath, destPath) {
  console.log('\n=== 演示 2：pipeline 中间流出错（自动错误传播）===');
  const errorPath = destPath + '.err';
  const rs = fs.createReadStream(srcPath);
  const ws = fs.createWriteStream(errorPath);
  // 故意在第 3 块时抛错
  const unstable = new UnstableTransform(3);

  pipeline(
    rs,
    unstable,
    ws,
    (err) => {
      if (err) {
        console.log('  ✅ 捕获到 pipeline 错误:', err.message);
        console.log('  ✅ 所有流已被自动 destroy()，无 fd 泄漏');
        console.log(`  ✅ 读流已销毁? ${rs.destroyed}, 写流已销毁? ${ws.destroyed}`);
        pipeErrorPitfallDemo(srcPath);
      } else {
        console.log('  未出错（不应走到这里）');
      }
    }
  );
}

// ---------------------------------------------------------------
// 4. 对比：pipe 的错误处理痛点
// pipe 不会传播错误，目标流不会被关闭，导致 fd 泄漏
// ---------------------------------------------------------------
function pipeErrorPitfallDemo(srcPath) {
  console.log('\n=== 演示 3：对比 pipe 的错误处理痛点 ===');
  console.log('  （pipe 不传播错误，源流出错时目标流不会被关闭）');

  const rs = fs.createReadStream(srcPath);
  const ws = fs.createWriteStream(srcPath + '.pipe-leak');
  const unstable = new UnstableTransform(2);

  // 必须给每个流单独挂 'error'，遗漏一个就崩
  rs.on('error', err => console.log('  rs error:', err.message));
  unstable.on('error', err => console.log('  unstable error:', err.message));
  ws.on('error', err => console.log('  ws error:', err.message));
  ws.on('finish', () => console.log('  ws finish（只有不出错才会触发）'));

  rs.pipe(unstable).pipe(ws);

  // 不稳定流出错后，pipe 不会自动关 ws，造成 fd 泄漏
  // 需要手动在 unstable 的 error 里 ws.destroy()
  unstable.on('error', () => {
    console.log('  ⚠️  pipe 模式下：unstable 出错，但 ws 仍打开，需手动 destroy');
    console.log(`  ⚠️  ws.destroyed = ${ws.destroyed}（true 表示已手动销毁）`);
    ws.destroy();
    console.log(`  ⚠️  手动 destroy 后 ws.destroyed = ${ws.destroyed}`);
    promisePipelineDemo(srcPath);
  });
}

// ---------------------------------------------------------------
// 5. Promise 版 pipeline（stream/promises）
// 配合 async/await，代码更清晰
// ---------------------------------------------------------------
async function promisePipelineDemo(srcPath) {
  console.log('\n=== 演示 4：Promise 版 pipeline（stream/promises）===');
  const destPath = srcPath + '.promise';

  try {
    await pipelinePromise(
      fs.createReadStream(srcPath),
      new LineNumberTransform(),
      fs.createWriteStream(destPath)
    );
    console.log('  ✅ Promise 版 pipeline 完成（await 正常返回）');
    console.log('  ✅ 无需 callback，配合 async/await 更直观');
  } catch (err) {
    console.error('  Promise 版 pipeline 出错:', err.message);
  }

  cleanup(srcPath);
}

// ---------------------------------------------------------------
// 6. 清理临时文件
// ---------------------------------------------------------------
function cleanup(srcPath) {
  console.log('\n=== 清理临时文件 ===');
  const files = [
    srcPath,
    srcPath + '.out',
    srcPath + '.out.err',
    srcPath + '.pipe-leak',
    srcPath + '.promise',
  ];
  for (const f of files) {
    try {
      fs.unlinkSync(f);
      console.log(`  已删除: ${path.basename(f)}`);
    } catch {
      // 文件可能不存在（出错场景），忽略
    }
  }
  console.log('\n✅ pipeline 演示完成');
}

// ---------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------
const tmpDir = require('os').tmpdir();
const srcFile = path.join(tmpDir, 'day06-pipeline-src.txt');
const destFile = path.join(tmpDir, 'day06-pipeline-dest.txt');

console.log('临时目录:', tmpDir);
createTempFile(srcFile, 1000);
normalPipelineDemo(srcFile, destFile);
