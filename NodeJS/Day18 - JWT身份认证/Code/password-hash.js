/**
 * password-hash.js
 * Day18 - JWT 身份认证
 *
 * 演示 bcrypt 的核心 API：
 *  - genSalt(cost)       生成盐
 *  - hash(plain, salt)   对明文密码做哈希
 *  - compare(plain, hash) 校验明文与哈希是否匹配
 *  - cost factor 工作因子对比，直观感受“慢哈希”对爆破的抑制
 *  - 密码强度校验函数
 *
 * 运行：node password-hash.js
 */

const bcrypt = require('bcryptjs');

// ============================
// 1. 基础用法：genSalt + hash + compare
// ============================
function basicUsage() {
  console.log('========== 1. bcrypt 基础用法 ==========\n');

  const plainPassword = 'P@ssw0rd!2024';

  // 1) 生成盐（默认 cost = 10）
  const salt = bcrypt.genSaltSync(10);
  console.log('生成的盐 salt :', salt);
  // 注意：salt 本身就已经包含了算法标识 + cost + 22 位随机盐
  // 例如 $2a$10$N9qo8uLOickgx2ZMRZoMy...
  //      ^^^  ^^  ^^^^^^^^^^^^^^^^^^^^
  //      算法 cost   22 位 base64 盐

  // 2) 用盐哈希密码
  const hashed = bcrypt.hashSync(plainPassword, salt);
  console.log('哈希结果 hash:', hashed);
  // 哈希结果总共 60 字符，自带盐，所以无需单独存盐

  // 3) 校验密码
  const isMatch = bcrypt.compareSync(plainPassword, hashed);
  const isWrong = bcrypt.compareSync('wrong-password', hashed);
  console.log('正确密码校验结果:', isMatch); // true
  console.log('错误密码校验结果:', isWrong); // false
  console.log();
}

// ============================
// 2. cost factor 工作因子对比
// ============================
async function compareCostFactors() {
  console.log('========== 2. cost factor 工作因子对比 ==========');
  console.log('说明：cost 每增加 1，哈希耗时约翻倍，对暴力破解呈指数级抑制\n');

  const password = 'MyStrong#Pwd_2024';
  const costs = [8, 10, 12, 14];

  // 表头
  console.log('| cost | 耗时(ms) | 说明                       |');
  console.log('|------|----------|----------------------------|');

  for (const cost of costs) {
    const start = Date.now();
    const hash = await bcrypt.hash(password, cost);
    const elapsed = Date.now() - start;
    const note = cost <= 8
      ? '测试环境可用'
      : cost <= 10
        ? '默认值，生产推荐'
        : cost <= 12
          ? '敏感账户推荐'
          : '极高安全场景';
    console.log(`| ${String(cost).padStart(4)} | ${String(elapsed).padStart(8)} | ${note.padEnd(26)} |`);
    // 仅校验最后一次确保 compare 仍可用
    if (cost === costs[costs.length - 1]) {
      const ok = await bcrypt.compare(password, hash);
      console.log(`\n最终校验：${ok ? '✓ 匹配' : '✗ 不匹配'}\n`);
    }
  }
}

// ============================
// 3. 同一密码每次哈希结果不同（因为盐随机）
// ============================
function hashIsNotDeterministic() {
  console.log('========== 3. 同一密码每次哈希结果不同 ==========\n');

  const pwd = 'SamePassword!';
  const h1 = bcrypt.hashSync(pwd, 10);
  const h2 = bcrypt.hashSync(pwd, 10);

  console.log('第一次哈希:', h1);
  console.log('第二次哈希:', h2);
  console.log('两次结果是否相同:', h1 === h2); // false，因为盐不同
  console.log('但都能正确校验:');
  console.log('  compare h1:', bcrypt.compareSync(pwd, h1)); // true
  console.log('  compare h2:', bcrypt.compareSync(pwd, h2)); // true
  console.log();
}

// ============================
// 4. 密码强度校验函数
// ============================

/**
 * 校验密码强度
 * 规则：
 *  - 至少 8 位
 *  - 必须包含大写字母
 *  - 必须包含小写字母
 *  - 必须包含数字
 *  - 必须包含特殊字符（!@#$%^&*...）
 * @param {string} password 明文密码
 * @returns {{valid: boolean, score: number, issues: string[]}}
 */
function checkPasswordStrength(password) {
  const issues = [];
  let score = 0;

  if (password.length >= 8) score += 1;
  else issues.push('长度至少 8 位');

  if (password.length >= 12) score += 1; // 额外加分

  if (/[A-Z]/.test(password)) score += 1;
  else issues.push('必须包含大写字母');

  if (/[a-z]/.test(password)) score += 1;
  else issues.push('必须包含小写字母');

  if (/[0-9]/.test(password)) score += 1;
  else issues.push('必须包含数字');

  if (/[!@#$%^&*()_+\-={}\[\]|\\:";'<>?,./~`]/.test(password)) score += 1;
  else issues.push('必须包含特殊字符');

  // 常见弱密码黑名单
  const weakList = ['password', '12345678', 'qwerty', 'abc123', 'iloveyou'];
  if (weakList.some((w) => password.toLowerCase().includes(w))) {
    issues.push('包含常见弱密码片段');
    score -= 1;
  }

  return {
    valid: issues.length === 0 && score >= 4,
    score, // 0-6 分
    issues,
  };
}

function demoStrengthCheck() {
  console.log('========== 4. 密码强度校验 ==========\n');

  const samples = ['123', 'password', 'abcdefg1', 'Abc12345', 'P@ssw0rd!2024', 'qwerty123'];

  for (const pwd of samples) {
    const r = checkPasswordStrength(pwd);
    const bar = '█'.repeat(r.score) + '░'.repeat(6 - r.score);
    console.log(`密码: ${pwd.padEnd(18)} 强度: [${bar}] ${r.score}/6  ${r.valid ? '✓ 通过' : '✗ ' + r.issues.join(', ')}`);
  }
  console.log();
}

// ============================
// 5. 模拟注册流程：强度校验 -> 哈希存储
// ============================
function simulateRegister(password) {
  console.log('========== 5. 模拟注册流程 ==========\n');

  const strength = checkPasswordStrength(password);
  if (!strength.valid) {
    console.log('注册失败：密码强度不足');
    console.log('问题：', strength.issues.join('；'));
    return null;
  }

  // 注意：实际生产用 await bcrypt.hash（异步版），避免阻塞事件循环
  const hashed = bcrypt.hashSync(password, 10);
  console.log('注册成功，存入“数据库”的记录：');
  console.log({ password: hashed, strength: strength.score });
  return hashed;
}

// ============================
// 主流程
// ============================
async function main() {
  basicUsage();
  await compareCostFactors();
  hashIsNotDeterministic();
  demoStrengthCheck();

  console.log('---- 注册“P@ssw0rd!2024” ----');
  const storedHash = simulateRegister('P@ssw0rd!2024');
  if (storedHash) {
    // 模拟登录校验
    const loginOk = bcrypt.compareSync('P@ssw0rd!2024', storedHash);
    const wrongOk = bcrypt.compareSync('WrongPwd!', storedHash);
    console.log('登录校验（正确密码）:', loginOk);
    console.log('登录校验（错误密码）:', wrongOk);
  }

  console.log('\n---- 注册弱密码“123” ----');
  simulateRegister('123');
}

main().catch(console.error);
