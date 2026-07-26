'use strict';

/**
 * Day06 - 背压（backpressure）与 highWaterMark 演示
 * 主题：write 返回 false 时的暂停-恢复处理，对比不同 highWaterMark
 * 运行：node backpressure-demo.js
 *
 * 场景：高速 Readable（每 1ms 产 64KB）+ 低速 Writable（每块处理 30ms）
 *      生产快于消费 → 背压 → write 返回 false → 暂停读取 → drain 后恢复
 */

const { Readable, Writable } = require('stream');

// ---------------------------------------------------------------
// 1. 高速 Readable：每 1ms push 一块 64KB 数据
// ---------------------------------------------------------------
class FastSource extends Readable {
  constructor(totalChunks, chunkSize, options) {
    super(options);
    this.totalChunks = totalChunks;
    this.chunkSize = chunkSize;
    this.pushed = 0;
  }
  _read() {
    // 用 setImmediate 模拟极速生产
    setImmediate(() => {
      if (this.pushed >= this.totalChunks) {
        this.push(null);
        return;
      }
      this.pushed++;
      // 生成一块 chunkSize 字节的 Buffer
      this.push(Buffer.alloc(this.chunkSize, this.pushed % 256));
    });
  }
}

// ---------------------------------------------------------------
// 2. 低速 Writable：每块处理 30ms（模拟慢磁盘 / 慢网络）
// ---------------------------------------------------------------
class SlowSink extends Writable {
  constructor(delayMs, options) {
    super(options);
    this.delayMs = delayMs;
    this.written = 0;
  }
  _write(chunk, encoding, callback) {
    // 模拟慢速 I/O：延迟后才通知“处理完”
    setTimeout(() => {
      this.written++;
      callback();
    }, this.delayMs);
  }
}

// ---------------------------------------------------------------
// 3. 手动处理背压的标准模式
//    write 返回 false → pause → 等 drain → resume
// ---------------------------------------------------------------
function runWithBackpressure(label, highWaterMark) {
  return new Promise((resolve) => {
    console.log(`\n=== ${label}（highWaterMark = ${highWaterMark} 字节）===`);

    const TOTAL_CHUNKS = 20;
    const CHUNK_SIZE = 64 * 1024; // 64KB
    const totalBytes = (TOTAL_CHUNKS * CHUNK_SIZE / 1024 / 1024).toFixed(2);

    const source = new FastSource(TOTAL_CHUNKS, CHUNK_SIZE);
    // 故意把 highWaterMark 设小一点，让背压更容易触发
    const sink = new SlowSink(30, { highWaterMark });

    let backpressureCount = 0;
    let chunkCount = 0;
    const startTime = Date.now();

    source.on('data', (chunk) => {
      chunkCount++;
      const ok = sink.write(chunk);

      if (!ok) {
        // write 返回 false：缓冲超过水位线，背压发生
        backpressureCount++;
        const t = ((Date.now() - startTime) / 1000).toFixed(2);
        console.log(`  [${t}s] chunk #${chunkCount} 触发背压！write 返回 false，暂停读取`);
        source.pause(); // 暂停生产
        sink.once('drain', () => {
          const t2 = ((Date.now() - startTime) / 1000).toFixed(2);
          console.log(`  [${t2}s] drain 触发，缓冲已排空，恢复读取`);
          source.resume(); // 恢复生产
        });
      }
    });

    source.on('end', () => {
      sink.end();
    });

    sink.on('finish', () => {
      const elapsed = Date.now() - startTime;
      console.log(`  ✅ 完成：共 ${chunkCount} 块 (${totalBytes} MB)，背压发生 ${backpressureCount} 次，耗时 ${elapsed}ms`);
      resolve();
    });

    source.on('error', err => console.error('源错误:', err.message));
    sink.on('error', err => console.error('汇错误:', err.message));
  });
}

// ---------------------------------------------------------------
// 4. 反例：不处理背压（无脑 write）
//    内存会持续堆积，生产环境中可能 OOM
// ---------------------------------------------------------------
function runWithoutBackpressure() {
  return new Promise((resolve) => {
    console.log('\n=== 反例：不处理背压（无脑 write，观察内存堆积）===');

    const TOTAL_CHUNKS = 10;
    const CHUNK_SIZE = 64 * 1024;
    const source = new FastSource(TOTAL_CHUNKS, CHUNK_SIZE);
    // highWaterMark 设很大，让 write 几乎不返回 false，模拟“不看返回值”
    const sink = new SlowSink(20, { highWaterMark: 100 * 1024 * 1024 });

    let chunkCount = 0;
    let falseCount = 0;
    let bufferedBytes = 0;

    source.on('data', (chunk) => {
      chunkCount++;
      bufferedBytes += chunk.length;
      const ok = sink.write(chunk);
      if (!ok) falseCount++;
      // ❌ 不看 ok，继续无脑 write —— 内存里堆积的未写数据越来越多
      const memMB = (bufferedBytes / 1024 / 1024).toFixed(2);
      console.log(`  chunk #${chunkCount}: 已接收 ${memMB} MB，write 返回 ${ok}（不看也不处理）`);
    });

    source.on('end', () => sink.end());

    sink.on('finish', () => {
      console.log(`  ⚠️  共 ${chunkCount} 块，write 返回 false ${falseCount} 次但未处理`);
      console.log('  ⚠️  生产环境中如果 chunk 更多、sink 更慢，内存会持续涨直到 OOM');
      console.log('  💡 正确做法：write 返回 false 时 pause，drain 后 resume（见上方标准模式）');
      resolve();
    });
  });
}

// ---------------------------------------------------------------
// 5. 优雅方案：用 pipe / pipeline 自动处理背压
//    pipe 内部已实现 pause/resume/drain 逻辑
// ---------------------------------------------------------------
function runWithPipe() {
  return new Promise((resolve) => {
    console.log('\n=== 优雅方案：pipe 自动处理背压 ===');

    const TOTAL_CHUNKS = 20;
    const CHUNK_SIZE = 64 * 1024;
    const source = new FastSource(TOTAL_CHUNKS, CHUNK_SIZE);
    const sink = new SlowSink(30, { highWaterMark: 16 * 1024 });
    const startTime = Date.now();

    sink.on('finish', () => {
      const elapsed = Date.now() - startTime;
      console.log(`  ✅ pipe 完成，耗时 ${elapsed}ms（无需手动 pause/resume，背压全自动）`);
      resolve();
    });

    // pipe 内部处理背压：当 write 返回 false，自动 pause 源流；drain 后自动 resume
    source.pipe(sink);
  });
}

// ---------------------------------------------------------------
// 主流程：依次演示不同 highWaterMark 与方案
// ---------------------------------------------------------------
(async () => {
  console.log('场景：高速源（每块 64KB）+ 低速汇（每块处理 30ms）\n');

  // 5.1 小水位线：背压频繁触发，但内存占用低
  await runWithBackpressure('小水位线', 16 * 1024); // 16KB

  // 5.2 大水位线：背压少触发，但内存占用高
  await runWithBackpressure('大水位线', 1024 * 1024); // 1MB

  // 5.3 反例：不处理背压
  await runWithoutBackpressure();

  // 5.4 优雅方案：pipe 自动背压
  await runWithPipe();

  console.log('\n✅ 背压演示完成');
  console.log('\n结论：');
  console.log('  - highWaterMark 小 → 背压频繁，内存省但 pause/resume 开销大');
  console.log('  - highWaterMark 大 → 背压少，吞吐高但内存占用高');
  console.log('  - 生产代码优先用 pipe / pipeline，背压全自动，避免手动处理的遗漏');
})();
