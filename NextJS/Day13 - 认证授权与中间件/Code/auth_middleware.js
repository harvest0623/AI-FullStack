// Day13 - auth_middleware.js  认证 + 授权 + 中间件流程演示
// 模拟登录、会话、中间件拦截（未登录重定向）、RBAC 角色判定。
// 离线可运行：node auth_middleware.js

// 模拟会话表
const sessions = new Map();
const users = {
  'admin@ai.com': { pass: 'admin123', role: 'admin' },
  'user@ai.com': { pass: 'user123', role: 'user' },
};

let sessionId = 0;

// 登录：核验 → 生成 session
function login(email, password) {
  const u = users[email];
  if (!u || u.pass !== password) return null;
  const sid = 'sid' + ++sessionId;
  sessions.set(sid, { email, role: u.role });
  return sid;
}

// 中间件：检查是否登录 + 是否授权
function middleware(hasCookie, role, protectedNeedsAdmin = false) {
  console.log('  中间件执行中...');

  if (!hasCookie) {
    return { redirect: '/login', reason: '未登录' };
  }

  if (protectedNeedsAdmin && role !== 'admin') {
    return { redirect: '/403', reason: '权限不足(仅管理员)' };
  }

  return { pass: true };
}

function main() {
  console.log('【认证 + 授权 + 中间件流程演示】\n');

  console.log('① 登录');
  const adminSid = login('admin@ai.com', 'admin123');
  const bad = login('user@ai.com', 'wrong');
  console.log('   admin@ai.com 登录 →', adminSid ? '成功 ✅' : '失败');
  console.log('   user@ai.com 密码错 →', bad ? '成功' : '失败 ❌\n');

  console.log('② 中间件保护 /dashboard（需登录即可）\n');
  const r1 = middleware(sessions.has(adminSid), sessions.get(adminSid)?.role);
  console.log(`   携带 Cookie 访问 → ${JSON.stringify(r1)}\n`);

  const r2 = middleware(false, null);
  console.log(`   无 Cookie 访问   → ${JSON.stringify(r2)}\n`);

  console.log('③ RBAC 管理接口（仅 admin）\n');
  const r3 = middleware(sessions.has(adminSid), sessions.get(adminSid)?.role, true);
  console.log(`   admin 访问管理接口 → ${JSON.stringify(r3)}`);
  const r4 = middleware(true, 'user', true);
  console.log(`   user 已登录访问管理接口 → ${JSON.stringify(r4)}\n`);

  console.log('【要点】');
  console.log('  · 中间件运行在边缘运行时，做顶层拦截/重定向');
  console.log('  · 认证=是谁，授权=能不能；权限判定务必放服务端');
  console.log('  · HttpOnly Cookie + JWT 会话，密钥只存服务端 .env');
}

main();