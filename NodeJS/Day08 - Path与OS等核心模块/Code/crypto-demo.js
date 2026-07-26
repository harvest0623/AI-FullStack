// Day08 - crypto 模块演示
// 主题：sha256 哈希、HMAC 签名、randomBytes/randomInt/randomUUID、AES-256-GCM 完整加解密
// 运行：node Code/crypto-demo.js
//
// 安全说明：
//  - KEY 在此为演示随机生成；生产环境应从环境变量/KMS/Secret Manager 读取，不要硬编码
//  - AES-GCM 的 IV（nonce）每次必须随机，且不可重复使用同一对 (KEY, IV)
//  - 密文必须连同 IV 与 authTag 一起保存，三者缺一不可解密
//  - 密码哈希请用 bcrypt/scrypt/argon2，不要直接 sha256

const crypto = require('crypto');

console.log('========================================');
console.log(' Day08 - crypto 模块演示');
console.log('========================================\n');

// ---------------------------------------------------------------
// 1. 哈希：createHash
// ---------------------------------------------------------------
console.log('--- 1. createHash：单向指纹 ---');

// 单次 update
const sha256 = crypto.createHash('sha256').update('hello world').digest('hex');
console.log(`  sha256('hello world') = ${sha256}`);
console.log(`  长度：${sha256.length} 个十六进制字符 = ${sha256.length * 4} bit\n`);

// 分块 update（流式场景）
const h = crypto.createHash('sha256');
h.update('hello');
h.update(' ');
h.update('world');
console.log(`  分块 update 等价：${h.digest('hex') === sha256}`);

// 对比不同算法
const md5 = crypto.createHash('md5').update('hello world').digest('hex');
const sha1 = crypto.createHash('sha1').update('hello world').digest('hex');
const sha512 = crypto.createHash('sha512').update('hello world').digest('hex');
console.log(`  md5    = ${md5}    ⚠️ 已不安全，仅兼容老系统`);
console.log(`  sha1   = ${sha1}    ⚠️ 已弱化`);
console.log(`  sha512 = ${sha512.slice(0, 32)}...(共 ${sha512.length} 字符)`);

// 文件指纹用途演示
const fileContent = 'some-large-file-content-to-dedup...';
const fingerprint = crypto.createHash('sha256').update(fileContent).digest('hex');
console.log(`\n  文件内容指纹（去重 key）：${fingerprint}`);

// ---------------------------------------------------------------
// 2. HMAC：带密钥的签名
// ---------------------------------------------------------------
console.log('\n--- 2. createHmac：带密钥签名 ---');

const secret = 'my-webhook-secret';
function sign(message, key) {
  return crypto.createHmac('sha256', key).update(message).digest('hex');
}

const message = `{"event":"push","ts":1700000000}`;
const signature = sign(message, secret);
console.log(`  message  = ${message}`);
console.log(`  secret    = ${secret}`);
console.log(`  signature = ${signature}`);

// 模拟接收方校验
const received = signature === sign(message, secret);
console.log(`  接收方校验：${received ? '✅ 通过' : '❌ 不通过'}`);

// 模拟篡改检测
const tampered = signature === sign(message + 'x', secret);
console.log(`  篡改后校验：${tampered ? '✅' : '❌ 不通过（被检测）'}`);

// ---------------------------------------------------------------
// 3. 随机数：randomBytes / randomInt / randomUUID
// ---------------------------------------------------------------
console.log('\n--- 3. crypto 随机数（密码学安全）---');

// 16 字节随机数据，可用于 token / IV / salt
const token = crypto.randomBytes(16).toString('hex');
console.log(`  randomBytes(16) → ${token}（${token.length} 字符 hex）`);

// 随机整数（含 min 不含 max）
const dice = crypto.randomInt(1, 7);
console.log(`  randomInt(1, 7) → ${dice}（掷骰子）`);

// 0~255 随机字节
const byte = crypto.randomInt(256);
console.log(`  randomInt(256) → ${byte}`);

// UUID v4
const uuid = crypto.randomUUID();
console.log(`  randomUUID() → ${uuid}`);

console.log(`\n  ⚠️ Math.random() 不安全，绝不能用于生成 token/密钥/nonce`);

// ---------------------------------------------------------------
// 4. AES-256-GCM 对称加解密
// ---------------------------------------------------------------
console.log('\n--- 4. AES-256-GCM 加解密 ---');

// 演示用：生成一次 KEY，实际项目应从安全存储读取
const KEY = crypto.randomBytes(32);  // 32 字节 = 256 bit
console.log(`  KEY（演示随机生成，${KEY.length} 字节）：${KEY.toString('hex').slice(0, 16)}...`);

/**
 * AES-256-GCM 加密
 * @param {string} plainText 明文
 * @returns {{iv: string, enc: string, authTag: string}} 三件套（hex）
 */
function encrypt(plainText) {
  const iv = crypto.randomBytes(12);                  // GCM 推荐 12 字节 IV
  const cipher = crypto.createCipheriv('aes-256-gcm', KEY, iv);
  const enc = Buffer.concat([
    cipher.update(plainText, 'utf8'),
    cipher.final(),
  ]);
  const authTag = cipher.getAuthTag();                 // 16 字节认证标签
  return {
    iv: iv.toString('hex'),
    enc: enc.toString('hex'),
    authTag: authTag.toString('hex'),
  };
}

/**
 * AES-256-GCM 解密
 * @param {{iv: string, enc: string, authTag: string}} payload 三件套
 * @returns {string} 明文
 */
function decrypt({ iv, enc, authTag }) {
  const decipher = crypto.createDecipheriv(
    'aes-256-gcm',
    KEY,
    Buffer.from(iv, 'hex')
  );
  decipher.setAuthTag(Buffer.from(authTag, 'hex'));   // 必须设置，否则解密失败
  const dec = Buffer.concat([
    decipher.update(Buffer.from(enc, 'hex')),
    decipher.final(),                                 // 这里校验 authTag，不匹配会抛 AEAD_BAD_TAG
  ]);
  return dec.toString('utf8');
}

// 演示加密一条 API key
const apiKey = 'sk-proj-1234567890abcdefghijklmnopqrstuvwxyz';
console.log(`\n  原文（API key）：${apiKey}`);

const encrypted = encrypt(apiKey);
console.log(`  加密结果：`);
console.log(`     iv      = ${encrypted.iv}`);
console.log(`     enc     = ${encrypted.enc}`);
console.log(`     authTag = ${encrypted.authTag}`);

const decrypted = decrypt(encrypted);
console.log(`  解密结果：${decrypted}`);
console.log(`  往返一致：${decrypted === apiKey ? '✅ 是' : '❌ 否'}`);

// 篡改检测：改一个字节的密文，验证 authTag 校验
console.log('\n  篡改检测：把密文最后一个字节 +1');
const tamperedEnc = Buffer.from(encrypted.enc, 'hex');
tamperedEnc[tamperedEnc.length - 1] ^= 0x01;   // 翻转最后一位
const tamperedPayload = { ...encrypted, enc: tamperedEnc.toString('hex') };
try {
  decrypt(tamperedPayload);
  console.log('  ❌ 异常：篡改后居然能解密');
} catch (err) {
  console.log(`  ✅ 预期抛错：${err.message}`);
  console.log('  ← GCM 自带认证，密文被改一字节都会被检测到');
}

// ---------------------------------------------------------------
// 5. 实战：API key 加密存储模拟
// ---------------------------------------------------------------
console.log('\n--- 5. 实战：API key 加密存储 ---');

const STORED_KEY_HEX = KEY.toString('hex');   // 模拟存到环境变量的主密钥
const secrets = [];

function storeSecret(secret) {
  const enc = encrypt(secret);
  secrets.push(enc);
  return enc;
}

function loadSecret(payload) {
  const k = Buffer.from(STORED_KEY_HEX, 'hex');
  const decipher = crypto.createDecipheriv('aes-256-gcm', k, Buffer.from(payload.iv, 'hex'));
  decipher.setAuthTag(Buffer.from(payload.authTag, 'hex'));
  const dec = Buffer.concat([
    decipher.update(Buffer.from(payload.enc, 'hex')),
    decipher.final(),
  ]);
  return dec.toString('utf8');
}

storeSecret('sk-openai-abc123');
storeSecret('sk-anthropic-xyz789');
storeSecret('postgresql://user:pwd@db:5432/prod');

console.log(`  已存 ${secrets.length} 条敏感信息（密文）：`);
secrets.forEach((s, i) => console.log(`    [${i}] enc=${s.enc.slice(0, 16)}...`));

console.log('\n  反解密验证：');
secrets.forEach((s, i) => {
  console.log(`    [${i}] ${loadSecret(s)}`);
});

// ---------------------------------------------------------------
console.log('\n=== 要点回顾 ===');
console.log('  1. createHash 一次性 update + digest；digest 只能调一次；');
console.log('  2. HMAC 需要密钥，验证"消息来自持密钥者"；');
console.log('  3. Math.random() 不安全，token/nonce 用 randomBytes/randomUUID；');
console.log('  4. AES-256-GCM 三件套：iv + enc + authTag 必须一起保存；');
console.log('  5. IV 每次必须随机，绝不能重复使用同一对 (KEY, IV)；');
console.log('  6. 密码哈希请用 bcrypt/scrypt/argon2，不要直接 sha256。');
