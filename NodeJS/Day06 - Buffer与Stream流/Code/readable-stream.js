'use strict';

/**
 * Day06 - 自定义 Readable 流演示
 * 主题：两种消费方式对比 —— 'data'/'end' 事件 vs for await...of 迭代
 * 运行：node readable-stream.js
 */

const { Readable } = require('stream');

// ---------------------------------------------------------------
// 自定义 Readable：模拟一个“逐行生成日志”的数据源
// 实现 _read(size)，在其中 push 数据；push(null) 表示结束
// ---------------------------------------------------------------
class LogSource extends Readable {
  constructor(lines, options) {
    // 显式声明 objectMode=false（默认），数据是 Buffer/string
    super({ ...options, objectMode: false });
    this.lines = lines;
    this.index = 0;
  }

  _read() {
    // 模拟异步：用 process.nextTick 让出一次事件循环
    process.nextTick(() => {
      if (this.index >= this.lines.length) {
        this.push(null); // 结束信号
        return;
      }
      const line = `[${this.index}] ${this.lines[this.index]}\n`;
      this.push(Buffer.from(line, 'utf8')); // 推送一块 Buffer
      this.index++;
    });
  }
}

// 准备测试数据
const sampleLines = [
  '应用启动完成',
  '已加载模型 gpt-4-mini',
  '收到用户请求 #1',
  '推理耗时 230ms',
  '响应已返回',
];

// ---------------------------------------------------------------
// 方式一：flowing 模式 —— 监听 'data' / 'end' 事件
// 监听 'data' 后流自动进入 flowing 模式，数据主动推送
// ---------------------------------------------------------------
function consumeWithEvents() {
  console.log('--- 方式一：data/end 事件消费（flowing 模式）---');
  const source = new LogSource(sampleLines);
  let chunkCount = 0;

  source.on('data', (chunk) => {
    chunkCount++;
    // chunk 是 Buffer
    process.stdout.write(`  [chunk ${chunkCount}] ${chunk.length} 字节: ${chunk.toString().trim()}\n`);
  });

  source.on('end', () => {
    console.log(`  → 共收到 ${chunkCount} 个 chunk，流结束（'end' 触发）\n`);
    consumeWithForAwait(); // 串行触发方式二
  });

  source.on('error', (err) => {
    console.error('  流错误:', err.message);
  });
}

// ---------------------------------------------------------------
// 方式二：异步迭代 —— for await...of
// 天然串行 + 背压 + try/catch，比 'data' 事件更安全
// ---------------------------------------------------------------
async function consumeWithForAwait() {
  console.log('--- 方式二：for await...of 异步迭代消费 ---');
  const source = new LogSource(sampleLines);
  let chunkCount = 0;

  try {
    for await (const chunk of source) {
      chunkCount++;
      // 可以在循环体内 await 任何异步操作，流会自动暂停（天然背压）
      process.stdout.write(`  [chunk ${chunkCount}] ${chunk.length} 字节: ${chunk.toString().trim()}\n`);
      // 模拟异步处理：每个 chunk 处理 10ms
      await new Promise(r => setTimeout(r, 10));
    }
    console.log(`  → 共收到 ${chunkCount} 个 chunk，迭代自然结束\n`);
  } catch (err) {
    console.error('  迭代错误:', err.message);
  }

  pausedModeDemo();
}

// ---------------------------------------------------------------
// 附加：paused 模式 —— 'readable' + read() 手动拉取
// ---------------------------------------------------------------
function pausedModeDemo() {
  console.log('--- 附加：paused 模式（readable + read 手动拉取）---');
  const source = new LogSource(['第一行', '第二行', '第三行']);
  let total = 0;

  source.on('readable', () => {
    let chunk;
    // 主动调用 read() 拉取，返回 null 表示当前没有更多数据（但不代表结束）
    while ((chunk = source.read()) !== null) {
      total++;
      process.stdout.write(`  手动拉取 ${chunk.length} 字节: ${chunk.toString().trim()}\n`);
    }
  });

  source.on('end', () => {
    console.log(`  → paused 模式共拉取 ${total} 个 chunk\n✅ Readable 流演示完成`);
  });
}

// 启动
consumeWithEvents();
