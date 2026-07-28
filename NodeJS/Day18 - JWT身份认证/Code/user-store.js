/**
 * user-store.js
 * Day18 - JWT 身份认证
 *
 * 内存版用户存储，模拟数据库：
 *  - 注册：密码 bcrypt 哈希后存储
 *  - 登录：bcrypt.compare 校验密码
 *  - 查询：按 username / sub 查找
 *
 * 注意：仅用于学习演示。生产环境必须使用真实数据库（MongoDB / PostgreSQL / MySQL 等），
 *       并对密码字段单独加密、对用户表加索引、对查询做参数化防止 SQL 注入。
 */

const bcrypt = require('bcryptjs');

// 模拟数据库表
// 结构：{ sub, username, passwordHash, role, createdAt }
const users = new Map();

// 自增 ID 生成器
let autoId = 0;
function nextId() {
  autoId += 1;
  return `user-${String(autoId).padStart(4, '0')}`;
}

/**
 * 注册新用户
 * @param {object} param0
 * @returns {{ ok: boolean, user?: object, error?: string }}
 */
function registerUser({ username, password, role = 'user' }) {
  // 用户名唯一性校验
  for (const u of users.values()) {
    if (u.username === username) {
      return { ok: false, error: 'username_already_exists' };
    }
  }

  // 密码强度校验（简单版，生产可用 zxcvbn 等更专业库）
  if (!password || password.length < 8) {
    return { ok: false, error: 'password_too_short' };
  }
  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
    return { ok: false, error: 'password_too_weak' };
  }

  // bcrypt 哈希（异步版推荐，避免阻塞事件循环；这里用 hashSync 简化演示）
  const passwordHash = bcrypt.hashSync(password, 10);

  const user = {
    sub: nextId(),
    username,
    passwordHash,
    role,
    createdAt: new Date().toISOString(),
  };

  users.set(user.sub, user);
  return { ok: true, user };
}

/**
 * 校验密码并返回用户（不含 passwordHash）
 * @param {string} username
 * @param {string} password
 * @returns {{ ok: boolean, user?: object, error?: string }}
 */
function verifyCredential(username, password) {
  let found = null;
  for (const u of users.values()) {
    if (u.username === username) {
      found = u;
      break;
    }
  }

  // 即使找不到用户也走一次 compare，避免“用户不存在”比“密码错误”返回更快的时序侧信道
  // 这里用假哈希兜底
  const dummyHash = '$2a$10$CwTycUXWue0Thq9StjUM0uJ8.7gM8V2gK3oXzS5Z8e2bQj2fM1yWq';
  const targetHash = found ? found.passwordHash : dummyHash;
  const isMatch = bcrypt.compareSync(password, targetHash);

  if (!found || !isMatch) {
    return { ok: false, error: 'invalid_username_or_password' };
  }

  // 返回时去掉 passwordHash，避免泄漏
  const { passwordHash, ...safe } = found;
  return { ok: true, user: safe };
}

/**
 * 按 sub 查询用户（不含 passwordHash）
 */
function findBySub(sub) {
  const u = users.get(sub);
  if (!u) return null;
  const { passwordHash, ...safe } = u;
  return safe;
}

/**
 * 调试用：列出所有用户（不含密码哈希）
 */
function listAll() {
  return Array.from(users.values()).map((u) => {
    const { passwordHash, ...safe } = u;
    return safe;
  });
}

/**
 * 调试用：重置存储（测试时使用）
 */
function reset() {
  users.clear();
  autoId = 0;
}

module.exports = {
  registerUser,
  verifyCredential,
  findBySub,
  listAll,
  reset,
};
