/**
 * auth-middleware.js
 * Day18 - JWT 身份认证
 *
 * 可复用的 Express JWT 中间件：
 *  - 从 Authorization: Bearer <token> 头部读取 token
 *  - 校验签名、过期时间、issuer / audience
 *  - 成功时把 payload 挂到 req.user
 *  - 失败时根据错误类型返回 401（未认证）/ 403（未生效）
 *
 * 用法：
 *   const { authRequired, authOptional } = require('./auth-middleware');
 *   router.get('/profile', authRequired, handler);
 */

const jwt = require('jsonwebtoken');

// 从环境变量读取，缺失时给开发兜底（生产必须设置）
const ACCESS_SECRET = process.env.JWT_ACCESS_SECRET || 'dev-access-secret-replace-in-prod';
const ISSUER = process.env.JWT_ISSUER || 'day18-demo-issuer';
const AUDIENCE = process.env.JWT_AUDIENCE || 'day18-demo-client';

/**
 * 统一从请求里提取 Bearer token
 * 支持两种位置（按需选用，本中间件默认只认 Authorization 头）：
 *   - Authorization: Bearer <token>  （推荐，跨域友好）
 *   - ?token=xxx                      （仅用于 SSE / WebSocket 等无法设头场景，不在默认实现内）
 */
function extractBearerToken(req) {
  const header = req.headers['authorization'] || req.headers['Authorization'];
  if (!header) return null;

  // 严格匹配 "Bearer <token>"
  const parts = header.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    return null;
  }
  return parts[1];
}

/**
 * 把 JWT 错误转成统一响应
 *  - TokenExpiredError  → 401，提示需要刷新
 *  - NotBeforeError     → 403，token 还未生效
 *  - JsonWebTokenError  → 401，签名无效/格式错误
 */
function handleJwtError(err, res) {
  if (err.name === 'TokenExpiredError') {
    return res.status(401).json({
      code: 4011,
      error: 'token_expired',
      message: 'access token 已过期，请使用 refresh token 重新获取',
      expiredAt: err.expiredAt,
    });
  }
  if (err.name === 'NotBeforeError') {
    return res.status(403).json({
      code: 4031,
      error: 'token_not_active',
      message: 'token 尚未生效',
      date: err.date,
    });
  }
  // 其余一律视为非法 token
  return res.status(401).json({
    code: 4010,
    error: 'invalid_token',
    message: 'token 无效或被篡改',
  });
}

/**
 * 强制鉴权中间件：必须携带合法 token，否则 401
 * @param {object} opts
 * @param {string[]} opts.roles  可选，要求用户必须具备的角色之一
 */
function authRequired(opts = {}) {
  return function (req, res, next) {
    const token = extractBearerToken(req);
    if (!token) {
      return res.status(401).json({
        code: 4010,
        error: 'no_token',
        message: '请求未携带 Authorization: Bearer <token>',
      });
    }

    jwt.verify(token, ACCESS_SECRET, { issuer: ISSUER, audience: AUDIENCE }, (err, decoded) => {
      if (err) return handleJwtError(err, res);

      // 挂载用户信息，后续 handler 可通过 req.user 访问
      req.user = {
        sub: decoded.sub,
        role: decoded.role,
        jti: decoded.jti, // token id，用于黑名单检查
        iat: decoded.iat,
        exp: decoded.exp,
        raw: decoded,
      };

      // 角色校验
      if (opts.roles && opts.roles.length > 0) {
        if (!opts.roles.includes(decoded.role)) {
          return res.status(403).json({
            code: 4030,
            error: 'forbidden',
            message: `权限不足，需要角色: ${opts.roles.join(' / ')}`,
          });
        }
      }

      next();
    });
  };
}

/**
 * 可选鉴权中间件：带了 token 就解析挂 req.user，没带或失败也不报错
 * 典型场景：公开列表接口，登录用户可见额外字段
 */
function authOptional() {
  return function (req, res, next) {
    const token = extractBearerToken(req);
    if (!token) return next();

    jwt.verify(token, ACCESS_SECRET, { issuer: ISSUER, audience: AUDIENCE }, (err, decoded) => {
      if (err) {
        // 可选鉴权下，token 失效不阻断请求，只是 req.user 为空
        req.user = null;
        return next();
      }
      req.user = {
        sub: decoded.sub,
        role: decoded.role,
        jti: decoded.jti,
        iat: decoded.iat,
        exp: decoded.exp,
        raw: decoded,
      };
      next();
    });
  };
}

/**
 * 暴露签发 access token 的工具函数（给 server.js / refresh-token.js 复用）
 */
function signAccessToken(payload, expiresIn = '15m') {
  return jwt.sign(payload, ACCESS_SECRET, {
    expiresIn,
    issuer: ISSUER,
    audience: AUDIENCE,
  });
}

module.exports = {
  ACCESS_SECRET,
  ISSUER,
  AUDIENCE,
  authRequired,
  authOptional,
  extractBearerToken,
  signAccessToken,
  handleJwtError,
};
