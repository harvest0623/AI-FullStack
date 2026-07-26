'use strict';

/**
 * Day06 - 自定义 Transform 流演示
 * 主题：用 pipe 链接 Readable → Transform → Writable
 * 运行：node transform-stream.js
 *
 * 流水线：日志源 → [加前缀 Transform] → [转大写 Transform] → 控制台输出
 */

const { Readable, Writable, Transform } = require('stream');

// ---------------------------------------------------------------
// 1. 自定义 Readable：日志源
// ---------------------------------------------------------------
class LogSource extends Readable {
  constructor(lines, options) {
    super(options);
    this.lines = lines;
    this.index = 0;
  }
  _read() {
    if (this.index >= this.lines.length) {
      this.push(null);
      return;
    }
    this.push(Buffer.from(`${this.lines[this.index]}\n`, 'utf8'));
    this.index++;
  }
}

// ---------------------------------------------------------------
// 2. 自定义 Transform A：给每行加前缀
// 实现 _transform(chunk, encoding, callback)
// 处理完后调用 callback(err, transformedChunk) 把数据推到读端
// ---------------------------------------------------------------
class PrefixTransform extends Transform {
  constructor(prefix, options) {
    super(options);
    this.prefix = prefix;
  }
  _transform(chunk, encoding, callback) {
    // chunk 是 Buffer，转成字符串加前缀后推送
    const text = chunk.toString('utf8');
    // 注意：流式数据可能把一行切成多个 chunk，这里简化处理（每 chunk 加前缀）
    const prefixed = `${this.prefix}${text}`;
    callback(null, Buffer.from(prefixed, 'utf8'));
  }
}

// ---------------------------------------------------------------
// 3. 自定义 Transform B：转大写
// ---------------------------------------------------------------
class UpperTransform extends Transform {
  _transform(chunk, encoding, callback) {
    callback(null, Buffer.from(chunk.toString('utf8').toUpperCase(), 'utf8'));
  }
}

// ---------------------------------------------------------------
// 4. 自定义 Writable：写到控制台
// 实现 _write(chunk, encoding, callback)，处理完必须调 callback()
// ---------------------------------------------------------------
class ConsoleSink extends Writable {
  _write(chunk, encoding, callback) {
    process.stdout.write(chunk);
    callback(); // 不调 callback 流会卡住
  }
  _final(callback) {
    process.stdout.write('--- 流水线结束 ---\n');
    callback();
  }
}

// ---------------------------------------------------------------
// 5. 用 pipe 串联：Readable → Transform → Transform → Writable
// pipe 内部已处理背压
// ---------------------------------------------------------------
function pipeChainDemo() {
  console.log('=== Transform 流 pipe 链演示 ===\n');

  const source = new LogSource([
    'user logged in',
    'model loaded',
    'inference started',
    'response sent',
  ]);

  const addPrefix = new PrefixTransform('[LOG] ');
  const toUpper = new UpperTransform();
  const sink = new ConsoleSink();

  // 管道链：每个 pipe 返回目标流，可以链式调用
  source
    .pipe(addPrefix)
    .pipe(toUpper)
    .pipe(sink);

  // 注意：pipe 不传播错误！每个流要单独监听 'error'
  // 这正是 pipeline 的优势（见 pipeline-demo.js）
  source.on('error', err => console.error('源错误:', err.message));
  addPrefix.on('error', err => console.error('前缀流错误:', err.message));
  toUpper.on('error', err => console.error('大写流错误:', err.message));
  sink.on('error', err => console.error('输出流错误:', err.message));

  sink.on('finish', () => {
    console.log('\n（pipe 链完成，finish 事件触发）\n');
    transformWithObjectMode();
  });
}

// ---------------------------------------------------------------
// 6. 对象模式 Transform：把字符串 chunk 解析成对象再加工
// 适合“解析 → 变换”场景（如 JSON 行解析、日志结构化）
// ---------------------------------------------------------------
class ParseLineTransform extends Transform {
  constructor(options) {
    // 对象模式：push 的可以是任意 JS 对象，不限于 Buffer/string
    super({ ...options, objectMode: true });
  }
  _transform(chunk, encoding, callback) {
    const text = chunk.toString('utf8').trim();
    if (text) {
      // 把每行解析成结构化对象
      callback(null, { raw: text, length: text.length, ts: Date.now() });
    } else {
      callback();
    }
  }
}

class FormatObjectTransform extends Transform {
  constructor(options) {
    // 输入是对象（objectMode），输出是 Buffer（非 objectMode）
    super({ ...options, readableObjectMode: false, writableObjectMode: true });
  }
  _transform(obj, encoding, callback) {
    const line = `→ ${obj.raw} (${obj.length} 字符 @ ${obj.ts})\n`;
    callback(null, Buffer.from(line, 'utf8'));
  }
}

function transformWithObjectMode() {
  console.log('=== 对象模式 Transform（解析 → 格式化）===\n');

  const source = new LogSource(['hello world', '你好 世界', 'stream is fun']);
  const parser = new ParseLineTransform();
  const formatter = new FormatObjectTransform();
  const sink = new ConsoleSink();

  source.pipe(parser).pipe(formatter).pipe(sink);

  sink.on('finish', () => {
    console.log('\n✅ Transform 流演示完成');
  });
}

pipeChainDemo();
