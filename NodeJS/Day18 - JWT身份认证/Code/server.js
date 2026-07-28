/**
 * server.js
 * Day18 - JWT 身份认证 —— 完整认证应用
 *
 * 接口清单：
 *   POST   /auth/register     注册（密码 bcrypt 哈希存储）
 *   POST   /auth/login        登录（校验密码，签发 access + refresh）
 *   GET    /auth/me           查看当前用户（需 access token）
 *   POST   /auth/refresh      用 refresh token 换新 access + refresh
 *   POST   /auth/logout       登出（refresh token 拉黑）
 *   GET    /admin/users       管理员接口（需 access token + role=admin）
 *
 * 启动：node server.js
 *
 * ---- 完整 curl 测试命令 ----
 *
 * # 1) 注册普通用户
 * curl -X POST http://localhost:3000/auth/register ^
 *   -H "Content-Type: application/json" ^
 *   -d "{\"username\":\"alice\",\"password\":\"Alice@2024\"}"
 *
 * # 2) 注册管理员
 * curl -X POST http://localhost:3000/auth/register ^
 *   -H "Content-Type: application/json" ^
 *   -d "{\"username\":\"admin\",\"password\":\"Admin@2024\",\"role\":\"admin\"}"
 *
 * # 3) 登录（拿到 accessToken + refreshToken）
 * curl -X POST http://localhost:3000/auth/login ^
 *   -H "Content-Type: application/json" ^
 *   -d "{\"username\":\"alice\",\"password\":\"Alice@2024\"}"
 *
 * # 4) 访问受保护接口（把 <ACCESS_TOKEN> 替换成上一步返回的 accessToken）
 * curl http://localhost:3000/auth/me ^
 *   -H "Authorization: Bearer <ACCESS_TOKEN>"
 *
 * # 5) 不带 token 访问受保护接口 → 401 no_token
 * curl http://localhost:3000/auth/me
 *
 * # 6) 篡改 token → 401 invalid_token
 * curl http://localhost:3000/auth/me ^
 *   -H "Authorization: Bearer aaa.bbb.ccc"
 *
 * # 7) 刷新 token（把 <REFRESH_TOKEN> 替换成登录返回的 refreshToken）
 * curl -X POST http://localhost:3000/auth/refresh ^
 *   -H "Content-Type: application/json" ^
 *   -d "{\"refreshToken\":\"<REFRESH_TOKEN>\"}"
 *
 * # 8) 用旧 refresh token 再次刷新 → 401 refresh_token_revoked（轮转生效）
 * curl -X POST http://localhost:3000/auth/refresh ^
 *   -H "Content-Type: application/json" ^
 *   -d "{\"refreshToken\":\"<REFRESH_TOKEN>\"}"
 *
 * # 9) 登出（拉黑当前 refresh token）
 * curl -X POST http://localhost:3000/auth/logout ^
 *   -H "Content-Type: application/json" ^
 *   -d "{\"refreshToken\":\"<REFRESH_TOKEN>\"}"
 *
 * # 10) 登出后再刷新 → 401 refresh_token_revoked
 * curl -X POST http://localhost:3000/auth/refresh ^
 *   -H "Content-Type: application/json" ^
 *   -d "{\"refreshToken\":\"<REFRESH_TOKEN>\"}"
 *
 * # 11) 普通用户访问管理员接口 → 403 forbidden
 * curl http://localhost:3000/admin/users ^
 *   -H "Authorization: Bearer <ALICE_ACCESS_TOKEN>"
 *
 * # 12) 管理员访问管理员接口 → 200
 * curl http://localhost:3000/admin/users ^
 *   -H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>"
 *
 * # 13) 故意制造一个过期 token（用 jwt.io 把 exp 改成过去时间，
 * #     或在 .env 里把 ACCESS_EXPIRES 改短后重启），
 * #     再访问 /auth/me → 401 token_expired
 *
 * 说明：Windows cmd 用 ^ 续行，PowerShell 用 ` 续行，bash 直接用 \。
 */

const express = require('express');
const { authRequired } = require('./auth-middleware');
const userStore = require('./user-store');
const {
  signAccessToken,
  signRefreshToken,
  verifyRefreshToken,
  revokeRefreshToken,
  revokeByJti,
  refreshTokens,
  blacklistSize,
  ACCESS_EXPIRES,
  REFRESH_EXPIRES,
} = require('./refresh-token');

const app = express();

// ---------- 全局中间件 ----------
app.use(express.json());

// 简易请求日志
app.use((req, _res, next) => {
  console.log(`${new Date().toISOString()}  ${req.method} ${req.url}`);
  next();
});

// ---------- 业务接口 ----------

/**
 * 健康检查
 */
app.get('/health', (_req, res) => {
  res.json({ ok: true, service: 'day18-jwt-auth', time: Date.now() });
});

/**
 * 注册
 * body: { username, password, role? }
 */
app.post('/auth/register', (req, res) => {
  const { username, password, role } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ code: 4000, error: 'bad_request', message: 'username 和 password 必填' });
  }

  const result = userStore.registerUser({ username, password, role });
  if (!result.ok) {
    return res.status(409).json({ code: 4090, error: result.error, message: '注册失败' });
  }

  // 注册成功返回脱敏后的用户信息（不含密码哈希）
  res.status(201).json({
    code: 0,
    message: '注册成功',
    user: result.user,
  });
});

/**
 * 登录
 * body: { username, password }
 * 返回：accessToken（15m）+ refreshToken（7d）
 */
app.post('/auth/login', (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ code: 4000, error: 'bad_request', message: 'username 和 password 必填' });
  }

  const result = userStore.verifyCredential(username, password);
  if (!result.ok) {
    // 401 而不是 404，避免泄漏“用户是否存在”
    return res.status(401).json({ code: 4010, error: result.error, message: '用户名或密码错误' });
  }

  const user = result.user;
  const accessToken = signAccessToken({ sub: user.sub, role: user.role });
  const refresh = signRefreshToken(user.sub);

  res.json({
    code: 0,
    message: '登录成功',
    accessToken,
    refreshToken: refresh.token,
    tokenType: 'Bearer',
    expiresIn: ACCESS_EXPIRES,
    refreshExpiresIn: REFRESH_EXPIRES,
    user: { sub: user.sub, username: user.username, role: user.role },
  });
});

/**
 * 当前用户信息（需 access token）
 */
app.get('/auth/me', authRequired(), (req, res) => {
  const user = userStore.findBySub(req.user.sub);
  if (!user) {
    return res.status(404).json({ code: 4040, error: 'user_not_found' });
  }
  res.json({
    code: 0,
    user,
    token: {
      iat: req.user.iat,
      exp: req.user.exp,
      jti: req.user.jti,
    },
  });
});

/**
 * 刷新 token
 * body: { refreshToken }
 * 流程：校验 → 旧 refresh 拉黑 → 签发新 access + 新 refresh（轮转）
 */
app.post('/auth/refresh', (req, res) => {
  const { refreshToken } = req.body || {};
  if (!refreshToken) {
    return res.status(400).json({ code: 4000, error: 'bad_request', message: 'refreshToken 必填' });
  }

  const userPayloadProvider = (sub) => {
    const u = userStore.findBySub(sub);
    if (!u) return null;
    return { sub: u.sub, role: u.role };
  };

  const result = refreshTokens(refreshToken, userPayloadProvider);
  if (!result.ok) {
    // refresh token 失效属于“未认证”
    return res.status(401).json({ code: 4010, error: result.error, message: '刷新失败，请重新登录' });
  }

  res.json({
    code: 0,
    message: '刷新成功',
    accessToken: result.accessToken,
    refreshToken: result.refreshToken,
    tokenType: 'Bearer',
    expiresIn: ACCESS_EXPIRES,
  });
});

/**
 * 登出
 * body: { refreshToken }
 * 实现：把 refresh token 加入黑名单。
 *      access token 因无状态无法立即失效，需等其自然过期（或客户端删除）。
 *      生产可结合 Redis 黑名单 + 短 access token 来缓解。
 */
app.post('/auth/logout', (req, res) => {
  const { refreshToken } = req.body || {};
  if (!refreshToken) {
    // 没有 refresh token 也算登出（客户端删除即可）
    return res.json({ code: 0, message: '登出成功（无 refresh token）' });
  }
  const revoked = revokeRefreshToken(refreshToken);
  res.json({
    code: 0,
    message: revoked ? '登出成功，refresh token 已撤销' : '登出成功（refresh token 已失效，无需撤销）',
    blacklistSize: blacklistSize(),
  });
});

/**
 * 管理员接口：列出所有用户
 * 演示 authRequired 的角色限制
 */
app.get('/admin/users', authRequired({ roles: ['admin'] }), (_req, res) => {
  res.json({
    code: 0,
    count: userStore.listAll().length,
    users: userStore.listAll(),
  });
});

// ---------- 统一错误处理 ----------

// 404
app.use((_req, res) => {
  res.status(404).json({ code: 4040, error: 'not_found', message: '接口不存在' });
});

// 兜底错误处理
app.use((err, _req, res, _next) => {
  console.error('未处理错误:', err);
  res.status(500).json({ code: 5000, error: 'internal_error', message: err.message });
});

// ---------- 启动 ----------

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`\n🚀 Day18 JWT 认证服务已启动: http://localhost:${PORT}`);
  console.log(`   健康检查: GET  /health`);
  console.log(`   注册:     POST /auth/register  { username, password }`);
  console.log(`   登录:     POST /auth/login     { username, password }`);
  console.log(`   当前用户: GET  /auth/me         Authorization: Bearer <token>`);
  console.log(`   刷新:     POST /auth/refresh    { refreshToken }`);
  console.log(`   登出:     POST /auth/logout     { refreshToken }`);
  console.log(`   管理员:   GET  /admin/users      (需 role=admin)\n`);
});
