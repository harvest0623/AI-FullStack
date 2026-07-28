/**
 * refresh-token.js
 * Day18 - JWT 身份认证
 *
 * 双 Token 机制：
 *  - access token：短期（默认 15 分钟），用于访问 API
 *  - refresh token：长期（默认 7 天），仅用于换新 access token，不直接访问业务 API
 *
 * 设计要点：
 *  1. access token 短期 → 即使泄露，攻击窗口小
 *  2. refresh token 长期 → 用户不必频繁登录
 *  3. refresh token 也能撤销（黑名单/白名单），用于“登出”或“踢人下线”
 *  4. refresh token 携带 jti（唯一 ID），黑名单存 jti 即可
 *
 * 本模块导出工具函数，供 server.js 调用。
 */

const crypto = require('crypto');
const jwt = require('jsonwebtoken');

// 实际项目务必用环境变量
const ACCESS_SECRET = process.env.JWT_ACCESS_SECRET || 'dev-access-secret-replace-in-prod';
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'dev-refresh-secret-replace-in-prod-xx-9a';
const ISSUER = process.env.JWT_ISSUER || 'day18-demo-issuer';
const AUDIENCE = process.env.JWT_AUDIENCE || 'day18-demo-client';

const ACCESS_EXPIRES = '15m';   // 15 分钟
const REFRESH_EXPIRES = '7d';   // 7 天

// refresh token 黑名单（存 jti）
// 生产环境用 Redis + 过期时间，避免内存膨胀
const refreshBlacklist = new Set();

/**
 * 生成随机 jti（JWT ID）
 */
function generateJti() {
  return crypto.randomBytes(16).toString('hex');
}

/**
 * 签发 access token
 * @param {{ sub: string, role: string }} payload
 */
function signAccessToken(payload) {
  return jwt.sign(payload, ACCESS_SECRET, {
    expiresIn: ACCESS_EXPIRES,
    issuer: ISSUER,
    audience: AUDIENCE,
  });
}

/**
 * 签发 refresh token
 * refresh token 的 payload 极简：只放 sub + jti
 * 不要把 role 等业务字段放进 refresh token（避免刷新时“提升权限”的幻觉）
 */
function signRefreshToken(sub) {
  const jti = generateJti();
  return {
    token: jwt.sign({ sub, jti }, REFRESH_SECRET, {
      expiresIn: REFRESH_EXPIRES,
      issuer: ISSUER,
      audience: AUDIENCE,
    }),
    jti,
  };
}

/**
 * 校验 refresh token
 *  - 签名、过期、iss/aud
 *  - 不在黑名单
 * @returns {{ ok: boolean, sub?: string, jti?: string, error?: string }}
 */
function verifyRefreshToken(token) {
  try {
    const decoded = jwt.verify(token, REFRESH_SECRET, { issuer: ISSUER, audience: AUDIENCE });
    if (refreshBlacklist.has(decoded.jti)) {
      return { ok: false, error: 'refresh_token_revoked' };
    }
    return { ok: true, sub: decoded.sub, jti: decoded.jti };
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return { ok: false, error: 'refresh_token_expired' };
    }
    return { ok: false, error: 'invalid_refresh_token' };
  }
}

/**
 * 把 refresh token 拉黑（登出 / 刷新轮转时调用）
 */
function revokeRefreshToken(token) {
  try {
    const decoded = jwt.verify(token, REFRESH_SECRET, { issuer: ISSUER, audience: AUDIENCE });
    refreshBlacklist.add(decoded.jti);
    return true;
  } catch (err) {
    // 已过期或非法的 token，无需加入黑名单
    return false;
  }
}

/**
 * 直接通过 jti 拉黑（不验签，用于已知 jti 的场景）
 */
function revokeByJti(jti) {
  if (jti) refreshBlacklist.add(jti);
}

/**
 * 刷新流程：
 *  1. 校验 refresh token
 *  2. （推荐）refresh token 轮转：旧的拉黑，签发新的 refresh token
 *  3. 签发新的 access token
 *
 * @returns {{ ok: boolean, accessToken?: string, refreshToken?: string, error?: string }}
 */
function refreshTokens(oldRefreshToken, userPayloadProvider) {
  // userPayloadProvider: (sub) => { sub, role } | null
  const result = verifyRefreshToken(oldRefreshToken);
  if (!result.ok) {
    return { ok: false, error: result.error };
  }

  const userPayload = userPayloadProvider(result.sub);
  if (!userPayload) {
    return { ok: false, error: 'user_not_found' };
  }

  // 关键：refresh token 轮转（rotation）—— 旧的拉黑，发新的
  // 这样即使 refresh token 被窃取并使用，原持有者下次刷新会失败并察觉
  revokeByJti(result.jti);

  const accessToken = signAccessToken(userPayload);
  const refresh = signRefreshToken(result.sub);

  return {
    ok: true,
    accessToken,
    refreshToken: refresh.token,
    refreshJti: refresh.jti,
  };
}

/**
 * 调试用：当前黑名单大小
 */
function blacklistSize() {
  return refreshBlacklist.size;
}

module.exports = {
  ACCESS_EXPIRES,
  REFRESH_EXPIRES,
  signAccessToken,
  signRefreshToken,
  verifyRefreshToken,
  revokeRefreshToken,
  revokeByJti,
  refreshTokens,
  blacklistSize,
};
