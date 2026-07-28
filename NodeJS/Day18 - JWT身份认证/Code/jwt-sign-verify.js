/**
 * jwt-sign-verify.js
 * Day18 - JWT 身份认证
 *
 * 演示 jsonwebtoken 的核心 API：
 *  - jwt.sign(payload, secret, options)   签发 token
 *  - jwt.verify(token, secret, options)   校验并解析 token
 *  - jwt.decode(token)                    仅解码不验签
 *  - payload 常用字段：sub / iat / exp / iss / aud / jti
 *  - 三类错误：TokenExpiredError / JsonWebTokenError / NotBeforeError
 *
 * 运行：node jwt-sign-verify.js
 */

const jwt = require('jsonwebtoken');

// 演示用密钥（生产环境务必用环境变量 + 强随机字符串，绝不要写死在代码里）
const SECRET = 'dev-secret-please-use-env-in-prod-3f9a7c2e';
const ISSUER = 'day18-demo-issuer';
const AUDIENCE = 'day18-demo-client';

// ============================
// 1. 基础签发与校验
// ============================
function basicSignVerify() {
  console.log('========== 1. 基础签发与校验 ==========\n');

  const payload = {
    sub: 'user-001',          // subject，通常放用户 ID
    role: 'admin',            // 自定义字段
    name: '张三',
  };

  const options = {
    expiresIn: '1h',          // 1 小时后过期
    issuer: ISSUER,           // 签发者
    audience: AUDIENCE,       // 接收方
  };

  // 签发（同步版）
  const token = jwt.sign(payload, SECRET, options);
  console.log('签发的 token:\n', token);

  // 看一下三段式结构
  const parts = token.split('.');
  console.log('\nJWT 三段式结构:');
  console.log('  Header    :', parts[0]);
  console.log('  Payload   :', parts[1]);
  console.log('  Signature :', parts[2]);

  // 校验（同步版）
  const decoded = jwt.verify(token, SECRET, { issuer: ISSUER, audience: AUDIENCE });
  console.log('\n校验成功，解码 payload:');
  console.log(decoded);
  // 注意返回值里会自动带上 iat（签发时间）、exp（过期时间）
  console.log();
}

// ============================
// 2. 解码不验签：jwt.decode
// ============================
function decodeWithoutVerify() {
  console.log('========== 2. jwt.decode（不验签） ==========\n');
  console.log('注意：decode 仅用于“查看 payload 内容”，绝不能用于鉴权！');
  console.log('任何持有 token 的人都能 decode，因此 payload 不要放敏感信息\n');

  const token = jwt.sign({ sub: 'user-002', email: 'a@b.com' }, SECRET, { expiresIn: '30m' });
  const decoded = jwt.decode(token);
  console.log('decode 结果:', decoded);
  console.log();

  // decode 篡改过的 token（只把 payload 替换）—— decode 不会报错，因为不验签
  const tampered = token.split('.').map((p, i) => {
    if (i === 1) {
      // 替换 payload 为 {"sub":"admin","role":"superuser"} 的 base64url
      const newPayload = Buffer.from(JSON.stringify({ sub: 'admin', role: 'superuser' })).toString('base64url');
      return newPayload;
    }
    return p;
  }).join('.');
  console.log('篡改后的 token:', tampered);
  console.log('decode 篡改 token（仍能解码）:', jwt.decode(tampered));
  console.log('verify 篡改 token（必然失败）:');
  try {
    jwt.verify(tampered, SECRET);
  } catch (err) {
    console.log('  → 抛出错误:', err.name, '-', err.message);
  }
  console.log();
}

// ============================
// 3. 过期时间策略
// ============================
function expiresInStrategies() {
  console.log('========== 3. 过期时间设置策略 ==========\n');

  // 字符串方式（常用）
  const t1 = jwt.sign({ sub: 'u1' }, SECRET, { expiresIn: '1h' });        // 1 小时
  const t2 = jwt.sign({ sub: 'u2' }, SECRET, { expiresIn: '7d' });        // 7 天
  const t3 = jwt.sign({ sub: 'u3' }, SECRET, { expiresIn: '30s' });       // 30 秒
  // 数字方式：秒数
  const t4 = jwt.sign({ sub: 'u4' }, SECRET, { expiresIn: 60 * 60 });     // 1 小时 = 3600 秒

  for (const [label, tk] of [['1h', t1], ['7d', t2], ['30s', t3], ['3600(秒)', t4]]) {
    const d = jwt.decode(tk);
    const expDate = new Date(d.exp * 1000).toLocaleString('zh-CN');
    const iatDate = new Date(d.iat * 1000).toLocaleString('zh-CN');
    console.log(`${label.padEnd(10)} → iat: ${iatDate}  exp: ${expDate}  (相差 ${d.exp - d.iat} 秒)`);
  }
  console.log();
}

// ============================
// 4. payload 常用字段演示
// ============================
function payloadFieldsDemo() {
  console.log('========== 4. payload 常用字段 ==========\n');

  // 说明：sub 既可写在 payload 里，也可通过 options.subject 指定；
  //      二者不能同时出现，否则 jsonwebtoken 会抛 "payload already has a sub property"。
  //      这里演示 options 写法（与 payload 写法二选一即可）。
  const token = jwt.sign(
    {
      jti: 'token-uuid-' + Date.now(),              // JWT ID：唯一标识本 token，可用于黑名单
    },
    SECRET,
    {
      expiresIn: '1h',
      issuer: ISSUER,                                // iss：签发者
      audience: AUDIENCE,                            // aud：接收方
      subject: 'user-003',                           // sub：用户唯一标识（等价于 payload.sub）
      notBefore: 0,                                  // nbf：生效时间，0 = 立即生效
    }
  );

  const d = jwt.decode(token);
  console.log('完整 payload 字段说明:');
  console.log('  sub:', d.sub, '          ← subject 用户标识');
  console.log('  iss:', d.iss, '   ← issuer 签发者');
  console.log('  aud:', d.aud, '   ← audience 接收方');
  console.log('  exp:', d.exp, '    ← expiration 过期时间（Unix 秒）');
  console.log('  iat:', d.iat, '    ← issued at 签发时间（Unix 秒）');
  console.log('  nbf:', d.nbf, '    ← not before 生效时间');
  console.log('  jti:', d.jti, '  ← JWT ID 唯一标识');
  console.log();
}

// ============================
// 5. 错误类型演示
// ============================
function errorTypesDemo() {
  console.log('========== 5. 三类错误类型 ==========\n');

  // 5.1 TokenExpiredError：token 已过期
  const expiredToken = jwt.sign({ sub: 'u1' }, SECRET, { expiresIn: '-1s' }); // 已过期
  try {
    jwt.verify(expiredToken, SECRET);
  } catch (err) {
    console.log('① TokenExpiredError');
    console.log('   name:', err.name);
    console.log('   message:', err.message);
    console.log('   expiredAt:', new Date(err.expiredAt).toLocaleString('zh-CN'));
    console.log('   → 处理建议：前端应触发 refresh token 流程，重新获取 access token\n');
  }

  // 5.2 JsonWebTokenError：签名错误 / 格式错误 / payload 不匹配
  const tamperedToken = jwt.sign({ sub: 'u1' }, SECRET) + 'x'; // 篡改签名
  try {
    jwt.verify(tamperedToken, SECRET);
  } catch (err) {
    console.log('② JsonWebTokenError（签名被篡改）');
    console.log('   name:', err.name);
    console.log('   message:', err.message);
    console.log('   → 处理建议：拒绝访问，可能是被中间人篡改，应立即登出\n');
  }

  // issuer / audience 不匹配也属于 JsonWebTokenError
  const tokenWithIss = jwt.sign({ sub: 'u1' }, SECRET, { issuer: 'wrong-issuer' });
  try {
    jwt.verify(tokenWithIss, SECRET, { issuer: ISSUER });
  } catch (err) {
    console.log('③ JsonWebTokenError（issuer 不匹配）');
    console.log('   name:', err.name);
    console.log('   message:', err.message);
    console.log('   → 处理建议：issuer/audience 不符，说明 token 用错了场景\n');
  }

  // 5.3 NotBeforeError：nbf 还没到生效时间
  const futureToken = jwt.sign({ sub: 'u1' }, SECRET, { notBefore: '1h' });
  try {
    jwt.verify(futureToken, SECRET);
  } catch (err) {
    console.log('④ NotBeforeError');
    console.log('   name:', err.name);
    console.log('   message:', err.message);
    console.log('   date:', new Date(err.date).toLocaleString('zh-CN'));
    console.log('   → 处理建议：常用于“预约生效”场景，生产中较少触发\n');
  }
}

// ============================
// 6. 异步版 API
// ============================
async function asyncApiDemo() {
  console.log('========== 6. 异步版 API（生产推荐） ==========\n');

  // 异步版基于回调或 Promise（不传 callback 时返回字符串，
  // 也可手动包装成 Promise 以避免阻塞事件循环——大量并发签发时尤其重要）
  const token = jwt.sign({ sub: 'u1', role: 'user' }, SECRET, { expiresIn: '1h' });

  // 校验：回调写法
  await new Promise((resolve) => {
    jwt.verify(token, SECRET, (err, decoded) => {
      if (err) console.log('校验失败:', err.message);
      else console.log('回调式校验成功:', decoded);
      resolve();
    });
  });
  console.log();
}

// ============================
// 主流程
// ============================
async function main() {
  basicSignVerify();
  decodeWithoutVerify();
  expiresInStrategies();
  payloadFieldsDemo();
  errorTypesDemo();
  await asyncApiDemo();
  console.log('✅ 所有演示完成。');
}

main().catch(console.error);
