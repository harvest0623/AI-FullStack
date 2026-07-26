'use strict';

/**
 * Day06 - Buffer 基础演示
 * 主题：创建方式、编码转换、中文处理、concat、subarray 共享内存 vs slice 拷贝
 * 运行：node buffer-basic.js
 */

// ---------------------------------------------------------------
// 1. 四种创建方式：alloc / allocUnsafe / from / concat
// ---------------------------------------------------------------
console.log('=== 1. Buffer 创建方式 ===');

// 1.1 alloc：分配并清零，安全
const a = Buffer.alloc(8);
console.log('alloc(8)               →', a);                  // 全是 0
const aFill = Buffer.alloc(8, 0xff);
console.log('alloc(8, 0xff)         →', aFill);              // 全是 255

// 1.2 allocUnsafe：分配不清零，可能残留旧数据（这里可能看到随机字节）
const unsafe = Buffer.allocUnsafe(8);
console.log('allocUnsafe(8)         →', unsafe, '（内容可能非零，需手动清零）');
unsafe.fill(0); // 手动清零后等价于 alloc
console.log('allocUnsafe 清零后      →', unsafe);

// 1.3 from：从字符串 / 数组 / 另一个 Buffer 创建
const fromStr = Buffer.from('Hi', 'utf8');
console.log("from('Hi','utf8')      →", fromStr, '→', fromStr.toString());
const fromArr = Buffer.from([72, 105]);
console.log('from([72,105])         →', fromArr, '→', fromArr.toString());
const fromCopy = Buffer.from(fromStr); // 从 Buffer 创建是拷贝
console.log('from(buffer) 拷贝       →', fromCopy, '=== 原?', fromCopy === fromStr);

// ---------------------------------------------------------------
// 2. Buffer 与 ArrayBuffer / Uint8Array 的关系
// ---------------------------------------------------------------
console.log('\n=== 2. Buffer 是 Uint8Array 的子类 ===');
const buf = Buffer.from('hello');
console.log('buf instanceof Uint8Array →', buf instanceof Uint8Array);   // true
console.log('buf instanceof Buffer     →', buf instanceof Buffer);       // true

// Buffer 与 ArrayBuffer 共享内存（零拷贝）
const ab = new ArrayBuffer(4);
const view = new Uint8Array(ab);
view[0] = 65; // 'A'
const bufFromAb = Buffer.from(ab); // 共享底层 ArrayBuffer
console.log('\n共享内存验证：');
console.log('  修改 view[0] = 65 后，bufFromAb →', bufFromAb); // <Buffer 41 00 00 00>
bufFromAb[1] = 66; // 修改 Buffer
console.log('  修改 bufFromAb[1] = 66 后，view →', view);     // Uint8Array [ 65, 66, 0, 0 ]

// ---------------------------------------------------------------
// 3. 编码转换：utf8 / base64 / hex / latin1 / ascii
// ---------------------------------------------------------------
console.log('\n=== 3. 编码转换 ===');
const text = 'A';
const b = Buffer.from(text, 'utf8');
console.log(`原字符串 '${text}'`);
console.log('  utf8    →', b.toString('utf8'));     // A
console.log('  base64  →', b.toString('base64'));  // QQ==
console.log('  hex     →', b.toString('hex'));     // 41
console.log('  latin1  →', b.toString('latin1'));  // A
console.log('  ascii   →', b.toString('ascii'));   // A

// base64 / hex 还原
console.log('  base64 还原 →', Buffer.from('QQ==', 'base64').toString('utf8')); // A
console.log('  hex    还原 →', Buffer.from('41', 'hex').toString('utf8'));      // A

// ---------------------------------------------------------------
// 4. 中文场景：UTF-8 下一个汉字占 3 字节
// ---------------------------------------------------------------
console.log('\n=== 4. 中文处理（UTF-8 每字 3 字节）===');
const zh = Buffer.from('你好世界', 'utf8');
console.log(`'你好世界' 字符数 = 4，但 Buffer.length = ${zh.length}（4 × 3 字节）`);

// 4.1 按字节切会切断汉字 → 乱码
const broken = zh.subarray(0, 1).toString('utf8');
console.log('subarray(0,1).toString() →', JSON.stringify(broken), '（半个“你”，乱码）');

// 4.2 按 3 字节切才能拿到完整汉字
const firstChar = zh.subarray(0, 3).toString('utf8');
console.log('subarray(0,3).toString() →', firstChar, '（完整“你”）');

// 4.3 逐字遍历的正确姿势：用 for...of 按码点
console.log('逐字遍历：');
for (const ch of '你好世界') {
  const c = Buffer.from(ch, 'utf8');
  console.log(`  '${ch}' → ${c.length} 字节, hex=${c.toString('hex')}`);
}

// 4.4 用 TextDecoder 的 stream 模式安全解码跨 chunk 的中文
console.log('\nTextDecoder stream 模式（模拟流式跨 chunk）：');
const decoder = new TextDecoder('utf-8');
// 把“你好”拆成 [0,2) 和 [2,6) 两段，第一段刚好切断“你”
const part1 = zh.subarray(0, 2);
const part2 = zh.subarray(2, 6);
const out1 = decoder.decode(part1, { stream: true }); // 不完整，留到下一轮
const out2 = decoder.decode(part2, { stream: true });
console.log(`  part1(0-2) 流式解码 → ${JSON.stringify(out1)}（暂存不完整字节）`);
console.log(`  part2(2-6) 流式解码 → ${JSON.stringify(out2)}（拼出完整汉字）`);

// ---------------------------------------------------------------
// 5. Buffer.concat 拼接
// ---------------------------------------------------------------
console.log('\n=== 5. Buffer.concat 拼接 ===');
const parts = [Buffer.from('你好'), Buffer.from('，'), Buffer.from('AI 全栈')];
const merged = Buffer.concat(parts);
console.log('concat 结果 →', merged.toString('utf8'));
console.log('总字节数    →', merged.length);

// 5.1 显式传入 totalLength 的性能对比
const bigParts = Array.from({ length: 1000 }, (_, i) => Buffer.from(`chunk${i};`));

console.time('concat 不传 totalLength');
for (let i = 0; i < 1000; i++) Buffer.concat(bigParts);
console.timeEnd('concat 不传 totalLength');

const total = bigParts.reduce((s, p) => s + p.length, 0);
console.time('concat 传 totalLength');
for (let i = 0; i < 1000; i++) Buffer.concat(bigParts, total);
console.timeEnd('concat 传 totalLength');
console.log('（传入 totalLength 可一次分配到位，避免动态扩容）');

// ---------------------------------------------------------------
// 6. 零拷贝验证：subarray 共享内存 vs slice 拷贝
// ---------------------------------------------------------------
console.log('\n=== 6. subarray 共享内存 vs slice 拷贝 ===');
const parent = Buffer.from('hello world');
console.log('原 Buffer →', parent.toString());

// 6.1 subarray：共享内存，修改切片会影响原 Buffer
const sub = parent.subarray(0, 5);
console.log('subarray(0,5) →', sub.toString());
sub[0] = 72; // 'H' 的 ASCII
console.log(`  修改 sub[0]=72 后，原 Buffer → "${parent.toString()}"（被修改！）`);
console.log(`  sub.buffer === parent.buffer? ${sub.buffer === parent.buffer}（共享底层 ArrayBuffer）`);

// 重置
parent[0] = 104; // 'h'

// 6.2 slice：拷贝，修改切片不影响原 Buffer
const sl = parent.slice(0, 5);
console.log('slice(0,5) →', sl.toString());
sl[0] = 72; // 'H'
console.log(`  修改 sl[0]=72 后，原 Buffer → "${parent.toString()}"（未变，拷贝）`);
console.log(`  sl.buffer === parent.buffer? ${sl.buffer === parent.buffer}（独立 ArrayBuffer）`);

// 6.3 字节级验证：subarray 的 byteOffset 指向原 Buffer
const offset = Buffer.from('0123456789');
const mid = offset.subarray(3, 6); // '345'
console.log('\nbyteOffset 验证：');
console.log(`  原 Buffer[3..6) = "${mid.toString()}"`);
console.log(`  mid.byteOffset = ${mid.byteOffset}（指向原 Buffer 偏移 3，零拷贝）`);

console.log('\n✅ Buffer 基础演示完成');
