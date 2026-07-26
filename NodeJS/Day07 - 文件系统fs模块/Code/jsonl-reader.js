'use strict';

/**
 * Day07 - JSONL 文件逐行读取与解析
 * 主题：readline + createReadStream 逐行读取 .jsonl，模拟处理 AI 训练数据
 * 运行：node jsonl-reader.js
 *
 * 演示要点：
 *   1. 生成一份模拟的 AI 训练数据 .jsonl 文件（每行一个 JSON 对象）
 *   2. 用 readline 逐行读取，避免把整个文件载入内存
 *   3. 逐行 JSON.parse，统计总行数与所有 prompt 字段
 *   4. 容错处理：跳过空行、捕获 JSON 解析失败
 *   5. 演示“错误行收集”与“正常行处理”两条路径
 *
 * 为什么用 readline 而不是 readFile + split('\n')？
 *   - readFile 会把整个文件读进内存，10GB 训练集直接 OOM
 *   - readline 基于 createReadStream，按行产出，内存恒定
 *   - 自动处理跨块换行（一行可能被切到两个 chunk 里）
 */

const fs = require('fs');
const fsp = require('fs/promises');
const readline = require('readline');
const path = require('path');

const workDir = path.join(__dirname, 'jsonl-workspace');
const dataFile = path.join(workDir, 'train.jsonl');

// ---------------------------------------------------------------
// 步骤 1：生成模拟训练数据
// 每行形如：{"id":1,"prompt":"你好","answer":"你好，有什么可以帮你？"}
// 故意混入几行“坏数据”（空行、非 JSON、缺字段）演示容错
// ---------------------------------------------------------------
async function generateJsonl() {
  console.log('[1] 生成模拟训练数据 .jsonl');
  await fsp.mkdir(workDir, { recursive: true });

  const samples = [
    { id: 1, prompt: '你好', answer: '你好，有什么可以帮你？' },
    { id: 2, prompt: '介绍一下 Node.js', answer: 'Node.js 是基于 V8 的 JavaScript 运行时。' },
    { id: 3, prompt: '什么是 fs 模块', answer: 'fs 是 Node.js 的文件系统模块。' },
    '',                                  // 空行（应跳过）
    'this is not a json line',           // 非 JSON（应报错并收集）
    { id: 4, prompt: 'Promise 是什么', answer: 'Promise 是异步编程的一种容器。' },
    { id: 5, answer: '缺 prompt 字段的行' }, // 缺字段（按业务规则处理）
    { id: 6, prompt: 'readline 怎么用', answer: '用 readline.createInterface 包装 ReadStream。' },
    '{ "id": 7, "broken": ',             // 截断的 JSON（应报错并收集）
    { id: 8, prompt: '大文件怎么读', answer: '用 createReadStream 配合 readline 逐行读。' },
    { id: 9, prompt: '原子写入', answer: '先写临时文件再 rename。' },
    { id: 10, prompt: '什么是背压', answer: '背压是流处理中下游反压上游的机制。' }
  ];

  const lines = samples.map(s =>
    typeof s === 'string' ? s : JSON.stringify(s)
  );
  await fsp.writeFile(dataFile, lines.join('\n') + '\n', 'utf8');

  const st = await fsp.stat(dataFile);
  console.log(`  已生成: ${path.basename(dataFile)} (${st.size} bytes, ${lines.length} 行)\n`);
}

// ---------------------------------------------------------------
// 步骤 2：用 readline 逐行读取并解析
// 这是处理 AI 训练数据的标准姿势
// ---------------------------------------------------------------
async function readAndParse() {
  console.log('[2] readline 逐行读取并解析');

  // createInterface 接收一个 ReadStream，按行产出
  // 注意 crlfDelay: Infinity 兼容 \r\n 与 \n 混用
  const rl = readline.createInterface({
    input: fs.createReadStream(dataFile, { encoding: 'utf8' }),
    crlfDelay: Infinity
  });

  let total = 0;          // 总行数（含空行、坏行）
  let valid = 0;          // 成功解析的 JSON 行数
  let skipped = 0;        // 空行数
  const prompts = [];     // 收集所有 prompt 字段
  const errors = [];      // 收集坏行的行号与原因
  let lineNo = 0;

  // 'line' 事件每读出一行触发一次（已去除换行符）
  for await (const line of rl) {
    lineNo++;
    total++;

    // ① 容错：跳过空行与纯空白行
    if (!line.trim()) {
      skipped++;
      continue;
    }

    // ② 容错：JSON.parse 可能抛错，用 try/catch 包裹
    let obj;
    try {
      obj = JSON.parse(line);
    } catch (err) {
      errors.push({ lineNo, reason: 'JSON 解析失败', raw: line.slice(0, 60) });
      continue;
    }

    // ③ 业务规则：必须有 prompt 字段才算“有效训练样本”
    if (typeof obj.prompt !== 'string') {
      errors.push({ lineNo, reason: '缺少 prompt 字段', raw: line.slice(0, 60) });
      continue;
    }

    valid++;
    prompts.push(obj.prompt);
    // 实际场景这里会做：分词、向量化、写入训练集等
  }

  console.log(`  总行数      : ${total}`);
  console.log(`  有效样本    : ${valid}`);
  console.log(`  空行跳过    : ${skipped}`);
  console.log(`  错误行数    : ${errors.length}`);
  console.log('  收集到的 prompt:');
  for (const p of prompts) {
    console.log('    -', p);
  }
  if (errors.length) {
    console.log('  错误行详情:');
    for (const e of errors) {
      console.log(`    第 ${e.lineNo} 行 [${e.reason}]: ${e.raw}`);
    }
  }
  console.log('');
  return { total, valid, skipped, errors: errors.length };
}

// ---------------------------------------------------------------
// 步骤 3（附加）：把处理结果写成新的 .jsonl（保留有效样本）
// 演示“读取 -> 处理 -> 写入”完整流水线
// ---------------------------------------------------------------
async function writeCleanedJsonl(stats) {
  console.log('[3] 把有效样本写入新 .jsonl 文件');
  const outFile = path.join(workDir, 'train-clean.jsonl');

  const rl = readline.createInterface({
    input: fs.createReadStream(dataFile, { encoding: 'utf8' }),
    crlfDelay: Infinity
  });

  const ws = fs.createWriteStream(outFile, { encoding: 'utf8' });
  let written = 0;
  for await (const line of rl) {
    if (!line.trim()) continue;
    try {
      const obj = JSON.parse(line);
      if (typeof obj.prompt === 'string') {
        // 每写一行就换行；可换成更紧凑的 JSON.stringify
        ws.write(JSON.stringify(obj) + '\n');
        written++;
      }
    } catch {
      // 跳过坏行
    }
  }
  await new Promise(resolve => ws.end(resolve));

  const st = await fsp.stat(outFile);
  console.log(`  已写入: ${path.basename(outFile)} (${st.size} bytes, ${written} 行)\n`);
}

// ---------------------------------------------------------------
// 清理：删除工作目录
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
    await generateJsonl();
    const stats = await readAndParse();
    await writeCleanedJsonl(stats);
  } catch (err) {
    console.error('主流程出错:', err.code, '-', err.message);
  } finally {
    await cleanup();
    console.log('=== 结论 ===');
    console.log('1. 处理大 .jsonl 文件用 readline + createReadStream，');
    console.log('   逐行产出，内存占用恒定，不会 OOM。');
    console.log('2. 每行 JSON.parse 都要 try/catch，避免单行损坏导致整个流程崩溃。');
    console.log('3. 用 for await (const line of rl) 是最简洁的逐行消费写法；');
    console.log('   也可用 rl.on(\'line\', cb) 事件式写法。');
    console.log('4. AI 场景：训练数据通常几 GB 到几十 GB，');
    console.log('   流式逐行解析 + 批量向量化 + 落盘是标准 ETL 流水线。');
  }
})();
