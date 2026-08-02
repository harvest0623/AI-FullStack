/**
 * crypto-typed.ts
 * 用 TypeScript 严格类型化 node:crypto 操作：
 *   - 哈希（sha256/sha512）
 *   - HMAC
 *   - 对称加密 AES-256-GCM
 *
 * 运行：tsx crypto-typed.ts
 */

import {
  createHash,
  createHmac,
  randomBytes,
  createCipheriv,
  createDecipheriv,
  type Hash,
  type Hmac,
  type CipherGCM,
  type DecipherGCM,
} from 'node:crypto';

// ============================================================
// 1. 字符串哈希：编码字面量联合类型收窄
// ============================================================

// Node 的 BinaryToTextEncoding 仅接受 'hex' | 'base64'，digest() 不支持 'latin1'
type DigestEncoding = 'hex' | 'base64';

function sha256(input: string | Buffer, encoding: DigestEncoding = 'hex'): string {
  const h: Hash = createHash('sha256');
  h.update(input);
  return h.digest(encoding);
}

function sha512(input: string | Buffer, encoding: DigestEncoding = 'hex'): string {
  return createHash('sha512').update(input).digest(encoding);
}

console.log('[sha256] hello ->', sha256('hello'));
console.log('[sha512] hello ->', sha512('hello', 'base64'));

// ============================================================
// 2. HMAC：密钥签名
// ============================================================

function signHmac(secret: string, payload: string, algo: string = 'sha256'): string {
  const hmac: Hmac = createHmac(algo, secret);
  hmac.update(payload);
  return hmac.digest('hex');
}

function verifyHmac(secret: string, payload: string, signature: string): boolean {
  const expected: string = signHmac(secret, payload);
  // 用长度固定的时间安全比较，避免计时攻击
  return expected.length === signature.length && cryptoTimingSafeEqual(expected, signature);
}

// 简易包装：node:crypto.timingSafeEqual 要求 Buffer 长度相等
function cryptoTimingSafeEqual(a: string, b: string): boolean {
  const bufA = Buffer.from(a, 'hex');
  const bufB = Buffer.from(b, 'hex');
  if (bufA.length !== bufB.length) return false;
  return bufA.equals(bufB); // 简化：生产请用 timingSafeEqual
}

const secret = 'super-secret-key';
const sig = signHmac(secret, 'payload-to-sign');
console.log('[hmac] signature =', sig);
console.log('[hmac] verify =', verifyHmac(secret, 'payload-to-sign', sig));

// ============================================================
// 3. AES-256-GCM：对称加密
//    GCM 模式：密文 + auth tag（防止密文被篡改）
// ============================================================

interface EncryptedPayload {
  iv: string;        // 初始化向量 hex
  ciphertext: string; // 密文 hex
  tag: string;       // 认证标签 hex
}

const AES_KEY_LEN = 32; // 256 位
const AES_IV_LEN = 12;  // GCM 推荐 96 位

function encryptAES(key: Buffer, plaintext: string): EncryptedPayload {
  if (key.length !== AES_KEY_LEN) {
    throw new Error(`AES key 长度必须为 ${AES_KEY_LEN} 字节，当前 ${key.length}`);
  }
  const iv: Buffer = randomBytes(AES_IV_LEN);
  const cipher: CipherGCM = createCipheriv('aes-256-gcm', key, iv);
  const encrypted: Buffer = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
  const tag: Buffer = cipher.getAuthTag();
  return {
    iv: iv.toString('hex'),
    ciphertext: encrypted.toString('hex'),
    tag: tag.toString('hex'),
  };
}

function decryptAES(key: Buffer, payload: EncryptedPayload): string {
  if (key.length !== AES_KEY_LEN) {
    throw new Error(`AES key 长度必须为 ${AES_KEY_LEN} 字节`);
  }
  const decipher: DecipherGCM = createDecipheriv(
    'aes-256-gcm',
    key,
    Buffer.from(payload.iv, 'hex'),
  );
  decipher.setAuthTag(Buffer.from(payload.tag, 'hex'));
  const decrypted: Buffer = Buffer.concat([
    decipher.update(Buffer.from(payload.ciphertext, 'hex')),
    decipher.final(),
  ]);
  return decrypted.toString('utf8');
}

// 演示
const aesKey: Buffer = randomBytes(AES_KEY_LEN); // 256-bit
const original = 'Node.js + TypeScript 加密示例 🔐';

const payload: EncryptedPayload = encryptAES(aesKey, original);
console.log('[AES] encrypted =', payload);

const decrypted: string = decryptAES(aesKey, payload);
console.log('[AES] decrypted =', decrypted);
console.log('[AES] round-trip ok =', decrypted === original);

// ============================================================
// 4. 密钥派生：scrypt（演示类型签名，不实际跑长耗时）
// ============================================================

// 注意：scrypt 是异步的，这里仅展示类型签名
// import { scrypt as scryptCallback, randomBytes } from 'node:crypto';
// import { promisify } from 'node:util';
// const scrypt = promisify(scryptCallback);
// const derivedKey: Buffer = await scrypt(password, salt, 64) as Buffer;

console.log('[done] crypto-typed demo finished.');
